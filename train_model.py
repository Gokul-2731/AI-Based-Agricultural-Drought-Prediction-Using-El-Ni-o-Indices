# train_model.py
# Step 4: your FIRST machine learning model.
# Goal: at the end of each month, predict the TOTAL rainfall of the next 3 months
# for a district, using recent weather and the El Nino index.
# Needs: pip install scikit-learn

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# 1. Load the two files made by the earlier scripts
weather = pd.read_csv("tn_weather_daily.csv", parse_dates=["date"])
oni = pd.read_csv("oni_monthly.csv")[["year", "month", "oni"]]

weather["year"] = weather["date"].dt.year
weather["month"] = weather["date"].dt.month

# 2. Turn daily data into monthly data
monthly = weather.groupby(["district", "year", "month"]).agg(
    rain=("rainfall_mm", "sum"),
    temp=("temp_avg_c", "mean"),
    humidity=("humidity_pct", "mean"),
).reset_index()

# 3. Add the El Nino index (we use LAST month's value so we never use the future)
monthly = monthly.merge(oni, on=["year", "month"], how="left")
monthly = monthly.sort_values(["district", "year", "month"]).reset_index(drop=True)
monthly["oni"] = monthly.groupby("district")["oni"].shift(1)

# 4. Build the features (inputs) and the target (what we want to predict)
g = monthly.groupby("district")
monthly["rain_prev1"] = g["rain"].shift(1)
monthly["rain_prev2"] = g["rain"].shift(2)
# Target: total rainfall of the next 3 months
monthly["target"] = g["rain"].shift(-1) + g["rain"].shift(-2) + g["rain"].shift(-3)

# The month as a circle (so December is next to January)
monthly["month_sin"] = np.sin(2 * np.pi * monthly["month"] / 12)
monthly["month_cos"] = np.cos(2 * np.pi * monthly["month"] / 12)

# Let the model know which district it is looking at
monthly = pd.get_dummies(monthly, columns=["district"], dtype=int)
district_cols = [c for c in monthly.columns if c.startswith("district_")]

features = ["rain", "rain_prev1", "rain_prev2", "temp", "humidity", "oni",
            "month_sin", "month_cos"] + district_cols
data = monthly.dropna(subset=features + ["target"]).copy()

# 5. Split by TIME: learn from the past, test on years the model has never seen
train = data[data["year"] <= 2017]
test = data[data["year"] >= 2018]
print("Training rows:", len(train), "| Testing rows:", len(test))

# 6. Train a Random Forest
model = RandomForestRegressor(n_estimators=300, min_samples_leaf=3,
                              random_state=42, n_jobs=-1)
model.fit(train[features], train["target"])
pred = model.predict(test[features])

# 7. A simple "baseline" to beat: just predict the long-term average for that
#    district and month. If our model can't beat this, it isn't adding value.
dcols = district_cols
train_key = train.copy()
train_key["district"] = train_key[dcols].idxmax(axis=1)
test_key = test.copy()
test_key["district"] = test_key[dcols].idxmax(axis=1)
avg = train_key.groupby(["district", "month"])["target"].mean().rename("baseline")
baseline = test_key.join(avg, on=["district", "month"])["baseline"]

print()
print("RESULTS on the test years (rainfall of next 3 months, in mm)")
print("  Baseline (average)  MAE:", round(mean_absolute_error(test["target"], baseline), 1),
      "| R2:", round(r2_score(test["target"], baseline), 2))
print("  Random Forest       MAE:", round(mean_absolute_error(test["target"], pred), 1),
      "| R2:", round(r2_score(test["target"], pred), 2))
print("  (MAE = average mistake, lower is better. R2 closer to 1 is better.)")

# 8. Which inputs mattered most?
print()
print("Most important inputs:")
importance = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print(importance.head(8).round(3))

# 9. Chart: predicted vs actual
plt.figure(figsize=(7, 6))
plt.scatter(test["target"], pred, alpha=0.5)
top = max(test["target"].max(), pred.max())
plt.plot([0, top], [0, top], color="red", linestyle="--")
plt.xlabel("Actual rainfall of next 3 months (mm)")
plt.ylabel("Predicted (mm)")
plt.title("Random Forest: predicted vs actual")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("model_results.png", dpi=150)

# 10. Save the trained model so the app can use it later
joblib.dump({"model": model, "features": features}, "rainfall_model.joblib")
print()
print("Saved rainfall_model.joblib and model_results.png")
plt.show()