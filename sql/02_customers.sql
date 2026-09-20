-- ============================================================
-- 02_customers.sql — Unique customers, repeat customers, frequency
-- ============================================================

-- Unique ordering customers vs. registered base, and overall repeat rate
SELECT
    (SELECT COUNT(*) FROM dim_users)                                   AS registered_users,
    COUNT(DISTINCT user_id)                                            AS ordering_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)                   AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
          / COUNT(DISTINCT user_id), 2)                                AS repeat_rate_pct
FROM (
    SELECT user_id, COUNT(*) AS order_count
    FROM fact_orders
    GROUP BY user_id
);

-- Customer order-frequency distribution (how many customers placed N orders)
SELECT
    order_count,
    COUNT(*) AS customers
FROM (
    SELECT user_id, COUNT(*) AS order_count
    FROM fact_orders
    GROUP BY user_id
)
GROUP BY order_count
ORDER BY order_count;

-- Top 20 customers by lifetime revenue
SELECT
    u.user_id,
    u.name,
    COUNT(*)                    AS orders,
    ROUND(SUM(f.revenue), 0)    AS lifetime_revenue
FROM fact_orders f
JOIN dim_users u ON f.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY lifetime_revenue DESC
LIMIT 20;
