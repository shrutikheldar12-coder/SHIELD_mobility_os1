import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor
import lightgbm as lgb

# 1. Load Data
df = pd.read_csv("data/predict_15.csv")

# 2. Feature Engineering
features = [
    "discharge_m3s", "flow_depth_m", "velocity_ms", 
    "froude", "b_over_y", "rate_of_scour_m_hr"
]
target = "sonar_scour_m"

X = df[features]
y = df[target]

# 3. Split Data (Rolling Origin approach)
split_idx = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

# 4. Base Learners
rf = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42)
xgb = XGBRegressor(n_estimators=200, max_depth=8, learning_rate=0.05, random_state=42)
lgbm = lgb.LGBMRegressor(n_estimators=200, max_depth=8, random_state=42, verbose=-1)

# 5. Train Base Models
print("Training Base Models...")
rf.fit(X_train, y_train)
xgb.fit(X_train, y_train)
lgbm.fit(X_train, y_train)

# 6. Meta-Learner (Stacking)
rf_preds = rf.predict(X_test)
xgb_preds = xgb.predict(X_test)
lgbm_preds = lgbm.predict(X_test)

stacked_X = np.column_stack((rf_preds, xgb_preds, lgbm_preds))
meta = Ridge(alpha=1.0)
meta.fit(stacked_X, y_test)

# 7. Evaluate
final_preds = meta.predict(stacked_X)
r2 = r2_score(y_test, final_preds)
rmse = np.sqrt(mean_squared_error(y_test, final_preds))

print(f"=== FINAL ENSEMBLE METRICS ===")
print(f"R2 Score: {r2*100:.2f}% (Target > 98%)")
print(f"RMSE: {rmse:.4f} m")

# 8. Save Models
joblib.dump(rf, "models/rf.pkl")
joblib.dump(xgb, "models/xgb.pkl")
joblib.dump(lgbm, "models/lgbm.pkl")
joblib.dump(meta, "models/meta.pkl")
joblib.dump(features, "models/feature_names.joblib")
print("Models saved successfully.")