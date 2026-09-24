import pytest
from sqlalchemy import text
from db.connection import get_engine


def test_foreign_key_rejects_invalid_category():
   """Inserting a product with a non-existent category_id should fail."""
   engine = get_engine()
   with pytest.raises(Exception):
      with engine.connect() as conn:
         conn.execute(text(
            "INSERT INTO products (product_name, category_id, supplier_id, unit_price) "
            "VALUES ('Test Invalid Product', 999, 1, 100.00)"
         ))
         conn.commit()


def test_all_products_have_valid_category():
   """Every product in the database must reference an existing category."""
   engine = get_engine()
   query = """
      SELECT COUNT(*) as invalid_count
      FROM products p
      LEFT JOIN categories c ON p.category_id = c.category_id
      WHERE c.category_id IS NULL;
   """
   with engine.connect() as conn:
      result = conn.execute(text(query)).fetchone()
   assert result[0] == 0


def test_all_order_items_reference_valid_orders():
   """Every order_item must reference an existing order (referential integrity)."""
   engine = get_engine()
   query = """
      SELECT COUNT(*) as invalid_count
      FROM order_items oi
      LEFT JOIN orders o ON oi.order_id = o.order_id
      WHERE o.order_id IS NULL;
   """
   with engine.connect() as conn:
      result = conn.execute(text(query)).fetchone()
   assert result[0] == 0