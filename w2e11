import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import requests
from iceweather import forecast_for_closest

# 1) Define locations
LOCATIONS = {
    "Reykjavik":   {"lat": 64.1466, "lon": -21.9426},
    "Akureyri":    {"lat": 65.6885, "lon": -18.1262},
    "Egilsstaðir": {"lat": 65.2672, "lon": -14.3948},
    "Ísafjörður":  {"lat": 66.0750, "lon": -23.1301},
    "Höfn":        {"lat": 64.2539, "lon": -15.2082},
}

# 2) Compute next weekend
today = date.today()
days_until_sat = (5 - today.weekday() + 7) % 7 or 7
sat = today + timedelta(days=days_until_sat)
sun = sat + timedelta(days=1)
TARGET = {sat, sun}

# 3) Data-fetchers
@st.cache(ttl=3600)
def fetch_yr(lat, lon):
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    headers = {"User-Agent": "live-weather-dashboard"}
    r = requests.get(url, headers=headers).json()["properties"]["timeseries"]
    pts = []
    for ts in r:
        t = datetime.fromisoformat(ts["time"].rstrip("Z"))
        if t.date() in TARGET and t.hour == 12:
            d = ts["data"]
            pts.append({
                "precip": d["next_1_hours"]["details"]["precipitation_amount"],
                "cloud":  d["instant"]["details"]["cloud_area_fraction"],
                "temp":   d["instant"]["details"]["air_temperature"],
            })
    return pd.DataFrame(pts).mean().to_dict()

@st.cache(ttl=3600)
def fetch_vedur(lat, lon):
    res = forecast_for_closest(lat, lon)
    pts = []
    for e in res["results"]:
        t = datetime.strptime(e["ftime"], "%Y-%m-%d %H:%M:%S")
        if t.date() in TARGET and t.hour == 12:
            pts.append({
                "precip": float(e.get("R", 0)),
                "cloud":  float(e.get("N", 0)),
                "temp":   float(e.get("T", 0)),
            })
    return pd.DataFrame(pts).mean().to_dict()

# 4) Build and display
st.title("Next Weekend’s Best Weather in Iceland")
rows = []
for name, coord in LOCATIONS.items():
    yr   = fetch_yr(**coord)
    ved  = fetch_vedur(**coord)
    score = ((1/(1+yr["precip"]))*(1-yr["cloud"]/100) + (1/(1+ved["precip"]))*(1-ved["cloud"]/100)) / 2
    rows.append({
        "Location":       name,
        "Yr precip (mm)": round(yr["precip"], 2),
        "Vedur precip":   round(ved["precip"],  2),
        "Yr cloud (%)":   round(yr["cloud"],   1),
        "Vedur cloud (%)":round(ved["cloud"],  1),
        "Score":          round(score, 3),
    })
df = pd.DataFrame(rows).sort_values("Score", ascending=False)
st.dataframe(df, use_container_width=True)
st.caption("Higher score ⇒ better (drier/clearer) forecast.")
