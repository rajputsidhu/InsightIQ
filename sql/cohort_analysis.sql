-- ==========================================================
-- Monthly Customer Cohort Retention Analysis
-- Tracks customer cohort acquisition and subsequent order activity
-- ==========================================================

WITH first_purchases AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(CAST(order_date AS DATE))) AS cohort_month
    FROM active_dataset
    WHERE customer_id IS NOT NULL AND order_date IS NOT NULL
    GROUP BY customer_id
),
customer_activities AS (
    SELECT
        a.customer_id,
        fp.cohort_month,
        DATE_TRUNC('month', CAST(a.order_date AS DATE)) AS activity_month
    FROM active_dataset a
    JOIN first_purchases fp ON a.customer_id = fp.customer_id
    WHERE a.order_date IS NOT NULL
)
SELECT
    STRFTIME(cohort_month, '%Y-%m') AS cohort,
    STRFTIME(activity_month, '%Y-%m') AS activity_period,
    COUNT(DISTINCT customer_id) AS active_retained_customers
FROM customer_activities
GROUP BY 1, 2
ORDER BY 1, 2;
