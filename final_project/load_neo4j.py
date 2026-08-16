from sqlalchemy import create_engine, text
from neo4j import GraphDatabase
import pandas as pd

print("Loading routes from PostgreSQL...")
engine = create_engine('postgresql+psycopg2://airlines:liora@db:5432/airlines_db')
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT origin, dest, origincityname, destcityname,
               COUNT(*) as total_flights,
               AVG(depdelay) as avg_delay,
               AVG(CASE WHEN depdel15 THEN 1.0 ELSE 0.0 END)*100 as delay_rate
        FROM bronze.flights
        WHERE cancelled = FALSE
        GROUP BY origin, dest, origincityname, destcityname
        HAVING COUNT(*) >= 10
    """), conn)

print(f"Routes: {len(df):,}")

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j","airlines123"))
with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")
    airports = set(df["origin"].tolist() + df["dest"].tolist())
    for iata in airports:
        rows = df[df["origin"]==iata]
        city = rows.iloc[0]["origincityname"] if len(rows)>0 else df[df["dest"]==iata].iloc[0]["destcityname"]
        session.run("MERGE (a:Airport {iata:$iata}) SET a.city=$city", iata=iata, city=city)
    print(f"✅ {len(airports)} airports loaded")
    for _, row in df.iterrows():
        params = {
            "origin": row["origin"],
            "dest": row["dest"],
            "flights": int(row["total_flights"]),
            "delay": float(row["avg_delay"] or 0),
            "rate": float(row["delay_rate"] or 0)
        }
        session.run("""
            MATCH (o:Airport {iata:$origin})
            MATCH (d:Airport {iata:$dest})
            MERGE (o)-[r:ROUTE]->(d)
            SET r.total_flights=$flights, r.avg_delay=$delay, r.delay_rate=$rate
        """, **params)
    print(f"✅ {len(df)} routes loaded")

driver.close()
print("✅ Neo4j loaded!")