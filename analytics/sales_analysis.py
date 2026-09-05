from analytics.query_runner import run_query
def best_sellers():
   query = """
      SELECT
         p.product_name,
         SUM(oi.quantity) AS total_quantity_sold,
         SUM(oi.quantity * oi.unit_price_at_order) AS total_revenue
      FROM order_items oi
      JOIN products p
         ON oi.product_id = p.product_id
      GROUP BY p.product_id, p.product_name
      ORDER BY total_revenue DESC;
   """
   return run_query(query)


def category_performance():
   query = """
      SELECT
         c.category_name,
         SUM(oi.quantity) AS total_quantity_sold,
         SUM(oi.quantity * oi.unit_price_at_order) AS total_revenue
      FROM order_items oi
      JOIN products p
         ON oi.product_id = p.product_id
      JOIN categories c
         ON p.category_id = c.category_id
      GROUP BY c.category_id, c.category_name
      ORDER BY total_revenue DESC;
   """
   return run_query(query)


def revenue_trends():
   query = """
      SELECT
         DATE_FORMAT(o.order_date, '%%Y-%%m') AS month,
         SUM(oi.quantity * oi.unit_price_at_order) AS total_revenue,
         COUNT(DISTINCT o.order_id) AS total_orders
      FROM order_items oi
      JOIN orders o
         ON oi.order_id = o.order_id
      GROUP BY month
      ORDER BY month;
   """
   return run_query(query)


def trend_analysis():
   query = """
      SELECT 
         p.product_name,
         SUM(CASE WHEN o.order_date < '2025-04-01' THEN oi.quantity ELSE 0 END) AS q1_quantity,
         SUM(CASE WHEN o.order_date >= '2025-10-01' THEN oi.quantity ELSE 0 END) AS q4_quantity
      FROM order_items oi
      JOIN orders o ON oi.order_id = o.order_id
      JOIN products p ON oi.product_id = p.product_id
      GROUP BY p.product_id, p.product_name
      ORDER BY p.product_id;
   """

   df = run_query(query)
   df["pct_change"] = (
      (df["q4_quantity"] - df["q1_quantity"])
      / df["q1_quantity"]
      * 100
   ).round(1)

   return df.sort_values("pct_change", ascending=False)


def low_stock_risk():
   query = """
      SELECT 
         p.product_id,
         p.product_name,
         i.stock_available,
         SUM(oi.quantity) / 30 AS avg_daily_demand_recent
      FROM order_items oi
      JOIN orders o ON oi.order_id = o.order_id
      JOIN products p ON oi.product_id = p.product_id
      JOIN inventory i ON p.product_id = i.product_id
      WHERE o.order_date >= '2025-12-01'
      GROUP BY p.product_id, p.product_name, i.stock_available;
   """

   df = run_query(query)
   df["days_of_stock_remaining"] = (
      df["stock_available"] / df["avg_daily_demand_recent"]
   ).round(1)

   return df.sort_values("days_of_stock_remaining")


def region_performance():
   query = """
      SELECT 
         c.region,
         COUNT(DISTINCT o.order_id) AS total_orders,
         SUM(oi.quantity * oi.unit_price_at_order) AS total_revenue
      FROM orders o
      JOIN customers c ON o.customer_id = c.customer_id
      JOIN order_items oi ON o.order_id = oi.order_id
      WHERE c.customer_id != -1
      GROUP BY c.region
      ORDER BY total_revenue DESC;
   """
   return run_query(query)


def top_customers():
   query = """
      SELECT 
         c.customer_id,
         c.name,
         c.region,
         SUM(oi.quantity * oi.unit_price_at_order) AS total_spend
      FROM orders o
      JOIN customers c ON o.customer_id = c.customer_id
      JOIN order_items oi ON o.order_id = oi.order_id
      WHERE c.customer_id != -1
      GROUP BY c.customer_id, c.name, c.region
      ORDER BY total_spend DESC
      LIMIT 10;
   """
   return run_query(query)


def generate_full_report():
   print("=" * 60)
   print("SALES & INVENTORY ANALYTICS REPORT")
   print("=" * 60)

   print("\n--- Best Sellers (by Revenue) ---")
   print(best_sellers().to_string(index=False))

   print("\n--- Category Performance ---")
   print(category_performance().to_string(index=False))

   print("\n--- Monthly Revenue Trends ---")
   print(revenue_trends().to_string(index=False))

   print("\n--- Product Trend Analysis (Q1 vs Q4) ---")
   print(trend_analysis().to_string(index=False))

   print("\n--- Low Stock Risk (Top 5) ---")
   print(low_stock_risk().head(5).to_string(index=False))

   print("\n--- Region Performance ---")
   print(region_performance().to_string(index=False))

   print("\n--- Top 10 Customers ---")
   print(top_customers().to_string(index=False))

   print("\n" + "=" * 60)
   print("END OF REPORT")
   print("=" * 60)


if __name__ == "__main__":
   generate_full_report()