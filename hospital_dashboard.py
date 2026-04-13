import random
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

DB_PATH = Path("hospital_live.db")
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = {
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
}

DEPARTMENTS = [
    "Trauma",
    "Cardiology",
    "General Medicine",
    "Pediatrics",
    "Orthopedics",
    "Neurology",
]

WEATHER_CODE_MAP = {
    0: "Clear",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Cloudy",
    45: "Fog",
    48: "Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Light Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Light Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    80: "Rain Showers",
    81: "Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm",
}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            patient_id TEXT,
            triage_level INTEGER,
            wait_time INTEGER,
            department TEXT,
            city TEXT,
            weather_flag TEXT
        )
    """)
    conn.commit()
    conn.close()


@st.cache_data(ttl=60)
def get_live_weather(city):
    info = CITIES[city]
    r = requests.get(
        WEATHER_API_URL,
        params={
            "latitude": info["lat"],
            "longitude": info["lon"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "timezone": "auto",
        },
        timeout=10,
    )
    r.raise_for_status()
    current = r.json().get("current", {})

    code = current.get("weather_code", -1)
    temp = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    wind = current.get("wind_speed_10m")
    condition = WEATHER_CODE_MAP.get(code, "Unknown")

    if code in {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}:
        impact = "Rain/Storm"
    elif temp is not None and temp >= 35:
        impact = "Heat"
    else:
        impact = "Normal"

    return {
        "City": city,
        "Condition": condition,
        "Temp (°C)": temp,
        "Humidity (%)": humidity,
        "Wind (km/h)": wind,
        "Impact": impact,
    }


def weather_snapshot():
    rows = []
    for city in CITIES:
        try:
            rows.append(get_live_weather(city))
        except Exception:
            rows.append({
                "City": city,
                "Condition": "Unavailable",
                "Temp (°C)": None,
                "Humidity (%)": None,
                "Wind (km/h)": None,
                "Impact": "Unknown",
            })
    return pd.DataFrame(rows)


def generate_patient():
    city = random.choice(list(CITIES.keys()))

    try:
        weather = get_live_weather(city)
        impact = weather["Impact"]
    except Exception:
        impact = "Unknown"

    triage = random.randint(1, 5)

    if impact == "Heat":
        wait_time = random.randint(15, 90)
    elif impact == "Rain/Storm":
        wait_time = random.randint(20, 100)
    else:
        wait_time = random.randint(5, 70)

    if impact in ["Heat", "Rain/Storm"] and random.random() < 0.35:
        triage = random.choice([1, 2, 3])

    return {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_id": f"PT-{random.randint(1000, 9999)}",
        "triage_level": triage,
        "wait_time": wait_time,
        "department": random.choice(DEPARTMENTS),
        "city": city,
        "weather_flag": impact,
    }


def insert_patient(row):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO patients(ts, patient_id, triage_level, wait_time, department, city, weather_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["ts"],
            row["patient_id"],
            row["triage_level"],
            row["wait_time"],
            row["department"],
            row["city"],
            row["weather_flag"],
        ),
    )
    conn.commit()
    conn.close()


def simulator():
    while True:
        insert_patient(generate_patient())
        time.sleep(60)


def seed_if_empty():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    conn.close()

    if count == 0:
        for _ in range(12):
            insert_patient(generate_patient())


def start_background_thread():
    if "hospital_sim_started" not in st.session_state:
        threading.Thread(target=simulator, daemon=True).start()
        st.session_state.hospital_sim_started = True


def load_patients():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM patients ORDER BY id DESC", conn)
    conn.close()
    return df


def hospital_view():
    patients = load_patients()
    weather = weather_snapshot()

    occupancy = int(len(patients)) if not patients.empty else 0
    avg_wait = float(patients["wait_time"].mean()) if not patients.empty else 0
    critical_patients = (
        int(patients["triage_level"].isin([1, 2]).sum())
        if not patients.empty
        else 0
    )

    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #08131a 0%, #101d2a 100%);
            color: white;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
        }
        .title-box {
            background: linear-gradient(90deg, rgba(255,77,109,.12), rgba(72,202,228,.05));
            border: 1px solid rgba(255,77,109,.25);
            padding: 18px 22px;
            border-radius: 16px;
            margin-bottom: 18px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="title-box">
            <h1 style="margin:0; color:#f7fbff;">🏥 ER Command Center + Live Weather</h1>
            <p style="margin:6px 0 0 0; color:#b7d5df;">
                Live patient feed, critical triage alerts, and weather-linked admission pressure.
            </p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Current ER Occupancy", occupancy)
    c2.metric("Average Wait Time", f"{avg_wait:.0f} min")
    c3.metric("Critical Triage Patients", critical_patients)

    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("Live Patient Feed")
        if not patients.empty:
            st.dataframe(
                patients[
                    ["ts", "patient_id", "triage_level", "wait_time", "department", "city", "weather_flag"]
                ].head(12),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No patient feed available yet.")

        st.subheader("Occupancy by Department")
        if not patients.empty:
            dept = (
                patients.groupby("department", as_index=False)["patient_id"]
                .count()
                .rename(columns={"patient_id": "patients"})
            )
            st.bar_chart(dept.set_index("department"))
        else:
            st.info("Department occupancy data not available.")

        st.subheader("Admissions Over Time")
        if not patients.empty:
            trend = patients.copy()
            trend["ts"] = pd.to_datetime(trend["ts"])
            trend = trend.sort_values("ts")
            trend = trend.groupby("ts", as_index=False)["patient_id"].count()
            trend = trend.rename(columns={"patient_id": "admissions"})
            trend = trend.set_index("ts")
            st.line_chart(trend)
        else:
            st.info("Admission trend data not available.")

    with right:
        st.subheader("Live Weather by City")
        st.dataframe(weather, use_container_width=True, hide_index=True)

        risk = weather[weather["Impact"].isin(["Heat", "Rain/Storm"])]
        if not risk.empty:
            cities = ", ".join(risk["City"].tolist())
            st.warning(f"⚠ Extreme weather active in: {cities}")
        else:
            st.success("✅ Weather conditions stable right now.")

        if critical_patients > 0:
            st.error(f"🚨 Critical triage alert: {critical_patients} patient(s) need immediate attention.")
        else:
            st.success("No critical triage patients at this moment.")

        st.subheader("Weather Impact Summary")
        impact_counts = weather["Impact"].value_counts()
        st.bar_chart(impact_counts)


def main():
    st.set_page_config(
        page_title="ER Command Center",
        page_icon="🏥",
        layout="wide"
    )

    init_db()
    seed_if_empty()
    start_background_thread()

    refresh = st.sidebar.slider("Auto refresh (sec)", 5, 60, 10)
    st.sidebar.markdown("### Dashboard Controls")
    st.sidebar.info("Fake patients every 60 seconds + live weather updates.")
    st.sidebar.code("python -m streamlit run hospital_dashboard.py")

    hospital_view()

    time.sleep(refresh)
    st.rerun()


if __name__ == "__main__":
    main()