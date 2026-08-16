-- =============================================================================
-- MEDALLION ARCHITECTURE: Flights + Weather ML Project
-- Layers: Bronze (cleaned) -> Silver (joined) -> Gold (ML-ready features)
-- =============================================================================
 
 
-- =============================================================================
-- SETUP: Use schemas to separate medallion layers cleanly
-- =============================================================================
 
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
 
 
-- =============================================================================
-- BRONZE LAYER: Ingestion of cleaned up data — types are defined, with null-constraints
-- Goal: mirror the CSV as faithfully as possible
-- =============================================================================

DROP TABLE IF EXISTS bronze.flights;
CREATE TABLE bronze.flights (
    flight_id SERIAL PRIMARY KEY,
    FlightDate DATE NOT NULL,
    Operating_Airline VARCHAR(20) NOT NULL,
    Tail_Number VARCHAR(20),
    Flight_Number_Operating_Airline INT NOT NULL,
    OriginAirportID INT NOT NULL,
    Origin VARCHAR(20) NOT NULL,
    OriginCityName VARCHAR(100) NOT NULL, 
    DestAirportID INT NOT NULL,
    Dest VARCHAR(20) NOT NULL,
    DestCityName VARCHAR(100) NOT NULL,
    CRSDepTime TIME,
    DepTime TIME,
    DepDelay INT,
    DepDel15 BOOLEAN,
    DepartureDelayGroups FLOAT,
    TaxiOut INT,
    WheelsOff TIME,
    WheelsOn TIME,
    TaxiIn INT,
    CRSArrTime TIME,
    ArrTime TIME,
    ArrDelay INT,
    ArrDelayMinutes INT,
    ArrDel15 BOOLEAN,
    ArrivalDelayGroups FLOAT,
    Cancelled BOOLEAN,
    CancellationCode VARCHAR(20),
    Diverted BOOLEAN,
    CRSElapsedTime INT,
    ActualElapsedTime INT,
    AirTime INT,
    Distance FLOAT,
    DistanceGroup INT,
    CarrierDelay INT,
    WeatherDelay INT,
    NASDelay INT,
    SecurityDelay INT,
    LateAircraftDelay INT,
    ingested_at TIMESTAMP DEFAULT NOW()
);

DROP TABLE IF EXISTS bronze.weather;
CREATE TABLE bronze.weather (
    weather_id SERIAL PRIMARY KEY,
    station_id VARCHAR(20),
    location_name VARCHAR(100) NOT NULL,   
    weather_date DATE NOT NULL, -- location_name + weather date = join key with flights
    temp FLOAT,
    temp_min_c FLOAT,
    temp_max_c FLOAT,
    relative_humidity FLOAT,
    precipitation_mm FLOAT,
    snow_mm FLOAT,
    wind_speed_kmh FLOAT,
    pressure_hpa FLOAT,
    cloud_cover FLOAT,
    ingested_at TIMESTAMP DEFAULT NOW()
);