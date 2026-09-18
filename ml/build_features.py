import pandas as pd
from analytics.query_runner import run_query
from config.products import PRODUCTS


def get_daily_sales():
   query = """
      SELECT
         oi.product_id,
         o.order_date,
         SUM(oi.quantity) AS quantity
      FROM order_items oi
      JOIN orders o ON oi.order_id = o.order_id
      GROUP BY oi.product_id, o.order_date
      ORDER BY oi.product_id, o.order_date;
   """
   return run_query(query)


def build_complete_grid():
   daily_sales = get_daily_sales()
   daily_sales["order_date"] = pd.to_datetime(daily_sales["order_date"])

   all_dates = pd.date_range(start="2025-01-01", end="2025-12-31", freq="D")
   all_product_ids = [p["product_id"] for p in PRODUCTS]

   grid = pd.MultiIndex.from_product(
      [all_product_ids, all_dates],
      names=["product_id", "order_date"]
   ).to_frame(index=False)

   full_data = grid.merge(
      daily_sales,
      on=["product_id", "order_date"],
      how="left"
   )

   full_data["quantity"] = full_data["quantity"].fillna(0)

   return full_data


def build_features(df):
   df = df.sort_values(["product_id", "order_date"]).reset_index(drop=True)

   df["day_of_week"] = df["order_date"].dt.dayofweek
   df["month"] = df["order_date"].dt.month
   df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
   df["is_festival_season"] = df["month"].isin([10, 11]).astype(int)

   df["quantity_lag_1"] = df.groupby("product_id")["quantity"].shift(1)
   df["quantity_lag_7"] = df.groupby("product_id")["quantity"].shift(7)
   df["quantity_rolling_7"] = (
      df.groupby("product_id")["quantity"]
      .shift(1)
      .rolling(window=7)
      .mean()
      .reset_index(level=0, drop=True)
   )

   return df


def finalize_features(df):
   before = len(df)
   df = df.dropna(subset=["quantity_lag_1", "quantity_lag_7", "quantity_rolling_7"])
   after = len(df)
   print(f"Dropped {before - after} rows with incomplete lag history")
   return df.reset_index(drop=True)


def chronological_split(df, split_date="2025-11-15"):
   split_date = pd.to_datetime(split_date)
   train = df[df["order_date"] < split_date].reset_index(drop=True)
   test = df[df["order_date"] >= split_date].reset_index(drop=True)
   return train, test


def verify_no_leakage(train, test):
   print("--- Leakage Check 1: Train/Test date overlap ---")
   train_max = train["order_date"].max()
   test_min = test["order_date"].min()
   overlap = train_max >= test_min
   print(f"Train max date: {train_max}, Test min date: {test_min}")
   print(f"Overlap detected: {overlap}")
   assert not overlap, "LEAKAGE: train and test date ranges overlap!"

   print("\n--- Leakage Check 2: Lag feature consistency (spot check) ---")
   sample = train[train["product_id"] == 1].sort_values("order_date").reset_index(drop=True)
   mismatches = 0
   for i in range(1, len(sample)):
      expected_lag_1 = sample.loc[i - 1, "quantity"]
      actual_lag_1 = sample.loc[i, "quantity_lag_1"]
      if abs(expected_lag_1 - actual_lag_1) > 0.001:
         mismatches += 1
   print(f"Lag_1 mismatches found (product_id=1): {mismatches} out of {len(sample) - 1} rows checked")
   assert mismatches == 0, "LEAKAGE: quantity_lag_1 does not match actual prior day!"

   print("\n--- Leakage Check 3: Target column not duplicated as a feature ---")
   feature_columns = [c for c in train.columns if c not in ["product_id", "order_date", "quantity"]]
   print(f"Feature columns: {feature_columns}")
   print(f"'quantity' in feature list: {'quantity' in feature_columns}")
   assert "quantity" not in feature_columns, "LEAKAGE: target column present in features!"

   print("\nAll leakage checks passed.")


if __name__ == "__main__":
   df = build_complete_grid()
   df = build_features(df)
   df = finalize_features(df)

   train, test = chronological_split(df)
   print(f"Train: {len(train)} rows, {train['order_date'].min()} to {train['order_date'].max()}")
   print(f"Test: {len(test)} rows, {test['order_date'].min()} to {test['order_date'].max()}")

   print()
   verify_no_leakage(train, test)