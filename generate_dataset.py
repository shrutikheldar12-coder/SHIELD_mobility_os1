"""
generate_dataset.py — Generates a professional 10-year dataset and splits it.
70% Training (Raw)
15% Prediction (Testing)
15% Validation
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# We simulate 10 years of 6-hourly data (4 readings per day)
# 10 years * 365 days * 4 = 14,600 rows
total_rows = 14600
timestamps = [datetime(2015, 1, 1) + timedelta(hours=6 * i) for i in range(total_rows)]

# 1. Simulate realistic Indian Monsoon Rainfall (Heavy June-Sept, Dry Oct-May)
day_of_year = np.array([t.timetuple().tm_yday for t in timestamps])
monsoon_factor = np.sin((day_of_year - 100) * (2 * np.pi / 365))
monsoon_factor = np.clip(monsoon_factor, 0, 1)  # 0 in winter, 1 in peak monsoon

base_rain = 50 * monsoon_factor
rainfall = np.random.gamma(shape=2.0, scale=base_rain + 0.1, size=total_rows)
# Add extreme flood events (cyclones/flash floods)
for _ in range(20):
    idx = np.random.randint(0, total_rows - 24)
    rainfall[idx:idx+24] += np.random.uniform(100, 300, 24)

# 2. Simulate River Discharge (m3/s) based on rainfall + base flow
base_flow = 80  # m3/s base flow
discharge = base_flow + (rainfall * 15) + np.random.normal(0, 15, total_rows)
discharge = np.clip(discharge, 50, 3500)

# 3. Simulate Flow Depth (m) using Manning's equation proxy
channel_width = 80 # meters
flow_depth = (discharge / (channel_width * 1.5)) ** (3/5)

# 4. Simulate Velocity (m/s)
velocity = discharge / (channel_width * flow_depth)

# 5. Froude Number
g = 9.81
froude = velocity / np.sqrt(g * flow_depth)

# 6. Lacey Scour Depth (Ground Truth)
silt_factor = 1.25
lacey_scour = 0.473 * (discharge / silt_factor) ** (1/3)

# 7. Sonar Sensor Measurement (with 5% noise)
sonar_scour = lacey_scour * (0.95 + 0.05 * np.random.rand(total_rows)) + np.random.normal(0, 0.05, total_rows)
sonar_scour = np.clip(sonar_scour, 0, None)

# 8. Rate of scour change (m/hr)
dS_dt = np.gradient(sonar_scour) * (1/6) # divided by 6 hours

# Create DataFrame
df = pd.DataFrame({
    "timestamp": timestamps,
    "rainfall_mm_hr": np.round(rainfall, 2),
    "discharge_m3s": np.round(discharge, 2),
    "flow_depth_m": np.round(flow_depth, 3),
    "velocity_ms": np.round(velocity, 3),
    "froude": np.round(froude, 3),
    "sonar_scour_m": np.round(sonar_scour, 4),
    "lacey_scour_m": np.round(lacey_scour, 4),
    "rate_of_scour_m_hr": np.round(dS_dt, 5),
    "b_over_y": np.round(2.0 / flow_depth, 3),
    "pier_width_m": 2.0,
    "d50_mm": 0.3
})

# ==========================================
# EXACT SPLIT: 70% Train, 15% Predict, 15% Validation
# ==========================================
train_end = int(total_rows * 0.70)
pred_end = int(total_rows * 0.85)

train_df = df.iloc[:train_end]
predict_df = df.iloc[train_end:pred_end]
validate_df = df.iloc[pred_end:]

# Save to CSV
train_df.to_csv("data/train_raw_70.csv", index=False)
predict_df.to_csv("data/predict_15.csv", index=False)
validate_df.to_csv("data/validate_15.csv", index=False)

print("✅ Dataset successfully generated!")
print(f"Total rows: {total_rows}")
print(f"-> data/train_raw_70.csv (70% raw data): {len(train_df)} rows")
print(f"-> data/predict_15.csv (15% prediction): {len(predict_df)} rows")
print(f"-> data/validate_15.csv (15% validation): {len(validate_df)} rows")