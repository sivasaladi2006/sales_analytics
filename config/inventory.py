import random

from config.products import PRODUCTS


INVENTORY = []

for product in PRODUCTS:
   stock_available = product["base_demand"] * random.randint(10, 21)

   last_restocked_day = random.randint(25, 31)
   last_restocked_date = f"2025-12-{last_restocked_day:02d}"

   INVENTORY.append({
      "product_id": product["product_id"],
      "stock_available": stock_available,
      "last_restocked_date": last_restocked_date,
   })

if __name__ == "__main__":
   print(len(INVENTORY))
   print(INVENTORY[0])
   print(INVENTORY[-1])