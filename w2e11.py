import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta, datetime
from iceweather import forecast_for_closest

# … your LOCATIONS and TARGET_DATES as before …

@st.cache_data(ttl=3600)
def fetch_vedur(lat, lon):
    pts = []
    try:
        res = forecast_for_closest(lat, lon)
        results = res.get("results", []) if isinstance(res, dict) else []
    except Exception:
        results = []
    for e in results:
        # parse only Sat/Sun @12 UTC
        try:
            t = datetime.strptime(e.get("ftime", ""), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if t.date() in TARGET_DATES and t.hour == 12:
            precip = float(e.get("R", 0))
            cloud  = float(e.get("N", 0))
            temp   = float(e.get("T", 0))
            pts.append({"precip": precip, "cloud": cloud, "temp": temp})
    if not pts:
        return {"precip": 0.0, "cloud": 0.0, "temp": None}
    return pd.DataFrame(pts).mean().to_dict()

# … fetch_yr (with st.cache_data and KeyError guard) and rest of your app …
