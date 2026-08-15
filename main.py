from datetime import date, timedelta

from config.products import PRODUCTS
from config.customers import CUSTOMERS

from data.generate_demand import generate_demand
from data.split_quantity import split_quantity
from data.create_order import find_or_create_order
from data.write_csv import write_to_csv


all_orders = []
all_order_items = []

order_id_counter = 1
order_item_id_counter = 1


# Product lookup dictionary
product_lookup = {
   product["product_name"]: product
   for product in PRODUCTS
}


start_date = date(2025, 1, 1)


for day in range(1, 366):

   current_date = start_date + timedelta(days=day - 1)
   current_month = current_date.month

   todays_orders = []


   # Generate demand for each product
   for product in PRODUCTS:

      total_qty_today = generate_demand(
         base_demand=product["base_demand"],
         day=day,
         trend=product["trend"],
         seasonal_months=product["seasonal_months"],
         seasonal_multiplier=product["seasonal_multiplier"],
         noise_range=product["noise_range"],
         zero_order_prob=product["zero_order_prob"],
         current_month=current_month
      )

      if total_qty_today == 0:
         continue


      quantity_parts = split_quantity(total_qty_today)


      # Add each quantity portion to a customer basket
      for portion in quantity_parts:

         find_or_create_order(
            todays_orders,
            product["product_name"],
            portion,
            CUSTOMERS
         )


   # Finalize today's orders
   for order in todays_orders:

      order_id = order_id_counter
      order_id_counter += 1

      all_orders.append({
         "order_id": order_id,
         "customer_id": order["customer_id"],
         "order_date": current_date,
      })


      # Create order item rows
      for item in order["items"]:

         order_item_id = order_item_id_counter
         order_item_id_counter += 1

         product = product_lookup[item["product_name"]]

         all_order_items.append({
            "order_item_id": order_item_id,
            "order_id": order_id,
            "product_name": item["product_name"],
            "quantity": item["quantity"],
            "unit_price_at_order": product["unit_price"],
         })

print(f"Total orders generated: {len(all_orders)}")
print(f"Total order items generated: {len(all_order_items)}")
print("\nSample order:", all_orders[0])
print("Sample order item:", all_order_items[0])

write_to_csv("data/orders.csv", all_orders)
write_to_csv("data/order_items.csv", all_order_items)

print("CSV files written successfully.")