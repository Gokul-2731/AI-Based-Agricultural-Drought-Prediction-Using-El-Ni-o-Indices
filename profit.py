# profit.py
# Step 7: the profit or loss calculation and the crop suggestions.
# app.py uses this file. It does NOT talk to the internet or to MySQL,
# so you can read it, test it and change the numbers easily.
#
# IMPORTANT: the crop numbers below are SAMPLE ESTIMATES to make the app work.
# Replace them with real values from TNAU, the Tamil Nadu agriculture department
# and CACP reports (your teammate can later move them into the MySQL "crops" table).

import numpy as np

# ---------- 1. Crop data (SAMPLE ESTIMATES, per acre, per season) ----------
# cost_per_acre      : money spent on seeds, labour, fertiliser, water (rupees)
# yield_q_per_acre   : harvest in quintals (1 quintal = 100 kg)
# price_per_q        : selling price per quintal (rupees)
# drought_sensitivity: 0 to 1. How much the harvest falls when rain is below normal.
#                      0.9 = very sensitive (rice), 0.25 = tolerant (millets)
# growing_days       : days from sowing to harvest
CROPS = {
    "rice":      {"name": "Rice (paddy)",     "cost_per_acre": 34000, "yield_q_per_acre": 20,  "price_per_q": 2300, "drought_sensitivity": 0.90, "growing_days": 120},
    "groundnut": {"name": "Groundnut",        "cost_per_acre": 28000, "yield_q_per_acre": 7,   "price_per_q": 6500, "drought_sensitivity": 0.50, "growing_days": 105},
    "millets":   {"name": "Millets (ragi)",   "cost_per_acre": 16000, "yield_q_per_acre": 7,   "price_per_q": 4200, "drought_sensitivity": 0.25, "growing_days": 120},
    "maize":     {"name": "Maize",            "cost_per_acre": 24000, "yield_q_per_acre": 18,  "price_per_q": 2200, "drought_sensitivity": 0.60, "growing_days": 110},
    "cotton":    {"name": "Cotton",           "cost_per_acre": 42000, "yield_q_per_acre": 7,   "price_per_q": 7000, "drought_sensitivity": 0.50, "growing_days": 180},
    "sugarcane": {"name": "Sugarcane",        "cost_per_acre": 65000, "yield_q_per_acre": 350, "price_per_q": 340,  "drought_sensitivity": 0.80, "growing_days": 360},
    "pulses":    {"name": "Pulses (black gram)", "cost_per_acre": 14000, "yield_q_per_acre": 3, "price_per_q": 7400, "drought_sensitivity": 0.30, "growing_days": 75},
}

# ---------- 2. How unsure are we? (also assumptions) ----------
RAIN_UNCERTAINTY = 25      # the forecast can be wrong by about 25 percentage points of "normal"
YIELD_NOISE = 0.10         # harvests vary by about 10% even in the same weather
PRICE_NOISE = 0.12         # prices move by about 12% between sowing and selling
SIMULATIONS = 2000         # how many "possible seasons" we imagine


def estimate(crop_key, area_acres, rain_percent):
    """Estimate profit or loss for one crop.
    rain_percent = forecast rain as a % of normal (100 = normal, 60 = very dry)."""
    crop = CROPS[crop_key]
    if rain_percent is None:
        rain_percent = 100

    # The same random numbers each time, so the same question gives the same answer
    rng = np.random.default_rng(42)

    # Imagine 2000 possible seasons. Rain varies around what the model forecast.
    rain = np.clip(rng.normal(rain_percent, RAIN_UNCERTAINTY, SIMULATIONS), 20, 200)

    # Less rain than normal lowers the harvest, more for sensitive crops.
    # Very heavy rain (over 130% of normal) also hurts a little.
    dry_loss = crop["drought_sensitivity"] * np.clip((100 - rain) / 100, 0, None)
    wet_loss = 0.10 * np.clip((rain - 130) / 100, 0, None)
    yield_factor = np.clip((1 - dry_loss - wet_loss) * rng.normal(1, YIELD_NOISE, SIMULATIONS), 0, None)

    price = crop["price_per_q"] * rng.normal(1, PRICE_NOISE, SIMULATIONS)

    harvest = crop["yield_q_per_acre"] * area_acres * yield_factor      # quintals
    income = harvest * price
    cost = crop["cost_per_acre"] * area_acres
    profit = income - cost

    # What the forecast alone does to the harvest (no random noise)
    forecast_factor = 1 - crop["drought_sensitivity"] * max(0, (100 - rain_percent) / 100)

    return {
        "crop": crop_key,
        "crop_name": crop["name"],
        "area_acres": area_acres,
        "chance_of_profit_percent": int(round(100 * np.mean(profit > 0))),
        "expected_profit": int(round(np.mean(profit))),
        "likely_range": [int(round(np.percentile(profit, 10))), int(round(np.percentile(profit, 90)))],
        "cost": int(round(cost)),
        "expected_income": int(round(np.mean(income))),
        "expected_harvest_q": round(float(np.mean(harvest)), 1),
        "yield_change_from_rain_percent": int(round((forecast_factor - 1) * 100)),
        "growing_days": crop["growing_days"],
        "profit_per_month": int(round(np.mean(profit) / (crop["growing_days"] / 30))),
    }


def suggest(area_acres, rain_percent, how_many=3):
    """Try every crop and return the best ones.
    Ranked by expected profit per month of growing, so a 12-month crop does not
    win just because it takes longer."""
    results = [estimate(key, area_acres, rain_percent) for key in CROPS]
    results.sort(key=lambda r: r["profit_per_month"], reverse=True)
    return results[:how_many]


if __name__ == "__main__":
    # Quick test: run  python profit.py  to see an example in the terminal
    for rain in (100, 60):
        print("Rain forecast =", rain, "% of normal, 2 acres:")
        for r in suggest(2, rain, how_many=7):
            print("  ", r["crop_name"].ljust(20), "profit chance", r["chance_of_profit_percent"], "%",
                  "| expected profit Rs", r["expected_profit"])
        print()