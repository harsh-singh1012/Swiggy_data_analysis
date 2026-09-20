# Business Insights & Recommendations

Executive summary first, then each major finding in **Evidence → Insight → Implication → Action** form, per the brief's framework. Every number here is traceable to a script and output file listed alongside it.

## Executive summary

Revenue and order volume are volatile month to month rather than steadily growing, and both show a broad decline through 2019 into 2020 that accelerates in the final months of the data. That decline is a **demand/order-frequency problem, not a pricing or basket-size problem** — statistical testing found no drop in average order value over the same window. Revenue is heavily concentrated by geography (a handful of cities) and, more subtly, by order-value skew rather than by any small set of "hero" restaurants, because this dataset shows essentially one order per restaurant. On the customer side, a small "Champions" segment (22% of customers) generates over a third of revenue, repeat customers are exactly as valuable per order as one-time customers (they just order more often), and month-1 retention is low and flat (~4-5%) rather than following the usual sharp early drop-off — meaning the loyalty problem is structural and marketplace-wide, not a first-30-days onboarding gap.

---

## 1. Revenue is driven by a small set of cities, not a broad base

**Evidence**: 821 cities have at least one attributable order; the top 10 account for 21.0% of total revenue, and the single largest city (Tirupati) alone contributes 4.4% from just 243 orders — a far higher per-order value than any comparable-revenue city (`docs/04_eda_summary.md`, `docs/05c_marketplace_analysis_summary.md`).

**Insight**: Revenue concentration is real, but it's driven by a mix of order volume (Bangalore/Pune metro areas) and a few outlier high-value cities (Tirupati, Sultanpur, Raipur) rather than one pattern.

**Implication**: Treating all 821 cities the same in marketing/ops spend wastes budget; treating the top 10 as a monolith also misses that some are volume-driven and others are value-driven, which call for different playbooks (retention/frequency campaigns vs. premium-order support).

**Action**: Split city investment into two tracks — volume markets (Electronic City/Bangalore, Baner/Pune, Malviya Nagar/Delhi: grow order frequency) and value markets (Tirupati, Sultanpur: protect and understand what drives the unusually high per-order spend before assuming it's repeatable elsewhere).

---

## 2. "Top restaurant" rankings are misleading without the ~1-order-per-restaurant context

**Evidence**: Mean orders per restaurant = 1.001, max = 2, across 148,540 restaurants (`docs/01_data_audit.md` §8). Restaurant revenue concentration looks severe by Gini (0.86, top 1% = 34% of revenue) but the very top 50 restaurants hold only 1.2% of revenue (`docs/05c_marketplace_analysis_summary.md`).

**Insight**: There is no cluster of consistently high-performing restaurants in this data — "top restaurant by revenue" just identifies whichever restaurant happened to receive one large order. The apparent inequality is order-value skew, not repeat-business concentration.

**Implication**: Any restaurant-partner program built on "reward our top restaurants" using this ranking would be rewarding a one-time lucky order, not a proven performer — a real risk if this framing reached a partnerships team unfiltered.

**Action**: Relabel restaurant leaderboards as "largest single order value" everywhere they appear (including in the Power BI dashboard, per the build guide), and build any restaurant-performance program on order *count* or a longer observation window once more repeat-order data exists, not on this single-order dataset.

---

## 3. A fifth of customers generate more than a third of revenue — and they're not who you'd guess

**Evidence**: RFM segmentation (`docs/05a_rfm_summary.md`) — Champions are 22.0% of ordering customers and 35.1% of revenue; Low Engagement is the largest group by headcount (42.5%) but a smaller share of revenue (27.3%); Loyal/Active (15.3% of customers) delivers 22.1% of revenue.

**Insight**: Revenue quality tracks recency and frequency together, not either alone — Champions combine both, which is why total revenue alone (as the brief anticipated) would have hidden this structure.

**Implication**: A blanket "reward high spenders" program would miss Champions who aren't necessarily the single biggest spenders, and a blanket re-engagement push aimed at all "inactive" customers would spread budget too thin across the 42.5% Low Engagement group, most of whom may never have been high-value even when active.

**Action**: Prioritize retention spend on Champions (protect the 35% of revenue concentrated there) and Loyal/Active (grow toward Champions), and treat Low Engagement as a lower-cost, lower-touch channel (email/push) rather than the same investment level as Champions.

---

## 4. Repeat customers are not bigger spenders per order — only more frequent ones

**Evidence**: Mann-Whitney U test on per-order value, repeat vs. one-time customers: median ₹519 vs. ₹523, p = 0.793, effect size ≈ 0 (`docs/05_statistical_analysis.md`, Test 1).

**Insight**: A repeat customer's extra lifetime value comes entirely from ordering more often, not from placing larger orders.

**Implication**: Retention tactics and basket-size tactics are two separate levers here — growing frequency won't naturally grow order size, and vice versa, so a single campaign shouldn't be expected to move both.

**Action**: Run retention (frequency) and upsell (basket-size) as separately measured initiatives with separate success metrics, rather than assuming a win on one implies a win on the other.

---

## 5. Retention is a marketplace-wide problem, not a first-month onboarding gap

**Evidence**: Cohort retention analysis (`docs/05b_cohort_retention_summary.md`) shows month-1 retention of only 4.6%, and the retention curve stays roughly flat (4-5%) through at least 12 months rather than showing the typical steep early decay.

**Insight**: Because retention doesn't decay sharply after month 1 — it's uniformly low from the start — the problem isn't "we lose people in their first 30 days," it's that most customers simply don't have an ongoing reason to reorder at any point in their lifecycle.

**Implication**: A classic "improve onboarding" fix targets the wrong window; the opportunity is a sustained engagement mechanism (loyalty program, recurring incentives) rather than a first-order follow-up email.

**Action**: Pilot an ongoing engagement mechanism (e.g., a punch-card style reward at order 2 and 3, not just order 1) and measure whether it changes the flat retention curve shape, not just month-1 retention in isolation.

---

## 6. The recent revenue decline is a demand/frequency problem, not a spending problem

**Evidence**: Revenue decomposition (`docs/06_revenue_decomposition_rca.md`) comparing Jan-Feb 2020 (baseline) to Mar-Jun 2020 (decline window): orders/day fell from 164.0 to 146.9 (-10.4%) while AOV held essentially flat (₹6,614 → ₹6,673). The orders-effect alone more than explains the full revenue/day decline (-9.2% overall), with AOV contributing a small *positive* offset. Both underlying statistical tests were borderline (p ≈ 0.05-0.07), reported honestly as directional rather than conclusive.

**Insight**: Whatever caused the early-2020 softness, it reduced how often people ordered, not how much they spent per order when they did.

**Implication**: Any response built around discounting or "increase basket size" promotions is solving the wrong problem — it targets AOV, which wasn't the issue, while ignoring order frequency, which was.

**Action**: Prioritize order-frequency recovery levers (reactivation pushes, delivery-fee waivers on a 2nd/3rd order) over price promotions, and investigate the cities and segments that pulled back the most (Koramangala/Bangalore, N A D/Vizag, and disproportionately the Low Engagement and Recent/New segments — Champions were comparatively resilient at -9.4% vs. -13.1% and -10.8%) before assuming the cause is uniform across the marketplace.

---

## 7. Rating does not predict order volume in this data — don't over-invest in rating-chasing

**Evidence**: Pearson r = -0.0095, Spearman ρ = -0.0100 between restaurant rating and order count (both p < 0.05 but the effect size is negligible); only 41.4% of restaurants have any numeric rating at all (`docs/05c_marketplace_analysis_summary.md`).

**Insight**: Given the ~1-order-per-restaurant ceiling, this test is really asking "did higher-rated restaurants get an order at all" — and even on that narrow question, rating shows no meaningful pull.

**Implication**: A strategy that assumes "improve restaurant ratings → orders will follow" has no support in this data, and correlation here wouldn't imply causation even if it existed.

**Action**: Don't fund a rating-improvement initiative on the promise of an order-volume lift; if ratings matter to the business for other reasons (customer trust, platform quality perception), justify it on those grounds instead, and revisit this test once the dataset has genuine repeat-order volume per restaurant to test against.

---

## 8. Menu/assortment analysis in this project is a partial view — treat it as indicative

**Evidence**: The menu extract contains exactly 1,048,575 rows — one short of Excel's row limit — covering only 12,117 of 148,540 restaurants (8.2%), and has no item-level link to actual orders (`docs/01_data_audit.md` §6).

**Insight**: Any catalog-level statement ("average menu price is ₹X," "Y% of items are Veg") describes only the restaurants that happen to be in this truncated extract, and nothing in the data connects a specific order to a specific dish.

**Implication**: Presenting menu-derived numbers as marketplace-wide facts, or claiming a "best-selling item," would overstate what the data supports.

**Action**: Label every menu-derived chart or number as "based on the available menu extract (8% of restaurants)" and pursue a complete menu pull with an order-to-item link before making assortment decisions off this data.
