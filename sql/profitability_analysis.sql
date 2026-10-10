-- ==========================================================
-- Product & Category Margin Profitability Analysis
-- Identifies highest margin drivers and loss-making items
-- ==========================================================

SELECT
    COALESCE(category, 'Unassigned') AS product_category,
    COALESCE(product_name, 'Unknown SKU') AS product,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(net_revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        CASE 
            WHEN SUM(net_revenue) > 0 
            THEN (SUM(profit) / SUM(net_revenue)) * 100.0 
            ELSE 0.0 
        END, 2
    ) AS margin_percentage,
    RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC) AS rank_in_category
FROM active_dataset
WHERE net_revenue IS NOT NULL
GROUP BY 1, 2
ORDER BY total_profit DESC
LIMIT 50;
