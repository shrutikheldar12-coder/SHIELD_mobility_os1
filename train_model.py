"""
train_model.py — Trains RF model using 70% train, validates on 15%.
"""
import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Load the split data
train_df = pd.read_csv("data/train_raw_70.csv")
val_df = pd.read_csv("data/validate_15.csv")

FEATURES = ["discharge_m3s", "flow_depth_m", "velocity_ms", "froude", "b_over_y", "rate_of_scour_m_hr"]
TARGET = "sonar_scour_m"

X_train, y_train = train_df[FEATURES], train_df[TARGET]
X_val, y_val = val_df[FEATURES], val_df[TARGET]

# Train Model
print("Training Random Forest on 70% raw data...")
rf = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

# Validate Model
pred_val = rf.predict(X_val)
rmse = np.sqrt(mean_squared_error(y_val, pred_val))
r2 = r2_score(y_val, pred_val)

print(f"=== Validation Results (15% unseen data) ===")
print(f"RMSE: {rmse:.4f} m")
print(f"R2 Score: {r2:.4f}")

# Save Model
joblib.dump(rf, "models/scour_model.joblib")
joblib.dump(FEATURES, "models/feature_names.joblib")
print("✅ Model saved.")

# Plot
plt.figure(figsize=(10, 4))
plt.plot(y_val.values[:200], label="Actual (Sonar)", color="black", linewidth=2)
plt.plot(pred_val[:200], label="AI Prediction", linestyle="--", color="red", linewidth=2)
plt.xlabel("Validation sample index (first 200 of 15%)")
plt.ylabel("Scour depth (m)")
plt.title("Validation: AI Prediction vs Actual")
plt.legend()
plt.tight_layout()
plt.savefig("outputs/validation_results.png", dpi=150)
print("✅ Saved validation plot to outputs/validation_results.png")