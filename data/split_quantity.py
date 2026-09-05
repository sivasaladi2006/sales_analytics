import random

def split_quantity(
  total_qty: float,
  min_buyers: int = 1,
  max_buyers: int = 6
) -> list[float]:
    
  if total_qty <= 0:
    raise ValueError("total_qty must be greater than 0")

  if min_buyers < 1:
    raise ValueError("min_buyers must be at least 1")

  if min_buyers > max_buyers:
    raise ValueError("min_buyers cannot be greater than max_buyers")

  # Don't create more parts than can be represented
  # as positive values rounded to 2 decimal places.
  max_possible_buyers = int(total_qty * 100)

  if max_possible_buyers < min_buyers:
    num_buyers = min_buyers
  else:
    num_buyers = random.randint(
      min_buyers,
      min(max_buyers, max_possible_buyers)
    )

  # Generate random weights
  weights = [
    random.uniform(0.5, 1.5)
    for _ in range(num_buyers)
  ]

  total_weight = sum(weights)

  # Scale weights to total quantity
  parts = [
    round(total_qty * weight / total_weight, 2)
    for weight in weights
  ]

  # Correct rounding difference
  difference = round(total_qty - sum(parts), 2)
  parts[-1] = round(parts[-1] + difference, 2)

  return parts
   