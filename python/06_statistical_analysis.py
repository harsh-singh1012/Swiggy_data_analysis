"""
06_statistical_analysis.py — Statistical Analysis

Four tests, each tied to a specific business question, each reported with:
business question -> hypothesis -> test -> result -> effect size ->
business interpretation -> limitation. Full write-up in
docs/05_statistical_analysis.md; this script prints the numbers behind it.
"""
import pandas as pd
import numpy as np
from scipy import stats

CLEANED = "../data/cleaned"

fact = pd.read_csv(f"{CLEANED}/fact_orders.csv", parse_dates=["order_date"])
users = pd.read_csv(f"{CLEANED}/dim_users.csv")
cust = pd.read_csv(f"{CLEANED}/customer_rfm.csv")

valid = fact[fact.is_zero_amount == 0].copy()

results = {}

# ---------------------------------------------------------------
# TEST 1 — Repeat customers vs one-time customers: order value
# ---------------------------------------------------------------
freq = fact.groupby("user_id").size()
repeat_users = freq[freq > 1].index
onetime_users = freq[freq == 1].index

repeat_amt = valid[valid.user_id.isin(repeat_users)]["amount"]
onetime_amt = valid[valid.user_id.isin(onetime_users)]["amount"]

u_stat, p1 = stats.mannwhitneyu(repeat_amt, onetime_amt, alternative="two-sided")
n1, n2 = len(repeat_amt), len(onetime_amt)
rank_biserial = 1 - (2 * u_stat) / (n1 * n2)

print("=== TEST 1: Repeat vs one-time customers — per-order value ===")
print(f"repeat median={repeat_amt.median():.0f} mean={repeat_amt.mean():.0f} n={n1}")
print(f"one-time median={onetime_amt.median():.0f} mean={onetime_amt.mean():.0f} n={n2}")
print(f"Mann-Whitney U={u_stat:.0f}, p={p1:.6g}, rank-biserial r={rank_biserial:.4f}")
results["test1"] = dict(median_repeat=repeat_amt.median(), median_onetime=onetime_amt.median(),
                         p=p1, effect=rank_biserial, n1=n1, n2=n2)

# ---------------------------------------------------------------
# TEST 2 — Gender vs repeat-purchase status (chi-square)
# ---------------------------------------------------------------
cust_gender = cust.merge(users[["user_id", "gender"]], on="user_id")
cust_gender["is_repeat"] = cust_gender["frequency"] > 1
ct = pd.crosstab(cust_gender["gender"], cust_gender["is_repeat"])
chi2, p2, dof, expected = stats.chi2_contingency(ct)
n = ct.values.sum()
cramers_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))

print("\n=== TEST 2: Gender vs repeat-purchase status ===")
print(ct)
print(f"chi2={chi2:.3f}, dof={dof}, p={p2:.6g}, Cramer's V={cramers_v:.4f}")
repeat_rate_by_gender = cust_gender.groupby("gender")["is_repeat"].mean() * 100
print(repeat_rate_by_gender.round(2))
results["test2"] = dict(chi2=chi2, p=p2, cramers_v=cramers_v, rates=repeat_rate_by_gender.to_dict())

# ---------------------------------------------------------------
# TEST 3 — AOV before vs during the flagged decline period
# (Jan-Feb 2020 "normal" vs Mar-Jun 2020, the period that showed the
#  steep drop in the EDA revenue trend chart)
# ---------------------------------------------------------------
valid["year_month"] = pd.to_datetime(valid["order_date"]).dt.to_period("M").astype(str)
before = valid[valid.year_month.isin(["2020-01", "2020-02"])]["amount"]
during = valid[valid.year_month.isin(["2020-03", "2020-04", "2020-05", "2020-06"])]["amount"]

u3, p3 = stats.mannwhitneyu(before, during, alternative="two-sided")
n1b, n2b = len(before), len(during)
rb3 = 1 - (2 * u3) / (n1b * n2b)

print("\n=== TEST 3: AOV — Jan/Feb 2020 vs Mar-Jun 2020 (flagged decline period) ===")
print(f"before median={before.median():.0f} mean={before.mean():.0f} n={n1b}")
print(f"during median={during.median():.0f} mean={during.mean():.0f} n={n2b}")
print(f"Mann-Whitney U={u3:.0f}, p={p3:.6g}, rank-biserial r={rb3:.4f}")
results["test3"] = dict(median_before=before.median(), median_during=during.median(), p=p3, effect=rb3)

# also test order VOLUME (count/day) difference to separate AOV effect from volume effect
vol_before = fact[fact.year_month.isin(["2020-01", "2020-02"])].groupby(
    pd.to_datetime(fact.loc[fact.year_month.isin(["2020-01","2020-02"]),"order_date"]).dt.date
).size()
vol_during = fact[fact.year_month.isin(["2020-03","2020-04","2020-05","2020-06"])].groupby(
    pd.to_datetime(fact.loc[fact.year_month.isin(["2020-03","2020-04","2020-05","2020-06"]),"order_date"]).dt.date
).size()
u3b, p3b = stats.mannwhitneyu(vol_before, vol_during, alternative="two-sided")
print(f"Daily order volume — before mean/day={vol_before.mean():.1f}, during mean/day={vol_during.mean():.1f}, "
      f"Mann-Whitney p={p3b:.6g}")
results["test3b"] = dict(vol_before=vol_before.mean(), vol_during=vol_during.mean(), p=p3b)

# ---------------------------------------------------------------
# TEST 4 — Order type (Veg/Non-Veg/Other) vs order value (Kruskal-Wallis)
# ---------------------------------------------------------------
groups = [valid.loc[valid.order_type == t, "amount"] for t in valid.order_type.unique()]
h_stat, p4 = stats.kruskal(*groups)
n_total = len(valid)
eps_sq = (h_stat - len(groups) + 1) / (n_total - len(groups))  # epsilon-squared effect size

print("\n=== TEST 4: Order type vs order value (Kruskal-Wallis) ===")
print(valid.groupby("order_type")["amount"].median())
print(f"H={h_stat:.3f}, p={p4:.6g}, epsilon-squared={eps_sq:.5f}")
results["test4"] = dict(medians=valid.groupby("order_type")["amount"].median().to_dict(), p=p4, effect=eps_sq)

import json
with open(f"{CLEANED}/statistical_test_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\nSaved statistical_test_results.json")
