import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def get_engine():
   user = os.getenv("DB_USER")
   password = quote_plus(os.getenv("DB_PASSWORD"))
   host = os.getenv("DB_HOST")
   database = os.getenv("DB_NAME")

   connection_string = f"mysql+pymysql://{user}:{password}@{host}/{database}"

   engine = create_engine(connection_string)

   return engine


if __name__ == "__main__":
   engine = get_engine()
   with engine.connect() as conn:
      result = conn.execute(text("SELECT 1"))
      print("Connection successful:", result.fetchone())