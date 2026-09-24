import pytest
from data.split_quantity import split_quantity


def test_split_quantity_sums_to_total():
   """Parts should always sum back to the original total."""
   for total in [24, 1.5, 0.1, 100, 0.33]:
      parts = split_quantity(total)
      assert abs(sum(parts) - total) < 0.01


def test_split_quantity_all_parts_positive():
   """No part should ever be zero or negative."""
   for total in [0.1, 0.5, 1.0, 24, 100]:
      parts = split_quantity(total)
      assert all(p > 0 for p in parts)


def test_split_quantity_raises_on_invalid_total():
   """Should raise ValueError for total_qty <= 0."""
   with pytest.raises(ValueError):
      split_quantity(0)
   with pytest.raises(ValueError):
      split_quantity(-5)


def test_split_quantity_respects_max_buyers():
   """Number of parts should never exceed max_buyers."""
   parts = split_quantity(1000, min_buyers=1, max_buyers=6)
   assert len(parts) <= 6