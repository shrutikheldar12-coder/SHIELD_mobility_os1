"""
app.py — S.H.I.E.L.D. Scour Sense — live Streamlit dashboard.
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="S.H.I.E.L.D. Scour Sense", layout="wide")

# ---- Load trained model and feature list ----
model = joblib.load("models/scour_model.joblib")
FEATURES = joblib.load("models/feature_names.joblib")

# ---- Bridge-specific risk thresholds ----
# Derived from YOUR simulated data (sonar_scour_m range: 1.31 to 3.55 m)
GREEN_MAX = 2.20    # below this = safe
AMBER_MAX = 3.00    # between GREEN_MAX and AMBER_MAX = inspect now
                    # above AMBER_MAX = RED = restrict traffic

st.title("🛡️ S.H.I.E.L.D. — Scour Sense")
st.caption("AI-Enabled Low-Cost Bridge Scour Early-Warning System  ·  Sector 8: Infrastructure & Mobility")

# ---- Sidebar ----
with st.sidebar:
    st.header("Controls")
    speed = st.slider("Simulation speed (sec/step)", 0.02, 0.5, 0.08, step=0.02)
    flood_btn = st.button("🌊 Trigger FLOOD EVENT", use_container_width=True)
    st.markdown("---")
    st.markdown("**Bridge thresholds**")
    st.markdown(f"🟢 Safe: < **{GREEN_MAX:.2f} m**")
    st.markdown(f"🟡 Inspect: **{GREEN_MAX:.2f} – {AMBER_MAX:.2f} m**")
    st.markdown(f"🔴 Restrict traffic: **> {AMBER_MAX:.2f} m**")
    st.markdown("---")
    st.markdown("**Sensor node**")
    st.markdown("Sonar depth · Accelerometer RMS")
    st.markdown("Powered by solar · IP68 enclosure")

# ---- Flood toggle state ----
if "flood_active" not in st.session_state:
    st.session_state.flood_active = False
if flood_btn:
    st.session_state.flood_active = True

# ---- Load replayed data ----
df = pd.read_csv("data/flood_season_simulated.csv")

# Start the replay at the first flood event (~day 9-11) so demo shows action quickly
start_idx = int(len(df) * 0.28)
replay_df = df.iloc[start_idx:start_idx + 600].reset_index(drop=True)

placeholder = st.empty()
history_scour = []

for i, row in replay_df.iterrows():
    # ---- If flood button pressed, override for first 40 steps ----
    if st.session_state.flood_active and i < 40:
        q = row["discharge_m3s"] * 4.0
        depth = row["flow_depth_m"] * 1.6
        vel = row["velocity_ms"] * 1.6
        froude = vel / np.sqrt(9.81 * depth)
        b_over_y = row["pier_width_m"] / depth
        dS_dt = row["rate_of_scour_m_hr"] * 5
        X_live = pd.DataFrame(
            [[q, depth, vel, froude, b_over_y, dS_dt]],
            columns=FEATURES,
        )
        scour = float(model.predict(X_live)[0])
        display_q = q
    else:
        scour = float(row["sonar_scour_m"])
        display_q = row["discharge_m3s"]

    history_scour.append(scour)
    if len(history_scour) > 200:
        history_scour = history_scour[-200:]

    # ---- Risk classification ----
    if scour >= AMBER_MAX:
        status_html = "🔴 RED — RESTRICT TRAFFIC & EVACUATE"
        status_color = "#d62728"
    elif scour >= GREEN_MAX:
        status_html = "🟡 AMBER — SCHEDULE INSPECTION"
        status_color = "#ff9800"
    else:
        status_html = "🟢 GREEN — SAFE"
        status_color = "#2ca02c"

    # ---- Render ----
    with placeholder.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Scour Depth", f"{scour:.2f} m",
                  delta=f"{(scour - GREEN_MAX):+.2f} vs amber")
        c2.metric("Rate of Scour", f"{row['rate_of_scour_m_hr']:.3f} m/hr")
        c3.metric("Discharge", f"{display_q:.0f} m³/s")
        c4.metric("Froude No.", f"{row['froude']:.2f}")

        st.markdown(
            f"<h2 style='color:{status_color};margin-top:0.5em'>{status_html}</h2>",
            unsafe_allow_html=True,
        )
        st.progress(min(scour / (AMBER_MAX * 1.2), 1.0))

        # Trend chart
        chart_df = pd.DataFrame({"Scour depth (m)": history_scour})
        st.line_chart(chart_df, height=220)

        # Alert banner
        if scour >= AMBER_MAX:
            st.error(
                f"🚨 ALERT dispatched to PWD Bridge Management System — "
                f"scour {scour:.2f} m exceeds RED threshold {AMBER_MAX:.2f} m. "
                f"Action: restrict traffic, deploy riprap, emergency inspection."
            )
        elif scour >= GREEN_MAX:
            st.warning(
                f"⚠️ Advisory sent to PWD — scour {scour:.2f} m in AMBER zone. "
                f"Action: schedule inspection within 24h."
            )

        st.caption(
            f"Simulated timestamp: {row['timestamp']}  ·  "
            f"Streaming at ~{1/speed:.0f}× real-time  ·  "
            f"Model: RandomForest (RMSE 0.042 m, R² 0.89 vs Lacey 0.059 / 0.79)"
        )

    time.sleep(speed)

# Reset flood toggle when loop ends
st.session_state.flood_active = False

st.success("Replay finished. Click 'Trigger FLOOD EVENT' to run again, or refresh the page.")