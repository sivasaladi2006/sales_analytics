import pandas as pd
from config.products import PRODUCTS

def handle_missing_customer_ids(orders: pd.DataFrame) -> pd.DataFrame:
   orders["customer_id"] = orders["customer_id"].fillna(-1)
   orders["customer_id"] = orders["customer_id"].astype(int)

   return orders

def remove_duplicate_orders(orders: pd.DataFrame) -> pd.DataFrame:
   orders = orders.drop_duplicates(
      subset=["order_id"],
       keep="first"
   )
   return orders

def remove_duplicate_order_items(order_items: pd.DataFrame) -> pd.DataFrame:
   order_items = order_items.drop_duplicates(
      subset=["order_item_id"],
      keep="first"
   )
   return order_items

def fix_malformed_dates(orders: pd.DataFrame) -> pd.DataFrame:
   parsed_a = pd.to_datetime(
      orders["order_date"],
      format="%Y-%m-%d",
      errors="coerce"
   )
   parsed_b = pd.to_datetime(
      orders["order_date"],
      format="%d/%m/%Y",
      errors="coerce"
   )
   orders["order_date"] = parsed_a.fillna(parsed_b)
   return orders

def check_price_sanity(
   order_items: pd.DataFrame,
   price_lookup: dict,
   threshold: float = 0.5
) -> pd.DataFrame:
   expected_price = order_items["product_name"].map(price_lookup)
   deviation = (
      abs(order_items["unit_price_at_order"] - expected_price)
      / expected_price
   )
   flagged_rows = order_items[deviation > threshold]
   return flagged_rows

def validate_cleaned_data(
   orders: pd.DataFrame,
   order_items: pd.DataFrame,
   valid_product_names: set
) -> bool:
   all_passed = True
   # 1. Check for unexpected missing values
   orders_missing = orders.isnull().sum().sum()
   order_items_missing = order_items.isnull().sum().sum()
   missing_passed = (
      orders_missing == 0
      and order_items_missing == 0
   )
   print(
      f"Missing values: "
      f"{'PASS' if missing_passed else 'FAIL'}"
   )
   if not missing_passed:
      print(f"  Orders missing values: {orders_missing}")
      print(f"  Order items missing values: {order_items_missing}")
   all_passed = all_passed and missing_passed

   # 2. Check duplicate order IDs
   duplicate_orders = orders["order_id"].duplicated().sum()
   duplicate_orders_passed = duplicate_orders == 0
   print(
      f"Duplicate order IDs: "
      f"{'PASS' if duplicate_orders_passed else 'FAIL'}"
   )
   if not duplicate_orders_passed:
      print(f"  Duplicate order IDs: {duplicate_orders}")
   all_passed = all_passed and duplicate_orders_passed

   # 3. Check duplicate order item IDs
   duplicate_order_items = (
      order_items["order_item_id"].duplicated().sum()
   )
   duplicate_order_items_passed = duplicate_order_items == 0
   print(
      f"Duplicate order item IDs: "
      f"{'PASS' if duplicate_order_items_passed else 'FAIL'}"
   )
   if not duplicate_order_items_passed:
      print(
         f"  Duplicate order item IDs: "
         f"{duplicate_order_items}"
      )
   all_passed = all_passed and duplicate_order_items_passed

   # 4. Check referential integrity
   invalid_order_ids = (
      ~order_items["order_id"].isin(orders["order_id"])
   ).sum()
   referential_integrity_passed = invalid_order_ids == 0
   print(
      f"Order ID referential integrity: "
      f"{'PASS' if referential_integrity_passed else 'FAIL'}"
   )
   if not referential_integrity_passed:
      print(f"  Invalid order IDs: {invalid_order_ids}")
   all_passed = all_passed and referential_integrity_passed

   # 5. Check product names
   invalid_product_names = (
      ~order_items["product_name"].isin(valid_product_names)
   ).sum()
   product_names_passed = invalid_product_names == 0
   print(
      f"Product name validity: "
      f"{'PASS' if product_names_passed else 'FAIL'}"
   )
   if not product_names_passed:
      print(
         f"  Invalid product names: "
         f"{invalid_product_names}"
      )
   all_passed = all_passed and product_names_passed

   # Final result
   print("\n" + "=" * 40)
   if all_passed:
      print("VALIDATION PASSED")
   else:
      print("VALIDATION FAILED")
   return all_passed

if __name__ == "__main__":
   orders = pd.read_csv("data/orders_raw.csv")
   order_items = pd.read_csv("data/order_items_raw.csv")

   orders = handle_missing_customer_ids(orders)

   print("Before dedup - orders:", orders.shape[0])
   orders = remove_duplicate_orders(orders)
   print("After dedup - orders:", orders.shape[0])
   print("Remaining duplicate order_ids:", orders.duplicated(subset=["order_id"]).sum())

   print("\nBefore dedup - order_items:", order_items.shape[0])
   order_items = remove_duplicate_order_items(order_items)
   print("After dedup - order_items:", order_items.shape[0])
   print("Remaining duplicate order_item_ids:", order_items.duplicated(subset=["order_item_id"]).sum())

   orders = fix_malformed_dates(orders)
   print("\nMissing dates after fix:", orders["order_date"].isnull().sum())
   print("order_date dtype:", orders["order_date"].dtype)

   price_lookup = {p["product_name"]: p["unit_price"] for p in PRODUCTS}
   flagged = check_price_sanity(order_items, price_lookup, threshold=0.5)
   print(f"\nPrice sanity check: {len(flagged)} rows exceed ±50% deviation")
   valid_product_names = set(p["product_name"] for p in PRODUCTS)
   validate_cleaned_data(orders, order_items, valid_product_names)