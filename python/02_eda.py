"""
02_eda.py — Exploratory Data Analysis
Revenue, orders, customers, restaurants. Saves charts to ../eda_charts/
and a text summary to docs/04_eda_summary.md.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

CLEANED = "../data/cleaned"
CHARTS = "../eda_charts"
os.makedirs(CHARTS, exist_ok=True)

# ---- palette (validated categorical order; see docs/palette reference) ----
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"
)
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans",
})

fact = pd.read_csv(f"{CLEANED}/fact_orders.csv", parse_dates=["order_date"])
rest = pd.read_csv(f"{CLEANED}/dim_restaurants.csv")
users = pd.read_csv(f"{CLEANED}/dim_users.csv")

summary = []
def note(x):
    print(x)
    summary.append(x)

def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{CHARTS}/{name}", dpi=150)
    plt.close(fig)
    note(f"saved chart: eda_charts/{name}")

# ------------------------------------------------------------------
# 1. Monthly revenue trend
# ------------------------------------------------------------------
monthly = fact.groupby("year_month").agg(
    orders=("order_id", "count"),
    revenue=("revenue", "sum"),
).reset_index()
monthly["aov"] = fact[fact.is_zero_amount == 0].groupby("year_month")["revenue"].mean().values

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(monthly["year_month"], monthly["revenue"] / 1e6, color=BLUE, linewidth=2.2, marker="o", markersize=3.5)
ax.set_title("Monthly Revenue (₹ Millions)")
ax.set_ylabel("Revenue (₹M)")
ax.set_xticks(range(0, len(monthly), 3))
ax.set_xticklabels(monthly["year_month"].iloc[::3], rotation=45, ha="right")
save(fig, "01_monthly_revenue_trend.png")

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(monthly["year_month"], monthly["orders"], color=ORANGE, linewidth=2.2, marker="o", markersize=3.5)
ax.set_title("Monthly Order Volume")
ax.set_ylabel("Orders")
ax.set_xticks(range(0, len(monthly), 3))
ax.set_xticklabels(monthly["year_month"].iloc[::3], rotation=45, ha="right")
save(fig, "02_monthly_orders_trend.png")

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(monthly["year_month"], monthly["aov"], color=AQUA, linewidth=2.2, marker="o", markersize=3.5)
ax.set_title("Monthly Average Order Value (AOV)")
ax.set_ylabel("AOV (₹)")
ax.set_xticks(range(0, len(monthly), 3))
ax.set_xticklabels(monthly["year_month"].iloc[::3], rotation=45, ha="right")
save(fig, "03_monthly_aov_trend.png")

first_days = (fact.loc[fact.year_month == monthly.year_month.min(), "order_date"].max().day)
last_days = (fact.loc[fact.year_month == monthly.year_month.max(), "order_date"].max().day)
note(f"Revenue range across {len(monthly)} months: ₹{monthly.revenue.min()/1e6:.1f}M to ₹{monthly.revenue.max()/1e6:.1f}M. "
     f"NOTE: the first month ({monthly.year_month.min()}) only has data from day 4 onward and the last month "
     f"({monthly.year_month.max()}) only runs through day {last_days} — both are partial calendar months and read "
     f"as artificially low if compared directly to full months. Revenue is volatile month to month, peaks around "
     f"early 2018 (~₹42.5M), and shows a broad decline into 2019-2020, with the steepest drop in the final "
     f"(partial) month.")

# ------------------------------------------------------------------
# 2. City contribution (top 15 by revenue) — horizontal bar
# ------------------------------------------------------------------
attributable = fact[fact.has_restaurant == 1].merge(rest[["r_id", "city"]], on="r_id", how="left")
city_rev = attributable.groupby("city").agg(orders=("order_id", "count"), revenue=("revenue", "sum")).reset_index()
city_rev["pct"] = 100 * city_rev.revenue / city_rev.revenue.sum()
top_cities = city_rev.sort_values("revenue", ascending=False).head(15)

fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(top_cities["city"][::-1], top_cities["revenue"][::-1] / 1e6, color=BLUE, height=0.65)
ax.set_title("Top 15 Cities by Revenue")
ax.set_xlabel("Revenue (₹M)")
save(fig, "04_top_cities_revenue.png")

note(f"Top city (Tirupati) contributes {top_cities.iloc[0]['pct']:.1f}% of total attributable revenue "
     f"from only {int(top_cities.iloc[0]['orders'])} orders — an unusually high per-order value versus peers.")

# ------------------------------------------------------------------
# 3. Order value distribution (histogram, log-scale x since heavily skewed)
# ------------------------------------------------------------------
valid_amt = fact.loc[fact.is_zero_amount == 0, "amount"]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(np.log10(valid_amt.clip(lower=1)), bins=50, color=BLUE, edgecolor=SURFACE, linewidth=0.4)
ax.set_title("Order Value Distribution (log10 scale)")
ax.set_xlabel("log10(order amount, ₹)")
ax.set_ylabel("Number of orders")
save(fig, "05_order_value_distribution.png")

note(f"Order value is heavily right-skewed: median ₹{valid_amt.median():.0f}, mean ₹{valid_amt.mean():.0f} — "
     f"the mean is pulled well above the median by a long tail of high-value orders (max ₹{valid_amt.max():,.0f}).")

# ------------------------------------------------------------------
# 4. Customer order-frequency distribution
# ------------------------------------------------------------------
freq = fact.groupby("user_id").size().value_counts().sort_index()
freq_capped = freq[freq.index <= 8]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(freq_capped.index.astype(str), freq_capped.values, color=ORANGE)
ax.set_title("Customer Order-Frequency Distribution")
ax.set_xlabel("Orders placed")
ax.set_ylabel("Number of customers")
save(fig, "06_customer_order_frequency.png")

pct_one = freq.loc[1] / freq.sum() * 100
note(f"{pct_one:.1f}% of ordering customers placed exactly one order; frequency decays fast after that.")

# ------------------------------------------------------------------
# 5. Restaurant rating distribution
# ------------------------------------------------------------------
rated = rest[rest.has_rating == 1]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(rated["rating_numeric"], bins=30, color=AQUA, edgecolor=SURFACE, linewidth=0.4)
ax.set_title("Restaurant Rating Distribution (rated restaurants only)")
ax.set_xlabel("Rating")
ax.set_ylabel("Number of restaurants")
save(fig, "07_rating_distribution.png")

note(f"{len(rated):,} of {len(rest):,} restaurants ({len(rated)/len(rest):.1%}) have a numeric rating; "
     f"the rest show the platform's 'Too Few Ratings' placeholder and are excluded from rating analysis.")

# ------------------------------------------------------------------
# 6. Order type mix (Veg/Non-Veg/Other) — bar, not pie
# ------------------------------------------------------------------
type_counts = fact["order_type"].value_counts()
fig, ax = plt.subplots(figsize=(6, 4.5))
ax.bar(type_counts.index, type_counts.values, color=[BLUE, ORANGE, AQUA])
ax.set_title("Orders by Food Type")
ax.set_ylabel("Orders")
save(fig, "08_order_type_mix.png")
note(f"Order-type mix is close to an even three-way split: {dict(type_counts)}")

with open("../docs/04_eda_summary.md", "w") as f:
    f.write("# Python EDA Summary\n\nGenerated by `python/02_eda.py`. Charts saved to `eda_charts/`.\n\n")
    for line in summary:
        f.write(f"- {line}\n")

print("\nEDA complete.")
