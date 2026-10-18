# app.py
# Step 5: the Flask backend. It loads the trained model and answers the question:
# "For this GPS location, how much rain is expected in the next 3 months,
#  and is there a drought risk?"
# Needs: pip install flask
#
# Run:   python app.py
# Test:  open http://127.0.0.1:5000/api/forecast?lat=9.92&lon=78.12   (Madurai)

import math
from datetime import date, timedelta

import joblib
import numpy as np
import pandas as pd
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------- Load everything once when the server starts ----------
saved = joblib.load("rainfall_model.joblib")
MODEL, FEATURES = saved["model"], saved["features"]

oni_table = pd.read_csv("oni_monthly.csv")[["year", "month", "oni"]]

DISTRICTS = {                       # same 5 districts as get_weather_data.py
    "Chennai":        (13.08, 80.27),
    "Madurai":        (9.92, 78.12),
    "Thanjavur":      (10.79, 79.14),
    "Coimbatore":     (11.00, 76.96),
    "Ramanathapuram": (9.37, 78.83),
}

# "Normal" 3-month rainfall for each district and starting month (from history)
hist = pd.read_csv("tn_weather_daily.csv", parse_dates=["date"])
hist["year"], hist["month"] = hist["date"].dt.year, hist["date"].dt.month
hist_monthly = (hist.groupby(["district", "year", "month"])["rainfall_mm"].sum()
                .reset_index().sort_values(["district", "year", "month"]))
g = hist_monthly.groupby("district")["rainfall_mm"]
hist_monthly["next3"] = g.shift(-1) + g.shift(-2) + g.shift(-3)
NORMAL = hist_monthly.groupby(["district", "month"])["next3"].mean()

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------- Helper functions ----------
def nearest_district(lat, lon):
    """Find which of our districts is closest to the user's GPS point."""
    def dist(item):
        _, (dlat, dlon) = item
        return math.hypot(lat - dlat, (lon - dlon) * math.cos(math.radians(lat)))
    return min(DISTRICTS.items(), key=dist)[0]


def last_complete_month():
    """The most recent month that has complete data (NASA lags a few days)."""
    today = date.today()
    end = today.replace(day=1) - timedelta(days=1)       # last day of last month
    if today.day <= 7:                                   # too fresh, go one more back
        end = end.replace(day=1) - timedelta(days=1)
    return end.year, end.month


def fetch_recent_months(lat, lon, year, month):
    """Download the last 3 months of daily weather up to (year, month) from NASA POWER.
    Returns a table with columns: year, month, rain, temp, humidity."""
    end = date(year, month, 1)
    start = end
    for _ in range(2):
        start = (start - timedelta(days=1)).replace(day=1)
    last_day = (date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1))
    params = {
        "parameters": "PRECTOTCORR,T2M,RH2M", "community": "AG",
        "latitude": lat, "longitude": lon,
        "start": start.strftime("%Y%m%d"), "end": last_day.strftime("%Y%m%d"),
        "format": "JSON",
    }
    r = requests.get("https://power.larc.nasa.gov/api/temporal/daily/point",
                     params=params, timeout=120)
    r.raise_for_status()
    data = pd.DataFrame(r.json()["properties"]["parameter"]).replace(-999, np.nan)
    data.index = pd.to_datetime(data.index, format="%Y%m%d")
    out = data.groupby([data.index.year, data.index.month]).agg(
        rain=("PRECTOTCORR", "sum"), temp=("T2M", "mean"), humidity=("RH2M", "mean"))
    out.index.names = ["year", "month"]
    return out.reset_index()


def risk_label(percent):
    if percent < 60:
        return "High drought risk (much less rain than normal)"
    if percent < 80:
        return "Moderate drought risk (below-normal rain)"
    if percent <= 120:
        return "Normal rainfall expected"
    return "Wetter than normal (flood or waterlogging care needed)"


def latest_oni(year, month):
    """ONI of the month before (the model uses last month's value)."""
    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    row = oni_table[(oni_table["year"] == prev_year) & (oni_table["month"] == prev_month)]
    if len(row):
        return float(row["oni"].iloc[0])
    return float(oni_table.dropna().iloc[-1]["oni"])     # fall back to latest we have


# ---------- The API ----------
@app.after_request
def allow_frontend(response):
    response.headers["Access-Control-Allow-Origin"] = "*"   # lets your HTML/JS call us
    return response


@app.route("/api/forecast")
def forecast():
    try:
        lat, lon = float(request.args["lat"]), float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify(error="Please give lat and lon, e.g. ?lat=9.92&lon=78.12"), 400

    district = nearest_district(lat, lon)
    year, month = last_complete_month()

    try:
        recent = fetch_recent_months(DISTRICTS[district][0], DISTRICTS[district][1], year, month)
    except Exception as e:
        return jsonify(error="Could not download recent weather data", details=str(e)), 502
    recent = recent.dropna()
    if len(recent) < 3:
        return jsonify(error="Not enough recent weather data yet. Try again later."), 503
    recent = recent.tail(3).reset_index(drop=True)

    row = {
        "rain": recent.loc[2, "rain"], "rain_prev1": recent.loc[1, "rain"],
        "rain_prev2": recent.loc[0, "rain"], "temp": recent.loc[2, "temp"],
        "humidity": recent.loc[2, "humidity"], "oni": latest_oni(year, month),
        "month_sin": math.sin(2 * math.pi * month / 12),
        "month_cos": math.cos(2 * math.pi * month / 12),
    }
    for d in DISTRICTS:
        row["district_" + d] = 1 if d == district else 0
    X = pd.DataFrame([row])[FEATURES]

    predicted = float(MODEL.predict(X)[0])
    normal = float(NORMAL.loc[(district, month)])
    percent = round(100 * predicted / normal) if normal > 0 else None

    next_months = [MONTH_NAMES[(month + i) % 12] for i in range(3)]   # month+1..+3
    return jsonify(
        district=district,
        forecast_months=next_months,
        predicted_rain_mm=round(predicted),
        normal_rain_mm=round(normal),
        percent_of_normal=percent,
        risk=risk_label(percent) if percent is not None else "Not enough history",
        based_on={"latest_complete_month": f"{MONTH_NAMES[month - 1]} {year}",
                  "el_nino_index": round(row["oni"], 2)},
        note="Forecast for the TOTAL rain of these 3 months. It is an estimate, not a guarantee.",
    )


@app.route("/")
def home():
    return "Drought prediction API is running. Try /api/forecast?lat=9.92&lon=78.12"


if __name__ == "__main__":
    app.run(debug=True)