-- ==========================================================
-- InsightIQ Production PostgreSQL Analytical Schema
-- ==========================================================

CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    dataset_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    row_count INT NOT NULL,
    col_count INT NOT NULL,
    quality_score NUMERIC(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_orders (
    id SERIAL PRIMARY KEY,
    dataset_id INT REFERENCES datasets(id) ON DELETE CASCADE,
    order_id VARCHAR(100),
    customer_id VARCHAR(100),
    order_date DATE,
    product_name VARCHAR(255),
    category VARCHAR(100),
    region VARCHAR(100),
    customer_segment VARCHAR(100),
    quantity INT,
    unit_price NUMERIC(12, 2),
    unit_cost NUMERIC(12, 2),
    discount_rate NUMERIC(5, 4),
    gross_revenue NUMERIC(14, 2),
    net_revenue NUMERIC(14, 2),
    profit NUMERIC(14, 2),
    payment_method VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_profiles (
    id SERIAL PRIMARY KEY,
    dataset_id INT REFERENCES datasets(id) ON DELETE CASCADE,
    customer_id VARCHAR(100) NOT NULL,
    recency_days INT,
    frequency_orders INT,
    monetary_spend NUMERIC(14, 2),
    avg_order_value NUMERIC(12, 2),
    rfm_score VARCHAR(10),
    rfm_segment VARCHAR(100),
    predicted_churn_prob NUMERIC(5, 4),
    churn_risk_tier VARCHAR(50),
    cluster_label VARCHAR(50),
    estimated_clv NUMERIC(14, 2),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ml_model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    target_metric VARCHAR(100) NOT NULL,
    accuracy NUMERIC(5, 4),
    precision_score NUMERIC(5, 4),
    recall_score NUMERIC(5, 4),
    f1_score NUMERIC(5, 4),
    roc_auc NUMERIC(5, 4),
    is_best_model BOOLEAN DEFAULT FALSE,
    trained_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS revenue_forecasts (
    id SERIAL PRIMARY KEY,
    dataset_id INT REFERENCES datasets(id) ON DELETE CASCADE,
    model_used VARCHAR(100) NOT NULL,
    forecast_date DATE NOT NULL,
    point_forecast NUMERIC(14, 2) NOT NULL,
    lower_80 NUMERIC(14, 2),
    upper_80 NUMERIC(14, 2),
    lower_95 NUMERIC(14, 2),
    upper_95 NUMERIC(14, 2),
    scenario_multiplier NUMERIC(5, 2) DEFAULT 1.0,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    dataset_id INT REFERENCES datasets(id) ON DELETE CASCADE,
    operation_name VARCHAR(100) NOT NULL,
    target_column VARCHAR(100),
    affected_rows INT NOT NULL,
    log_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analytical Indices
CREATE INDEX IF NOT EXISTS idx_orders_customer ON raw_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON raw_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_category ON raw_orders(category);
