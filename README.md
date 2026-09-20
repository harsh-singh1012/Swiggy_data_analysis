# Swiggy Marketplace Intelligence

An end-to-end business analytics case study built on six raw Swiggy-style extracts (users, orders, order-type tags, restaurants, food catalog, menu). It follows the full pipeline: **Data Audit → Data Cleaning → SQL Analysis → Python EDA → Customer Analytics (RFM + Cohorts) → Marketplace Analytics → Statistical Analysis → Revenue Decomposition & Root-Cause Analysis → Power BI → Business Recommendations.**

Every number in every doc in this folder comes from actually running the corresponding script against the real data — nothing here is illustrative or fabricated. Re-run any script yourself (see "Reproducing this project" below) and you'll get the same output.

> **Note on this package**: `data/raw/` (the six original `.xlsx` files) is not included in this delivered zip to keep it under the file-size limit for chat delivery — you already have those originals. `sql/swiggy.db` is also omitted since it's a compiled, regenerable artifact (`sql/00_build_database.py` rebuilds it from `data/cleaned/` in a few seconds). Everything else — all cleaned data, code, SQL, charts, stats, and docs — is included as-is. If you'd like the raw files bundled in too, just ask and I'll package a second archive with them.

## Headline numbers

- **150,278** valid orders, **₹986.5M** total revenue, Oct 2017 – Jun 2020 (first and last months are partial calendar months — see the data audit)
- **100,000** registered users, of whom **77,929 (78%)** ever ordered; **57.1%** repeat rate among those who did
- **148,540** restaurants across **821** cities
- Top RFM segment (**Champions**, 22% of customers) generates **35.1%** of revenue
- Month-1 customer retention: **4.6%**, and it stays roughly flat through 12 months rather than decaying sharply — a structural engagement problem, not an onboarding one
- The 2020 revenue decline traces to **order frequency falling (~10%)**, not average order value (which held flat) — see the RCA

## Folder structure

```
swiggy-marketplace-intelligence/
│
├── README.md                    ← you are here
│
├── data/
│   ├── raw/                     ← the 6 source files, untouched
│   └── cleaned/                 ← analysis-ready star-schema CSVs + derived tables
│
├── docs/                        ← every write-up, in pipeline order
│   ├── 01_data_audit.md
│   ├── 02_cleaning_log.md
│   ├── 03_sql_analysis_summary.md
│   ├── 04_eda_summary.md
│   ├── 05_statistical_analysis.md
│   ├── 05a_rfm_summary.md
│   ├── 05b_cohort_retention_summary.md
│   ├── 05c_marketplace_analysis_summary.md
│   ├── 06_revenue_decomposition_rca.md
│   └── 08_dataviz_palette_reference.md
│
├── python/                      ← numbered, runnable, reproducible scripts
│   ├── 01_data_cleaning.py
│   ├── 02_eda.py
│   ├── 03_rfm_segmentation.py
│   ├── 04_cohort_retention.py
│   ├── 05_marketplace_analysis.py
│   ├── 06_statistical_analysis.py
│   ├── 07_revenue_decomposition_rca.py
│   └── 08_powerbi_prep.py
│
├── sql/                         ← the SQL analytical layer (SQLite)
│   ├── 00_build_database.py     (loads cleaned CSVs into swiggy.db)
│   ├── 01_revenue.sql
│   ├── 02_customers.sql
│   ├── 03_marketplace.sql       (RANK/DENSE_RANK/ROW_NUMBER, Lorenz-style running totals)
│   ├── 04_time_analysis.sql     (LAG, MoM growth, running totals)
│   ├── run_all_queries.py       (executes every .sql file, saves results/)
│   └── results/                 ← every query's actual output, as CSV
│
├── eda_charts/                  ← every chart referenced in the docs, as PNG
│
├── powerbi/
│   ├── dashboard_build_guide.md ← page-by-page build instructions (4 pages)
│   ├── dax_measures.dax         ← full DAX measure library
│   └── model/                   ← star-schema CSVs ready for Power BI import
│
└── insights/
    └── business_insights_and_recommendations.md   ← Evidence → Insight → Implication → Action
```

## Why this structure

Everything is organized by pipeline *stage*, not by output type, because that's the order a reader (or a hiring manager) actually consumes it in: read the audit before trusting a KPI, read the cleaning log to see what changed, then SQL/Python/stats build on each other, and Power BI + insights are the last mile. Each doc names the exact script and output file behind every number so the chain from raw file to business claim is always traceable.

## Reproducing this project

Everything runs from the raw files in `data/raw/`. From inside `python/`, in order:

```bash
python3 01_data_cleaning.py          # -> data/cleaned/*.csv
python3 02_eda.py                    # -> eda_charts/01-08*.png, docs/04_eda_summary.md
python3 03_rfm_segmentation.py       # -> data/cleaned/customer_rfm.csv, docs/05a_rfm_summary.md
python3 04_cohort_retention.py       # -> data/cleaned/cohort_retention_*.csv, docs/05b_*.md
python3 05_marketplace_analysis.py   # -> data/cleaned/city_performance.csv, docs/05c_*.md
python3 06_statistical_analysis.py   # -> data/cleaned/statistical_test_results.json
python3 07_revenue_decomposition_rca.py  # -> data/cleaned/rca_*.csv, docs/06_*.md
python3 08_powerbi_prep.py           # -> powerbi/model/*.csv
```

Then, from inside `sql/`:

```bash
python3 00_build_database.py   # builds swiggy.db from data/cleaned/*.csv
python3 run_all_queries.py     # runs every .sql file, writes sql/results/*.csv
```

Requires `pandas`, `numpy`, `scipy`, `matplotlib`, `openpyxl` (all standard; no exotic dependencies).

## Known data limitations (see `docs/01_data_audit.md` for full detail)

These are disclosed everywhere they affect a result, not just here:

1. **No shared key between `orders_1` and `orders_Type`** — the Veg/Non-Veg/Other tag is joined positionally (by row order), which is the only usable option given the files as supplied, but it is an assumption, not a verified match.
2. **~1 order per restaurant** (mean 1.001, max 2) — restaurant-level "top performer" language throughout this project means "received one high-value order," not sustained performance. City-level analysis is the more reliable cut.
3. **Menu extract is partial** — exactly 1,048,575 rows (one short of Excel's row cap), covering only 8.2% of restaurants, with no item-level link to actual orders. Menu/assortment findings are labeled as indicative wherever they appear.
4. **First and last calendar months are partial** (Oct 2017 from day 4; Jun 2020 through day 26) — trend charts and the RCA period comparison account for this by normalizing to per-day rates.

## Reading order

1. `docs/01_data_audit.md` — trust the foundation first
2. `docs/03_sql_analysis_summary.md` and `docs/04_eda_summary.md` — what's happening
3. `docs/05a_rfm_summary.md`, `docs/05b_cohort_retention_summary.md`, `docs/05c_marketplace_analysis_summary.md` — who's driving it
4. `docs/05_statistical_analysis.md` and `docs/06_revenue_decomposition_rca.md` — why it's happening
5. `powerbi/dashboard_build_guide.md` — how it's communicated
6. `insights/business_insights_and_recommendations.md` — what to do about it
"# Swiggy_data_analysis" 
