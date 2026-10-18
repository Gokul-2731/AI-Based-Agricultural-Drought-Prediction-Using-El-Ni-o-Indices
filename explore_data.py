# explore_data.py
# Step 2: look at the weather data, find yearly rainfall and spot dry years.
# Needs: pip install matplotlib

import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the file made by get_weather_data.py
weather = pd.read_csv("tn_weather_daily.csv", parse_dates=["date"])
weather["year"] = weather["date"].dt.year

# 2. Basic health check: how many rows and how many missing values?
print("Rows:", len(weather))
print("Missing values per column:")
print(weather.isna().sum())
print()

# 3. Total rainfall per year for each district (mm)
yearly = weather.groupby(["district", "year"])["rainfall_mm"].sum().unstack(0)
print("Yearly rainfall (mm):")
print(yearly.round(0))
print()

# 4. Simple dry-year rule for learning:
#    a year is "dry" if rainfall is below 80% of that district's average.
average = yearly.mean()
dry_years = yearly < (0.8 * average)
for district in yearly.columns:
    years = list(yearly.index[dry_years[district]])
    print(district, "- average:", round(average[district]), "mm - dry years:", years)

# 5. Chart 1: yearly rainfall for every district
yearly.plot(figsize=(11, 5), marker="o")
plt.title("Yearly rainfall by district")
plt.xlabel("Year")
plt.ylabel("Rainfall (mm)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("yearly_rainfall.png", dpi=150)

# 6. Chart 2: average rainfall in each month (shows the monsoon pattern)
weather["month"] = weather["date"].dt.month
monthly = weather.groupby(["district", "month", "year"])["rainfall_mm"].sum()
monthly = monthly.groupby(["district", "month"]).mean().unstack(0)
monthly.plot(kind="bar", figsize=(11, 5))
plt.title("Average monthly rainfall by district")
plt.xlabel("Month (1 = Jan, 12 = Dec)")
plt.ylabel("Rainfall (mm)")
plt.tight_layout()
plt.savefig("monthly_rainfall.png", dpi=150)

print()
print("Saved yearly_rainfall.png and monthly_rainfall.png")
plt.show()