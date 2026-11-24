# src/collect.py
import requests
import pandas as pd
from pathlib import Path
LAT, LON = 33.68, 73.05
TZ = "Asia/Karachi"
CSV = Path("data/raw/islamabad_aqi.csv")
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL = "https://api.open-meteo.com/v1/forecast"
AQ_VARS = ["pm2_5", "pm10", "nitrogen_dioxide", "sulphur_dioxide",
           "ozone", "carbon_monoxide", "us_aqi"]
WX_VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m",
           "surface_pressure", "precipitation"]
def fetch(url, variables, past_days=3):
    params = {"latitude": LAT, "longitude": LON,
              "hourly": ",".join(variables),
              "past_days": past_days, "forecast_days": 1,
              "timezone": TZ}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df
def main():
    aq = fetch(AQ_URL, AQ_VARS)
    wx = fetch(WX_URL, WX_VARS)
    new = aq.merge(wx, on="time", how="inner")
    # keep only hours that have already finished
    now = pd.Timestamp.now(tz=TZ).tz_localize(None).floor("h")
    new = new[new["time"] < now]
    CSV.parent.mkdir(parents=True, exist_ok=True)
    if CSV.exists():
        old = pd.read_csv(CSV, parse_dates=["time"])
        new = pd.concat([old, new])
    new = (new.drop_duplicates(subset="time", keep="last")
              .sort_values("time"))
    new.to_csv(CSV, index=False)
    print(f"Saved {len(new)} rows, last hour: {new['time'].max()}")
if __name__ == "__main__":
    main()