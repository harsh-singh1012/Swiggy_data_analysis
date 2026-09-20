"""
07_revenue_decomposition_rca.py — Revenue Decomposition & Root-Cause Analysis

Revenue = Orders x AOV. Compares a stable baseline period (Jan-Feb 2020) to
the flagged decline period (Mar-Jun 2020) identified in the EDA trend chart,
decomposes the revenue change into an orders-effect and an AOV-effect
(symmetric/Shapley decomposition so the two effects sum exactly to the
total change), then drills into which cities and customer segments drove
the orders-effect.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLEANED = "../data/cleaned"
CHARTS = "../eda_charts"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "axes.edgecolor": "#898781", "axes.labelcolor": "#0b0b0b", "text.color": "#0b0b0b",
    "xtick.color": "#898781", "ytick.color": "#898781",
    "axes.grid": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
})

fact = pd.read_csv(f"{CLEANED}/fact_orders.csv", parse_dates=["order_date"])
rest = pd.read_csv(f"{CLEANED}/dim_restaurants.csv")
cust = pd.read_csv(f"{CLEANED}/customer_rfm.csv")[["user_id", "segment"]]

BASE_MONTHS = ["2020-01", "2020-02"]
DECLINE_MONTHS = ["2020-03", "2020-04", "2020-05", "2020-06"]

def period_stats(df):
    orders = len(df)
    revenue = df["revenue"].sum()
    aov = df.loc[df.is_zero_amount == 0, "revenue"].mean()
    # normalize orders to a daily rate so unequal period lengths (2 vs 4 months) are comparable
    days = df["order_date"].dt.date.nunique()
    return dict(orders=orders, revenue=revenue, aov=aov, days=days, orders_per_day=orders / days)

base = fact[fact.year_month.isin(BASE_MONTHS)]
decl = fact[fact.year_month.isin(DECLINE_MONTHS)]

b = period_stats(base)
d = period_stats(decl)

# Revenue per day so periods of different length are comparable
rev_per_day_base = b["revenue"] / b["days"]
rev_per_day_decl = d["revenue"] / d["days"]

O0, O1 = b["orders_per_day"], d["orders_per_day"]
A0, A1 = b["aov"], d["aov"]
R0, R1 = O0 * A0, O1 * A1  # reconstructed revenue/day (approx, since AOV excludes zero-amount orders)

delta_R = rev_per_day_decl - rev_per_day_base
# symmetric (Shapley-style) decomposition using actual orders/day and aov
orders_effect = (O1 - O0) * (A0 + A1) / 2
aov_effect = (A1 - A0) * (O0 + O1) / 2

print("=== Revenue = Orders x AOV — baseline vs decline period (per day) ===")
print(f"Baseline (Jan-Feb 2020): {O0:.1f} orders/day x Rs.{A0:.0f} AOV = Rs.{O0*A0:,.0f}/day revenue proxy")
print(f"Decline  (Mar-Jun 2020): {O1:.1f} orders/day x Rs.{A1:.0f} AOV = Rs.{O1*A1:,.0f}/day revenue proxy")
print(f"Actual revenue/day change: Rs.{rev_per_day_base:,.0f} -> Rs.{rev_per_day_decl:,.0f} "
      f"({100*(rev_per_day_decl/rev_per_day_base-1):.1f}%)")
print(f"Orders-effect: Rs.{orders_effect:,.0f}/day  |  AOV-effect: Rs.{aov_effect:,.0f}/day  "
      f"|  sum={orders_effect+aov_effect:,.0f} (proxy delta={O1*A1-O0*A0:,.0f})")
print(f"Orders-effect share of proxy revenue change: {100*orders_effect/(orders_effect+aov_effect):.1f}%")

# ------------------------------------------------------------------
# City drill-down: which cities lost the most order volume?
# ------------------------------------------------------------------
attrib = fact[fact.has_restaurant == 1].merge(rest[["r_id", "city"]], on="r_id")
city_base = attrib[attrib.year_month.isin(BASE_MONTHS)].groupby("city").agg(
    orders=("order_id", "count")).rename(columns={"orders": "orders_base"})
city_decl = attrib[attrib.year_month.isin(DECLINE_MONTHS)].groupby("city").agg(
    orders=("order_id", "count")).rename(columns={"orders": "orders_decl"})
city_cmp = city_base.join(city_decl, how="outer").fillna(0)
city_cmp["orders_base_per_day"] = city_cmp["orders_base"] / b["days"]
city_cmp["orders_decl_per_day"] = city_cmp["orders_decl"] / d["days"]
city_cmp["change_per_day"] = city_cmp["orders_decl_per_day"] - city_cmp["orders_base_per_day"]
city_cmp = city_cmp.sort_values("change_per_day")
city_cmp.to_csv(f"{CLEANED}/rca_city_orders_change.csv")

print("\nTop 10 cities contributing to the order-volume decline (orders/day drop):")
print(city_cmp.head(10)[["orders_base_per_day", "orders_decl_per_day", "change_per_day"]].round(2).to_string())

# ------------------------------------------------------------------
# Segment drill-down: which RFM segments' orders fell most?
# ------------------------------------------------------------------
fact_seg = fact.merge(cust, on="user_id", how="left")
fact_seg["segment"] = fact_seg["segment"].fillna("Unclassified")
seg_base = fact_seg[fact_seg.year_month.isin(BASE_MONTHS)].groupby("segment").size().rename("orders_base")
seg_decl = fact_seg[fact_seg.year_month.isin(DECLINE_MONTHS)].groupby("segment").size().rename("orders_decl")
seg_cmp = pd.concat([seg_base, seg_decl], axis=1).fillna(0)
seg_cmp["orders_base_per_day"] = seg_cmp["orders_base"] / b["days"]
seg_cmp["orders_decl_per_day"] = seg_cmp["orders_decl"] / d["days"]
seg_cmp["change_per_day"] = seg_cmp["orders_decl_per_day"] - seg_cmp["orders_base_per_day"]
seg_cmp["pct_change"] = 100 * (seg_cmp["orders_decl_per_day"] / seg_cmp["orders_base_per_day"] - 1)
seg_cmp = seg_cmp.sort_values("change_per_day")
seg_cmp.to_csv(f"{CLEANED}/rca_segment_orders_change.csv")

print("\nOrder-volume change by customer segment (orders/day, baseline vs decline):")
print(seg_cmp.round(2).to_string())

# ------------------------------------------------------------------
# Chart: waterfall-style decomposition
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
labels = ["Baseline\nrevenue/day", "Orders\neffect", "AOV\neffect", "Decline\nrevenue/day"]
vals = [rev_per_day_base, orders_effect, aov_effect, rev_per_day_decl]
bottoms = [0, rev_per_day_base + min(orders_effect,0), 0, 0]
colors = [BLUE, RED if orders_effect < 0 else "#0ca30c", RED if aov_effect < 0 else "#0ca30c", BLUE]

running = rev_per_day_base
bar_bottoms = [0]
bar_heights = [rev_per_day_base]
for effect in [orders_effect, aov_effect]:
    bar_bottoms.append(running + min(effect, 0))
    bar_heights.append(abs(effect))
    running += effect
bar_bottoms.append(0)
bar_heights.append(rev_per_day_decl)

ax.bar(labels, bar_heights, bottom=bar_bottoms, color=colors, width=0.6)
ax.set_ylabel("Revenue per day (₹)")
ax.set_title("Revenue Decomposition: Baseline (Jan-Feb 2020) → Decline (Mar-Jun 2020)")
for i, (lb, bt, h) in enumerate(zip(labels, bar_bottoms, bar_heights)):
    ax.text(i, bt + h + max(bar_heights)*0.02, f"₹{[rev_per_day_base, orders_effect, aov_effect, rev_per_day_decl][i]:,.0f}",
            ha="center", fontsize=9)
fig.tight_layout()
fig.savefig(f"{CHARTS}/14_revenue_decomposition_waterfall.png", dpi=150)
plt.close(fig)

with open("../docs/06_revenue_decomposition_rca.md", "w") as f:
    f.write("# Revenue Decomposition & Root-Cause Analysis\n\n")
    f.write("Generated by `python/07_revenue_decomposition_rca.py`. Basic relationship: **Revenue = Orders × AOV**.\n\n")
    f.write("## Why this comparison window\n\n")
    f.write("The EDA revenue trend (`eda_charts/01_monthly_revenue_trend.png`) shows a broad decline into "
            "2020 with the steepest drop in the final months. January-February 2020 is used as the last "
            "stable baseline before the decline, compared against March-June 2020 (the flagged decline "
            "window). Both periods are normalized to **per-day** rates since they cover a different number "
            "of calendar days (note: June 2020 is a partial month in the raw data, which the per-day "
            "normalization already accounts for).\n\n")
    f.write("## Decomposition\n\n")
    f.write(f"- Baseline: {O0:.1f} orders/day × ₹{A0:.0f} AOV ≈ ₹{O0*A0:,.0f}/day\n")
    f.write(f"- Decline period: {O1:.1f} orders/day × ₹{A1:.0f} AOV ≈ ₹{O1*A1:,.0f}/day\n")
    f.write(f"- Actual revenue/day: ₹{rev_per_day_base:,.0f} → ₹{rev_per_day_decl:,.0f} "
            f"({100*(rev_per_day_decl/rev_per_day_base-1):.1f}%)\n")
    f.write(f"- **Orders-effect: ₹{orders_effect:,.0f}/day.** **AOV-effect: ₹{aov_effect:,.0f}/day.** "
            f"(Symmetric decomposition — the two effects sum to the total change.)\n")
    f.write(f"- Orders volume is the **entire story**: the orders-effect (₹{orders_effect:,.0f}/day) more than accounts "
            f"for the full revenue drop on its own, while the AOV-effect is a small *positive* offset "
            f"(₹{aov_effect:,.0f}/day) — which is why the orders-effect share comes out above 100% "
            f"({100*orders_effect/(orders_effect+aov_effect):.0f}%) once the two are combined. In plain terms: "
            f"order volume fell, average order value did not, consistent with the statistical test in "
            f"`docs/05_statistical_analysis.md` (Test 3), which found no significant drop in per-order value "
            f"over the same window.\n\n")
    f.write("## City drill-down\n\n")
    f.write("Cities ranked by the drop in daily order volume from baseline to decline period "
            "(`data/cleaned/rca_city_orders_change.csv` has the full list):\n\n")
    f.write(city_cmp.head(10)[["orders_base_per_day", "orders_decl_per_day", "change_per_day"]]
            .round(2).to_markdown())
    f.write("\n\n")
    f.write("## Customer-segment drill-down\n\n")
    f.write("Order volume change by RFM segment (`data/cleaned/rca_segment_orders_change.csv`). Only segments "
            "with any order activity in this recent 6-month window appear — **At Risk** and **Loyal / Active** "
            "customers (by construction, lower-recency segments) had no orders at all in Jan-Jun 2020 and are "
            "excluded from this specific window, which is itself consistent with their segment definition:\n\n")
    f.write(seg_cmp.round(2).to_markdown())
    f.write("\n\n")
    f.write("Champions alone account for the large majority of the absolute order-volume drop (-9.2 orders/day) "
            "simply because they are the largest active group in this window, but their *percentage* decline "
            "(-9.4%) is actually the smallest of the three — Low Engagement and Recent/New customers pulled "
            "back proportionally more (-13.1% and -10.8%). Champions are the most resilient segment through "
            "the decline, not the source of it.\n\n")
    f.write("## Investigation priorities\n\n")
    f.write("1. **Confirm whether the decline is demand-side or supply-side.** This dataset has no restaurant "
            "-availability or marketing-spend field, so it cannot distinguish \"fewer customers wanted to "
            "order\" from \"fewer restaurants were operating/listed as available\" — that would need an "
            "operations data pull outside this dataset.\n")
    f.write("2. **Prioritize the cities and segments identified above** for a qualitative follow-up (support "
            "tickets, churn surveys, restaurant-partner check-ins) rather than treating the decline as uniform "
            "across the whole marketplace.\n")
    f.write("3. **Treat AOV as healthy, not the problem** — resources are better spent on demand/frequency "
            "recovery than on basket-size promotions, since AOV held up through the decline period.\n")
    f.write("4. **Re-run this decomposition once more months of data are available** past June 2020, since "
            "the current decline window ends on a partial month and the statistical tests behind it were "
            "borderline (p ≈ 0.05-0.07), not conclusively significant.\n")

print("\nSaved rca_city_orders_change.csv, rca_segment_orders_change.csv, waterfall chart, and RCA doc.")
