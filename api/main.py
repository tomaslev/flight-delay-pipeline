from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
import pickle


app = FastAPI(title="Liora Flight Delay")

# loading the pre-trained ml-model
with open("logistic_regression.pkl", "rb") as f:
    model = pickle.load(f)

# defining the needed features for the flight itselfs and the origin and destination airports the model was trained on
MODEL_FEATURES = [
    "distance",
    "distancegroup",
    "temp_o",
    "temp_min_c_o",
    "temp_max_c_o",
    "relative_humidity_o",
    "precipitation_mm_o",
    "snow_mm_o",
    "wind_speed_kmh_o",
    "pressure_hpa_o",
    "cloud_cover_o",
    "temp_d",
    "temp_min_c_d",
    "temp_max_c_d",
    "relative_humidity_d",
    "precipitation_mm_d",
    "snow_mm_d",
    "wind_speed_kmh_d",
    "pressure_hpa_d",
    "cloud_cover_d",
    "diverted",
    "origin",
    "dest"
]


class FlightInput(BaseModel):
    flightdate: str
    origin: str
    origincityname: str
    dest: str
    destcityname: str
    distance: float
    distancegroup: int
    diverted: int


class WeatherInput(BaseModel):
    weather_date: str
    location_name: str
    temp: float
    temp_min_c: float
    temp_max_c: float
    relative_humidity: float
    precipitation_mm: float
    snow_mm: Optional[float] = 0
    wind_speed_kmh: float
    pressure_hpa: float
    cloud_cover: float


class PredictionRequest(BaseModel):
    flights: List[FlightInput]
    weather: List[WeatherInput]


@app.get("/")
def health_check():
    return {"status": "ok"}

# post request which returns a prediction
@app.post("/predict")
def predict_delay(payload: PredictionRequest):
    # loading and cleaning up the data from the request, making it suitable for the prediction model
    df_flight = pd.DataFrame([flight.model_dump() for flight in payload.flights])
    df_weather = pd.DataFrame([weather.model_dump() for weather in payload.weather])

    df_weather["snow_mm"] = df_weather["snow_mm"].fillna(0)

    df_merge = pd.merge(
        df_flight,
        df_weather,
        left_on=["flightdate", "origincityname"],
        right_on=["weather_date", "location_name"],
        how="inner"
    )

    df_merge = df_merge.rename(columns={
        "temp": "temp_o",
        "temp_min_c": "temp_min_c_o",
        "temp_max_c": "temp_max_c_o",
        "relative_humidity": "relative_humidity_o",
        "precipitation_mm": "precipitation_mm_o",
        "snow_mm": "snow_mm_o",
        "wind_speed_kmh": "wind_speed_kmh_o",
        "pressure_hpa": "pressure_hpa_o",
        "cloud_cover": "cloud_cover_o"
    })

    df_merge = pd.merge(
        df_merge,
        df_weather,
        left_on=["flightdate", "destcityname"],
        right_on=["weather_date", "location_name"],
        how="inner"
    )

    df_merge = df_merge.rename(columns={
        "temp": "temp_d",
        "temp_min_c": "temp_min_c_d",
        "temp_max_c": "temp_max_c_d",
        "relative_humidity": "relative_humidity_d",
        "precipitation_mm": "precipitation_mm_d",
        "snow_mm": "snow_mm_d",
        "wind_speed_kmh": "wind_speed_kmh_d",
        "pressure_hpa": "pressure_hpa_d",
        "cloud_cover": "cloud_cover_d"
    })

    if df_merge.empty:
        return {
            "error": "no matching data"
        }

    missing_features = [
        column for column in MODEL_FEATURES
        if column not in df_merge.columns
    ]

    if missing_features:
        return {
            "error": "missing features",
            "missing_features": missing_features
        }
    # cleaning the data is finished and the data is made available as feats
    feats = df_merge[MODEL_FEATURES]
    # prediction model is called
    predictions = model.predict(feats)

    response = {
        "predictions": [bool(prediction) for prediction in predictions],
        "rows_predicted": int(len(predictions))
    }
    # prediction probability is called
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(feats)
        response["delay_probabilities"] = [
            float(probability)
            for probability in probabilities[:, 1]
        ]

    unique, counts = np.unique(predictions, return_counts=True)
    response["counts"] = {
        str(key): int(value)
        for key, value in zip(unique, counts)
    }

    return response