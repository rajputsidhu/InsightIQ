"""
Generate realistic synthetic demonstration datasets for InsightIQ.
These datasets are designed for business intelligence, churn prediction,
revenue forecasting, and customer segmentation demonstrations.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_ecommerce_data(num_records=1250) -> pd.DataFrame:
    """Generate realistic e-commerce retail transactions."""
    categories = {
        "Electronics": [
            ("Wireless Noise-Canceling Headphones", 149.99, 85.00),
            ("Smart Watch Ultra", 299.99, 170.00),
            ("4K Ultra HD Monitor 27-inch", 349.99, 210.00),
            ("Ergonomic Mechanical Keyboard", 119.99, 65.00),
            ("USB-C Multi-Port Hub", 49.99, 22.00),
            ("Portable Bluetooth Speaker", 79.99, 38.00),
        ],
        "Office Supplies": [
            ("Premium Ergonomic Desk Chair", 289.99, 160.00),
            ("Adjustable Standing Desk Riser", 189.99, 95.00),
            ("High-Density Memory Foam Cushion", 45.00, 18.00),
            ("Dual Monitor Aluminum Desk Mount", 69.99, 32.00),
            ("LED Desk Lamp with Wireless Charger", 59.99, 26.00),
        ],
        "Software & Services": [
            ("Annual Cloud Backup License (1TB)", 99.00, 15.00),
            ("Cybersecurity Suite Pro (Annual)", 129.00, 20.00),
            ("Productivity & AI Workflow Suite", 199.00, 35.00),
            ("Developer Tooling Enterprise Seat", 350.00, 50.00),
        ],
        "Home & Lifestyle": [
            ("Aroma Diffuser & Essential Oils Kit", 39.99, 16.00),
            ("Stainless Steel Thermal Water Bottle", 29.99, 11.00),
            ("Smart Indoor Air Quality Monitor", 129.99, 68.00),
            ("Compact HEPA Air Purifier", 159.99, 85.00),
        ],
    }

    regions = ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East"]
    region_weights = [0.42, 0.28, 0.18, 0.07, 0.05]
    
    payment_methods = ["Credit Card", "Bank Transfer", "PayPal", "Corporate Invoice", "Digital Wallet"]
    customer_segments = ["Enterprise", "Mid-Market", "Small Business", "Consumer"]
    segment_weights = [0.22, 0.33, 0.30, 0.15]

    # Generate 320 unique customers
    customer_pool = [
        {
            "customer_id": f"CUST-{1000 + i}",
            "segment": random.choices(customer_segments, weights=segment_weights)[0],
            "region": random.choices(regions, weights=region_weights)[0],
        }
        for i in range(320)
    ]

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    rows = []
    for i in range(num_records):
        cust = random.choice(customer_pool)
        
        # Pick category and product
        cat = random.choice(list(categories.keys()))
        prod_name, unit_price, unit_cost = random.choice(categories[cat])

        # Quantity depends on segment
        if cust["segment"] == "Enterprise":
            qty = random.randint(3, 15)
            discount = random.choice([0.05, 0.10, 0.15, 0.20])
        elif cust["segment"] == "Mid-Market":
            qty = random.randint(1, 6)
            discount = random.choice([0.0, 0.05, 0.10, 0.15])
        else:
            qty = random.randint(1, 3)
            discount = random.choice([0.0, 0.0, 0.05, 0.10])

        # Date distribution with seasonality (Q4 boost)
        day_offset = random.randint(0, date_range_days)
        order_date = start_date + timedelta(days=day_offset)
        # Add slight Q4 weight
        if order_date.month in [10, 11, 12] and random.random() < 0.25:
            # Shift some orders into Q4
            pass

        gross_revenue = round(unit_price * qty, 2)
        total_discount_amount = round(gross_revenue * discount, 2)
        net_revenue = round(gross_revenue - total_discount_amount, 2)
        total_cost = round(unit_cost * qty, 2)
        profit = round(net_revenue - total_cost, 2)

        payment = random.choice(payment_methods)
        order_status = random.choices(["Delivered", "Shipped", "Processing", "Cancelled"], weights=[0.88, 0.06, 0.04, 0.02])[0]

        rows.append({
            "order_id": f"ORD-{2023000 + i}",
            "customer_id": cust["customer_id"],
            "order_date": order_date.strftime("%Y-%m-%d"),
            "product_name": prod_name,
            "category": cat,
            "region": cust["region"],
            "customer_segment": cust["segment"],
            "quantity": qty,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "discount_rate": discount,
            "gross_revenue": gross_revenue,
            "discount_amount": total_discount_amount,
            "net_revenue": net_revenue,
            "profit": profit,
            "payment_method": payment,
            "status": order_status,
        })

    df = pd.DataFrame(rows)
    df.sort_values(by="order_date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def generate_churn_data(num_records=1100) -> pd.DataFrame:
    """Generate realistic customer subscription churn dataset."""
    contract_types = ["Month-to-month", "One year", "Two year"]
    internet_services = ["Fiber optic", "DSL", "No"]
    payment_methods = ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]

    rows = []
    for i in range(num_records):
        cust_id = f"TELCO-{5000 + i}"
        gender = random.choice(["Male", "Female"])
        senior = random.choices([0, 1], weights=[0.84, 0.16])[0]
        partner = random.choice(["Yes", "No"])
        dependents = "Yes" if partner == "Yes" and random.random() < 0.45 else "No"
        
        contract = random.choices(contract_types, weights=[0.55, 0.25, 0.20])[0]
        internet = random.choices(internet_services, weights=[0.45, 0.35, 0.20])[0]

        # Monthly charges
        base_charge = 25.0
        if internet == "Fiber optic":
            base_charge += random.uniform(45.0, 65.0)
        elif internet == "DSL":
            base_charge += random.uniform(20.0, 35.0)

        # Tech support & Online security
        tech_support = "No"
        online_security = "No"
        if internet != "No":
            tech_support = random.choice(["Yes", "No"])
            online_security = random.choice(["Yes", "No"])
            if tech_support == "Yes":
                base_charge += 10.0
            if online_security == "Yes":
                base_charge += 8.0

        monthly_charges = round(base_charge + random.uniform(-3, 8), 2)
        
        # Tenure
        if contract == "Month-to-month":
            tenure = random.randint(1, 36)
        elif contract == "One year":
            tenure = random.randint(12, 55)
        else:
            tenure = random.randint(24, 72)

        total_charges = round(monthly_charges * tenure * random.uniform(0.92, 1.05), 2)
        paperless = random.choice(["Yes", "No"])
        payment = random.choice(payment_methods)
        support_tickets = random.choices([0, 1, 2, 3, 4, 5], weights=[0.45, 0.25, 0.15, 0.08, 0.05, 0.02])[0]

        # Calculate realistic churn probability based on risk factors
        logit = -1.8
        if contract == "Month-to-month":
            logit += 1.4
        elif contract == "Two year":
            logit -= 1.3
            
        if tenure < 12:
            logit += 0.8
        elif tenure > 48:
            logit -= 1.0

        if payment == "Electronic check":
            logit += 0.5
        if tech_support == "No" and internet != "No":
            logit += 0.4
        if support_tickets >= 3:
            logit += 0.9
        if monthly_charges > 80:
            logit += 0.4
        if senior == 1:
            logit += 0.2

        prob = 1 / (1 + np.exp(-logit))
        churn = 1 if random.random() < prob else 0

        churn_reasons = [
            "Competitor offered better price",
            "Customer dissatisfaction with support response time",
            "Service reliability and speed issues",
            "Relocation to uncovered service area",
            "Price increase after promotional period",
            "Switched to bundled streaming package",
        ]
        churn_reason = random.choice(churn_reasons) if churn == 1 else "Active Subscriber"

        rows.append({
            "customer_id": cust_id,
            "gender": gender,
            "senior_citizen": senior,
            "partner": partner,
            "dependents": dependents,
            "tenure_months": tenure,
            "phone_service": "Yes",
            "internet_service": internet,
            "online_security": online_security,
            "tech_support": tech_support,
            "contract_type": contract,
            "paperless_billing": paperless,
            "payment_method": payment,
            "support_tickets": support_tickets,
            "monthly_charges": monthly_charges,
            "total_charges": total_charges,
            "churn": churn,
            "churn_reason": churn_reason,
        })

    df = pd.DataFrame(rows)
    return df


def generate_saas_metrics(num_months=36) -> pd.DataFrame:
    """Generate 36 months of monthly SaaS metrics for time-series forecasting."""
    start_date = datetime(2022, 1, 1)
    base_mrr = 45000.0
    growth_rate = 0.035

    rows = []
    current_mrr = base_mrr
    current_customers = 180

    for m in range(num_months):
        dt = start_date + timedelta(days=int(m * 30.4375))
        
        # Add trend + seasonality + random noise
        seasonal_factor = 1.0 + 0.08 * np.sin(2 * np.pi * dt.month / 12) + (0.05 if dt.month == 12 else 0.0)
        noise = np.random.normal(0, 0.02)
        growth = (growth_rate + noise) * seasonal_factor
        current_mrr = current_mrr * (1 + growth)

        new_cust = max(5, int(15 + m * 0.8 + np.random.normal(0, 3)))
        churned_cust = max(1, int(current_customers * random.uniform(0.015, 0.035)))
        current_customers = current_customers + new_cust - churned_cust

        arpu = round(current_mrr / max(1, current_customers), 2)
        arr = round(current_mrr * 12, 2)
        nrr = round(102.0 + np.random.normal(0, 2.5), 1)
        cac = round(320.0 + np.random.normal(0, 25), 2)
        operating_expense = round(current_mrr * random.uniform(0.60, 0.75), 2)
        net_profit = round(current_mrr - operating_expense, 2)

        rows.append({
            "date": dt.strftime("%Y-%m-%d"),
            "mrr": round(current_mrr, 2),
            "arr": arr,
            "active_customers": current_customers,
            "new_customers": new_cust,
            "churned_customers": churned_cust,
            "arpu": arpu,
            "net_revenue_retention_pct": nrr,
            "customer_acquisition_cost": cac,
            "operating_expense": operating_expense,
            "net_profit": net_profit,
        })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    ecom_df = generate_ecommerce_data()
    churn_df = generate_churn_data()
    saas_df = generate_saas_metrics()

    ecom_path = os.path.join(BASE_DIR, "sample_ecommerce_orders.csv")
    churn_path = os.path.join(BASE_DIR, "sample_telecom_churn.csv")
    saas_path = os.path.join(BASE_DIR, "sample_saas_metrics.csv")

    ecom_df.to_csv(ecom_path, index=False)
    churn_df.to_csv(churn_path, index=False)
    saas_df.to_csv(saas_path, index=False)

    print(f"Generated E-Commerce Orders: {len(ecom_df)} rows -> {ecom_path}")
    print(f"Generated Telecom Churn: {len(churn_df)} rows -> {churn_path}")
    print(f"Generated SaaS Time Series: {len(saas_df)} rows -> {saas_path}")
