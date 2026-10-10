-- ==========================================================
-- SQL RFM Quintile Scoring & Customer Tier Classification
-- Calculates RFM scores directly within database engine
-- ==========================================================

WITH customer_rfm_raw AS (
    SELECT
        customer_id,
        DATE_DIFF('day', MAX(CAST(order_date AS DATE)), CURRENT_DATE) AS recency_days,
        COUNT(DISTINCT order_id) AS frequency_orders,
        SUM(net_revenue) AS monetary_spend
    FROM active_dataset
    WHERE customer_id IS NOT NULL AND order_date IS NOT NULL
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        recency_days,
        frequency_orders,
        ROUND(monetary_spend, 2) AS monetary_spend,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency_orders ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary_spend ASC) AS m_score
    FROM customer_rfm_raw
)
SELECT
    customer_id,
    recency_days,
    frequency_orders,
    monetary_spend,
    r_score,
    f_score,
    m_score,
    (CAST(r_score AS VARCHAR) || CAST(f_score AS VARCHAR) || CAST(m_score AS VARCHAR)) AS rfm_combined_score
FROM rfm_scores
ORDER BY monetary_spend DESC
LIMIT 100;
