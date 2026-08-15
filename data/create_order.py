import random


def find_or_create_order(
   todays_orders: list[dict],
   product_name: str,
   quantity: float,
   customers: list[dict]
) -> None:
   
   for order in todays_orders:
      product_exists = any(
         item["product_name"] == product_name
         for item in order["items"]
      )

      if len(order["items"]) < 4 and not product_exists:
         order["items"].append({
            "product_name": product_name,
            "quantity": quantity,
         })
         return

   customer = random.choice(customers)

   new_order = {
      "customer_id": customer["customer_id"],
      "items": [
         {
            "product_name": product_name,
            "quantity": quantity,
         }
      ],
   }

   todays_orders.append(new_order)