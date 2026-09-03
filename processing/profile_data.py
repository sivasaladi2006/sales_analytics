import pandas as pd

from config.products import PRODUCTS


# Load raw data
orders = pd.read_csv("data/orders_raw.csv")
order_items = pd.read_csv("data/order_items_raw.csv")

# Orders profiling

print("========== ORDERS PROFILING ==========\n")

print("Shape:")
print(orders.shape)

print("\nMissing values:")
print(orders.isnull().sum())

print("\nDuplicate rows:")
print(orders.duplicated().sum())


missing_customer_ids = orders["customer_id"].isnull().sum()
total_orders = len(orders)

missing_customer_percentage = (
   missing_customer_ids / total_orders
) * 100

print("\nMissing customer_id:")
print(f"Count: {missing_customer_ids}")
print(f"Percentage: {missing_customer_percentage:.2f}%")

# Date profiling

print("\nOrder date format profiling:")

valid_dates = pd.to_datetime(
   orders["order_date"],
   format="%Y-%m-%d",
   errors="coerce"
)

valid_date_count = valid_dates.notna().sum()
invalid_date_count = valid_dates.isna().sum()

print(f"Valid YYYY-MM-DD dates: {valid_date_count}")
print(f"Invalid/malformed dates: {invalid_date_count}")

invalid_date_percentage = (
   invalid_date_count / len(orders)
) * 100

print(f"Invalid date percentage: {invalid_date_percentage:.2f}%")

# Order items profiling

print("\n========== ORDER ITEMS PROFILING ==========\n")

print("Shape:")
print(order_items.shape)

print("\nMissing values:")
print(order_items.isnull().sum())

print("\nDuplicate rows:")
print(order_items.duplicated().sum())

# Price anomaly profiling

print("\nPrice anomaly profiling:")

price_lookup = {
   product["product_name"]: product["unit_price"]
   for product in PRODUCTS
}

order_items["expected_price"] = order_items["product_name"].map(
   price_lookup
)

order_items["price_difference"] = (
   order_items["unit_price_at_order"]
   != order_items["expected_price"]
)

price_anomaly_count = order_items["price_difference"].sum()

print(f"Price anomalies: {price_anomaly_count}")

price_anomaly_percentage = (
   price_anomaly_count / len(order_items)
) * 100

print(f"Price anomaly percentage: {price_anomaly_percentage:.2f}%")

# Profiling summary

print("\n========== PROFILING SUMMARY ==========")

print(f"Orders: {len(orders)}")
print(f"Order items: {len(order_items)}")
print(f"Missing customer IDs: {missing_customer_ids}")
print(f"Duplicate orders: {orders.duplicated().sum()}")
print(f"Duplicate order items: {order_items.duplicated().sum()}")
print(f"Malformed dates: {invalid_date_count}")
print(f"Price anomalies: {price_anomaly_count}")