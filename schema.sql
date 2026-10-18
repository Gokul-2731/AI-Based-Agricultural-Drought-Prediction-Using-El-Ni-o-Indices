-- schema.sql
-- Creates the Fieldwatch database and its first tables.
-- Run by load_data.py, or paste into MySQL Workbench and run it yourself.
-- Safe to run again: "IF NOT EXISTS" means it will not delete anything.

CREATE DATABASE IF NOT EXISTS fieldwatch
  CHARACTER SET utf8mb4;      -- utf8mb4 lets us store Tamil and Hindi text later

USE fieldwatch;


-- 1. DISTRICTS: one row per district we have data for
CREATE TABLE IF NOT EXISTS districts (
  district_id  INT AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(60) NOT NULL UNIQUE,
  latitude     DECIMAL(8,5) NOT NULL,
  longitude    DECIMAL(8,5) NOT NULL
);


-- 2. WEATHER_DAILY: the NASA POWER data (one row per district per day)
--    NULL means "no data for that day".
CREATE TABLE IF NOT EXISTS weather_daily (
  district_id   INT NOT NULL,
  obs_date      DATE NOT NULL,
  rainfall_mm   FLOAT NULL,
  temp_avg_c    FLOAT NULL,
  temp_max_c    FLOAT NULL,
  temp_min_c    FLOAT NULL,
  humidity_pct  FLOAT NULL,
  PRIMARY KEY (district_id, obs_date),          -- no district can have two rows for one day
  FOREIGN KEY (district_id) REFERENCES districts (district_id)
);


-- 3. ENSO_INDEX: the El Nino (ONI) value for each month
CREATE TABLE IF NOT EXISTS enso_index (
  year      SMALLINT NOT NULL,
  month     TINYINT NOT NULL,
  season    CHAR(3) NOT NULL,          -- for example DJF, JFM
  oni       FLOAT NOT NULL,
  phase     VARCHAR(10) NOT NULL,      -- El Nino, La Nina or Neutral
  PRIMARY KEY (year, month)
);


-- 4. FORECASTS: every forecast the app makes (filled by app.py later)
--    Keeping them lets you check afterwards how accurate they were.
CREATE TABLE IF NOT EXISTS forecasts (
  forecast_id        INT AUTO_INCREMENT PRIMARY KEY,
  district_id        INT NOT NULL,
  made_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
  based_on_month     VARCHAR(10),          -- for example Sep 2026
  forecast_months    VARCHAR(20),          -- for example Oct,Nov,Dec
  predicted_rain_mm  FLOAT,
  normal_rain_mm     FLOAT,
  percent_of_normal  INT,
  risk_label         VARCHAR(100),
  oni_used           FLOAT,
  FOREIGN KEY (district_id) REFERENCES districts (district_id)
);


-- 5. CROPS: typical facts about each crop (you will fill this by hand from
--    TNAU and government reports, so keep the source and year)
CREATE TABLE IF NOT EXISTS crops (
  crop_id                 INT AUTO_INCREMENT PRIMARY KEY,
  name                    VARCHAR(60) NOT NULL UNIQUE,
  season                  VARCHAR(40),
  growing_days            INT,
  water_need              VARCHAR(20),        -- low, medium or high
  cost_per_acre           DECIMAL(10,2),      -- rupees
  yield_per_acre_quintal  DECIMAL(8,2),
  source                  VARCHAR(120),
  source_year             SMALLINT
);


-- 6. CROP_PRICES: daily prices (filled from Consumer Affairs and Agmarknet later)
--    price_type tells us if it is a retail or a wholesale (mandi) price.
CREATE TABLE IF NOT EXISTS crop_prices (
  price_id           INT AUTO_INCREMENT PRIMARY KEY,
  crop_id            INT NOT NULL,
  district_id        INT NULL,                -- NULL if the price is for the whole state
  price_date         DATE NOT NULL,
  price_per_quintal  DECIMAL(10,2) NOT NULL,  -- convert kg prices: price per kg x 100
  price_type         ENUM('retail', 'wholesale') NOT NULL,
  source             VARCHAR(80),
  FOREIGN KEY (crop_id) REFERENCES crops (crop_id),
  FOREIGN KEY (district_id) REFERENCES districts (district_id)
);
