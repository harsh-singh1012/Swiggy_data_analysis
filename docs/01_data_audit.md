# Data Audit — Swiggy Marketplace Intelligence

This audit was run against the six raw files exactly as supplied, before any cleaning. Its job is to establish what each table actually contains, whether the tables can be safely joined, and which values need to be fixed or excluded before any KPI is trusted. All numbers below come from running pandas/openpyxl against the raw files, not from assumption.

## 1. Inventory

| File | Rows | Columns | What one row represents |
|---|---|---|---|
| `users_1.xlsx` | 100,000 | 6 | One registered customer |
| `orders_1.xlsx` | 150,281 | 6 | One order (date, quantity, amount, customer, restaurant) |
| `orders_Type.xlsx` | 150,281 | 2 | One order's food-type tag (Veg / Non-Veg / Other) |
| `restaurant.xlsx` | 148,540 | 9 | One restaurant listing on the platform |
| `food_1.xlsx` | 371,560 | 3 | One food item in the catalog |
| `menu.xlsx` | 1,048,575 | 5 | One (restaurant, food item) price listing |

## 2. Schema and dtypes per table

**users_1**: `user_id` (int, PK), `name` (str), `Age` (int), `Gender` (str), `Marital Status` (str), `Occupation` (str). No location field — the dataset has no customer-city attribute, only restaurant-city, so all "city" analysis in this project is by restaurant/fulfillment city, not customer residence.

**orders_1**: `order_date` (datetime), `sales_qty` (int), `sales_amount` (int — currency minor unit not specified, treated as INR), `currency` (str, constant `INR`), `user_id` (int, FK → users), `r_id` (float — nullable FK → restaurant.id).

**orders_Type**: `Order_Id` (str, e.g. `B496840219`), `Type` (str: Veg / Non-Veg / Other).

**restaurant**: `id` (int, PK), `name` (str), `Country` (str, constant `India`), `city` (str), `rating` (mixed str/float — numeric string or the placeholder `--`), `rating_count` (str bucket, e.g. `50+ ratings`, `Too Few Ratings`), `cuisine` (comma-separated str), `link` (URL str), `address` (str).

**food_1**: `f_id` (str, e.g. `fd0`), `item` (mixed type — a handful of rows have a bare number instead of text), `veg_or_non_veg` (str: `Veg` / `Non-veg` / null).

**menu**: `menu_id` (str), `r_id` (int, FK → restaurant.id), `f_id` (str, FK → food_1.f_id), `cuisine` (str), `price` (float).

## 3. Row/column counts, missing values, duplicates

| Table | Nulls found | Duplicate rows |
|---|---|---|
| users_1 | none | 0 |
| orders_1 | `r_id`: 1,617 (1.1%) | 0 |
| orders_Type | none | 0 |
| restaurant | `name`/`rating`/`rating_count`/`address`: 86 each; `cuisine`: 99 | 0 |
| food_1 | 8 rows entirely null | 7 exact duplicate rows |
| menu | `price`: 1 | 0 |

## 4. Invalid, zero, and negative values

- `orders_1.sales_amount`: 2 rows negative (min = **-1**), 1,609 rows exactly **0** (1.1% of orders). Negative values are treated as data-entry errors and excluded from revenue. Zero-amount orders are kept in order-count metrics but excluded from AOV/monetary sums (they would silently drag AOV down and distort RFM monetary scores).
- `orders_1.sales_qty`: no negatives/zeros, but heavily right-skewed — median 1, 75th percentile 7, **max 14,049**. The extreme tail is capped (winsorized at the 99th percentile) for any qty-based aggregate so a handful of outlier rows don't dominate city/restaurant averages; raw values are kept in the cleaned file for traceability.
- `restaurant.rating`: the placeholder `--` (no numeric rating yet) is converted to null rather than 0, so "no rating" restaurants aren't scored as the worst-rated ones.
- `restaurant.rating_count`: not a real count — it's a marketing-style bucket (`Too Few Ratings`, `20+ ratings`, …, `10K+ ratings`). It's mapped to an ordered category and a lower-bound numeric proxy (0/20/50/100/500/1,000/5,000/10,000) so it can be sorted and used as a rough popularity floor, but it is **not** treated as an exact rating count anywhere in this project.
- `menu.price`: min = 0 (a small number of free/₹0 listings), no negatives.

## 5. Uniqueness / candidate keys

- `users_1.user_id`, `restaurant.id`, `food_1.f_id` are each unique and serve as primary keys for their tables.
- `orders_1` has **no explicit order ID column** — it is one row per order with no primary key of its own.
- `orders_Type.Order_Id` values are unique but **do not appear anywhere in `orders_1`** — there is no shared key between the two files.

## 6. Relationships between tables and join validation

- **orders_1 → users_1** on `user_id`: clean. All 150,281 order rows resolve to a user that exists in `users_1` (0 orphans). Of the 100,000 registered users, only 77,929 (78%) ever placed an order — the rest are registered but inactive, which matters for any "active customer base" framing.
- **orders_1 → restaurant** on `r_id`: 1,617 orders (1.1%) have a null `r_id` and can't be attributed to any restaurant/city — these are kept for customer-level totals but excluded from restaurant/city breakdowns. Of the remaining rows, exactly 1 references an `r_id` not present in the restaurant table; it is dropped.
- **orders_1 ↔ orders_Type**: same row count (150,281) but **no shared key**. The join used throughout this project is **positional** (row order in the raw file) — this is an assumption, not a verified key match, and is called out explicitly here because it is the single biggest structural risk in the dataset. If the two files were ever re-sorted independently, this join would silently become wrong. Given they were supplied as a matched pair with identical row counts and no alternative join field exists, positional join is the only usable option, but any downstream user of this project should know that "Veg/Non-Veg/Other" per order rests on that assumption.
- **menu → restaurant** on `r_id`: 273 of 1,048,575 menu rows (0.03%) reference a restaurant id that doesn't exist in `restaurant.xlsx`; dropped as orphans.
- **menu → food_1** on `f_id`: 1,205 of 1,048,575 menu rows (0.11%) reference a food id that doesn't exist in `food_1.xlsx`; dropped as orphans.
- **Menu coverage is partial, not exhaustive**: `menu.xlsx` contains exactly **1,048,575 rows — one short of Excel's 1,048,576-row hard limit**. That is a strong signal the source extract was truncated when it was saved to `.xlsx`, not that this is the complete menu. Confirming this: the menu file only covers **12,117 of the 148,540 restaurants (8.2%)**. Any menu/assortment analysis in this project is therefore explicitly scoped as **indicative, catalog-level, and partial** — it should not be read as "92% of restaurants have no menu," only as "92% of restaurants have no menu *in this extract*."
- **No item-level link from orders to menu/food**: `orders_1` records `(user_id, r_id, sales_qty, sales_amount)` but never which food item was bought. `menu`/`food_1` describe a restaurant's catalog (what it *sells*, at what price), not what any specific order *contained*. This means "best-selling item" or "revenue by dish" cannot be computed — only catalog composition (price positioning, veg/non-veg mix, cuisine breadth) per restaurant/city.

## 7. Date range

`orders_1.order_date` spans **2017-10-04 to 2020-06-26** (~33 months). This range is used for all trend, cohort, and MoM analysis; the last calendar month in the data is partial in some cases and is flagged wherever it would distort a trend line.

## 8. Structural finding discovered during SQL analysis: ~1 order per restaurant

Running the SQL analytical layer surfaced a finding that changes how restaurant-level results should be read: across the 148,540 restaurants, the mean number of orders per restaurant is **1.001**, with a maximum of **2**. In other words, this dataset does not contain repeat business at the restaurant level — almost every restaurant appears in the order fact table exactly once.

This means "top restaurants by revenue" is not measuring sustained performance or popularity; it is effectively measuring **which restaurant happened to receive the single largest individual order**. Restaurant-level rankings, concentration curves, and "top performer" language are still computed and shown (the brief asks for them), but they are labeled throughout this project as **largest single-order value by restaurant**, not restaurant performance over time. City-level aggregation is far more meaningful here, since each city contains many restaurants and therefore many independent orders — city rankings and city contribution % are the trustworthy unit of marketplace analysis in this dataset, and restaurant rating vs. order-volume correlation should be read with this ceiling (0 or 1 order per restaurant) in mind rather than as a true volume metric.

## 9. Net effect on analytical scope

Everything above is either fixed in cleaning (Section 3 of the brief) or explicitly scoped as a stated limitation:

1. Revenue/AOV analysis excludes negative and zero-amount orders from monetary sums, but keeps them in order-volume counts.
2. Restaurant/city cuts exclude the 1,618 orders with no resolvable restaurant.
3. Veg/Non-Veg/Other order-type analysis is valid only under the positional-join assumption with `orders_Type`, which is disclosed everywhere that field is used.
4. Rating analysis uses `rating` only where present (null "not yet rated" restaurants are excluded from rating correlation, not coded as low ratings) and treats `rating_count` as an ordinal popularity bucket, not a literal number.
5. Menu/assortment analysis is restricted to the 8.2% of restaurants present in the (truncated) menu extract and is labeled as partial everywhere it appears.
