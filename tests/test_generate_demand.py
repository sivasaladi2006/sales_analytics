import pytest
from data.generate_demand import generate_demand


def test_generate_demand_returns_non_negative():
   """Demand should never be negative regardless of noise."""
   for _ in range(100):
      result = generate_demand(
         base_demand=10, day=50, trend=0.0,
         seasonal_months=[], seasonal_multiplier=1.0,
         noise_range=(0.1, 3.0), zero_order_prob=0.0
      )
      assert result >= 0


def test_generate_demand_zero_order_probability_one():
   """With zero_order_prob=1.0, result should always be exactly 0."""
   result = generate_demand(
      base_demand=10, day=50, trend=0.0,
      seasonal_months=[], seasonal_multiplier=1.0,
      noise_range=(0.9, 1.1), zero_order_prob=1.0
   )
   assert result == 0.0


def test_generate_demand_seasonal_multiplier_applied():
   """Demand should be higher in a seasonal month than a non-seasonal one, on average."""
   import random
   random.seed(42)
   seasonal_results = [
      generate_demand(
         base_demand=10, day=300, trend=0.0,
         seasonal_months=[10], seasonal_multiplier=3.0,
         noise_range=(0.95, 1.05), zero_order_prob=0.0, current_month=10
      ) for _ in range(20)
   ]
   non_seasonal_results = [
      generate_demand(
         base_demand=10, day=50, trend=0.0,
         seasonal_months=[10], seasonal_multiplier=3.0,
         noise_range=(0.95, 1.05), zero_order_prob=0.0, current_month=2
      ) for _ in range(20)
   ]
   assert sum(seasonal_results) / len(seasonal_results) > sum(non_seasonal_results) / len(non_seasonal_results) * 2