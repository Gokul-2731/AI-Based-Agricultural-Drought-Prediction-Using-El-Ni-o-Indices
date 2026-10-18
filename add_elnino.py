# add_elnino.py
# Step 3: download El Nino data (ONI index) from NOAA and compare it
# with the rainfall of each district.

import pandas as pd
import matplotlib.pyplot as plt

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

# 1. Download the ONI table. Columns: SEAS (3-month season), YR, TOTAL, ANOM
#    ANOM is the value we want: above +0.5 = El Nino, below -0.5 = La Nina.
oni = pd.read_csv(ONI_URL, sep=r"\s+")
oni = oni.rename(columns={"YR": "year", "ANOM": "oni"})

# 2. Each season is centred on one month (DJF is centred on January, etc.)
centre_month = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
                "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
oni["month"] = oni["SEAS"].map(centre_month)
oni.to_csv("oni_monthly.csv", index=False)

# 3. One El Nino number per year: the average ONI from July to October,
#    which is when the monsoon seasons are building up.
season = oni[(oni["month"] >= 7) & (oni["month"] <= 10)]
oni_year = season.groupby("year")["oni"].mean().rename("oni_jul_oct")

def phase(value):
    if value >= 0.5:
        return "El Nino"
    if value <= -0.5:
        return "La Nina"
    return "Neutral"

# 4. Load rainfall and work out yearly totals
weather = pd.read_csv("tn_weather_daily.csv", parse_dates=["date"])
weather["year"] = weather["date"].dt.year
weather["month"] = weather["date"].dt.month

yearly = weather.groupby(["district", "year"])["rainfall_mm"].sum().unstack(0)

# North-east monsoon (Oct to Dec) is the main rainy season for Tamil Nadu
nem = weather[weather["month"] >= 10].groupby(["district", "year"])["rainfall_mm"].sum().unstack(0)

# 5. Join rainfall with El Nino data
table = yearly.join(oni_year, how="left")
table["phase"] = table["oni_jul_oct"].apply(phase)
print("Yearly rainfall (mm) with El Nino phase:")
print(table.round(1))
print()

# 6. Does El Nino go together with rainfall? (correlation: -1 to +1)
print("Correlation between ONI and TOTAL yearly rainfall:")
for d in yearly.columns:
    print("  ", d, round(yearly[d].corr(oni_year), 2))
print()
print("Correlation between ONI and OCT-DEC (north-east monsoon) rainfall:")
for d in nem.columns:
    print("  ", d, round(nem[d].corr(oni_year), 2))
print()
print("Note: with only ~24 years of data, treat these numbers as hints, not proof.")

# 7. Chart: Oct-Dec rainfall of one district against El Nino strength
district = list(nem.columns)[0]
colors = table["phase"].map({"El Nino": "red", "La Nina": "blue", "Neutral": "gray"})
plt.figure(figsize=(8, 5))
plt.scatter(oni_year.reindex(nem.index), nem[district], c=colors, s=70)
plt.axvline(0.5, color="red", linestyle="--", alpha=0.4)
plt.axvline(-0.5, color="blue", linestyle="--", alpha=0.4)
plt.title(district + ": Oct-Dec rainfall vs El Nino index")
plt.xlabel("ONI (average Jul-Oct)")
plt.ylabel("Oct-Dec rainfall (mm)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("elnino_vs_rainfall.png", dpi=150)
print("Saved elnino_vs_rainfall.png and oni_monthly.csv")
plt.show()