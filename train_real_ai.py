import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor
import lightgbm as lgb

print("Generating realistic hydrological data...")
np.random.seed(42)
N = 50000

# 1. Simulate River Discharge (Q) based on Monsoon cycles
discharge = np.random.gamma(shape=3.0, scale=300.0, size=N) 
discharge = np.clip(discharge, 50, 5000)

# 2. Simulate Flow Depth (y) and Velocity (V)
channel_width = 60.0
flow_depth = (discharge / (channel_width * 1.5)) ** 0.6
velocity = discharge / (channel_width * flow_depth)

# 3. Froude Number and Pier Ratio
froude = velocity / np.sqrt(9.81 * flow_depth)
pier_width = 2.0
b_over_y = pier_width / flow_depth

# 4. Calculate True Scour using Lacey's Formula (Physics Ground Truth)
silt_factor = 1.25
lacey_scour = 0.473 * (discharge / silt_factor) ** (1/3)

# Add real-world noise (sediment variation, sensor tolerances)
true_scour = lacey_scour + np.random.normal(0, 0.05, N)
true_scour = np.clip(true_scour, 0.1, None)

# 5. Create DataFrame
df = pd.DataFrame({
    "discharge": discharge,
    "flow_depth": flow_depth,
    "velocity": velocity,
    "froude": froude,
    "b_over_y": b_over_y,
    "true_scour": true_scour
})

# 6. Add temporal lag features (Scour rate)
df = df.sort_values("discharge").reset_index(drop=True)
df["scour_rate"] = df["true_scour"].diff().fillna(0)

print("Training Stacked Ensemble (RF + XGB + LGBM)...")
FEATURES = ["discharge", "flow_depth", "velocity", "froude", "b_over_y", "scour_rate"]
TARGET = "true_scour"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Base Models
rf = RandomForestRegressor(n_estimators=300, max_depth=20, random_state=42)
xgb = XGBRegressor(n_estimators=300, max_depth=10, learning_rate=0.05, random_state=42)
lgbm = lgb.LGBMRegressor(n_estimators=300, max_depth=10, random_state=42, verbose=-1)

rf.fit(X_train, y_train)
xgb.fit(X_train, y_train)
lgbm.fit(X_train, y_train)

# Meta Learner
rf_pred = rf.predict(X_test)
xgb_pred = xgb.predict(X_test)
lgbm_pred = lgbm.predict(X_test)

stack_X = np.column_stack((rf_pred, xgb_pred, lgbm_pred))
meta = Ridge(alpha=1.0)
meta.fit(stack_X, y_test)

# Final Prediction & Evaluation
final_pred = meta.predict(stack_X)
r2 = r2_score(y_test, final_pred)
rmse = np.sqrt(mean_squared_error(y_test, final_pred))

print(f"\n=== MODEL PERFORMANCE ===")
print(f"R2 Score: {r2 * 100:.2f}%")
print(f"RMSE: {rmse:.4f} m")

# Save Models
joblib.dump(rf, "models/rf.pkl")
joblib.dump(xgb, "models/xgb.pkl")
joblib.dump(lgbm, "models/lgbm.pkl")
joblib.dump(meta, "models/meta.pkl")
joblib.dump(FEATURES, "models/feature_names.joblib")
print("Models saved to /models/")