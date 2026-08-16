# 🚀 Dashboard Setup Guide — DST Airlines

> Complete guide to run the full project on your machine

---

## Requirements

- Docker Desktop installed and running
- 8 GB RAM minimum
- 5 GB free disk space
- The CSV file: `flight_data_2018_2024.csv` (281 MB — download from Kaggle)

---

## Architecture Note

The dashboard communicates with the database through FastAPI endpoints rather than direct PostgreSQL connections. This ensures:
- Clean separation of concerns
- Automatic fallback to mock data if API is unavailable
- Production-ready foundation for authentication and scaling

---

## Option 1 — Full Project with Docker (Recommended)

### Step 1 — Clone and Start

```bash
git clone https://github.com/DataScientest-Studio/FEB26-BDE-AIRLINES
cd FEB26-BDE-AIRLINES
docker-compose up -d
```

This starts all 7 containers automatically:

| Container | Port | Purpose |
|-----------|------|---------|
| `pg_airlines` | 5432 | PostgreSQL — stores all flight data |
| `pgadmin_airlines` | 5050 | pgAdmin — PostgreSQL web interface |
| `mongo_airlines` | 27017 | MongoDB — live flight data |
| `mongo_express_airlines` | 8081 | Mongo Express — MongoDB web interface |
| `neo4j_airlines` | 7474/7687 | Neo4j — airport route graph |
| `airlines_api` | 8000 | FastAPI — REST API |
| `airlines_dashboard` | 8050 | Dash — main dashboard |

### Step 2 — Load Flight Data into PostgreSQL

Copy the CSV file into the dashboard container and run the loader:

```bash
docker cp flight_data_2018_2024.csv airlines_dashboard:/app/flight_data_2018_2024.csv
docker cp dashboard/train_models.py airlines_dashboard:/app/train_models.py
```

Create a file called `load_data.py` with this content:

```python
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('/app/flight_data_2018_2024.csv',
    usecols=['FlightDate','Operating_Airline ','Origin','OriginCityName',
             'Dest','DestCityName','OriginAirportID','DestAirportID',
             'DepDelay','DepDel15','ArrDelay','ArrDel15',
             'Cancelled','Diverted','Distance','DistanceGroup',
             'CarrierDelay','WeatherDelay','NASDelay',
             'SecurityDelay','LateAircraftDelay'], low_memory=False)
df = df.rename(columns={'Operating_Airline ': 'Operating_Airline'})
df = df[df['Cancelled'] != 1.0]
for col in ['DepDel15','ArrDel15','Cancelled','Diverted']:
    df[col] = df[col].fillna(0).astype(bool)
df.columns = [c.lower() for c in df.columns]
engine = create_engine('postgresql+psycopg2://airlines:liora@db:5432/airlines_db')
df.to_sql('flights', engine, schema='bronze', if_exists='append', index=False, chunksize=1000)
print('Done!')
```

Then run it:
```bash
docker cp load_data.py airlines_dashboard:/app/load_data.py
docker exec -d airlines_dashboard python3 /app/load_data.py
```

Wait 10 minutes, then verify:
```bash
docker exec -i pg_airlines psql -U airlines -d airlines_db -c "SELECT COUNT(*) FROM bronze.flights;"
# Should show: 560352
```

### Step 3 — Load Neo4j Route Graph

```bash
docker cp load_neo4j.py airlines_dashboard:/app/load_neo4j.py
docker exec airlines_dashboard pip install neo4j
docker exec airlines_dashboard python3 /app/load_neo4j.py
# Result: 346 airports + 5,167 routes loaded ✅
```

### Step 4 — Train the ML Models

```bash
docker exec airlines_dashboard pip install scikit-learn
docker exec airlines_dashboard python3 /app/train_models.py
# Result: Classification + Regression models saved to /app/models.pkl ✅
```

### Step 5 — Open the Dashboard

```
Dashboard     → http://localhost:8050
API Docs      → http://localhost:8000/docs
pgAdmin       → http://localhost:5050  (admin@airlines.com / airlines123)
Mongo Express → http://localhost:8081
Neo4j Browser → http://localhost:7474  (neo4j / airlines123)
```

---

## Option 2 — Run Dashboard Locally (without Docker)

### Step 1 — Install Requirements

```bash
pip install dash==2.17.0 plotly==5.22.0 dash-bootstrap-components==1.6.0 \
            pandas==2.2.2 numpy==1.26.4 sqlalchemy==2.0.30 psycopg2-binary==2.9.9 \
            requests==2.32.0 scikit-learn neo4j
```

### Step 2 — Set Environment Variables

```bash
# Linux / Mac
export API_URL="http://localhost:8000"

# Windows (PowerShell)
$env:API_URL="http://localhost:8000"
```

### Step 3 — Run

```bash
cd dashboard/
python app.py
# Open: http://localhost:8050
```

> **Note:** Without API access, the dashboard uses 2,000 mock flights automatically.

---

## Dashboard Pages Explained

### 1. Overview
The main summary page. Shows:
- **6 KPI cards** at the top: total flights, delayed flights, delay rate, avg delay, number of airlines, number of routes
- **Monthly Delay Trend**: line chart (avg delay) + bar chart (delayed count) per month
- **Avg Delay by Day of Week**: which day has the worst delays (usually Tuesday)
- **Departure Delay Distribution**: histogram showing how long delays usually are
- **Top 10 Most Delayed Routes**: horizontal bar chart with exact minutes

### 2. Airlines
Compares all airlines side by side:
- **Delay Rate by Airline**: sorted bar chart with color gradient (green=good, red=bad)
- **Delay Causes by Airline**: stacked bar showing the 5 delay causes:
  - 🟠 Late Aircraft (most common — previous flight was late)
  - 🩵 Carrier (airline's own fault)
  - 🔵 Weather
  - 🟣 NAS (National Airspace System)
  - 🟢 Security

### 3. Routes
Spatial analysis of delays:
- **Route Delay Heatmap**: top 20 busiest airports on X and Y axes. Brighter color = higher delay. Hover to see exact minutes
- **Busiest Routes Bubble Chart**: each bubble is one route. X = avg delay, Y = total flights, bubble size = delay rate %

### 4. Trends
Detailed time analysis:
- **Monthly Delay Trend**: same as Overview but bigger and more detailed
- **Top 10 Most Delayed Routes**: shows exact average delay in minutes. Some routes exceed 200+ minutes!

### 5. ⚡ Flight Risk Analyzer
The most advanced page — combines everything:
1. Select Airline → Origin airports filter automatically
2. Select Origin → Destination airports filter automatically
3. Select Day of Week
4. Live weather fetched automatically from **Open-Meteo API** (no key needed)
5. Click **Analyze Flight Risk**
6. The ML model (trained on 100,000 real flights) returns:
   - Risk level: **LOW / MEDIUM / HIGH**
   - Delay probability percentage
   - Expected delay in minutes
   - Gauge chart visualization
   - 4 stats cards: route delay rate, day delay rate, airline delay rate, avg delay

### 6. 🗺️ Airport Delay Map
Interactive US map powered by Plotly Geo:
- Each dot = one US airport
- **Dot size** = total departing flights (bigger = busier)
- **Dot color** = delay rate (green=low, yellow=medium, red=high)
- Hover over any airport for: name, total flights, avg delay, delay rate %

### 7. 🕸️ Route Graph (Neo4j)
Uses Neo4j graph database to find connections:
- Type any two airport codes (e.g. JFK → MIA)
- Neo4j's **shortestPath** algorithm finds the optimal connection
- Shows all intermediate stops in order
- This is impossible to do efficiently with SQL — Neo4j is designed for exactly this

---

## Sidebar Filters

All 4 filters update **all charts instantly** across all pages:

| Filter | How It Works |
|--------|-------------|
| **Airline** | Filter all data to one airline |
| **Origin Airport** | Filter all data to one departure airport |
| **Month Range** | Slider from Jan to Dec |
| **Show Only Delayed** | Toggle between all flights and delayed-only |

---

## How the Dashboard Connects to Data

```
app.py
  └── data.py → get_flights_df()
        ├── Calls API via requests.get() (API_BASE_URL/api/flights)
        │     └── API queries PostgreSQL → Returns 100,000 random real flights
        └── Falls back → 2,000 mock flights (if API unavailable)

weather.py → get_weather(iata)
  └── Open-Meteo API → real temperature, wind, rain, clouds

ML Models → /app/models.pkl
  ├── LogisticRegression → delayed? (yes/no + probability)
  └── LinearRegression   → how many minutes?

Neo4j → bolt://neo4j:7687
  └── shortestPath query → route stops
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Dashboard shows 2,000 flights | API not connected — check API_URL environment variable |
| Port 8050 in use | Change port in last line of app.py |
| Risk Analyzer shows no results | Run train_models.py to generate models.pkl |
| Weather shows "No data" | Airport not in AIRPORT_COORDS dict in weather.py |
| Neo4j graph empty | Run load_neo4j.py script |
| Container not starting | Run `docker-compose logs <container_name>` |

---

## Database Credentials

| Database | Host | Port | User | Password | DB Name |
|----------|------|------|------|----------|---------|
| PostgreSQL | localhost | 5432 | airlines | liora | airlines_db |
| MongoDB | localhost | 27017 | — | — | airlines_db |
| Neo4j | localhost | 7687 | neo4j | airlines123 | — |
