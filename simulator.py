"""
simulator.py — Generates 30 days of synthetic flood-season sensor data.
Uses Lacey's formula as "ground truth" scour depth, then adds sensor noise.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ---- Bridge & river parameters (edit these to match your pilot bridge) ----
DESIGN_Q = 500.0        # m3/s design discharge
SILT_FACTOR_F = 1.25    # Lacey silt factor (typical for medium silt)
PIER_WIDTH_B = 2.0      # m
SEDIMENT_D50 = 0.3      # mm

# ---- Generate 30 days at 15-minute intervals ----
N_DAYS = 30
INTERVAL_MIN = 15
STEPS = N_DAYS * 24 * 60 // INTERVAL_MIN  # = 2880 rows

timestamps = [datetime(2025, 6, 1) + timedelta(minutes=INTERVAL_MIN * i) for i in range(STEPS)]

# Base discharge with slow seasonal variation + two flood events
t = np.linspace(0, 1, STEPS)
base_q = 80 + 40 * np.sin(2 * np.pi * t)                        # base flow

# Flood event 1: peaks around day 10
flood1 = 350 * np.exp(-((t - 0.33) ** 2) / 0.002)

# Flood event 2: peaks around day 22
flood2 = 500 * np.exp(-((t - 0.73) ** 2) / 0.0015)

discharge = base_q + flood1 + flood2 + np.random.normal(0, 8, STEPS)
discharge = np.clip(discharge, 20, None)

# Rainfall (mm/hr) — rough correlation with discharge
rainfall = np.clip((discharge - 100) / 12 + np.random.normal(0, 3, STEPS), 0, None)

# Flow depth (m) — Manning-like power relation to discharge
flow_depth = 0.35 * (discharge / 100.0) ** 0.6

# Flow velocity (m/s)
velocity = discharge / (flow_depth * 60.0)   # assumed 60 m channel width

# Froude number
g = 9.81
froude = velocity / np.sqrt(g * flow_depth)

# ---- Lacey scour depth (ground truth) ----
d_lacey = 0.473 * (discharge / SILT_FACTOR_F) ** (1/3)

# ---- Simulated sensor measurements ----
# Sonar measures depth with 5% noise + slow drift
sonar_scour = d_lacey * (0.95 + 0.05 * np.random.rand(STEPS)) + np.random.normal(0, 0.03, STEPS)
sonar_scour = np.clip(sonar_scour, 0, None)

# Accelerometer RMS (g) — rises with velocity and scour
accel_rms = 0.005 + 0.02 * (velocity / velocity.max()) + 0.01 * (sonar_scour / sonar_scour.max())
accel_rms += np.random.normal(0, 0.001, STEPS)

# Rate of scour change (m per hour)
dS_dt = np.gradient(sonar_scour) * (60 / INTERVAL_MIN)   # convert per-15-min to per-hour

# ---- Assemble DataFrame ----
df = pd.DataFrame({
    "timestamp": timestamps,
    "rainfall_mm_hr": np.round(rainfall, 3),
    "discharge_m3s": np.round(discharge, 2),
    "flow_depth_m": np.round(flow_depth, 3),
    "velocity_ms": np.round(velocity, 3),
    "froude": np.round(froude, 3),
    "sonar_scour_m": np.round(sonar_scour, 4),
    "accel_rms_g": np.round(accel_rms, 5),
    "rate_of_scour_m_hr": np.round(dS_dt, 5),
    "lacey_scour_m": np.round(d_lacey, 4),
    "pier_width_m": PIER_WIDTH_B,
    "d50_mm": SEDIMENT_D50,
    "b_over_y": np.round(PIER_WIDTH_B / flow_depth, 3),
})

df.to_csv("data/flood_season_simulated.csv", index=False)
print(f"OK: Saved {len(df)} rows to data/flood_season_simulated.csv")
print(df.head())
print("\nScour depth range:", df.sonar_scour_m.min(), "to", df.sonar_scour_m.max(), "m")