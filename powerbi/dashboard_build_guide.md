# Power BI Dashboard — Build Guide

This project was built end-to-end in SQL/Python in a cloud environment that cannot run Power BI Desktop itself, so this folder hands off a ready-to-import data model, a full DAX measure library (`dax_measures.dax`), and this page-by-page build guide — everything needed to build the actual `.pbix` in Power BI Desktop without re-doing any analysis.

## 1. Import the model

In Power BI Desktop: **Get Data → Text/CSV**, import the four core star-schema tables straight from **`data/cleaned/`** (they're not duplicated under `powerbi/` to keep this delivered folder from carrying the same ~100MB of data twice), plus the small supporting tables from **`powerbi/model/`**:

| File | Location | Role |
|---|---|---|
| `fact_orders.csv` | `data/cleaned/` | **Fact table** — one row per order |
| `dim_restaurants.csv` | `data/cleaned/` | Dimension — one row per restaurant |
| `dim_users.csv` | `data/cleaned/` | Dimension — one row per registered user |
| `customer_rfm.csv` | `data/cleaned/` | Dimension — one row per *ordering* customer, with recency/frequency/monetary and RFM `segment` |
| `dim_date.csv` | `powerbi/model/` | Calendar table — one row per day across the full order history |
| `city_performance.csv`, `rfm_segment_summary.csv`, `cohort_retention_matrix.csv`, `cohort_retention_overall_curve.csv`, `rca_city_orders_change.csv`, `rca_segment_orders_change.csv` | `powerbi/model/` | Pre-computed reference tables — optional, useful for the RCA and retention visuals on Page 2/4 without re-deriving them in DAX |

## 2. Build the relationships (Model view)

```
dim_date[date]  1 ────< *  fact_orders[order_date]
dim_restaurants[r_id]  1 ──< *  fact_orders[r_id]
customer_rfm[user_id]  1 ──< *  fact_orders[user_id]
dim_users[user_id]  1 ──< *  customer_rfm[user_id]
```

All relationships are one-to-many, single-direction (dimension → fact), which is the standard star-schema setup. Mark `dim_date` as a **Date table** (Table tools → Mark as Date Table → `date` column) so the DAX time-intelligence functions (`DATEADD`, etc.) work.

## 3. Paste in the DAX measures

Create a dedicated measures table (a blank query named `_Measures` is a common pattern) and paste in every measure from `dax_measures.dax`. They're grouped by page in that file. Because they all key off `fact_orders`/`customer_rfm`/`dim_restaurants` through the relationships above, any slicer (city, segment, date range) automatically updates every measure — that's the "select a city and Revenue/Orders/AOV/Customers/Repeat Rate all move together" behavior the brief asks for.

## 4. Page 1 — Executive Overview

**Layout**: a KPI row across the top, two trend lines below, one contribution chart, one insight-callout text box.

| Visual | Type | Fields |
|---|---|---|
| KPI cards | Card ×5 | `Revenue`, `Orders`, `AOV`, `Customers`, `Repeat Rate %` |
| Revenue trend | Line chart | Axis: `dim_date[year_month]`; Value: `Revenue` |
| Orders trend | Line chart | Axis: `dim_date[year_month]`; Value: `Orders` |
| AOV trend | Line chart | Axis: `dim_date[year_month]`; Value: `AOV` |
| City contribution | Horizontal bar (top 10) | Axis: `dim_restaurants[city]`; Value: `Revenue`; sort descending |
| Insight callouts | Text boxes | Pull 2-3 lines straight from `insights/business_insights_and_recommendations.md` (e.g. the Tirupati concentration finding, the Champions revenue share) |

A city slicer and a date-range slicer at the top of the page drive every visual below via the relationships.

## 5. Page 2 — Customer Intelligence

| Visual | Type | Fields |
|---|---|---|
| Segment revenue vs. customer share | Clustered bar | Axis: `customer_rfm[segment]`; Values: `Segment Contribution %`, and a second measure `% of Customers = DIVIDE(DISTINCTCOUNT(customer_rfm[user_id]), CALCULATE(DISTINCTCOUNT(customer_rfm[user_id]), ALL(customer_rfm[segment])))` |
| RFM scatter | Scatter chart | X: `Avg Recency (days)`, Y: `Avg Frequency`, Size: `Avg Monetary`, Legend: `segment` — build off `customer_rfm` directly (not aggregated) for a true per-customer scatter, or use the segment-level averages for a cleaner 5-point view |
| Repeat vs. one-time split | Bar chart | `Repeat Customers` vs. `Customers - Repeat Customers` |
| Cohort retention | Matrix/heatmap (import `cohort_retention_matrix.csv` as its own table) | Rows: cohort month; Columns: period number; Values: retention % — Power BI's matrix visual with conditional-formatting background color reproduces the heatmap from `eda_charts/10_cohort_retention_heatmap.png` |
| Retention curve | Line chart (from `cohort_retention_overall_curve.csv`) | X: period number; Y: retention % |

## 6. Page 3 — Marketplace Intelligence

| Visual | Type | Fields |
|---|---|---|
| City performance table | Table | `city`, `Orders`, `Revenue`, `AOV`, `City Contribution %`, sorted by revenue |
| Restaurant leaderboard | Horizontal bar (top 20) | Axis: `dim_restaurants[name]`; Value: `Revenue`. **Label this "Largest single-order value by restaurant"**, not "top-performing restaurants" — see the data audit's ~1-order-per-restaurant finding, so this ranks individual order size, not repeat performance. |
| Restaurant concentration | Line chart (import a cumulative-% table, or reuse the Lorenz-curve values from `eda_charts/12_restaurant_revenue_lorenz.png`'s underlying data) | Cumulative % of restaurants vs. cumulative % of revenue |
| Rating distribution | Histogram (Power BI histogram or binned bar) | `dim_restaurants[rating_numeric]`, filtered to `has_rating = TRUE` |
| Rating vs. orders | Scatter chart | X: `rating_numeric`, Y: order count per restaurant — annotate with the Pearson/Spearman values from `docs/05c_marketplace_analysis_summary.md` (both ≈ 0; note the correlation-is-not-causation caveat directly on the page) |
| Menu/assortment note | Text box | State plainly that menu coverage is partial (8% of restaurants, ~1.05M truncated rows) per the data audit — don't present catalog stats as if they cover the whole marketplace |

## 7. Page 4 — Diagnostic / Root-Cause Analysis

Build this page as a top-to-bottom narrative, not a grid of unrelated charts:

1. **Headline card row**: `Revenue`, `MoM Revenue Growth %`, with the date slicer set to the decline window (Mar–Jun 2020) vs. the whole-history default.
2. **Decomposition waterfall**: Power BI's native Waterfall visual, categories = `Baseline`, `Orders effect`, `AOV effect`, `Decline` — import the four values computed in `docs/06_revenue_decomposition_rca.md` (or recreate with a small DAX table, since the symmetric decomposition needs the two-period comparison done once, not as a live measure).
3. **City drill-down**: Horizontal bar of the top 10 cities by order-volume *change* (from `rca_city_orders_change.csv`), colored by direction (decline = red-adjacent step, per the palette's status colors, growth = green-adjacent).
4. **Segment drill-down**: Bar chart from `rca_segment_orders_change.csv` — % change in order volume by segment.
5. **Investigation priorities**: a text box listing the four priorities from `docs/06_revenue_decomposition_rca.md` — this is the page's "so what."

## 8. Visualization rules applied throughout

- No pie charts anywhere — composition is shown with bars or a Lorenz-style cumulative line, per the brief's own visualization philosophy.
- One y-axis per chart; anything comparing two differently-scaled measures (e.g., Orders vs. AOV) is two charts side by side, not a dual-axis combo chart.
- A single consistent categorical color order is used across all pages (see `docs/08_dataviz_palette_reference.md`) so "Champions" or a given city is always the same color wherever it reappears.
- Every ranking uses a horizontal bar (easier to read long restaurant/city names) rather than a vertical bar or, worse, a pie.
