"""
forecast_train.py — Train 24h and 48h ahead scour forecast models.
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_csv("data/flood_season_simulated.csv")

FEATURES = [
    "discharge_m3s", "flow_depth_m", "velocity_ms",
    "froude", "b_over_y", "rate_of_scour_m_hr",
]
TARGET = "sonar_scour_m"

for horizon, steps in [("24h", 96), ("48h", 192)]:
    d = df.copy()
    d["target"] = d[TARGET].shift(-steps)
    d = d.dropna(subset=["target"])

    X = d[FEATURES]
    y = d["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    rf = RandomForestRegressor(
        n_estimators=200, max_depth=12, random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    pred = rf.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2 = r2_score(y_test, pred)
    print(f"T+{horizon} model -> RMSE {rmse:.4f} m | R2 {r2:.4f}")
    joblib.dump(rf, f"models/scour_model_{horizon}.joblib")

print("Saved models/scour_model_24h.joblib and models/scour_model_48h.joblib")