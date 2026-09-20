-- ============================================================
-- 01_revenue.sql — Revenue by month, city, restaurant
-- Revenue = SUM(revenue) which already excludes zero-amount rows
-- (see docs/01_data_audit.md); order counts include them.
-- ============================================================

-- Revenue, orders and AOV by calendar month
SELECT
    year_month,
    COUNT(*)                                   AS orders,
    ROUND(SUM(revenue), 0)                     AS revenue,
    ROUND(SUM(revenue) * 1.0 / NULLIF(SUM(CASE WHEN is_zero_amount = 0 THEN 1 ELSE 0 END), 0), 2) AS aov
FROM fact_orders
GROUP BY year_month
ORDER BY year_month;

-- Revenue by city (via restaurant), with contribution %
SELECT
    r.city,
    COUNT(*)                                            AS orders,
    ROUND(SUM(f.revenue), 0)                            AS revenue,
    ROUND(100.0 * SUM(f.revenue) / (SELECT SUM(revenue) FROM fact_orders WHERE has_restaurant = 1), 2) AS pct_of_total_revenue
FROM fact_orders f
JOIN dim_restaurants r ON f.r_id = r.r_id
WHERE f.has_restaurant = 1
GROUP BY r.city
ORDER BY revenue DESC
LIMIT 25;

-- Revenue by restaurant (top 25)
SELECT
    r.r_id,
    r.name,
    r.city,
    COUNT(*)                       AS orders,
    ROUND(SUM(f.revenue), 0)       AS revenue,
    ROUND(AVG(f.revenue), 2)       AS aov
FROM fact_orders f
JOIN dim_restaurants r ON f.r_id = r.r_id
WHERE f.has_restaurant = 1
GROUP BY r.r_id, r.name, r.city
ORDER BY revenue DESC
LIMIT 25;
