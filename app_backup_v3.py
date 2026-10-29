"""
app.py — S.H.I.E.L.D. Scour Sense v3
Streams historical validation data (15% split) and predicts in real-time.
Multilanguage (EN/HI/MR) · Auto-save · Folium map
"""
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from translations import TRANSLATIONS

# ---------------------------------------------------------------- page setup
st.set_page_config(page_title="S.H.I.E.L.D. Scour Sense", layout="wide")

# ---------------------------------------------------------------- language selector
with st.sidebar:
    lang_choice = st.selectbox("🌐 Language", ["English", "हिंदी", "मराठी"])
T = TRANSLATIONS[lang_choice]

# ---------------------------------------------------------------- header
st.title(f"🛡️ {T['title']}")
st.caption(T["subtitle"])
st.caption("Demo Mode — PWD Admin")

# ---------------------------------------------------------------- load model & data
model = joblib.load("models/scour_model.joblib")
FEATURES = joblib.load("models/feature_names.joblib")

try:
    df = pd.read_csv("data/predict_15.csv")
except FileNotFoundError:
    st.error("Data not found. Please run `python generate_dataset.py` first.")
    st.stop()

# Bridge thresholds
GREEN_MAX = 2.20
AMBER_MAX = 3.00
AUTOSAVE_PATH = "outputs/autosave_predictions.csv"

# Load forecast models if they exist
FORECAST_24 = None
FORECAST_48 = None
if os.path.exists("models/scour_model_24h.joblib"):
    FORECAST_24 = joblib.load("models/scour_model_24h.joblib")
if os.path.exists("models/scour_model_48h.joblib"):
    FORECAST_48 = joblib.load("models/scour_model_48h.joblib")

# ---------------------------------------------------------------- sidebar controls
with st.sidebar:
    st.markdown("---")
    speed = st.slider(T["speed"], 0.01, 0.2, 0.02, step=0.01)
    flood_btn = st.button(f"🌊 {T['flood_button']}", use_container_width=True)
    st.markdown("---")
    st.markdown(f"**{T['thresholds']}**")
    st.markdown(f"🟢 < **{GREEN_MAX:.2f} m**")
    st.markdown(f"🟡 **{GREEN_MAX:.2f} – {AMBER_MAX:.2f} m**")
    st.markdown(f"🔴 **> {AMBER_MAX:.2f} m**")
    st.markdown("---")
    st.markdown("**Sensor node**")
    st.markdown("Sonar · Accelerometer · Solar IP68")
    st.markdown("---")

# ---------------------------------------------------------------- tabs
tab_live, tab_fc, tab_map, tab_charts, tab_alerts = st.tabs([
    f"📊 {T['tab_live']}",
    f"🔮 {T['tab_forecast']}",
    f"🗺️ {T['tab_map']}",
    f"📈 {T['tab_charts']}",
    f"🚨 {T['tab_alerts']}",
])

# ================================================================ TAB 1: LIVE
with tab_live:
    # Limit to 30 steps to prevent freezing other tabs
    stream_df = df.iloc[:30].reset_index(drop=True)

    placeholder = st.empty()
    history_scour = []
    history_actual = []
    alert_log = []

    for i, row in stream_df.iterrows():
        X_live = pd.DataFrame([[
            row["discharge_m3s"], row["flow_depth_m"], row["velocity_ms"],
            row["froude"], row["b_over_y"], row["rate_of_scour_m_hr"]
        ]], columns=FEATURES)
        
        scour_pred = float(model.predict(X_live)[0])
        actual_scour = float(row["sonar_scour_m"])
        display_q = row["discharge_m3s"]

        history_scour.append(scour_pred)
        history_actual.append(actual_scour)
        if len(history_scour) > 100:
            history_scour = history_scour[-100:]
            history_actual = history_actual[-100:]

        if scour_pred >= AMBER_MAX:
            status_key, color = "red", "#d62728"
        elif scour_pred >= GREEN_MAX:
            status_key, color = "amber", "#ff9800"
        else:
            status_key, color = "green", "#2ca02c"

        # Auto-save safely
        if i % 5 == 0:
            os.makedirs("outputs", exist_ok=True)
            pd.DataFrame({
                "timestamp": [row["timestamp"]],
                "predicted_scour": [round(scour_pred, 4)],
                "actual_scour": [round(actual_scour, 4)],
                "risk": [status_key],
            }).to_csv(
                AUTOSAVE_PATH, mode="a",
                header=not os.path.exists(AUTOSAVE_PATH), index=False,
            )

        if status_key in ("red", "amber") and (not alert_log or alert_log[-1]["level"] != status_key):
            alert_log.append({
                "time": row["timestamp"], "level": status_key, "scour_m": round(scour_pred, 2),
            })

        with placeholder.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("AI Predicted Scour", f"{scour_pred:.2f} m", delta=f"{scour_pred - actual_scour:+.2f} vs actual")
            c2.metric("Actual Sensor", f"{actual_scour:.2f} m")
            c3.metric(T["discharge"], f"{display_q:.0f} m³/s")
            c4.metric(T["froude"], f"{row['froude']:.2f}")

            st.markdown(f"<h2 style='color:{color}'>{T[status_key]}</h2>", unsafe_allow_html=True)
            st.progress(min(scour_pred / (AMBER_MAX * 1.2), 1.0))
            
            chart_data = pd.DataFrame({
                "AI Predicted": history_scour,
                "Actual Sonar": history_actual
            })
            st.line_chart(chart_data, height=250)

            if status_key == "red":
                st.error(f"🚨 {T['alert_red']}")
            elif status_key == "amber":
                st.warning(f"⚠️ {T['alert_amber']}")

            st.caption(f"Timestamp: {row['timestamp']} · Historical Validation Replay")
        time.sleep(speed)

    st.success("Validation Replay finished. Click other tabs to view forecasts and maps.")
    if alert_log:
        st.markdown(f"**{T['alert_log']}** (this session)")
        st.dataframe(pd.DataFrame(alert_log), use_container_width=True)

# ================================================================ TAB 2: FORECAST
with tab_fc:
    st.subheader(T["forecast_title"])
    if FORECAST_24 is None or FORECAST_48 is None:
        st.info(T["forecast_not_ready"])
        st.code("python forecast_train.py")
    else:
        last = df.iloc[0]
        X_now = pd.DataFrame([[
            last["discharge_m3s"], last["flow_depth_m"], last["velocity_ms"],
            last["froude"], last["b_over_y"], last["rate_of_scour_m_hr"]
        ]], columns=FEATURES)
        
        pred_now = float(model.predict(X_now)[0])
        pred_24 = float(FORECAST_24.predict(X_now)[0])
        pred_48 = float(FORECAST_48.predict(X_now)[0])

        col1, col2, col3 = st.columns(3)
        col1.metric("Now", f"{pred_now:.2f} m")
        col2.metric("T+24h", f"{pred_24:.2f} m", delta=f"{pred_24 - pred_now:+.2f}")
        col3.metric("T+48h", f"{pred_48:.2f} m", delta=f"{pred_48 - pred_now:+.2f}")

        st.markdown(f"**{T['rainfall_forecast']}**")
        rain_24 = max(0, last["rainfall_mm_hr"] * (1 + 0.3 * np.random.randn()))
        rain_48 = max(0, last["rainfall_mm_hr"] * (1 + 0.6 * np.random.randn()))
        c1, c2 = st.columns(2)
        c1.metric("T+24h rainfall", f"{rain_24:.1f} mm/hr")
        c2.metric("T+48h rainfall", f"{rain_48:.1f} mm/hr")

        def risk_label(v):
            if v >= AMBER_MAX: return "🔴 " + T["red"]
            if v >= GREEN_MAX: return "🟡 " + T["amber"]
            return "🟢 " + T["green"]

        st.markdown(f"**24h risk forecast:** {risk_label(pred_24)}")
        st.markdown(f"**48h risk forecast:** {risk_label(pred_48)}")

# ================================================================ TAB 3: MAP
with tab_map:
    st.subheader(T["map_title"])
    m = folium.Map(location=[19.5, 75.5], zoom_start=6, tiles="OpenStreetMap")

    rivers = {
        "Godavari": [[19.93, 73.53], [19.5, 75.0], [19.1, 77.0], [18.8, 79.5]],
        "Krishna":  [[17.9, 73.7], [17.5, 75.0], [16.9, 76.5], [16.5, 78.0]],
        "Bhima":    [[19.0, 73.8], [18.5, 75.0], [17.9, 76.5]],
        "Tapi":     [[21.0, 73.9], [21.0, 75.0], [21.1, 77.0]],
        "Narmada":  [[22.0, 73.7], [21.9, 75.0], [21.9, 77.5]],
    }
    for name, coords in rivers.items():
        folium.PolyLine(coords, color="blue", weight=3, tooltip=name).add_to(m)

    dams = {
        "Ujani Dam":   [18.13, 75.13], "Koyna Dam": [17.40, 73.75],
        "Jayakwadi":   [19.48, 75.37], "Warna": [17.20, 74.10],
    }
    for name, coord in dams.items():
        folium.Marker(coord, tooltip=name, icon=folium.Icon(color="darkblue", icon="tint")).add_to(m)

    PILOT_BRIDGE = {"name": "Pilot Bridge (Solapur)", "coords": [17.66, 75.90]}
    folium.Marker(PILOT_BRIDGE["coords"], popup=PILOT_BRIDGE["name"], 
                  icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)

    folium_static(m, width=1100, height=600)

# ================================================================ TAB 4: CHARTS
with tab_charts:
    st.subheader(T["charts_title"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Scour depth distribution (10-year dataset)**")
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.hist(df["sonar_scour_m"], bins=30, color="steelblue", edgecolor="black")
        ax.set_xlabel("Scour depth (m)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

    with c2:
        st.markdown("**Risk level share**")
        risk_counts = pd.cut(
            df["sonar_scour_m"], bins=[-np.inf, GREEN_MAX, AMBER_MAX, np.inf],
            labels=["Green", "Amber", "Red"],
        ).value_counts()
        fig2, ax2 = plt.subplots(figsize=(4, 3))
        ax2.pie(risk_counts, labels=risk_counts.index, autopct="%1.0f%%", colors=["#2ca02c", "#ff9800", "#d62728"])
        st.pyplot(fig2)

    st.markdown("**Rainfall vs scour depth**")
    fig3, ax3 = plt.subplots(figsize=(9, 3))
    ax3.scatter(df["rainfall_mm_hr"], df["sonar_scour_m"], alpha=0.3, s=8)
    ax3.set_xlabel("Rainfall (mm/hr)")
    ax3.set_ylabel("Scour depth (m)")
    st.pyplot(fig3)

# ================================================================ TAB 5: ALERTS
with tab_alerts:
    st.subheader(T["alert_log"])
    if os.path.exists(AUTOSAVE_PATH):
        try:
            # on_bad_lines='skip' prevents crashing if the Live tab is writing to it
            saved = pd.read_csv(AUTOSAVE_PATH, on_bad_lines='skip')
            st.markdown(f"**{T['autosave']}** — {len(saved)} rows in `{AUTOSAVE_PATH}`")
            st.dataframe(saved.tail(50), use_container_width=True)
            st.download_button(
                "⬇️ Download full log (CSV)",
                data=saved.to_csv(index=False).encode(),
                file_name="scour_alerts.csv",
                mime="text/csv",
            )
        except Exception:
            st.info("Autosave file is currently updating. Refresh in a moment.")
    else:
        st.info("No alerts logged yet. Run the Live Dashboard first.")