import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta, datetime
from iceweather import forecast_for_closest

# 1) Locations to compare
LOCATIONS = {
    "Reykjavik":   {"lat": 64.1466, "lon": -21.9426},
    "Akureyri":    {"lat": 65.6885, "lon": -18.1262},
    "Egilsstaðir": {"lat": 65.2672, "lon": -14.3948},
    "Ísafjörður":  {"lat": 66.0750, "lon": -23.1301},
    "Höfn":        {"lat": 64.2539, "lon": -15.2082},
}

# 2) Compute next weekend dates
today = date.today()
days_until_sat = (5 - today.weekday() + 7) % 7 or 7
sat = today + timedelta(days=days_until_sat)
sun = sat + timedelta(days=1)
TARGET_DATES = {sat, sun}

# 3) Fetchers with new caching decorator and key-checks

@st.cache_data(ttl=3600)
def fetch_yr(lat, lon):
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    headers = {"User-Agent": "live-weather-dashboard"}
    data = requests.get(url, headers=headers).json()["properties"]["timeseries"]
    pts = []
    for ts in data:
        t = datetime.fromisoformat(ts["time"].rstrip("Z"))
        if t.date() in TARGET_DATES and t.hour == 12:
            d = ts["data"]
            # skip if no next_1_hours block
            if "next_1_hours" not in d or d["next_1_hours"] is None:
                continue
            details = d["next_1_hours"]["details"]
            inst    = d["instant"]["details"]
            precip = details.get("precipitation_amount", 0.0)
            cloud  = inst.get("cloud_area_fraction", 0.0)
            temp   = inst.get("air_temperature", None)
            if temp is None:
                continue
            pts.append({"precip": precip, "cloud": cloud, "temp": temp})
    if not pts:
        return {"precip": 0.0, "cloud": 0.0, "temp": None}
    df = pd.DataFrame(pts)
    return df.mean().to_dict()

@st.cache_data(ttl=3600)
def fetch_vedur(lat, lon):
    res = forecast_for_closest(lat, lon)
    pts = []
    for e in res["results"]:
        t = datetime.strptime(e["ftime"], "%Y-%m-%d %H:%M:%S")
        if t.date() in TARGET_DATES and t.hour == 12:
            pts.append({
                "precip": float(e.get("R", 0)),
                "cloud":  float(e.get("N", 0)),
                "temp":   float(e.get("T", 0)),
            })
    if not pts:
        return {"precip": 0.0, "cloud": 0.0, "temp": None}
    df = pd.DataFrame(pts)
    return df.mean().to_dict()

# 4) Build and display dashboard
st.title("Next Weekend’s Best Weather in Iceland")

rows = []
for name, coord in LOCATIONS.items():
    yr   = fetch_yr(**coord)
    ved  = fetch_vedur(**coord)
    # guard against None temps
    score_yr   = (1/(1+yr["precip"])) * (1 - yr["cloud"]/100)
    score_ved  = (1/(1+ved["precip"])) * (1 - ved["cloud"]/100)
    score      = (score_yr + score_ved) / 2
    rows.append({
        "Location":        name,
        "Yr precip (mm)":  round(yr["precip"],  2),
        "Vedur precip":    round(ved["precip"],  2),
        "Yr cloud (%)":    round(yr["cloud"],    1),
        "Vedur cloud (%)": round(ved["cloud"],   1),
        "Score (0–1)":     round(score,         3),
    })

df = pd.DataFrame(rows).sort_values("Score (0–1)", ascending=False)
st.dataframe(df, use_container_width=True)
st.caption("Higher score ⇒ drier & clearer next weekend")
