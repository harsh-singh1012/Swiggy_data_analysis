# Statistical Analysis

Four tests, run in `python/06_statistical_analysis.py` against the cleaned data. Each follows the same structure: business question, hypothesis, test choice and why, result, effect size, business interpretation, and limitation. Non-parametric tests (Mann-Whitney U, Kruskal-Wallis) are used wherever the underlying metric is order value, because order value is heavily right-skewed (EDA: median ₹519 vs. mean ₹6,636) — a t-test's equal-variance/normality assumptions would be a poor fit, and a rank-based test is the honest choice.

---

## Test 1 — Do repeat customers spend more per order than one-time customers?

**Business question**: Repeat customers already generate more lifetime revenue by definition (more orders) — but is each individual order from a repeat customer also worth more, or is their extra value purely coming from ordering more often?

**Hypothesis**: H0: the distribution of per-order value is the same for repeat and one-time customers. H1: they differ.

**Test**: Mann-Whitney U (two-sided), chosen over a t-test because order value is heavily right-skewed in both groups.

**Result**: Repeat-customer orders: median ₹519 (n=115,554). One-time-customer orders: median ₹523 (n=33,115). U = 1,911,477,424, **p = 0.793**.

**Effect size**: Rank-biserial r = 0.0009 — essentially zero.

**Business interpretation**: There is no evidence that repeat customers spend more per order than one-time customers. A repeat customer's higher lifetime value comes entirely from ordering more often, not from placing bigger orders. This means retention initiatives (turning one-time customers into repeat ones) are a volume/frequency lever, not a basket-size lever — pairing retention pushes with upsell/cross-sell tactics would need a separate mechanism, since order size doesn't naturally grow with tenure in this data.

**Limitation**: This is a single snapshot comparison across the full ~33-month window, not a within-customer before/after comparison, so it cannot rule out that an individual customer's own order size changes over their lifetime — it only says the two population distributions don't differ.

---

## Test 2 — Is repeat-purchase behavior associated with customer gender?

**Business question**: If repeat behavior skewed strongly by gender, that would change how retention campaigns should be targeted and messaged.

**Hypothesis**: H0: gender and repeat-purchase status (ordered more than once vs. exactly once) are independent. H1: they are associated.

**Test**: Chi-square test of independence on a 2×2 contingency table (gender × repeat/one-time).

**Result**: Female repeat rate 57.2% (n=33,347), Male repeat rate 57.0% (n=44,582). χ² = 0.562, dof = 1, **p = 0.453**.

**Effect size**: Cramér's V = 0.0027 — negligible association.

**Business interpretation**: Repeat-purchase behavior is essentially identical across the two recorded gender categories. There is no basis in this data for gender-differentiated retention strategy — the segments worth targeting differently are the RFM segments (Section "Customer Analytics"), not gender.

**Limitation**: The dataset's gender field only has two categories recorded; any other categories or non-disclosure aren't represented, and this test says nothing about age, occupation, or marital status, which were not tested here.

---

## Test 3 — Did the revenue decline in early-2020 come from fewer orders, smaller orders, or both?

**Business question**: The EDA revenue trend chart shows a broad decline into 2020 with a steep final drop. Before attributing that to any specific cause, the first diagnostic question is mechanical: did customers place fewer orders, place smaller orders, or both, in March–June 2020 versus the more stable January–February 2020?

**Hypothesis**: H0 (value): the distribution of per-order value is the same Jan–Feb 2020 vs. Mar–Jun 2020. H0 (volume): daily order counts come from the same distribution in both periods.

**Test**: Mann-Whitney U on order value; Mann-Whitney U on daily order counts (volume).

**Result**:
- Order value: Jan–Feb median ₹569 (n=7,951) vs. Mar–Jun median ₹625 (n=13,434). **p = 0.065** (not significant at 0.05) — and directionally *higher*, not lower, in the later period.
- Daily order volume: Jan–Feb mean 164.0 orders/day vs. Mar–Jun mean 146.9 orders/day. **p = 0.055** (borderline).

**Effect size**: Order-value rank-biserial r = 0.015 (negligible). Volume difference is ~10% lower in the later period (descriptive; the rank test is borderline rather than conclusive).

**Business interpretation**: The signal points toward **order volume softening**, not customers spending less per order — if anything, per-order value held up or ticked up slightly. That reframes the revenue-decomposition story in the RCA section: the 2020 revenue softness is best investigated as a demand/order-frequency problem (fewer people ordering, or ordering less often), not a basket-size or discounting problem.

**Limitation**: Neither result clears the conventional p < 0.05 bar — both are borderline. This is reported honestly rather than rounded up to "significant," and the RCA section treats this as a directional signal worth investigating further (e.g., with a longer post-period once more months are available), not a proven cause.

---

## Test 4 — Does order value differ by food type (Veg / Non-Veg / Other)?

**Business question**: If Non-Veg or "Other" orders were reliably higher-value, that would inform cuisine-mix and promotional decisions.

**Hypothesis**: H0: the distribution of order value is the same across Veg, Non-Veg, and Other. H1: at least one differs.

**Test**: Kruskal-Wallis H-test (three independent groups, non-normal metric).

**Result**: Median order value — Non-Veg ₹514, Veg ₹519, Other ₹528. H = 3.570, dof = 2, **p = 0.168**.

**Effect size**: Epsilon-squared = 0.00001 — effectively zero.

**Business interpretation**: Food type has no meaningful relationship with order value in this data. There is no statistical basis for treating Veg/Non-Veg/Other as a value driver — order value is driven by other factors (see the heavy right-skew in the EDA, which looks more like occasional large basket/bulk orders than a food-type effect).

**Limitation**: Recall from the data audit that the Veg/Non-Veg/Other tag is joined to orders **positionally** (no shared key exists between `orders_1` and `orders_Type`) — if that positional alignment were ever wrong, this result would be testing a meaningless pairing. It is reported under that stated assumption.

---

## What these tests add up to

Three of four tests found no meaningful effect, and the fourth was borderline. That is a legitimate, useful result: it rules out several plausible explanations (repeat status, gender, food type) as drivers of order value, and it points the revenue-decline investigation toward **order frequency/volume**, not basket size — which is exactly the kind of statistical grounding the root-cause analysis (next section) needs before drilling into city- and segment-level detail.
