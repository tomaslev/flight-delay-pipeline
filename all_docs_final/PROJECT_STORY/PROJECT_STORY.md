# My Project Story — DST Airlines
## What I did, step by step, from the beginning to the end

---

## What Was the Project?

The project is called DST Airlines. It is a full data engineering platform.
We collect real flight data, store it in three different databases,
and show it in a live interactive dashboard with machine learning predictions.

The data is real — **560,352 US domestic flights from 2018 to 2024**.

My job was:
- Build the Dashboard — 7 pages, professional dark theme
- Load real flight data into PostgreSQL (560,352 flights)
- Train ML models for delay prediction
- Add real-time weather from Open-Meteo API
- Build the Neo4j airport route graph (346 airports, 5,167 routes)
- Create an interactive US airport map
- Write all documentation

---

## Step 1 — Set Up the Environment

I worked on a remote server using VS Code and SSH (Ubuntu 20.04 on AWS).
Later I moved to my local Windows machine with Docker Desktop.

Docker Compose was not installed on the server. I installed it manually:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version  # ✅ Docker Compose version v2.27.0
```

---

## Step 2 — Start All Services with Docker

One command starts everything:
```bash
cd dst_airlines_full
docker-compose up -d
```

This starts 7 containers at the same time:
- PostgreSQL (port 5432) — stores all flight data
- pgAdmin (port 5050) — web interface for PostgreSQL
- MongoDB (port 27017) — stores live flight positions
- Mongo Express (port 8081) — web interface for MongoDB
- Neo4j (port 7474/7687) — airport route graph database
- FastAPI (port 8000) — REST API with 11 endpoints
- Dash Dashboard (port 8050) — the main user interface

The `-d` flag means "run in the background" so the terminal stays free.

---

## Step 3 — Load Real Flight Data into PostgreSQL

I downloaded `flight_data_2018_2024.csv` (281 MB) from Kaggle.

First, I copied it into the container:
```bash
docker cp flight_data_2018_2024.csv airlines_dashboard:/app/flight_data_2018_2024.csv
```

Then I ran this Python script inside the container:
```python
import pandas as pd
from sqlalchemy import create_engine

# Read only the columns we need (not all 100+ columns)
df = pd.read_csv('/app/flight_data_2018_2024.csv',
    usecols=['FlightDate','Operating_Airline ','Origin','Dest',
             'DepDelay','DepDel15','Distance',
             'CarrierDelay','WeatherDelay','NASDelay',
             'SecurityDelay','LateAircraftDelay',
             'Cancelled','Diverted'], low_memory=False)

# Clean the data
df = df.rename(columns={'Operating_Airline ': 'Operating_Airline'})
df = df[df['Cancelled'] != 1.0]  # remove cancelled flights

# Fix boolean columns (0.0/1.0 → True/False)
for col in ['DepDel15','ArrDel15','Cancelled','Diverted']:
    df[col] = df[col].fillna(0).astype(bool)

# Make all column names lowercase
df.columns = [c.lower() for c in df.columns]

# Load into PostgreSQL — 1,000 rows at a time (chunksize)
engine = create_engine('postgresql+psycopg2://airlines:liora@db:5432/airlines_db')
df.to_sql('flights', engine, schema='bronze', if_exists='append',
          index=False, chunksize=1000)
# Result: 560,352 flights loaded ✅
```

Why `chunksize=1000`? Loading 560,000 rows at once would use too much memory.
Sending 1,000 rows at a time keeps memory usage low.

Verify the count:
```bash
docker exec -i pg_airlines psql -U airlines -d airlines_db \
  -c "SELECT COUNT(*) FROM bronze.flights;"
# count: 560352 ✅
```

---

## Step 4 — Build the Dashboard Files

### data.py — How the Dashboard Gets Data

This file first tries to connect to PostgreSQL.
If it cannot connect, it automatically uses 2,000 fake flights.
This means the dashboard **always works**, even without a database.

```python
AIRLINE_MAP = {
    "AA": "American Airlines", "DL": "Delta Air Lines",
    "UA": "United Airlines",   "WN": "Southwest Airlines", ...
}

def get_flights_df():
    try:
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql("""
            SELECT * FROM bronze.flights
            WHERE cancelled = FALSE
            ORDER BY RANDOM()   -- random sample, not just first rows
            LIMIT 100000
        """, engine)
        # Convert airline codes to full names
        df["Operating_Airline"] = df["Operating_Airline"].map(AIRLINE_MAP)
        return df
    except Exception:
        return mock_data  # automatic fallback
```

Why `ORDER BY RANDOM()`? To get a balanced sample from all months,
not just the first 100,000 rows which would all be from January.

### charts.py — The Chart Factory (OOP)

All charts are methods of one class. Each method takes a DataFrame and returns a Plotly figure:

```python
class ChartFactory:
    def monthly_trend(self, df): ...      # line + bar chart per month
    def airline_delay_bar(self, df): ...  # horizontal bar, sorted by delay rate
    def delay_cause_stack(self, df): ...  # stacked bar — 5 delay causes
    def route_heatmap_top(self, df): ...  # 20x20 heatmap, busiest airports
    def top_routes_bubble(self, df): ...  # bubble chart — 3 metrics at once
    def dow_delay(self, df): ...          # delay by day of week
    def delay_histogram(self, df): ...    # distribution of delay minutes
    def top_routes(self, df): ...         # top 10 most delayed routes
    def risk_gauge(self, probability): .. # gauge chart for risk level
    def airport_map(self, df): ...        # interactive US map
```

### app.py — The Main Application (OOP)

Two classes work together:

**LB (LayoutBuilder)** — builds all visual components:
```python
class LB:
    def navbar(self): ...       # top bar with logo + API status badge
    def sidebar(self): ...      # left panel with 4 filters
    def kpi(self): ...          # number cards at the top
    def footer(self): ...       # bottom bar with tech stack
    def page_overview(self): ...
    def page_airlines(self): ...
    def page_routes(self): ...
    def page_trends(self): ...
    def page_risk(self, df): ...   # uses real data for dropdowns
    def page_map(self): ...
    def page_graph(self): ...
```

**App** — registers callbacks and runs the server:
```python
class App:
    def __init__(self):
        self.app = dash.Dash(...)
        self._layout()     # build all pages
        self._callbacks()  # connect filters to charts

    def run(self, port=8050):
        self.app.run(host="0.0.0.0", port=port)
```

**How do filters work?**
When a user changes a filter, Dash automatically calls the matching callback function.
The function filters the DataFrame and returns updated charts — no page reload needed.

```python
@app.callback(
    Output("chart-monthly", "figure"),
    Input("filter-airline", "value"),
    Input("filter-month", "value"),
    Input("filter-delayed", "value")
)
def update_monthly_chart(airline, months, delayed_filter):
    df = get_flights_df()
    if airline != "ALL":
        df = df[df["Operating_Airline"] == airline]
    df = df[df["Month"].between(months[0], months[1])]
    if delayed_filter == "delayed":
        df = df[df["Delayed"] == 1]
    return charts.monthly_trend(df)
```

---

## Step 5 — Train the Machine Learning Models

I trained two models on 100,000 real flights from PostgreSQL:

```python
# train_models.py
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import LabelEncoder
import pickle

# Get data from PostgreSQL
df = pd.read_sql("SELECT ... FROM bronze.flights LIMIT 100000", engine)

# Encode text columns as numbers
le_airline = LabelEncoder()
le_origin  = LabelEncoder()
le_dest    = LabelEncoder()
df['airline_enc'] = le_airline.fit_transform(df['operating_airline'])
df['origin_enc']  = le_origin.fit_transform(df['origin'])
df['dest_enc']    = le_dest.fit_transform(df['dest'])

features = ['airline_enc', 'origin_enc', 'dest_enc', 'distance']
X = df[features]

# Model 1: Will the flight be delayed? (Classification)
cls_model = LogisticRegression(max_iter=1000)
cls_model.fit(X, df['delayed'])

# Model 2: How many minutes delayed? (Regression)
mask = df['depdelay'] > 0
reg_model = LinearRegression()
reg_model.fit(X[mask], df[mask]['depdelay'])

# Save both models + encoders
with open('/app/models.pkl', 'wb') as f:
    pickle.dump({
        'cls': cls_model, 'reg': reg_model,
        'le_airline': le_airline, 'le_origin': le_origin, 'le_dest': le_dest
    }, f)
```

Run the training:
```bash
docker exec airlines_dashboard pip install scikit-learn
docker exec airlines_dashboard python3 /app/train_models.py
# Classification model trained ✅
# Regression model trained ✅
# Done! Models saved to /app/models.pkl ✅
```

---

## Step 6 — Add Real-Time Weather (Open-Meteo API)

I created `weather.py` which fetches real weather for any US airport — for free, with no API key.

```python
import requests

# 346 US airports with exact GPS coordinates
AIRPORT_COORDS = {
    "ATL": (33.6407, -84.4277),  # Atlanta
    "JFK": (40.6413, -73.7781),  # New York JFK
    "LAX": (33.9425, -118.4081), # Los Angeles
    # ... 346 airports total
}

def get_weather(iata: str) -> dict:
    lat, lon = AIRPORT_COORDS[iata]
    response = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,precipitation,cloud_cover",
        "timezone": "auto"
    })
    data = response.json()["current"]
    return {
        "temp":        data["temperature_2m"],     # degrees Celsius
        "wind_speed":  data["wind_speed_10m"],     # km/h
        "precip":      data["precipitation"],      # mm
        "cloud_cover": data["cloud_cover"] / 100 * 8  # convert % to oktas
    }
```

When the user selects an airport in the Risk Analyzer,
the weather for both airports is fetched automatically and shown instantly.

---

## Step 7 — Build the Risk Analyzer Page

This page combines everything into one powerful tool:

**Cascading Dropdowns** — filters connect to each other:
```python
# When airline changes → update origin airports
@app.callback(Output("risk-origin","options"), Input("risk-airline","value"))
def update_origins(airline):
    df = get_flights_df()
    if airline: df = df[df["Operating_Airline"] == airline]
    return [{"label": v, "value": v} for v in sorted(df["Origin"].unique())]

# When origin changes → update destination airports
@app.callback(Output("risk-dest","options"),
              Input("risk-airline","value"), Input("risk-origin","value"))
def update_dests(airline, origin):
    df = get_flights_df()
    if airline: df = df[df["Operating_Airline"] == airline]
    if origin:  df = df[df["Origin"] == origin]
    return [{"label": v, "value": v} for v in sorted(df["Dest"].unique())]
```

**Auto Weather** — fetches when airport selected:
```python
@app.callback(Output("weather-preview","children"),
              Input("risk-origin","value"), Input("risk-dest","value"))
def weather_preview(origin, dest):
    w_origin = get_weather(origin)  # real weather right now
    w_dest   = get_weather(dest)
    return [show_weather_card(origin, w_origin),
            show_weather_card(dest, w_dest)]
```

**ML Prediction** — when button clicked:
```python
@app.callback(Output("risk-result","children"), Input("btn-risk","n_clicks"), ...)
def analyze_risk(n, origin, dest, airline, day):
    models = pickle.load(open("/app/models.pkl", "rb"))
    
    # Encode inputs for the model
    a_enc = models["le_airline"].transform([airline])[0]
    o_enc = models["le_origin"].transform([origin])[0]
    d_enc = models["le_dest"].transform([dest])[0]
    dist  = get_avg_distance(origin, dest)

    # Model 1: probability of delay
    prob = models["cls"].predict_proba([[a_enc, o_enc, d_enc, dist]])[0][1]

    # Model 2: expected delay in minutes
    exp_delay = models["reg"].predict([[a_enc, o_enc, d_enc, dist]])[0]

    # Show risk level
    if prob < 0.3:   return "LOW RISK ✅"
    elif prob < 0.6: return "MEDIUM RISK ⚠️"
    else:            return "HIGH RISK 🔴"
```

---

## Step 8 — Build the Neo4j Route Graph

### Load Data into Neo4j

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j","airlines123"))

with driver.session() as session:
    # Create one node per airport
    session.run("MERGE (a:Airport {iata:$iata}) SET a.city=$city",
                iata="JFK", city="New York")

    # Create one relationship per route
    session.run("""
        MATCH (o:Airport {iata:$origin})
        MATCH (d:Airport {iata:$dest})
        MERGE (o)-[r:ROUTE]->(d)
        SET r.total_flights = $flights,
            r.avg_delay     = $delay,
            r.delay_rate    = $rate
    """, origin="JFK", dest="LAX", flights=1250, delay=14.5, rate=28.3)

# Result: 346 airports + 5,167 routes ✅
```

### Find Shortest Path in the Dashboard

```python
result = session.run("""
    MATCH path = shortestPath(
        (a:Airport {iata:$from})-[:ROUTE*..10]->(b:Airport {iata:$to})
    )
    RETURN [n in nodes(path) | n.iata] AS stops,
           length(path) AS hops
""", **{"from": "JFK", "to": "MIA"})

# Example result: JFK → CLT → MIA (2 hops)
```

Why Neo4j and not SQL?
SQL needs complex recursive queries (CTEs) to find paths in a graph.
Neo4j has `shortestPath` built in — it is fast and simple.

---

## Step 9 — Airport Delay Map

```python
def airport_map(self, df):
    # Aggregate stats per airport
    grp = df.groupby("Origin").agg(
        total   = ("DepDelay", "count"),
        avg_delay = ("DepDelay", "mean"),
        delayed = ("Delayed", "sum")
    ).reset_index()
    grp["delay_rate"] = grp["delayed"] / grp["total"] * 100

    # Add GPS coordinates for each airport
    grp["lat"] = grp["Origin"].map(lambda x: AIRPORT_COORDS.get(x,(None,None))[0])
    grp["lon"] = grp["Origin"].map(lambda x: AIRPORT_COORDS.get(x,(None,None))[1])

    fig = go.Figure(go.Scattergeo(
        lat=grp["lat"],
        lon=grp["lon"],
        mode="markers",
        marker=dict(
            size=grp["total"] / grp["total"].max() * 40 + 6,  # size = flight volume
            color=grp["delay_rate"],                            # color = delay rate
            colorscale=[[0,"green"],[0.4,"yellow"],[1,"red"]],
        ),
    ))
    fig.update_layout(geo=dict(scope="usa", projection_type="albers usa"))
    return fig
```

---

## Final Numbers

| What | How Many |
|------|----------|
| Real flights in PostgreSQL | 560,352 |
| Airports in Neo4j | 346 |
| Routes in Neo4j | 5,167 |
| Airport GPS coordinates (weather) | 346 |
| ML training flights | 100,000 |
| API endpoints | 11 |
| Dashboard pages | 7 |
| Docker containers | 7 |
| Databases | 3 |

---

## Questions You Might Be Asked

**Q: Why 3 different databases?**
A: Each database is good at a different type of data:
- PostgreSQL: structured historical data — SQL queries, joins, Medallion Architecture
- MongoDB: flexible live data — flight positions change shape each time
- Neo4j: graph data — connections between airports, shortest path algorithm

**Q: What is the Medallion Architecture?**
A: Three layers of data quality:
- Bronze: raw data exactly as it came from the CSV file — no changes
- Silver: cleaned data joined with weather data — ready for analysis
- Gold: aggregated stats per airline and route — ready for ML

**Q: How does the Risk Analyzer work?**
A: It combines three things at once:
1. PostgreSQL: historical delay rates for the route, day, and airline
2. Open-Meteo API: real current weather at both airports
3. ML Model: Logistic Regression trained on 100,000 real flights
The result is a delay probability percentage and expected minutes.

**Q: Why Neo4j for routes?**
A: SQL needs complex recursive CTEs to find paths between nodes.
Neo4j is a graph database — it has `shortestPath` built in as a native algorithm.
It is fast, simple, and designed exactly for this type of problem.

**Q: How do the filters work?**
A: Dash uses Callbacks. When a user changes any filter, Dash automatically calls the matching callback function. That function filters the DataFrame and returns updated charts — all charts update instantly without reloading the page.

**Q: How does the weather work?**
A: When the user selects an airport in the Risk Analyzer, a callback function calls `get_weather(iata)`. This sends a request to the Open-Meteo API with the airport's GPS coordinates. The API returns current temperature, wind speed, precipitation, and cloud cover — for free, with no API key needed.

**Q: How did you connect the dashboard to the database?**
A: In `docker-compose.yml`, I set the `DATABASE_URL` environment variable for the dashboard container:
```yaml
dashboard:
  environment:
    DATABASE_URL: postgresql+psycopg2://airlines:liora@db:5432/airlines_db
```
Inside Docker, containers talk to each other by name — `db` is the name of the PostgreSQL container, not `localhost`.
