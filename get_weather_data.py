# get_weather_data.py
# Step 1 of the project: download daily weather history for 5 Tamil Nadu districts
# from the free NASA POWER API and save it as one CSV file.

import time
import requests
import pandas as pd

# 1. The districts we start with (name, latitude, longitude)
DISTRICTS = {
    "Chennai":        (13.08, 80.27),
    "Madurai":        (9.92, 78.12),
    "Thanjavur":      (10.79, 79.14),
    "Coimbatore":     (11.00, 76.96),
    "Ramanathapuram": (9.37, 78.83),
}

# 2. What we want to download
# PRECTOTCORR = rainfall (mm/day), T2M = average temperature (C),
# T2M_MAX / T2M_MIN = highest / lowest temperature, RH2M = humidity (%)
PARAMETERS = "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M"
START = "20000101"   # year, month, day
END = "20231231"

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def download_district(name, lat, lon):
    """Ask NASA POWER for one district and return a pandas table."""
    params = {
        "parameters": PARAMETERS,
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": START,
        "end": END,
        "format": "JSON",
    }
    response = requests.get(URL, params=params, timeout=120)
    response.raise_for_status()          # stops with an error if something went wrong
    data = response.json()["properties"]["parameter"]

    table = pd.DataFrame(data)           # each parameter becomes a column
    table.index = pd.to_datetime(table.index, format="%Y%m%d")
    table.index.name = "date"
    table = table.reset_index()
    table.insert(0, "district", name)
    return table


all_tables = []
for name, (lat, lon) in DISTRICTS.items():
    print("Downloading", name, "...")
    all_tables.append(download_district(name, lat, lon))
    time.sleep(2)                        # small pause to be polite to the server

weather = pd.concat(all_tables, ignore_index=True)

# NASA uses -999 for "no data", so turn it into an empty value
weather = weather.replace(-999, pd.NA)

# Give the columns friendlier names
weather = weather.rename(columns={
    "PRECTOTCORR": "rainfall_mm",
    "T2M": "temp_avg_c",
    "T2M_MAX": "temp_max_c",
    "T2M_MIN": "temp_min_c",
    "RH2M": "humidity_pct",
})

weather.to_csv("tn_weather_daily.csv", index=False)
print("Done! Saved", len(weather), "rows to tn_weather_daily.csv")
print(weather.head())
