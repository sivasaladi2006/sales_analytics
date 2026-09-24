import pandas as pd
from ml.build_features import build_complete_grid, build_features, finalize_features, chronological_split


def test_no_date_overlap_between_train_and_test():
   """Train and test date ranges must never overlap."""
   df = build_complete_grid()
   df = build_features(df)
   df = finalize_features(df)
   train, test = chronological_split(df)

   assert train["order_date"].max() < test["order_date"].min()


def test_lag_1_matches_actual_previous_day():
   """quantity_lag_1 must exactly match the prior day's actual quantity."""
   df = build_complete_grid()
   df = build_features(df)
   df = finalize_features(df)

   sample = df[df["product_id"] == 1].sort_values("order_date").reset_index(drop=True)

   for i in range(1, min(50, len(sample))):
      expected = sample.loc[i - 1, "quantity"]
      actual = sample.loc[i, "quantity_lag_1"]
      assert abs(expected - actual) < 0.001


def test_target_not_in_feature_columns():
   """The target column 'quantity' must never appear among features."""
   df = build_complete_grid()
   df = build_features(df)
   df = finalize_features(df)

   feature_columns = [c for c in df.columns if c not in ["product_id", "order_date", "quantity"]]
   assert "quantity" not in feature_columns