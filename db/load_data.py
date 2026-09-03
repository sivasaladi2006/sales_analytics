import pandas as pd
from sqlalchemy import text

from config.categories import CATEGORIES
from config.suppliers import SUPPLIERS
from config.customers import CUSTOMERS
from config.products import PRODUCTS
from config.inventory import INVENTORY
from processing.clean_data import (
   handle_missing_customer_ids,
   remove_duplicate_orders,
   remove_duplicate_order_items,
   fix_malformed_dates,
)
from db.connection import get_engine


def clear_all_tables(engine):
   with engine.connect() as conn:
      conn.execute(text("DELETE FROM inventory"))
      conn.execute(text("DELETE FROM order_items"))
      conn.execute(text("DELETE FROM orders"))
      conn.execute(text("DELETE FROM products"))
      conn.execute(text("DELETE FROM suppliers"))
      conn.execute(text("DELETE FROM customers"))
      conn.execute(text("DELETE FROM categories"))
      conn.commit()


def load_categories(engine):
   categories_df = pd.DataFrame(CATEGORIES)
   categories_df.to_sql("categories", engine, if_exists="append", index=False)
   result = pd.read_sql("SELECT * FROM categories", engine)
   print(result)


def load_suppliers(engine):
   suppliers_df = pd.DataFrame(SUPPLIERS)
   suppliers_df = suppliers_df.drop(columns=["category"])
   suppliers_df.to_sql("suppliers", engine, if_exists="append", index=False)
   result = pd.read_sql("SELECT * FROM suppliers", engine)
   print(result)


def load_customers(engine):
   customers_df = pd.DataFrame(CUSTOMERS)

   unknown_customer = pd.DataFrame([{
      "customer_id": -1,
      "name": "Unknown Customer",
      "region": "Unknown"
   }])
   customers_df = pd.concat([customers_df, unknown_customer], ignore_index=True)

   customers_df.to_sql("customers", engine, if_exists="append", index=False)
   result = pd.read_sql("SELECT * FROM customers", engine)
   print(result)


def load_products(engine):
   products_df = pd.DataFrame(PRODUCTS)

   category_lookup = {c["category_name"]: c["category_id"] for c in CATEGORIES}
   supplier_lookup = {s["category"]: s["supplier_id"] for s in SUPPLIERS}

   products_df["category_id"] = products_df["category"].map(category_lookup)
   products_df["supplier_id"] = products_df["category"].map(supplier_lookup)

   products_df = products_df[["product_id", "product_name", "category_id", "supplier_id", "unit_price"]]

   products_df.to_sql("products", engine, if_exists="append", index=False)
   result = pd.read_sql("SELECT * FROM products", engine)
   print(result)


def load_inventory(engine):
   inventory_df = pd.DataFrame(INVENTORY)
   inventory_df.to_sql("inventory", engine, if_exists="append", index=False)
   result = pd.read_sql("SELECT * FROM inventory", engine)
   print(result)


def load_orders_and_order_items(engine):
   orders = pd.read_csv("data/orders_raw.csv")
   order_items = pd.read_csv("data/order_items_raw.csv")

   orders = handle_missing_customer_ids(orders)
   orders = remove_duplicate_orders(orders)
   order_items = remove_duplicate_order_items(order_items)
   orders = fix_malformed_dates(orders)

   product_id_lookup = {p["product_name"]: p["product_id"] for p in PRODUCTS}
   order_items["product_id"] = order_items["product_name"].map(product_id_lookup)
   order_items = order_items[["order_item_id", "order_id", "product_id", "quantity", "unit_price_at_order"]]

   orders.to_sql("orders", engine, if_exists="append", index=False)
   order_items.to_sql("order_items", engine, if_exists="append", index=False)

   print("Orders loaded:", len(orders))
   print("Order items loaded:", len(order_items))


if __name__ == "__main__":
   engine = get_engine()

   clear_all_tables(engine)
   load_categories(engine)
   load_suppliers(engine)
   load_customers(engine)
   load_products(engine)
   load_inventory(engine)
   load_orders_and_order_items(engine)