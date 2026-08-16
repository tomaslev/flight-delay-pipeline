"""
collector.py — DST Airlines Data Collector
Step 1: Collects flight data from Kaggle CSV + enriches with OpenSky API (free, no key needed)

Usage:
    python collector.py --source kaggle --file kaggle_flights_clean.csv
    python collector.py --source opensky --limit 500
    python collector.py --source both --file kaggle_flights_clean.csv
"""

import requests
import pandas as pd
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("collector.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)

OUTPUT_DIR = Path("collected_data")
OUTPUT_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# Base Collector
# ═══════════════════════════════════════════════════════════════════════════
class BaseCollector:
    """Abstract base — all collectors inherit from this."""

    def collect(self) -> pd.DataFrame:
        raise NotImplementedError

    def save(self, df: pd.DataFrame, filename: str) -> Path:
        path = OUTPUT_DIR / filename
        df.to_csv(path, index=False)
        log.info(f"✅ Saved {len(df):,} rows → {path}")
        return path

    def summary(self, df: pd.DataFrame) -> dict:
        return {
            "rows": len(df),
            "columns": list(df.columns),
            "collected_at": datetime.utcnow().isoformat(),
            "nulls": df.isnull().sum().to_dict(),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Kaggle CSV Collector
# ═══════════════════════════════════════════════════════════════════════════
class KaggleCollector(BaseCollector):
    """
    Reads the Kaggle flight delay CSV and standardises column names.
    CSV source: https://www.kaggle.com/datasets/shubhamsingh42/flight-delay-dataset-2018-2024
    """

    # Columns we actually need — drop the rest
    KEEP_COLS = [
        "FlightDate", "Operating_Airline", "Tail_Number",
        "Flight_Number_Operating_Airline",
        "Origin", "OriginCityName", "OriginAirportID",
        "Dest", "DestCityName", "DestAirportID",
        "DepDelay", "DepDel15", "ArrDelay", "ArrDel15",
        "Cancelled", "Diverted",
        "Distance", "DistanceGroup",
        "CarrierDelay", "WeatherDelay", "NASDelay",
        "SecurityDelay", "LateAircraftDelay",
    ]

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

    def collect(self) -> pd.DataFrame:
        log.info(f"📂 Reading Kaggle CSV: {self.csv_path}")
        df = pd.read_csv(self.csv_path, low_memory=False)
        log.info(f"   Raw shape: {df.shape}")

        # Normalise column names (lowercase from DB, TitleCase from raw CSV)
        df.columns = [c.strip() for c in df.columns]

        # Keep only available columns from our list
        available = [c for c in self.KEEP_COLS if c in df.columns]
        # Also try lowercase versions
        col_map = {c.lower(): c for c in df.columns}
        for wanted in self.KEEP_COLS:
            if wanted not in available and wanted.lower() in col_map:
                df.rename(columns={col_map[wanted.lower()]: wanted}, inplace=True)
                available.append(wanted)

        df = df[[c for c in self.KEEP_COLS if c in df.columns]].copy()

        # Clean
        df = df[df["Cancelled"] == False].copy() if "Cancelled" in df.columns else df
        df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors="coerce")
        df.dropna(subset=["FlightDate", "Origin", "Dest"], inplace=True)

        log.info(f"   Clean shape: {df.shape}")
        return df


# ═══════════════════════════════════════════════════════════════════════════
# OpenSky API Collector (free, no key needed)
# ═══════════════════════════════════════════════════════════════════════════
class OpenSkyCollector(BaseCollector):
    """
    Fetches live/recent flight states from OpenSky Network (free, no API key).
    Docs: https://openskynetwork.github.io/opensky-api/rest.html
    """

    BASE_URL = "https://opensky-network.org/api"
    RATE_LIMIT_SLEEP = 10  # seconds between requests (anonymous limit)

    def __init__(self, limit: int = 500):
        self.limit = limit

    def _get_states(self) -> dict | None:
        """GET /states/all — returns all current flight states."""
        url = f"{self.BASE_URL}/states/all"
        try:
            log.info("🌐 Calling OpenSky /states/all ...")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            log.error(f"OpenSky request failed: {e}")
            return None

    def _get_arrivals(self, airport: str, hours_back: int = 2) -> list:
        """GET /flights/arrival — arrivals for a given airport."""
        end   = int(time.time())
        begin = end - (hours_back * 3600)
        url   = f"{self.BASE_URL}/flights/arrival"
        params = {"airport": airport, "begin": begin, "end": end}
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            log.warning(f"Arrival fetch failed for {airport}: {e}")
            return []

    def collect(self) -> pd.DataFrame:
        data = self._get_states()
        if not data or "states" not in data:
            log.warning("No OpenSky data — using sample fallback")
            return self._fallback_sample()

        cols = [
            "icao24", "callsign", "origin_country", "time_position",
            "last_contact", "longitude", "latitude", "baro_altitude",
            "on_ground", "velocity", "true_track", "vertical_rate",
            "sensors", "geo_altitude", "squawk", "spi", "position_source",
        ]
        rows = data["states"][:self.limit]
        df = pd.DataFrame(rows, columns=cols[:len(rows[0])] if rows else cols)

        # Keep only airborne flights with position
        df = df[df["on_ground"] == False].copy()
        df = df.dropna(subset=["latitude", "longitude", "callsign"])
        df["callsign"] = df["callsign"].str.strip()
        df["collected_at"] = datetime.utcnow().isoformat()

        log.info(f"   OpenSky: {len(df):,} airborne flights")
        return df

    def _fallback_sample(self) -> pd.DataFrame:
        """Return a tiny synthetic sample when API is unavailable."""
        return pd.DataFrame({
            "icao24": ["abc123", "def456"],
            "callsign": ["DLH123", "UAL456"],
            "origin_country": ["Germany", "United States"],
            "longitude": [8.56, -73.78],
            "latitude":  [50.03,  40.63],
            "baro_altitude": [10600, 11200],
            "on_ground": [False, False],
            "velocity":  [240.0, 260.0],
            "collected_at": [datetime.utcnow().isoformat()] * 2,
        })


# ═══════════════════════════════════════════════════════════════════════════
# IATA Code Scraper (static reference data)
# ═══════════════════════════════════════════════════════════════════════════
class IATAScraper:
    """
    Builds a local IATA→Airport mapping from the Kaggle data itself.
    In a real setup you'd scrape https://www.iata.org/en/publications/directories/code-search/
    but that requires login — so we extract from the CSV instead.
    """

    def extract_from_df(self, df: pd.DataFrame) -> pd.DataFrame:
        origins = df[["Origin", "OriginCityName", "OriginAirportID"]].rename(
            columns={"Origin": "iata", "OriginCityName": "city", "OriginAirportID": "airport_id"}
        )
        dests = df[["Dest", "DestCityName", "DestAirportID"]].rename(
            columns={"Dest": "iata", "DestCityName": "city", "DestAirportID": "airport_id"}
        )
        airports = pd.concat([origins, dests]).drop_duplicates(subset=["iata"])
        airports["country"] = "United States"  # Kaggle dataset is US domestic
        log.info(f"   IATA codes extracted: {len(airports)}")
        return airports.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Main orchestrator
# ═══════════════════════════════════════════════════════════════════════════
class DataPipeline:
    """Orchestrates collection, saves outputs, writes summary report."""

    def __init__(self, source: str, csv_path: str = None, limit: int = 500):
        self.source   = source
        self.csv_path = csv_path
        self.limit    = limit
        self.report   = {}

    def run(self):
        log.info("=" * 60)
        log.info("DST Airlines — Data Collection Pipeline")
        log.info(f"Source: {self.source} | Time: {datetime.utcnow().isoformat()}")
        log.info("=" * 60)

        # ── Kaggle ──────────────────────────────────────────────────────
        if self.source in ("kaggle", "both"):
            if not self.csv_path:
                log.error("--file required for kaggle source")
                return
            collector = KaggleCollector(self.csv_path)
            df_flights = collector.collect()
            collector.save(df_flights, "flights_clean.csv")
            self.report["flights"] = collector.summary(df_flights)

            # Extract IATA codes
            iata = IATAScraper().extract_from_df(df_flights)
            iata.to_csv(OUTPUT_DIR / "airports_iata.csv", index=False)
            self.report["airports"] = {"rows": len(iata)}
            log.info(f"✅ Kaggle collection done — {len(df_flights):,} flights")

        # ── OpenSky ─────────────────────────────────────────────────────
        if self.source in ("opensky", "both"):
            collector = OpenSkyCollector(limit=self.limit)
            df_live = collector.collect()
            collector.save(df_live, "live_flights.csv")
            self.report["live_flights"] = collector.summary(df_live)
            log.info(f"✅ OpenSky collection done — {len(df_live):,} live flights")

        # ── Save report ─────────────────────────────────────────────────
        report_path = OUTPUT_DIR / "collection_report.json"
        with open(report_path, "w") as f:
            json.dump(self.report, f, indent=2, default=str)
        log.info(f"📄 Report saved → {report_path}")
        log.info("=" * 60)
        log.info("Collection complete ✅")


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DST Airlines Data Collector")
    parser.add_argument("--source", choices=["kaggle", "opensky", "both"],
                        default="opensky", help="Data source")
    parser.add_argument("--file", default=None,
                        help="Path to Kaggle CSV (required for kaggle/both)")
    parser.add_argument("--limit", type=int, default=500,
                        help="Max rows from OpenSky")
    args = parser.parse_args()

    pipeline = DataPipeline(source=args.source, csv_path=args.file, limit=args.limit)
    pipeline.run()
