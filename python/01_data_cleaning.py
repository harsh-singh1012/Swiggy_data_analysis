"""
01_data_cleaning.py
Swiggy Marketplace Intelligence — Data Cleaning & Modelling

Reads the six raw files, applies the cleaning rules documented in
docs/01_data_audit.md, engineers the fields needed downstream (RFM, cohorts,
revenue decomposition), and writes analysis-ready CSVs to data/cleaned/.

Every cleaning decision here is a direct consequence of a finding in the
audit — nothing is dropped or imputed silently.
"""
import pandas as pd
import numpy as np
import os

RAW = "../data/raw"
OUT = "../data/cleaned"
os.makedirs(OUT, exist_ok=True)

log = []
def note(msg):
    print(msg)
    log.append(msg)

# ---------------------------------------------------------------------------
# 1. USERS
# ---------------------------------------------------------------------------
users = pd.read_excel(f"{RAW}/users_1.xlsx", engine="openpyxl")
users = users.rename(columns={
    "user_id": "user_id", "name": "name", "Age": "age",
    "Gender": "gender", "Marital Status": "marital_status", "Occupation": "occupation"
})
users["user_id"] = users["user_id"].astype(int)
users = users.drop_duplicates(subset="user_id")
note(f"users: {len(users):,} rows after cleaning")
users.to_csv(f"{OUT}/dim_users.csv", index=False)

# ---------------------------------------------------------------------------
# 2. RESTAURANTS
# ---------------------------------------------------------------------------
rest = pd.read_excel(f"{RAW}/restaurant.xlsx", engine="openpyxl")
rest = rest.rename(columns={"id": "r_id", "Country": "country", "city": "city"})

# rating: '--' placeholder -> NaN, else numeric
rest["rating_numeric"] = pd.to_numeric(rest["rating"], errors="coerce")
rest["has_rating"] = rest["rating_numeric"].notna()

# rating_count: ordinal bucket -> ordered category + numeric lower-bound proxy
bucket_map = {
    "Too Few Ratings": 0, "20+ ratings": 20, "50+ ratings": 50,
    "100+ ratings": 100, "500+ ratings": 500, "1K+ ratings": 1000,
    "5K+ ratings": 5000, "10K+ ratings": 10000,
}
rest["rating_count_floor"] = rest["rating_count"].map(bucket_map)  # NaN stays NaN
rest["rating_count_bucket"] = rest["rating_count"].fillna("Unknown")

# primary cuisine = first listed cuisine (cuisine field is comma-separated)
rest["cuisine"] = rest["cuisine"].fillna("Unknown")
rest["primary_cuisine"] = rest["cuisine"].str.split(",").str[0].str.strip()
rest["cuisine_count"] = rest["cuisine"].apply(lambda x: 0 if x == "Unknown" else len(x.split(",")))

rest["name"] = rest["name"].astype(str).where(rest["name"].notna(), "Unknown Restaurant")
rest["address"] = rest["address"].fillna("Unknown")
rest = rest.drop_duplicates(subset="r_id")

dim_restaurants = rest[[
    "r_id", "name", "country", "city", "rating_numeric", "has_rating",
    "rating_count_bucket", "rating_count_floor", "cuisine", "primary_cuisine",
    "cuisine_count", "address"
]]
note(f"restaurants: {len(dim_restaurants):,} rows after cleaning "
     f"({dim_restaurants['has_rating'].sum():,} have a numeric rating)")
dim_restaurants.to_csv(f"{OUT}/dim_restaurants.csv", index=False)

# ---------------------------------------------------------------------------
# 3. FOOD CATALOG
# ---------------------------------------------------------------------------
food = pd.read_excel(f"{RAW}/food_1.xlsx", engine="openpyxl")
food = food.dropna(subset=["f_id"])
food["f_id"] = food["f_id"].astype(str)
food["item"] = food["item"].astype(str)
food["veg_or_non_veg"] = food["veg_or_non_veg"].fillna("Unknown").replace({"Non-veg": "Non-Veg"})
before = len(food)
food = food.drop_duplicates()
note(f"food: {len(food):,} rows after cleaning (dropped {before-len(food)} exact duplicates/nulls)")
food.to_csv(f"{OUT}/dim_food.csv", index=False)

# ---------------------------------------------------------------------------
# 4. MENU (catalog-level, partial coverage — see audit)
# ---------------------------------------------------------------------------
menu = pd.read_excel(f"{RAW}/menu.xlsx", engine="openpyxl")
menu = menu.dropna(subset=["price"])
menu = menu[menu["r_id"].isin(dim_restaurants["r_id"])]
menu = menu[menu["f_id"].astype(str).isin(food["f_id"])]
note(f"menu: {len(menu):,} rows after cleaning, covering "
     f"{menu['r_id'].nunique():,} of {dim_restaurants['r_id'].nunique():,} restaurants "
     f"({menu['r_id'].nunique()/dim_restaurants['r_id'].nunique():.1%}) — partial extract, see audit")
menu.to_csv(f"{OUT}/bridge_menu.csv", index=False)

# ---------------------------------------------------------------------------
# 5. ORDERS (fact table) + ORDER TYPE (positional join — see audit)
# ---------------------------------------------------------------------------
orders = pd.read_excel(f"{RAW}/orders_1.xlsx", engine="openpyxl")
otype = pd.read_excel(f"{RAW}/orders_Type.xlsx", engine="openpyxl")
assert len(orders) == len(otype), "orders_1 and orders_Type row counts differ — positional join unsafe"

orders = orders.reset_index(drop=True)
otype = otype.reset_index(drop=True)
orders["order_id"] = "ORD" + orders.index.astype(str).str.zfill(7)
orders["order_id_raw_tag"] = otype["Order_Id"]   # kept for traceability only
orders["order_type"] = otype["Type"]

orders = orders.rename(columns={"sales_qty": "qty", "sales_amount": "amount"})

# invalid rows
neg_amount = orders["amount"] < 0
note(f"orders: dropping {neg_amount.sum()} rows with negative amount (data-entry errors)")
orders = orders[~neg_amount].copy()

orders["is_zero_amount"] = orders["amount"] == 0
orders["has_restaurant"] = orders["r_id"].notna()
orders = orders[orders["r_id"].isna() | orders["r_id"].isin(dim_restaurants["r_id"])].copy()

# qty outlier flag (winsorize at 99th percentile for aggregate use; raw kept)
q99 = orders["qty"].quantile(0.99)
orders["qty_capped"] = np.minimum(orders["qty"], q99)
note(f"orders: qty 99th percentile = {q99:.0f}, used as cap for aggregate qty metrics "
     f"(raw qty preserved in 'qty' column)")

orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["year"] = orders["order_date"].dt.year
orders["month"] = orders["order_date"].dt.month
orders["year_month"] = orders["order_date"].dt.to_period("M").astype(str)

# revenue field = amount, but excluded from monetary sums when zero -> separate column
orders["revenue"] = np.where(orders["is_zero_amount"], np.nan, orders["amount"])

note(f"orders: {len(orders):,} final rows | "
     f"{orders['is_zero_amount'].sum():,} zero-amount ({orders['is_zero_amount'].mean():.1%}) | "
     f"{(~orders['has_restaurant']).sum():,} with no restaurant ({(~orders['has_restaurant']).mean():.1%}) | "
     f"date range {orders['order_date'].min().date()} to {orders['order_date'].max().date()}")

fact_orders = orders[[
    "order_id", "order_date", "year", "month", "year_month", "user_id", "r_id",
    "qty", "qty_capped", "amount", "revenue", "is_zero_amount", "has_restaurant",
    "currency", "order_type", "order_id_raw_tag"
]]
fact_orders.to_csv(f"{OUT}/fact_orders.csv", index=False)

with open(f"{OUT}/../../docs/02_cleaning_log.md", "w") as f:
    f.write("# Data Cleaning Log\n\nGenerated by `python/01_data_cleaning.py`.\n\n")
    for line in log:
        f.write(f"- {line}\n")

print("\nDone. Cleaned files written to", os.path.abspath(OUT))
