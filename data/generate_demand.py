import random

def generate_demand(
   base_demand: float,
   day: int,
   trend: float,              
   seasonal_months: list[int] | None,
   seasonal_multiplier: float,
   noise_range: tuple[float, float],
   zero_order_prob: float = 0.0,
   current_month: int = 1
) -> float:
   # Random zero-order day
   if random.random() < zero_order_prob:
      return 0.0

   # Trend
   trend_multiplier = 1.0 + trend * (day / 365)

   # Seasonality
   if seasonal_months is not None and current_month in seasonal_months:
      seasonal_factor = seasonal_multiplier
   else:
      seasonal_factor = 1.0

   # Noise
   noise_factor = random.uniform(noise_range[0], noise_range[1])

   # Demand
   daily_quantity = base_demand * trend_multiplier * seasonal_factor * noise_factor
   daily_quantity = max(0, daily_quantity)

   return round(daily_quantity, 2)