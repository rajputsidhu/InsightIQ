-- ==========================================================
-- Customer Spending & Purchase Frequency Distribution
-- Analyzes customer lifetime transactions and spending percentiles
-- ==========================================================

WITH customer_totals AS (
    SELECT
        customer_id,
        MIN(CAST(order_date AS DATE)) AS first_order_date,
        MAX(CAST(order_date AS DATE)) AS last_order_date,
        COUNT(DISTINCT order_id) AS total_orders,
        ROUND(SUM(net_revenue), 2) AS total_spend,
        ROUND(AVG(net_revenue), 2) AS avg_order_value
    FROM active_dataset
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    customer_id,
    first_order_date,
    last_order_date,
    total_orders,
    total_spend,
    avg_order_value,
    NTILE(4) OVER (ORDER BY total_spend DESC) AS spending_quartile,
    DENSE_RANK() OVER (ORDER BY total_spend DESC) AS spend_rank
FROM customer_totals
ORDER BY total_spend DESC
LIMIT 100;
