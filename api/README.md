## FastAPI Documentation

### Start the containers from the root folder:
`cd <pathToProject>`

`docker compose up -d`

### Example querys:
Below you will find 3 example querys that you can query against the api from your cli. Adapt them to the needed format for your UI interface.

<details>
<summary style="font-size:1.2em">Washington Flight</summary>

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "flights": [
      {
        "flightdate": "2024-01-14",
        "origin": "IAD",
        "origincityname": "Washington, DC",
        "dest": "EWR",
        "destcityname": "Newark, NJ",
        "distance": 212.0,
        "distancegroup": 1,
        "diverted": 0
      }
    ],
    "weather": [
      {
        "weather_date": "2024-01-14",
        "location_name": "Washington, DC",
        "temp": 4.2,
        "temp_min_c": 1.1,
        "temp_max_c": 8.9,
        "relative_humidity": 59.0,
        "precipitation_mm": 0.0,
        "snow_mm": 0.0,
        "wind_speed_kmh": 9.0,
        "pressure_hpa": 1018.1,
        "cloud_cover": 6.0
      },
      {
        "weather_date": "2024-01-14",
        "location_name": "Newark, NJ",
        "temp": 5.6,
        "temp_min_c": 0.0,
        "temp_max_c": 8.3,
        "relative_humidity": 55.0,
        "precipitation_mm": 0.0,
        "snow_mm": 0.0,
        "wind_speed_kmh": 18.0,
        "pressure_hpa": 1019.0,
        "cloud_cover": 5.0
      }
    ]
  }'
  ```
  </details>

<details>
<summary style="font-size:1.2em">Des Moines Flight</summary>

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "flights": [
      {
        "flightdate": "2024-01-08",
        "origin": "DSM",
        "origincityname": "Des Moines, IA",
        "dest": "ATL",
        "destcityname": "Atlanta, GA",
        "distance": 743.0,
        "distancegroup": 3,
        "diverted": 0
      }
    ],
    "weather": [
      {
        "weather_date": "2024-01-08",
        "location_name": "Des Moines, IA",
        "temp": -1.4,
        "temp_min_c": -2.7,
        "temp_max_c": 2.2,
        "relative_humidity": 88.0,
        "precipitation_mm": 7.9,
        "snow_mm": 0.0,
        "wind_speed_kmh": 21.6,
        "pressure_hpa": 1014.5,
        "cloud_cover": 8.0
      },
      {
        "weather_date": "2024-01-08",
        "location_name": "Atlanta, GA",
        "temp": 4.1,
        "temp_min_c": -2.8,
        "temp_max_c": 10.6,
        "relative_humidity": 70.0,
        "precipitation_mm": 0.0,
        "snow_mm": 0.0,
        "wind_speed_kmh": 11.2,
        "pressure_hpa": 1023.5,
        "cloud_cover": 2.0
      }
    ]
  }'
```

</details>

<details>
<summary style="font-size:1.2em">Hawaii Interisland Flight</summary>

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "flights": [
      {
        "flightdate": "2024-01-22",
        "origin": "OGG",
        "origincityname": "Kahului, HI",
        "dest": "HNL",
        "destcityname": "Honolulu, HI",
        "distance": 100.0,
        "distancegroup": 1,
        "diverted": 0
      }
    ],
    "weather": [
      {
        "weather_date": "2024-01-22",
        "location_name": "Kahului, HI",
        "temp": 23.8,
        "temp_min_c": 19.4,
        "temp_max_c": 28.3,
        "relative_humidity": 70.0,
        "precipitation_mm": 0.0,
        "snow_mm": 0.0,
        "wind_speed_kmh": 18.4,
        "pressure_hpa": 1014.5,
        "cloud_cover": 1.0
      },
      {
        "weather_date": "2024-01-22",
        "location_name": "Honolulu, HI",
        "temp": 23.7,
        "temp_min_c": 20.6,
        "temp_max_c": 26.7,
        "relative_humidity": 78.0,
        "precipitation_mm": 0.3,
        "snow_mm": 0.0,
        "wind_speed_kmh": 15.5,
        "pressure_hpa": 1013.7,
        "cloud_cover": 4.0
      }
    ]
  }'
```

</details>