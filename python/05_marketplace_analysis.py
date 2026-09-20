"""
05_marketplace_analysis.py — Marketplace Analysis: Cities, Restaurants, Ratings

City/restaurant performance & concentration, and rating vs. order-volume
correlation (Pearson + Spearman), with an explicit correlation-is-not-
causation note and a disclosure of the near-degenerate orders-per-restaurant
ceiling found during the SQL analysis.
"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLEANED = "../data/cleaned"
CHARTS = "../eda_charts"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "axes.edgecolor": "#898781", "axes.labelcolor": "#0b0b0b", "text.color": "#0b0b0b",
    "xtick.color": "#898781", "ytick.color": "#898781",
    "axes.grid": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
})

fact = pd.read_csv(f"{CLEANED}/fact_orders.csv", parse_dates=["order_date"])
rest = pd.read_csv(f"{CLEANED}/dim_restaurants.csv")

attributable = fact[fact.has_restaurant == 1]

# ---------------------------------------------------------------
# City performance table
# ---------------------------------------------------------------
city_perf = attributable.merge(rest[["r_id", "city"]], on="r_id").groupby("city").agg(
    orders=("order_id", "count"),
    revenue=("revenue", "sum"),
    restaurants=("r_id", "nunique"),
).reset_index()
city_perf["aov"] = attributable.merge(rest[["r_id", "city"]], on="r_id")[
    lambda d: d.is_zero_amount == 0
].groupby("city")["revenue"].mean().reindex(city_perf["city"]).values
city_perf["pct_revenue"] = 100 * city_perf["revenue"] / city_perf["revenue"].sum()
city_perf = city_perf.sort_values("revenue", ascending=False)
city_perf.to_csv(f"{CLEANED}/city_performance.csv", index=False)
print("Top 10 cities by revenue:\n", city_perf.head(10).round(1).to_string(index=False))
print(f"\nTotal cities with any revenue: {len(city_perf)}")
print(f"Top 10 cities = {city_perf.head(10)['pct_revenue'].sum():.1f}% of total revenue "
      f"(out of {len(city_perf)} cities)")

# ---------------------------------------------------------------
# Restaurant concentration (Lorenz curve + Gini)
# ---------------------------------------------------------------
rest_rev = attributable.groupby("r_id")["revenue"].sum().sort_values(ascending=False)
cum_rev = rest_rev.cumsum() / rest_rev.sum()
cum_rest = np.arange(1, len(rest_rev) + 1) / len(rest_rev)

def gini(values):
    v = np.sort(values.values)
    n = len(v)
    cum = np.cumsum(v)
    return (2 * np.sum((np.arange(1, n + 1)) * v) - (n + 1) * cum[-1]) / (n * cum[-1])

g = gini(rest_rev)
print(f"\nRestaurant revenue Gini coefficient: {g:.3f} "
      f"(near 0 = evenly spread, near 1 = highly concentrated)")
top1pct_share = cum_rev.iloc[int(len(cum_rev) * 0.01)] * 100
print(f"Top 1% of restaurants (by revenue) hold {top1pct_share:.1f}% of restaurant-attributable revenue")

fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(cum_rest * 100, cum_rev.values * 100, color=BLUE, linewidth=2.2, label="Actual (Lorenz curve)")
ax.plot([0, 100], [0, 100], color="#898781", linewidth=1.2, linestyle="--", label="Perfect equality")
ax.set_xlabel("% of restaurants (ranked by revenue)")
ax.set_ylabel("Cumulative % of revenue")
ax.set_title(f"Restaurant Revenue Concentration (Gini = {g:.2f})")
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig(f"{CHARTS}/12_restaurant_revenue_lorenz.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------
# Rating vs. order-volume correlation
# ---------------------------------------------------------------
rated = rest[rest.has_rating == 1].merge(
    attributable.groupby("r_id").agg(orders=("order_id", "count"), revenue=("revenue", "sum")).reset_index(),
    on="r_id", how="left"
)
rated["orders"] = rated["orders"].fillna(0)
rated["revenue"] = rated["revenue"].fillna(0)

pearson_r, pearson_p = stats.pearsonr(rated["rating_numeric"], rated["orders"])
spearman_r, spearman_p = stats.spearmanr(rated["rating_numeric"], rated["orders"])
print(f"\nRating vs. order count — Pearson r = {pearson_r:.4f} (p={pearson_p:.4f}), "
      f"Spearman rho = {spearman_r:.4f} (p={spearman_p:.4f})")
print(f"NOTE: orders-per-restaurant is essentially binary here (0, 1, or rarely 2) — see data audit "
      f"Section 8 — so this correlation measures 'did a rated restaurant receive any order at all', "
      f"not a true volume relationship, and should be read as a scoped/limited test.")

fig, ax = plt.subplots(figsize=(7, 5))
jitter = np.random.default_rng(42).normal(0, 0.03, size=len(rated))
ax.scatter(rated["rating_numeric"], rated["orders"] + jitter, s=8, alpha=0.15, color=BLUE)
ax.set_xlabel("Restaurant rating")
ax.set_ylabel("Orders received (jittered)")
ax.set_title(f"Rating vs. Orders (Pearson r={pearson_r:.3f}, Spearman ρ={spearman_r:.3f})")
fig.tight_layout()
fig.savefig(f"{CHARTS}/13_rating_vs_orders_scatter.png", dpi=150)
plt.close(fig)

# rating vs revenue among restaurants that did receive an order (excludes the structural zeros)
got_order = rated[rated.orders > 0]
pearson_r2, pearson_p2 = stats.pearsonr(got_order["rating_numeric"], got_order["revenue"])
spearman_r2, spearman_p2 = stats.spearmanr(got_order["rating_numeric"], got_order["revenue"])
print(f"\nAmong rated restaurants that received an order ({len(got_order):,}), "
      f"rating vs. that order's value — Pearson r = {pearson_r2:.4f} (p={pearson_p2:.4f}), "
      f"Spearman rho = {spearman_r2:.4f} (p={spearman_p2:.4f})")

with open("../docs/05c_marketplace_analysis_summary.md", "w") as f:
    f.write("# Marketplace Analysis Summary — Cities, Restaurants, Ratings\n\n")
    f.write("Generated by `python/05_marketplace_analysis.py`.\n\n")
    f.write("## Cities\n\n")
    f.write(f"- {len(city_perf)} cities have at least one attributable order. "
            f"The top 10 cities account for **{city_perf.head(10)['pct_revenue'].sum():.1f}%** of total revenue.\n")
    f.write(f"- Tirupati is the single largest city by revenue ({city_perf.iloc[0]['pct_revenue']:.1f}%) "
            f"despite a modest order count, driven by high-value individual orders rather than order volume.\n\n")
    f.write("## Restaurant concentration\n\n")
    f.write(f"- Gini coefficient on restaurant-level revenue: **{g:.3f}** (0 = perfectly even, 1 = a single "
            f"restaurant holds everything) — on its face this looks like strong concentration.\n")
    f.write(f"- But the *source* of that concentration is different from a normal marketplace: since almost "
            f"every restaurant receives exactly 0 or 1 orders (see data audit Section 8), each restaurant's "
            f"\"revenue\" is really just the value of the single order it happened to get, and order values "
            f"are themselves heavily right-skewed (EDA: median ₹519, mean ₹6,636, max ₹1.5M). The Gini is "
            f"measuring **order-value skew spread across restaurants**, not a small set of repeat-business "
            f"\"hero\" restaurants.\n")
    f.write(f"- Two views make this concrete: the very top 50 restaurants (0.03% of all restaurants) hold "
            f"only ~1.2% of revenue — there is no tiny dominant cluster at the extreme top — while the top "
            f"1% (~1,485 restaurants) hold **{top1pct_share:.1f}%**, because there are enough large individual "
            f"orders scattered across many different restaurants to add up. City-level concentration (above) "
            f"is the more meaningful and stable cut for this dataset; restaurant-level \"top performer\" "
            f"language should be read as \"received one high-value order,\" not \"consistently strong.\"\n\n")
    f.write("## Rating vs. order volume\n\n")
    f.write(f"- Pearson r = {pearson_r:.4f} (p={pearson_p:.4f}), Spearman ρ = {spearman_r:.4f} (p={spearman_p:.4f}) "
            f"between rating and order count across all rated restaurants.\n")
    f.write(f"- Both correlations are negligible in magnitude. This is expected given the structural ceiling: "
            f"since almost every restaurant receives 0 or 1 orders, this test is really measuring whether "
            f"higher-rated restaurants were more likely to receive an order at all, not whether they moved "
            f"more volume — and even on that narrower question, rating shows no meaningful relationship "
            f"in this data.\n")
    f.write(f"- **Correlation is not causation**: even if a relationship were found, it would not establish "
            f"that improving a restaurant's rating causes more orders — both could be driven by a third "
            f"factor (e.g., cuisine type, city, price point, tenure on the platform).\n")

print("\nSaved city_performance.csv, Lorenz curve, rating scatter, and summary doc.")
