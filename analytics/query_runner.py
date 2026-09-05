import pandas as pd
from db.connection import get_engine


def run_query(query: str) -> pd.DataFrame:

   engine = get_engine()
   df = pd.read_sql(query, engine)
   return df


if __name__ == "__main__":
   df = run_query("SELECT COUNT(*) AS total_orders FROM orders")
   print(df)