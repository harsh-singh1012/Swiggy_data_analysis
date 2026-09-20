# SQL Analytical Layer — Summary

All queries live in `sql/01_revenue.sql` through `sql/04_time_analysis.sql`, run against a local SQLite database (`sql/swiggy.db`) built from the cleaned CSVs by `sql/00_build_database.py`. Every number below is a real query result (see `sql/results/*.csv`), not illustrative.

## Revenue (`01_revenue.sql`)
- Monthly revenue ranges roughly ₹26.3M–₹42.5M across the 33 months in the data (Oct 2017 – Jun 2020), with AOV swinging between ~₹6,200 and ~₹8,100 month to month — there is no smooth trend, it moves up and down every few months.
- City revenue is **highly concentrated**: Tirupati alone accounts for 4.4% of total attributable revenue from just 243 orders — far more per-order value than the next cities (Electronic City/Bangalore, Baner/Pune, Raipur), which get to similar revenue with 2–4x more orders.
- Top-25 restaurants by revenue are each driven by a **single order** (see Section 8 of the data audit) — this list identifies the largest individual order values, not repeat-business winners.

## Customers (`02_customers.sql`)
- Of 100,000 registered users, 77,929 (78%) ever placed an order.
- Of those ordering customers, 44,472 ordered more than once — a **57.1% repeat rate** among active customers.
- Order-frequency distribution is a fast-decaying curve: 33,457 customers ordered exactly once, dropping to 25,455 at 2 orders, 12,505 at 3, and under 100 customers place 7+ orders — most of the customer base is light/occasional, and heavy repeaters are rare.

## Marketplace (`03_marketplace.sql`)
- `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()` produce identical rankings for city revenue in this data because no two cities tie on revenue — included to demonstrate the three window functions side by side even where the distinction doesn't bite.
- A running-total window function over restaurants ranked by revenue shows the very top 50 restaurants (0.03% of all restaurants) account for only ~1.2% of total revenue — there is no tiny dominant cluster at the extreme top. Zooming out, the Python analysis (`docs/05c_marketplace_analysis_summary.md`) finds the top 1% of restaurants hold 34% of revenue and an overall Gini of 0.86 — but this reflects the skew of individual order values landing on a ~1-order-per-restaurant dataset, not repeat "hero" restaurants. **City-level concentration is the more stable, meaningful cut** for this dataset (see above).
- A restaurant-level rating/order-volume extract (61,441 rated restaurants) was produced for the Pearson/Spearman correlation test carried out in Python (see `docs/05_statistical_analysis.md`).

## Time analysis (`04_time_analysis.sql`)
- `LAG()` and a windowed running total were used to compute month-over-month revenue growth and a cumulative revenue total. MoM revenue growth swings between roughly **-17% and +34%** — there is no steady growth trend, just volatility, which is the entry point for the root-cause analysis in `docs/06_revenue_decomposition_rca.md`.
- A second query decomposes each month's revenue change into its order-volume and AOV components side by side, which is the SQL-side seed for the full RCA.
