import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle

# 1. Load and Prepare Data
df = pd.read_csv("c_class_ml_features_fixed.csv")
df = pd.get_dummies(df, columns=['trim'], drop_first=True)

X = df.drop(columns=['price'])
y = df['price']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- STAGE 1: The Base Linear Model ---
linear_base = LinearRegression()
linear_base.fit(X_train, y_train)

# Get the linear predictions on the training set
train_linear_preds = linear_base.predict(X_train)

# Calculate the residuals (what the linear model missed)
residuals = y_train - train_linear_preds

# --- STAGE 2: The Random Forest Corrector ---
# Train the tree ONLY on the residuals
rf_corrector = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
rf_corrector.fit(X_train, residuals)

# --- EVALUATION: The Combined Ensemble ---
# To predict, we sum the outputs of both models
test_linear_preds = linear_base.predict(X_test)
test_rf_corrections = rf_corrector.predict(X_test)

final_predictions = test_linear_preds + test_rf_corrections

mae = mean_absolute_error(y_test, final_predictions)
r2 = r2_score(y_test, final_predictions)

print("--- Residual Ensemble Evaluation ---")
print(f"Mean Absolute Error (MAE): ${mae:,.2f}")
print(f"R-squared Score: {r2:.3f}")

# --- EXPORT ---
# We must save both models to load them in our FastAPI backend
with open("linear_base.pkl", "wb") as f:
    pickle.dump(linear_base, f)

with open("rf_corrector.pkl", "wb") as f:
    pickle.dump(rf_corrector, f)
    
with open("model_columns.pkl", "wb") as f:
    pickle.dump(list(X.columns), f)
