import joblib
import pandas as pd
from ml.build_features import build_complete_grid, build_features, finalize_features
from config.products import PRODUCTS
from db.connection import get_engine


def load_model(filepath="ml/models/demand_model.joblib"):
   """
   Load the saved model and its feature column order.
   """
   saved = joblib.load(filepath)
   return saved["model"], saved["feature_columns"]


def forecast_next_n_days(model, feature_columns, n_days=7):
   """
   Recursively forecast demand for each product for the next n_days,
   starting from the end of the known dataset.
   """
   df = build_complete_grid()
   df = build_features(df)
   df = finalize_features(df)

   last_date = df["order_date"].max()
   predictions = []

   for product in PRODUCTS:
      product_id = product["product_id"]
      history = df[df["product_id"] == product_id].sort_values("order_date").copy()

      for i in range(1, n_days + 1):
         next_date = last_date + pd.Timedelta(days=i)

         recent = history["quantity"].tolist()
         lag_1 = recent[-1]
         lag_7 = recent[-7] if len(recent) >= 7 else recent[0]
         rolling_7 = sum(recent[-7:]) / min(7, len(recent))

         row = {
            "day_of_week": next_date.dayofweek,
            "month": next_date.month,
            "is_weekend": int(next_date.dayofweek in [5, 6]),
            "is_festival_season": int(next_date.month in [10, 11]),
            "quantity_lag_1": lag_1,
            "quantity_lag_7": lag_7,
            "quantity_rolling_7": rolling_7,
         }
         for p in PRODUCTS:
            row[f"product_{p['product_id']}"] = (p["product_id"] == product_id)

         X_row = pd.DataFrame([row])[feature_columns]
         predicted_qty = model.predict(X_row)[0]
         
         predictions.append({
            "product_id": product_id,
            "product_name": product["product_name"],
            "date": next_date,
            "predicted_quantity": round(predicted_qty, 2)
         })
         
         history = pd.concat([
            history,
            pd.DataFrame([{"product_id": product_id, "order_date": next_date, "quantity": predicted_qty}])
         ], ignore_index=True)

   return pd.DataFrame(predictions)


def load_current_inventory():
   """
   Load current stock levels from the database.
   """
   engine = get_engine()
   query = "SELECT product_id, stock_available FROM inventory;"
   return pd.read_sql(query, engine)


def compute_reorder_points(model, feature_columns, lead_time_days=7):
   """
   Compute each product's reorder point: predicted daily demand
   (based on most recent known data) x lead_time_days.
   """
   df = build_complete_grid()
   df = build_features(df)
   df = finalize_features(df)

   last_date = df["order_date"].max()
   reorder_points = []

   for product in PRODUCTS:
      product_id = product["product_id"]
      history = df[df["product_id"] == product_id].sort_values("order_date")

      recent = history["quantity"].tolist()
      lag_1 = recent[-1]
      lag_7 = recent[-7] if len(recent) >= 7 else recent[0]
      rolling_7 = sum(recent[-7:]) / min(7, len(recent))

      next_date = last_date + pd.Timedelta(days=1)

      row = {
         "day_of_week": next_date.dayofweek,
         "month": next_date.month,
         "is_weekend": int(next_date.dayofweek in [5, 6]),
         "is_festival_season": int(next_date.month in [10, 11]),
         "quantity_lag_1": lag_1,
         "quantity_lag_7": lag_7,
         "quantity_rolling_7": rolling_7,
      }
      for p in PRODUCTS:
         row[f"product_{p['product_id']}"] = (p["product_id"] == product_id)

      X_row = pd.DataFrame([row])[feature_columns]
      predicted_daily_demand = model.predict(X_row)[0]

      reorder_points.append({
         "product_id": product_id,
         "product_name": product["product_name"],
         "predicted_daily_demand": round(predicted_daily_demand, 2),
         "reorder_point": round(round(predicted_daily_demand * lead_time_days / 5) * 5, 2)
      })

   return pd.DataFrame(reorder_points)


def check_reorder_triggers(reorder_points, inventory):
   """
   Flag products whose current stock has dropped to or below
   their computed reorder point.
   """
   merged = reorder_points.merge(inventory, on="product_id")
   merged["needs_reorder"] = merged["stock_available"] <= merged["reorder_point"]
   return merged.sort_values("needs_reorder", ascending=False)


def compute_order_quantities(triggers, order_coverage_days=30, round_to=5):
   """
   For products that need reordering, compute an order quantity
   sized to cover order_coverage_days of predicted demand.
   Rounds to the nearest `round_to` units for practical ordering,
   and flags erratic products where demand-based sizing may be
   less reliable.
   """
   triggers = triggers.copy()

   raw_qty = (
      (triggers["predicted_daily_demand"] * order_coverage_days) - triggers["stock_available"]
   )
   raw_qty = raw_qty.where(triggers["needs_reorder"], 0)
   raw_qty = raw_qty.clip(lower=0)

   triggers["recommended_order_qty"] = (
      (raw_qty / round_to).round() * round_to
   ).round(2)

   erratic_product_ids = [
      p["product_id"] for p in PRODUCTS if p.get("zero_order_prob", 0) > 0
   ]
   triggers["erratic_demand_flag"] = triggers["product_id"].isin(erratic_product_ids)

   negative_demand = (triggers["predicted_daily_demand"] < 0).sum()
   negative_orders = (triggers["recommended_order_qty"] < 0).sum()
   print(f"Sanity check — negative predicted demand: {negative_demand}, negative order quantities: {negative_orders}")

   return triggers


def generate_inventory_report(n_days=7, lead_time_days=7, order_coverage_days=30, round_to=5):
   """
   Run the full inventory recommendation pipeline and print a
   consolidated, presentable report.
   """
   model, feature_columns = load_model()
   inventory = load_current_inventory()

   reorder_points = compute_reorder_points(model, feature_columns, lead_time_days=lead_time_days)
   triggers = check_reorder_triggers(reorder_points, inventory)
   recommendations = compute_order_quantities(triggers, order_coverage_days=order_coverage_days, round_to=round_to)

   print("=" * 70)
   print("INVENTORY RECOMMENDATION REPORT")
   print("=" * 70)

   needs_action = recommendations[recommendations["needs_reorder"]]
   no_action = recommendations[~recommendations["needs_reorder"]]

   print(f"\n--- Products Requiring Reorder ({len(needs_action)}) ---")
   if len(needs_action) > 0:
      display_cols = ["product_name", "stock_available", "reorder_point", "recommended_order_qty", "erratic_demand_flag"]
      print(needs_action[display_cols].to_string(index=False))
   else:
      print("None — all products above their reorder points.")

   print(f"\n--- Products OK for Now ({len(no_action)}) ---")
   display_cols = ["product_name", "stock_available", "reorder_point"]
   print(no_action[display_cols].to_string(index=False))

   if needs_action["erratic_demand_flag"].any():
      print("\nNote: Some flagged products have erratic demand patterns.")
      print("Recommended quantities for these should be reviewed manually,")
      print("as averaging-based forecasts are less reliable for intermittent demand.")

   print("\n" + "=" * 70)
   print("END OF REPORT")
   print("=" * 70)

   return recommendations


if __name__ == "__main__":
   generate_inventory_report()