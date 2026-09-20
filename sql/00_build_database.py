"""
Loads the cleaned CSVs into a local SQLite database (swiggy.db) so the
.sql files in this folder can be run as real, executable SQL against
structured business data — not just illustrative snippets.
"""
import sqlite3
import pandas as pd
import os

CLEANED = "../data/cleaned"
DB = "swiggy.db"

if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)

tables = {
    "dim_users": "dim_users.csv",
    "dim_restaurants": "dim_restaurants.csv",
    "dim_food": "dim_food.csv",
    "bridge_menu": "bridge_menu.csv",
    "fact_orders": "fact_orders.csv",
}

for table, fname in tables.items():
    df = pd.read_csv(f"{CLEANED}/{fname}")
    if table == "fact_orders":
        df["order_date"] = pd.to_datetime(df["order_date"])
    df.to_sql(table, conn, if_exists="replace", index=False)
    print(f"loaded {table}: {len(df):,} rows")

# helpful indexes for join/aggregation performance
cur = conn.cursor()
cur.execute("CREATE INDEX idx_orders_user ON fact_orders(user_id)")
cur.execute("CREATE INDEX idx_orders_r ON fact_orders(r_id)")
cur.execute("CREATE INDEX idx_orders_date ON fact_orders(order_date)")
cur.execute("CREATE INDEX idx_orders_ym ON fact_orders(year_month)")
cur.execute("CREATE INDEX idx_rest_id ON dim_restaurants(r_id)")
cur.execute("CREATE INDEX idx_rest_city ON dim_restaurants(city)")
conn.commit()
conn.close()
print("swiggy.db built with indexes.")
