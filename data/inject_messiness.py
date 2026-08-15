import csv
import random

from data.write_csv import write_to_csv


def read_csv(filepath: str) -> list[dict]:
   """Read a CSV file into a list of dicts."""

   with open(filepath, "r", newline="") as f:
      reader = csv.DictReader(f)
      return list(reader)


def inject_missing_customer_ids(
   orders: list[dict],
   missing_fraction: float = 0.03
) -> None:
   """Randomly blank out customer_id for a fraction of orders."""

   number_to_modify = int(
      len(orders) * missing_fraction
   )

   selected_orders = random.sample(
      orders,
      number_to_modify
   )

   for order in selected_orders:
      order["customer_id"] = ""


def inject_duplicates(
   rows: list[dict],
   duplicate_fraction: float = 0.02
) -> None:
   """Randomly duplicate a fraction of rows."""

   number_to_duplicate = int(
      len(rows) * duplicate_fraction
   )

   selected_rows = random.sample(
      rows,
      number_to_duplicate
   )

   for row in selected_rows:
      rows.append(row.copy())


def inject_price_inconsistencies(
   order_items: list[dict],
   price_fraction: float = 0.04
) -> None:
   """Randomly alter unit prices by approximately ±10–20%."""

   number_to_modify = int(
      len(order_items) * price_fraction
   )

   selected_items = random.sample(
      order_items,
      number_to_modify
   )

   for item in selected_items:

      price = float(item["unit_price_at_order"])

      change = random.uniform(0.10, 0.20)

      if random.choice([True, False]):
         price *= (1 + change)
      else:
         price *= (1 - change)

      item["unit_price_at_order"] = round(price, 2)


def inject_malformed_dates(
   orders: list[dict],
   date_fraction: float = 0.015
) -> None:
   """Randomly change some dates into malformed formats."""

   number_to_modify = int(
      len(orders) * date_fraction
   )

   selected_orders = random.sample(
      orders,
      number_to_modify
   )

   for order in selected_orders:

      date_value = order["order_date"]

      parts = date_value.split("-")

      if len(parts) == 3:
         year, month, day = parts

         order["order_date"] = (
            f"{day}/{month}/{year}"
         )


def main():

   orders = read_csv("data/orders.csv")
   order_items = read_csv("data/order_items.csv")

   print(f"Clean orders: {len(orders)}")
   print(f"Clean order items: {len(order_items)}")


   # Missing customer IDs
   inject_missing_customer_ids(
      orders,
      missing_fraction=0.03
   )


   # Duplicate rows
   inject_duplicates(
      orders,
      duplicate_fraction=0.02
   )

   inject_duplicates(
      order_items,
      duplicate_fraction=0.02
   )


   # Price inconsistencies
   inject_price_inconsistencies(
      order_items,
      price_fraction=0.04
   )


   # Malformed dates
   inject_malformed_dates(
      orders,
      date_fraction=0.015
   )


   # Write messy/raw files
   write_to_csv(
      "data/orders_raw.csv",
      orders
   )

   write_to_csv(
      "data/order_items_raw.csv",
      order_items
   )


   print(f"Raw orders: {len(orders)}")
   print(f"Raw order items: {len(order_items)}")

   print("\nMessiness injection complete.")
   print("Created:")
   print("  data/orders_raw.csv")
   print("  data/order_items_raw.csv")


if __name__ == "__main__":
   main()