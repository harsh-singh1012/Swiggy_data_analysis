-- ============================================================
-- 04_time_analysis.sql — Month-over-month, running totals, LAG
-- ============================================================

-- Month-over-month revenue growth using LAG()
WITH monthly AS (
    SELECT
        year_month,
        COUNT(*)              AS orders,
        SUM(revenue)          AS revenue
    FROM fact_orders
    GROUP BY year_month
)
SELECT
    year_month,
    orders,
    ROUND(revenue, 0)                                                    AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY year_month), 0)                     AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year_month))
          / NULLIF(LAG(revenue) OVER (ORDER BY year_month), 0), 2)        AS mom_revenue_growth_pct,
    ROUND(SUM(revenue) OVER (ORDER BY year_month
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_total_revenue
FROM monthly
ORDER BY year_month;

-- Month-over-month order volume and AOV growth together
WITH monthly AS (
    SELECT
        year_month,
        COUNT(*)                                                              AS orders,
        SUM(revenue)                                                          AS revenue,
        SUM(revenue) * 1.0 / NULLIF(SUM(CASE WHEN is_zero_amount=0 THEN 1 ELSE 0 END),0) AS aov
    FROM fact_orders
    GROUP BY year_month
)
SELECT
    year_month,
    orders,
    ROUND(revenue, 0) AS revenue,
    ROUND(aov, 2) AS aov,
    ROUND(100.0 * (orders - LAG(orders) OVER (ORDER BY year_month)) / NULLIF(LAG(orders) OVER (ORDER BY year_month), 0), 2) AS mom_orders_growth_pct,
    ROUND(100.0 * (aov - LAG(aov) OVER (ORDER BY year_month)) / NULLIF(LAG(aov) OVER (ORDER BY year_month), 0), 2)         AS mom_aov_growth_pct
FROM monthly
ORDER BY year_month;
