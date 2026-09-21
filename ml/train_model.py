import pandas as pd
from ml.build_features import build_complete_grid, build_features, finalize_features, chronological_split
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
from ml.build_features import build_complete_grid, build_features, finalize_features, chronological_split

from sklearn.linear_model import LinearRegression

from sklearn.ensemble import RandomForestRegressor

from sklearn.ensemble import GradientBoostingRegressor

import joblib

BASE_FEATURE_COLUMNS = [
   "day_of_week",
   "month",
   "is_weekend",
   "is_festival_season",
   "quantity_lag_1",
   "quantity_lag_7",
   "quantity_rolling_7",
]
TARGET_COLUMN = "quantity"


def prepare_data():
   df = build_complete_grid()
   df = build_features(df)
   df = finalize_features(df)

   # One-hot encode product_id
   product_dummies = pd.get_dummies(df["product_id"], prefix="product")
   df = pd.concat([df, product_dummies], axis=1)

   product_columns = list(product_dummies.columns)
   feature_columns = BASE_FEATURE_COLUMNS + product_columns

   train, test = chronological_split(df)

   X_train = train[feature_columns]
   y_train = train[TARGET_COLUMN]
   X_test = test[feature_columns]
   y_test = test[TARGET_COLUMN]

   return X_train, X_test, y_train, y_test, feature_columns


def evaluate_predictions(y_true, y_pred, model_name):
   """
   Compute and print MAE, MSE, RMSE, R² for a set of predictions.
   """
   mae = mean_absolute_error(y_true, y_pred)
   mse = mean_squared_error(y_true, y_pred)
   rmse = np.sqrt(mse)
   r2 = r2_score(y_true, y_pred)

   print(f"\n--- {model_name} ---")
   print(f"MAE:  {mae:.3f}")
   print(f"MSE:  {mse:.3f}")
   print(f"RMSE: {rmse:.3f}")
   print(f"R2:   {r2:.3f}")

   return {"model": model_name, "MAE": mae, "MSE": mse, "RMSE": rmse, "R2": r2}


def mean_baseline(y_train, y_test):
   """
   Predict the training mean for every test row.
   """
   mean_value = y_train.mean()
   y_pred = np.full(len(y_test), mean_value)
   return evaluate_predictions(y_test, y_pred, "Mean Baseline")


def naive_lag_baseline(X_test, y_test):
   """
   Predict quantity_lag_1 (yesterday's value) as today's demand.
   """
   y_pred = X_test["quantity_lag_1"]
   return evaluate_predictions(y_test, y_pred, "Naive Lag Baseline")


def train_linear_regression(X_train, y_train, X_test, y_test):
   """
   Train a Linear Regression model and evaluate it on the test set.
   """
   model = LinearRegression()
   model.fit(X_train, y_train)

   y_pred = model.predict(X_test)
   metrics = evaluate_predictions(y_test, y_pred, "Linear Regression")

   return model, metrics


def train_random_forest(X_train, y_train, X_test, y_test, max_depth=None, min_samples_leaf=1, label="Random Forest"):
   """
   Train a Random Forest Regressor and evaluate it on the test set.
   """
   model = RandomForestRegressor(
      n_estimators=100,
      max_depth=max_depth,
      min_samples_leaf=min_samples_leaf,
      random_state=42,
      n_jobs=-1
   )
   model.fit(X_train, y_train)

   y_pred = model.predict(X_test)
   metrics = evaluate_predictions(y_test, y_pred, label)

   return model, metrics


def train_gradient_boosting(X_train, y_train, X_test, y_test, max_depth=3, n_estimators=100, learning_rate=0.1, label="Gradient Boosting"):
   """
   Train a Gradient Boosting Regressor and evaluate it on the test set.
   """
   model = GradientBoostingRegressor(
      n_estimators=n_estimators,
      max_depth=max_depth,
      learning_rate=learning_rate,
      random_state=42
   )
   model.fit(X_train, y_train)

   y_pred = model.predict(X_test)
   metrics = evaluate_predictions(y_test, y_pred, label)

   return model, metrics


def feature_importance_analysis(model, feature_columns):
   """
   Print feature importances from a trained tree-based model,
   sorted from most to least important.
   """
   importances = pd.Series(model.feature_importances_, index=feature_columns)
   importances = importances.sort_values(ascending=False)

   print("\n--- Feature Importance (Random Forest) ---")
   print(importances.head(15).to_string())

   return importances


def save_model(model, feature_columns, filepath="ml/models/demand_model.joblib"):
   """
   Save the trained model and its feature column order to disk.
   """
   import os
   os.makedirs(os.path.dirname(filepath), exist_ok=True)

   joblib.dump({"model": model, "feature_columns": feature_columns}, filepath)
   print(f"\nModel saved to {filepath}")


if __name__ == "__main__":
   X_train, X_test, y_train, y_test, feature_columns = prepare_data()
   print("X_train shape:", X_train.shape)
   print("X_test shape:", X_test.shape)

   mean_baseline(y_train, y_test)
   naive_lag_baseline(X_test, y_test)
   train_linear_regression(X_train, y_train, X_test, y_test)

   train_random_forest(X_train, y_train, X_test, y_test, label="Random Forest (default)")
   best_rf_model, best_rf_metrics = train_random_forest(
      X_train, y_train, X_test, y_test,
      max_depth=6, min_samples_leaf=5,
      label="Random Forest (best)"
   )

   train_gradient_boosting(X_train, y_train, X_test, y_test, label="Gradient Boosting (default)")
   train_gradient_boosting(
      X_train, y_train, X_test, y_test,
      max_depth=3, n_estimators=200, learning_rate=0.05,
      label="Gradient Boosting (best)"
   )

   feature_importance_analysis(best_rf_model, feature_columns)

   save_model(best_rf_model, feature_columns)