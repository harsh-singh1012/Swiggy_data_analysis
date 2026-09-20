"""
08_powerbi_prep.py — Power BI data model prep

Builds the calendar table (dim_date.csv) and copies pre-aggregated
reference/validation tables into powerbi/model/. The four large
star-schema tables (fact_orders, dim_restaurants, dim_users,
customer_rfm) are NOT duplicated here — they already live in
data/cleaned/ and the dashboard build guide points Power BI's
Get Data step there directly, so the same ~200MB of order/restaurant
data isn't copied twice into this delivered project folder.
"""
import pandas as pd
import numpy as np
import os
import shutil

CLEANED = "../data/cleaned"
MODEL = "model"
os.makedirs(MODEL, exist_ok=True)

fact = pd.read_csv(f"{CLEANED}/fact_orders.csv", parse_dates=["order_date"])

# ---- dim_date calendar table spanning the full order history ----
full_range = pd.date_range(fact["order_date"].min(), fact["order_date"].max(), freq="D")
dim_date = pd.DataFrame({"date": full_range})
dim_date["year"] = dim_date["date"].dt.year
dim_date["month_num"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.strftime("%b")
dim_date["year_month"] = dim_date["date"].dt.to_period("M").astype(str)
dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
dim_date["year_quarter"] = dim_date["year"].astype(str) + "-" + dim_date["quarter"]
dim_date["day_of_week"] = dim_date["date"].dt.day_name()
dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5
dim_date.to_csv(f"{MODEL}/dim_date.csv", index=False)

# NOTE: fact_orders.csv, dim_restaurants.csv, dim_users.csv and customer_rfm.csv
# are intentionally NOT copied here — import them straight from data/cleaned/
# in Power BI's Get Data step (see powerbi/dashboard_build_guide.md). Copying
# them into powerbi/model/ too would duplicate ~100MB of data for no benefit.

# ---- reference/validation tables (optional visuals, not required by DAX) ----
for fname in ["rfm_segment_summary.csv", "city_performance.csv", "cohort_retention_matrix.csv",
              "cohort_retention_overall_curve.csv", "rca_city_orders_change.csv", "rca_segment_orders_change.csv"]:
    src = f"{CLEANED}/{fname}"
    if os.path.exists(src):
        shutil.copy(src, f"{MODEL}/{fname}")

print("Power BI model folder contents:")
for f in sorted(os.listdir(MODEL)):
    size = os.path.getsize(f"{MODEL}/{f}") / 1e6
    print(f"  {f}  ({size:.1f} MB)")
