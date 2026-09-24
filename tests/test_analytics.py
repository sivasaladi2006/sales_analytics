from analytics.sales_analysis import best_sellers, category_performance


def test_best_sellers_returns_all_products():
   """best_sellers() should return exactly 20 rows (one per product)."""
   df = best_sellers()
   assert len(df) == 20


def test_best_sellers_revenue_is_positive():
   """All revenue values should be positive."""
   df = best_sellers()
   assert (df["total_revenue"] > 0).all()


def test_category_performance_returns_all_categories():
   """category_performance() should return exactly 6 rows (one per category)."""
   df = category_performance()
   assert len(df) == 6


def test_category_revenue_sums_to_total():
   """Sum of category revenue should approximately match sum of product revenue."""
   products_df = best_sellers()
   categories_df = category_performance()
   assert abs(products_df["total_revenue"].sum() - categories_df["total_revenue"].sum()) < 1.0