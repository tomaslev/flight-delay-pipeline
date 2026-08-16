"""
data.py — DST Airlines Dashboard Data Layer
Fetches from FastAPI first, falls back to mock data if API unavailable.
"""
import os
import requests
import pandas as pd
import numpy as np
from functools import lru_cache

API_URL  = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT  = 5  # seconds

np.random.seed(42)

AIRLINES = [
    "American Airlines", "Delta Air Lines", "United Airlines",
    "Southwest Airlines", "JetBlue Airways", "Alaska Airlines",
]
AIRPORTS = {
    "JFK": "New York",    "LAX": "Los Angeles", "ORD": "Chicago",
    "ATL": "Atlanta",     "DFW": "Dallas",       "DEN": "Denver",
    "SFO": "San Francisco","SEA": "Seattle",      "MIA": "Miami",
    "BOS": "Boston",
}
DELAY_CAUSES = [
    "CarrierDelay", "WeatherDelay", "NASDelay",
    "SecurityDelay", "LateAircraftDelay",
]


# ── API helpers ────────────────────────────────────────────────────────────
def _api_get(path: str, params: dict = None) -> dict | None:
    try:
        resp = requests.get(f"{API_URL}{path}", params=params, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def api_healthy() -> bool:
    result = _api_get("/")
    return result is not None and result.get("status") == "ok"


# ── Mock data (fallback) ──────────────────────────────────────────────────
def _make_mock_flights(n: int = 2000) -> pd.DataFrame:
    origins = np.random.choice(list(AIRPORTS.keys()), n)
    dests   = np.random.choice(list(AIRPORTS.keys()), n)
    same = origins == dests
    dests[same] = np.roll(list(AIRPORTS.keys()), 1)[np.where(same)[0] % 10]

    dates     = pd.date_range("2024-01-01", "2024-12-31", periods=n)
    dep_delay = np.round(np.random.exponential(18, n) - 5, 1)
    arr_delay = dep_delay + np.random.normal(0, 5, n)

    df = pd.DataFrame({
        "FlightDate":        dates,
        "Operating_Airline": np.random.choice(AIRLINES, n),
        "Origin":            origins,
        "Dest":              dests,
        "OriginCity":        [AIRPORTS[o] for o in origins],
        "DestCity":          [AIRPORTS[d] for d in dests],
        "Distance":          np.random.randint(200, 3000, n),
        "DepDelay":          np.clip(dep_delay, -30, 300),
        "ArrDelay":          np.clip(arr_delay, -60, 300),
        "Delayed":           (dep_delay > 15).astype(int),
        "CarrierDelay":      np.clip(np.random.exponential(5, n), 0, 120),
        "WeatherDelay":      np.clip(np.random.exponential(3, n), 0, 90),
        "NASDelay":          np.clip(np.random.exponential(4, n), 0, 100),
        "SecurityDelay":     np.clip(np.random.exponential(1, n), 0, 30),
        "LateAircraftDelay": np.clip(np.random.exponential(6, n), 0, 150),
    })
    df["Month"]      = df["FlightDate"].dt.month
    df["DayOfWeek"]  = df["FlightDate"].dt.day_name()
    return df


_MOCK_DF: pd.DataFrame = _make_mock_flights()


# ── Public API ─────────────────────────────────────────────────────────────
def get_flights_df(airline: str = "ALL", months: list = None) -> pd.DataFrame:
    """
    Try to fetch from real API. Fall back to mock data if unavailable.
    Returns a DataFrame with standardised columns.
    """
    months = months or [1, 12]

    data = _api_get("/flights/stats")
    if data and data.get("data"):
        df = pd.DataFrame(data["data"])
        # Normalise column names to match mock schema
        rename = {
            "operating_airline": "Operating_Airline",
            "origin": "Origin", "dest": "Dest",
            "total_flights": "total_flights",
            "avg_dep_delay": "DepDelay",
            "delay_rate_pct": "delay_rate",
            "avg_carrier_delay": "CarrierDelay",
            "avg_weather_delay": "WeatherDelay",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        df["Delayed"]  = (df.get("delay_rate", 0) > 15).astype(int)
        df["Month"]    = 6  # default mid-year for API data
        df["DayOfWeek"] = "Monday"
        df["NASDelay"]          = 0
        df["SecurityDelay"]     = 0
        df["LateAircraftDelay"] = 0
        df["OriginCity"] = df.get("Origin", "")
        df["DestCity"]   = df.get("Dest", "")
        df["Distance"]   = df.get("avg_distance", 1000)
        df["ArrDelay"]   = df.get("DepDelay", 0)
        df["FlightDate"] = pd.Timestamp("2024-06-01")
        return df

    # Fallback: mock data with filters applied
    df = _MOCK_DF.copy()
    if airline != "ALL":
        df = df[df["Operating_Airline"] == airline]
    df = df[df["Month"].between(months[0], months[1])]
    return df


def get_summary_stats() -> dict:
    data = _api_get("/flights/stats")
    if data and data.get("data"):
        rows = data["data"]
        total  = sum(r.get("total_flights", 0) for r in rows)
        delayed = sum(r.get("delayed_count", 0) for r in rows)
        return {
            "total_flights":   total,
            "delayed_flights": delayed,
            "delay_rate":      round(delayed / total * 100, 1) if total else 0,
            "avg_dep_delay":   round(
                sum(r.get("avg_dep_delay", 0) or 0 for r in rows) / len(rows), 1
            ) if rows else 0,
            "airlines": len({r["operating_airline"] for r in rows
                             if "operating_airline" in r}),
            "routes":   len(rows),
            "source":   "api",
        }

    # Fallback
    df = _MOCK_DF
    return {
        "total_flights":   len(df),
        "delayed_flights": int(df["Delayed"].sum()),
        "delay_rate":      round(df["Delayed"].mean() * 100, 1),
        "avg_dep_delay":   round(df[df["DepDelay"] > 0]["DepDelay"].mean(), 1),
        "airlines":        df["Operating_Airline"].nunique(),
        "routes":          df.groupby(["Origin", "Dest"]).ngroups,
        "source":          "mock",
    }


def get_live_flights() -> list:
    data = _api_get("/live", params={"limit": 50})
    if data and data.get("data"):
        return data["data"]
    return []


def get_graph_data() -> dict:
    data = _api_get("/routes/graph", params={"limit": 100})
    if data:
        return data
    return {"nodes": [], "edges": []}
