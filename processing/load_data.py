import pandas as pd


orders = pd.read_csv("data/orders_raw.csv")
order_items = pd.read_csv("data/order_items_raw.csv")


print("Orders shape:", orders.shape)
print("Order items shape:", order_items.shape)


print("\nOrders info:")
orders.info()


print("\nOrder items info:")
order_items.info()