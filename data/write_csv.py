import csv

def write_to_csv(filepath: str, rows: list[dict]) -> None:

   if not rows:
     return

   with open(filepath, "w", newline="") as f:
      fieldnames = rows[0].keys()
      
      writer = csv.DictWriter(
         f,
         fieldnames=fieldnames
      )

      writer.writeheader()
      writer.writerows(rows)