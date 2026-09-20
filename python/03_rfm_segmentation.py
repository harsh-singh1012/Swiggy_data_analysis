"""
03_rfm_segmentation.py — Customer Analytics: RFM

Builds Recency / Frequency / Monetary at the customer level, scores each
1-5 via data-driven quantiles (qcut on rank to survive heavy ties), and
maps R/F scores to business segments. Saves customer_rfm.csv and a
segment summary + chart.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

CLEANED = "../data/cleaned"
CHARTS = "../eda_charts"

BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "axes.edgecolor": "#898781", "axes.labelcolor": "#0b0b0b", "text.color": "#0b0b0b",
    "xtick.color": "#898781", "ytick.color": "#898781",
    "axes.grid": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
})

fact = pd.read_csv(f"{CLEANED}/fact_orders.csv", parse_dates=["order_date"])

analysis_date = fact["order_date"].max() + pd.Timedelta(days=1)

# monetary uses revenue only (zero-amount orders excluded from spend, per audit)
cust = fact.groupby("user_id").agg(
    recency_days=("order_date", lambda s: (analysis_date - s.max()).days),
    frequency=("order_id", "count"),
    monetary=("revenue", "sum"),
    first_order=("order_date", "min"),
    last_order=("order_date", "max"),
).reset_index()
cust["monetary"] = cust["monetary"].fillna(0)

print(f"Customers scored: {len(cust):,}")
print(cust[["recency_days", "frequency", "monetary"]].describe())

# ---- quantile scoring (1=worst, 5=best), rank-based to handle heavy ties ----
def qscore(series, ascending_is_better):
    # rank() is set up so that the "best" customers always land at rank 1
    # (ascending=True when a LOW raw value is better, e.g. recency_days;
    #  ascending=False when a HIGH raw value is better, e.g. frequency/monetary).
    # qcut then assigns labels in rank order, so the first bin (rank~1, the
    # best customers) must get the HIGHEST score -> labels run 5 down to 1.
    ranks = series.rank(method="first", ascending=ascending_is_better)
    return pd.qcut(ranks, 5, labels=[5, 4, 3, 2, 1]).astype(int)

cust["R_score"] = qscore(cust["recency_days"], ascending_is_better=True)   # low recency_days = better = score 5
cust["F_score"] = qscore(cust["frequency"], ascending_is_better=False)     # high frequency = better = score 5
cust["M_score"] = qscore(cust["monetary"], ascending_is_better=False)      # high monetary = better = score 5
cust["RFM_score"] = cust["R_score"].astype(str) + cust["F_score"].astype(str) + cust["M_score"].astype(str)
cust["RFM_sum"] = cust["R_score"] + cust["F_score"] + cust["M_score"]

print("\nActual bin edges (data-driven, not fixed):")
print("recency_days quintiles:", cust["recency_days"].quantile([0, .2, .4, .6, .8, 1]).round(0).to_dict())
print("frequency quintiles:", cust["frequency"].quantile([0, .2, .4, .6, .8, 1]).to_dict())
print("monetary quintiles:", cust["monetary"].quantile([0, .2, .4, .6, .8, 1]).round(0).to_dict())

# ---- rule-based segmentation on R/F scores (M used to describe, not assign) ----
def segment(row):
    r, f = row["R_score"], row["F_score"]
    if r >= 4 and f >= 4:
        return "Champions"
    if f >= 4 and r >= 2:
        return "Loyal / Active"
    if r >= 4 and f <= 2:
        return "Recent / New"
    if r <= 2 and f >= 3:
        return "At Risk"
    return "Low Engagement"

cust["segment"] = cust.apply(segment, axis=1)

seg_summary = cust.groupby("segment").agg(
    customers=("user_id", "count"),
    avg_recency_days=("recency_days", "mean"),
    avg_frequency=("frequency", "mean"),
    avg_monetary=("monetary", "mean"),
    total_revenue=("monetary", "sum"),
).reset_index()
seg_summary["pct_customers"] = 100 * seg_summary["customers"] / seg_summary["customers"].sum()
seg_summary["pct_revenue"] = 100 * seg_summary["total_revenue"] / seg_summary["total_revenue"].sum()
seg_summary = seg_summary.sort_values("total_revenue", ascending=False)
print("\nSegment summary:\n", seg_summary.round(1).to_string(index=False))

cust.to_csv(f"{CLEANED}/customer_rfm.csv", index=False)
seg_summary.to_csv(f"{CLEANED}/rfm_segment_summary.csv", index=False)

# ---- chart: revenue share vs customer share by segment ----
order = seg_summary["segment"].tolist()
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(order))
w = 0.35
ax.bar(x - w/2, seg_summary.set_index("segment").loc[order, "pct_customers"], width=w, label="% of customers", color=BLUE)
ax.bar(x + w/2, seg_summary.set_index("segment").loc[order, "pct_revenue"], width=w, label="% of revenue", color=ORANGE)
ax.set_xticks(x)
ax.set_xticklabels(order, rotation=15, ha="right")
ax.set_ylabel("Percent")
ax.set_title("RFM Segments: Share of Customers vs. Share of Revenue")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(f"{CHARTS}/09_rfm_segments_revenue_share.png", dpi=150)
plt.close(fig)

with open("../docs/05a_rfm_summary.md", "w") as f:
    f.write("# RFM Segmentation Summary\n\nGenerated by `python/03_rfm_segmentation.py`.\n\n")
    f.write(f"Analysis date used for recency: {analysis_date.date()} (day after the last order in the data).\n\n")
    f.write("Scoring is quintile-based (`pd.qcut` on rank, 1=worst, 5=best) computed from the actual "
            "distribution of each metric — not fixed business thresholds. Segments are assigned from "
            "the R and F scores (Monetary describes segment value rather than driving assignment, "
            "consistent with 'total revenue alone doesn't explain customer quality').\n\n")
    f.write("## Segment definitions used\n\n")
    f.write("- **Champions**: R score >= 4 and F score >= 4 — ordered recently and often.\n")
    f.write("- **Loyal / Active**: F score >= 4 (regardless of recency) — high lifetime order count.\n")
    f.write("- **Recent / New**: R score >= 4 and F score <= 2 — recently acquired, not yet frequent.\n")
    f.write("- **At Risk**: R score <= 2 and F score >= 3 — used to order regularly, gone quiet.\n")
    f.write("- **Low Engagement**: everyone else — low recency and low frequency.\n\n")
    f.write("## Results\n\n")
    f.write(seg_summary.round(1).to_markdown(index=False))
    f.write("\n")

print("\nSaved customer_rfm.csv, rfm_segment_summary.csv, chart, and summary doc.")
