# load_data.py
# Step 6: put your two CSV files into the MySQL database.
#   - tn_weather_daily.csv  ->  districts + weather_daily
#   - oni_monthly.csv       ->  enso_index
# Needs: pip install mysql-connector-python
# Safe to run again: existing rows are updated, nothing is duplicated.

import getpass
import pandas as pd
import mysql.connector
from mysql.connector import Error

# 1. Connection settings. Change HOST/USER only if yours are different.
HOST = "localhost"
USER = "root"
PASSWORD = getpass.getpass("MySQL password (typing is hidden, press Enter after): ")
DATABASE = "fieldwatch"

# The 5 starter districts (same as get_weather_data.py)
DISTRICTS = {
    "Chennai":        (13.08, 80.27),
    "Madurai":        (9.92, 78.12),
    "Thanjavur":      (10.79, 79.14),
    "Coimbatore":     (11.00, 76.96),
    "Ramanathapuram": (9.37, 78.83),
}


def clean(table):
    """MySQL understands None, not NaN, for 'no data'."""
    return table.astype(object).where(table.notna(), None)


def oni_phase(value):
    if value >= 0.5:
        return "El Nino"
    if value <= -0.5:
        return "La Nina"
    return "Neutral"


def insert_in_batches(cursor, sql, rows, batch_size=5000):
    for start in range(0, len(rows), batch_size):
        cursor.executemany(sql, rows[start:start + batch_size])


try:
    # 2. Connect to MySQL (no database yet, because schema.sql creates it)
    connection = mysql.connector.connect(host=HOST, user=USER, password=PASSWORD)
    cursor = connection.cursor()
    print("Connected to MySQL.")

    # 3. Run schema.sql to create the database and tables
    with open("schema.sql", encoding="utf-8") as f:
        statements = [s.strip() for s in f.read().split(";") if s.strip()]
    for statement in statements:
        cursor.execute(statement)
    connection.commit()
    print("Tables are ready.")

    # 4. Districts
    for name, (lat, lon) in DISTRICTS.items():
        cursor.execute(
            "INSERT INTO districts (name, latitude, longitude) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE latitude = VALUES(latitude), longitude = VALUES(longitude)",
            (name, lat, lon),
        )
    connection.commit()
    cursor.execute("SELECT name, district_id FROM districts")
    district_id = dict(cursor.fetchall())

    # 5. Weather: read the CSV, then insert row by row (in batches)
    weather = pd.read_csv("tn_weather_daily.csv", parse_dates=["date"])
    weather["district_id"] = weather["district"].map(district_id)
    weather["obs_date"] = weather["date"].dt.strftime("%Y-%m-%d")
    weather = clean(weather[["district_id", "obs_date", "rainfall_mm", "temp_avg_c",
                             "temp_max_c", "temp_min_c", "humidity_pct"]])
    rows = list(weather.itertuples(index=False, name=None))
    print("Loading", len(rows), "weather rows (this can take a minute)...")
    insert_in_batches(cursor, """
        INSERT INTO weather_daily
          (district_id, obs_date, rainfall_mm, temp_avg_c, temp_max_c, temp_min_c, humidity_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          rainfall_mm = VALUES(rainfall_mm), temp_avg_c = VALUES(temp_avg_c),
          temp_max_c = VALUES(temp_max_c), temp_min_c = VALUES(temp_min_c),
          humidity_pct = VALUES(humidity_pct)
    """, rows)
    connection.commit()

    # 6. El Nino index
    oni = pd.read_csv("oni_monthly.csv").dropna(subset=["oni"])
    oni_rows = [(int(r.year), int(r.month), r.SEAS, float(r.oni), oni_phase(r.oni))
                for r in oni.itertuples(index=False)]
    insert_in_batches(cursor, """
        INSERT INTO enso_index (year, month, season, oni, phase)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE season = VALUES(season), oni = VALUES(oni), phase = VALUES(phase)
    """, oni_rows)
    connection.commit()

    # 7. Check the result
    cursor.execute(f"USE {DATABASE}")
    print()
    print("Rows now in the database:")
    for table in ["districts", "weather_daily", "enso_index"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        print("  ", table, ":", cursor.fetchone()[0])
    print("Done!")

except Error as error:
    print()
    print("MySQL problem:", error)
    print("Check that MySQL is running and that the user and password are right.")
except FileNotFoundError as error:
    print()
    print("Missing file:", error.filename, "- run this script from your project folder.")
else:
    cursor.close()
    connection.close()
