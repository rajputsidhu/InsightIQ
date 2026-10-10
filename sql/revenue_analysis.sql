-- ==========================================================
-- Monthly Revenue & Growth Trend Analysis
-- Calculates monthly net revenue, order volume, and month-over-month growth
-- ==========================================================

WITH monthly_summary AS (
    SELECT
        DATE_TRUNC('month', CAST(order_date AS DATE)) AS revenue_month,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT customer_id) AS active_buyers,
        SUM(net_revenue) AS monthly_revenue,
        SUM(profit) AS monthly_profit,
        ROUND(AVG(net_revenue), 2) AS average_order_value
    FROM active_dataset
    WHERE order_date IS NOT NULL
    GROUP BY 1
),
growth_calc AS (
    SELECT
        revenue_month,
        total_orders,
        active_buyers,
        monthly_revenue,
        monthly_profit,
        average_order_value,
        LAG(monthly_revenue, 1) OVER (ORDER BY revenue_month) AS prev_month_revenue
    FROM monthly_summary
)
SELECT
    STRFTIME(revenue_month, '%Y-%m') AS order_period,
    total_orders,
    active_buyers,
    ROUND(monthly_revenue, 2) AS total_revenue,
    ROUND(monthly_profit, 2) AS total_profit,
    average_order_value,
    ROUND(
        CASE 
            WHEN prev_month_revenue IS NOT NULL AND prev_month_revenue > 0
            THEN ((monthly_revenue - prev_month_revenue) / prev_month_revenue) * 100.0
            ELSE 0.0
        END, 2
    ) AS mom_growth_pct
FROM growth_calc
ORDER BY revenue_month DESC;
