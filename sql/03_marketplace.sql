-- ============================================================
-- 03_marketplace.sql — Top restaurants, city rankings, contribution
-- Uses RANK() / DENSE_RANK() / ROW_NUMBER() window functions
-- ============================================================

-- City rankings by revenue, with three ranking styles for comparison
WITH city_revenue AS (
    SELECT
        r.city,
        COUNT(*)                 AS orders,
        SUM(f.revenue)            AS revenue
    FROM fact_orders f
    JOIN dim_restaurants r ON f.r_id = r.r_id
    WHERE f.has_restaurant = 1
    GROUP BY r.city
)
SELECT
    city,
    orders,
    ROUND(revenue, 0)                                     AS revenue,
    ROW_NUMBER() OVER (ORDER BY revenue DESC)              AS row_num_rank,
    RANK()       OVER (ORDER BY revenue DESC)              AS rank,
    DENSE_RANK() OVER (ORDER BY revenue DESC)               AS dense_rank
FROM city_revenue
ORDER BY revenue DESC
LIMIT 20;

-- Restaurant concentration: cumulative revenue share of top-ranked restaurants
-- (running total via window function) — used to test the 80/20 pattern
WITH restaurant_revenue AS (
    SELECT r.r_id, r.name, r.city, SUM(f.revenue) AS revenue
    FROM fact_orders f
    JOIN dim_restaurants r ON f.r_id = r.r_id
    WHERE f.has_restaurant = 1
    GROUP BY r.r_id, r.name, r.city
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rnk,
        SUM(revenue) OVER (ORDER BY revenue DESC
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue,
        SUM(revenue) OVER ()                       AS total_revenue
    FROM restaurant_revenue
)
SELECT
    rnk,
    r_id,
    name,
    city,
    ROUND(revenue, 0)                                  AS revenue,
    ROUND(100.0 * running_revenue / total_revenue, 2)  AS cumulative_pct_of_revenue
FROM ranked
WHERE rnk <= 50
ORDER BY rnk;

-- Rating vs. order volume — restaurant-level table for correlation analysis in Python
SELECT
    r.r_id,
    r.rating_numeric,
    r.rating_count_floor,
    COUNT(f.order_id)          AS orders,
    ROUND(SUM(f.revenue), 0)   AS revenue
FROM dim_restaurants r
LEFT JOIN fact_orders f ON f.r_id = r.r_id AND f.has_restaurant = 1
WHERE r.has_rating = 1
GROUP BY r.r_id, r.rating_numeric, r.rating_count_floor;
