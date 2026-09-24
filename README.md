# Sales & Inventory Analytics + Demand Prediction System

An end-to-end data engineering and machine learning project simulating one year of transactions for a single-store household grocery business, built to analyze sales, predict future demand, and recommend inventory restocking — from raw data generation through a live database, SQL analytics, and a trained ML model.

This project was built as a fully self-contained, interview-defensible portfolio piece: every design decision — from schema normalization to feature engineering to model selection — was made deliberately and can be explained and justified.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Setup & Installation](#setup--installation)
- [Database Schema](#database-schema)
- [Key SQL Queries](#key-sql-queries)
- [Key Algorithms](#key-algorithms)
- [Machine Learning](#machine-learning)
- [Inventory Recommendation Engine](#inventory-recommendation-engine)
- [Testing Strategy](#testing-strategy)
- [Ground-Truth Validation](#ground-truth-validation)
- [Known Limitations](#known-limitations)

---

## Project Overview

**Goal:** Given historical sales and inventory data, identify best-sellers, declining products, revenue trends, and low-stock risk — and predict future daily demand per product to generate data-driven restock recommendations.

**Scope:** 20 products across 6 categories (Rice & Grains, Pulses & Lentils, Masalas & Spices, Dry Fruits & Nuts, Cooking Oils & Ghee, Sugar/Salt & Sweeteners), 200 customers, 6 suppliers, one full year (2025) of daily transaction history — roughly 6,900 orders and 24,900 order line items.

**Core tech:** Python, SQL (MySQL), Pandas, NumPy, Scikit-learn, SQLAlchemy, pytest.

**Pipeline:**
```
Synthetic Data Generation → Messiness Injection → Ingestion & Cleaning (Pandas)
        → Normalized MySQL Database → SQL Analytics
        → ML Feature Engineering → Model Training & Evaluation
        → Inventory Recommendation Engine
```

A defining design choice: the dataset is **synthetic but built with a known ground truth**. Each product was assigned a deliberate demand personality (steady, trending up/down, seasonal-spike, or erratic) with an explicit mathematical formula. This meant every downstream phase — analytics, ML, inventory logic — could be validated against a known answer, not just trusted blindly. See [Ground-Truth Validation](#ground-truth-validation).

---

## Architecture

The project is organized as a linear pipeline, with each stage's output feeding the next:

1. **Data Generation** (`config/`, `data/`) — a parameterized demand-simulation function generates a full year of daily transactions per product, respecting each product's designed trend/seasonality/noise, then deliberately injects realistic messiness (missing values, duplicates, malformed dates, price inconsistencies).
2. **Database** (`db/`) — a normalized (3NF) MySQL schema with enforced foreign keys and indexes, built and deployed via a single `schema.sql`.
3. **Ingestion & Cleaning** (`processing/`) — a Pandas pipeline that profiles the raw data (quantifying every issue), cleans it (justified strategy per issue type), validates the result, and loads it into MySQL.
4. **Analytics** (`analytics/`) — a SQL-driven reporting module answering concrete business questions: best-sellers, category performance, monthly revenue trends, product-level growth/decline, low-stock risk, and customer/region breakdowns.
5. **ML Pipeline** (`ml/`) — feature engineering (calendar features, lag/rolling demand features, one-hot product identity) with a strict chronological train/test split, followed by baseline, Linear Regression, Random Forest, and Gradient Boosting model training and evaluation.
6. **Inventory Engine** (`inventory/`) — uses the trained model to forecast near-term demand per product, derives a personality-aware reorder point, and recommends a 30-day-coverage order quantity once triggered.
7. **Tests** (`tests/`) — 17 automated pytest tests covering data generation edge cases, ML leakage prevention, database referential integrity, and analytics correctness.

---

## Folder Structure

```
sales_analytics/
├── config/          # Static seed/config data: products, categories, suppliers, customers, inventory
├── data/            # Data generation logic: demand simulation, order splitting, basket assembly, CSV I/O, messiness injection
├── db/              # Database connection, schema DDL, and data-loading scripts
├── processing/      # Data profiling and cleaning pipeline
├── analytics/       # SQL query runner and business analytics functions
├── ml/              # Feature engineering and model training/evaluation
├── inventory/        # Demand forecasting and reorder recommendation logic
├── tests/           # Automated test suite (pytest)
├── main.py          # Orchestrates full synthetic dataset generation
├── requirements.txt
└── .gitignore
```

Each folder has a single, clear responsibility — `data/` doesn't know about SQL, `ml/` doesn't know how data was cleaned. This separation was deliberate, matching the same principle used to justify database normalization.

---

## Setup & Installation

**Prerequisites:** Python 3.12+, MySQL (tested with MySQL 9.x via Homebrew), pip.

```bash
# 1. Clone the repo
git clone https://github.com/sivasaladi2006/sales_analytics.git
cd sales_analytics

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up the database
mysql -u root -p -e "CREATE DATABASE sales_analytics_db;"
mysql -u root -p sales_analytics_db < db/schema.sql

# 5. Configure credentials
# Create a .env file in the project root:
#   DB_USER=root
#   DB_PASSWORD=your_password
#   DB_HOST=localhost
#   DB_NAME=sales_analytics_db

# 6. Generate the synthetic dataset
python3 main.py
python3 -m data.inject_messiness

# 7. Load everything into MySQL (seed data + cleaned transactions)
python3 -m db.load_data

# 8. Run the analytics report
python3 -m analytics.sales_analysis

# 9. Train the ML model
python3 -m ml.train_model

# 10. Generate inventory recommendations
python3 -m inventory.forecast

# 11. Run the test suite
python3 -m pytest tests/ -v
```

---

## Database Schema

A normalized (1NF → 3NF) relational schema, 7 tables:

```sql
categories(category_id PK, category_name)
suppliers(supplier_id PK, name, contact_info)
products(product_id PK, product_name, category_id FK, supplier_id FK, unit_price)
customers(customer_id PK, name, region)
orders(order_id PK, customer_id FK, order_date)
order_items(order_item_id PK, order_id FK, product_id FK, quantity, unit_price_at_order)
inventory(product_id PK/FK, stock_available, last_restocked_date)
```

**Key design decisions:**

- **`unit_price_at_order` is separate from `products.unit_price`.** A product's catalog price changes over time, but a completed order is a historical record — it must reflect what the customer was actually charged at the time of purchase, not the current price. Storing them separately prevents a future price change from silently rewriting past transactions.
- **`order_items` exists instead of flattening into `orders`.** One order can contain multiple products (a "basket"). Flattening would either repeat customer/date data per product line (violating 3NF, risking update anomalies) or force non-atomic values into one row (violating 1NF).
- **`inventory.product_id` is both primary key and foreign key**, rather than a separate surrogate ID. The relationship between a product and its inventory record is strictly one-to-one; reusing `product_id` as the PK lets the database itself enforce that constraint, rather than relying on application logic.
- **`DECIMAL(10,2)`, not `FLOAT`, for all money and quantity columns.** Floating-point types can't represent decimal fractions exactly, risking rounding errors that compound across many transactions — unacceptable for financial and inventory data.
- **Indexes** on `orders.order_date` and `inventory.stock_available` — added deliberately, tied to actual query patterns (date-range filtering is used throughout analytics/ML; low-stock filtering is a named requirement), not applied blanket across every column. Foreign key columns are auto-indexed by MySQL/InnoDB.

---

## Key SQL Queries

**Best-sellers by revenue:**
```sql
SELECT p.product_name,
       SUM(oi.quantity) AS total_quantity_sold,
       SUM(oi.quantity * oi.unit_price_at_order) AS total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY total_revenue DESC;
```

**Product trend analysis (Q1 vs Q4, conditional aggregation):**
```sql
SELECT p.product_name,
       SUM(CASE WHEN o.order_date < '2025-04-01' THEN oi.quantity ELSE 0 END) AS q1_quantity,
       SUM(CASE WHEN o.order_date >= '2025-10-01' THEN oi.quantity ELSE 0 END) AS q4_quantity
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name;
```

**Low-stock risk (days of stock remaining):**
```sql
SELECT p.product_id, p.product_name, i.stock_available,
       SUM(oi.quantity) / 30 AS avg_daily_demand_recent
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN inventory i ON p.product_id = i.product_id
WHERE o.order_date >= '2025-12-01'
GROUP BY p.product_id, p.product_name, i.stock_available;
-- days_of_stock_remaining = stock_available / avg_daily_demand_recent
```

Full analytics module: `analytics/sales_analysis.py` (8 functions covering best-sellers, category performance, monthly revenue trends, product trends, low-stock risk, region performance, top customers, and a consolidated report).

---

## Key Algorithms

**Demand simulation (`data/generate_demand.py`):** a single parameterized function drives all five demand personalities (steady, trending, seasonal-spike, erratic), rather than one function per personality — an application of the Open/Closed Principle, so adding a new personality only requires new parameter values, not new code.

```
daily_quantity = base_demand × trend_factor × seasonal_factor × noise_factor
```
with an independent zero-order-day probability check for erratic products (modeling real intermittent demand, not just wide noise).

**Order/basket assembly (`data/create_order.py`, `data/split_quantity.py`):** a day's total demand for a product is split into a random number of positive parts (via weighted proportional splitting with a rounding-drift correction), then each part is assigned to an existing open order (if it has fewer than 4 items and doesn't already contain that product) or a new order with a random customer — simulating realistic multi-item shopping baskets rather than one order per product per day.

**Chronological train/test split (`ml/build_features.py`):** rather than a random shuffle, the data is split strictly by date — train on everything before a cutoff, test on everything after. A random split would let the model implicitly "see the future" via lag/rolling features computed from later dates leaking into earlier training rows — a well-known, serious mistake for time-series data.

---

## Machine Learning

**Problem framing:** predict daily demand quantity, per product, per day (not weekly or category-level) — matching the granularity of the underlying data generation and giving enough data points (7,300 product-days) for training.

**Features (27 total):** `day_of_week`, `month`, `is_weekend`, `is_festival_season`, `quantity_lag_1`, `quantity_lag_7`, `quantity_rolling_7`, plus 20 one-hot encoded product identity columns.

**Leakage prevention:**
- Chronological split (train ≤ Nov 14 2025, test ≥ Nov 15 2025) — automatically verified with a `pytest` assertion that dates never overlap.
- Rolling averages are shifted by one day before the window is applied, so a day's rolling feature never includes that day's own value.
- The target column is asserted absent from the feature list.
- The first 7 days of each product's history are dropped (insufficient lag history to compute safely) rather than filled with fabricated values.

**Model comparison** (test set, Nov 15 – Dec 31 2025):

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Mean Baseline | 3.359 | 4.058 | -0.029 |
| Naive Lag Baseline (yesterday = today) | 0.642 | 1.019 | 0.935 |
| Linear Regression | 0.613 | 1.005 | 0.937 |
| Random Forest (default) | 0.737 | 1.115 | 0.922 |
| **Random Forest (tuned: max_depth=6, min_samples_leaf=5)** | **0.557** | **0.871** | **0.953** |
| Gradient Boosting (default) | 0.619 | 0.928 | 0.946 |
| Gradient Boosting (tuned: n=200, lr=0.05) | 0.580 | 0.883 | 0.951 |

**Winner: tuned Random Forest.** An initial unconstrained Random Forest run actually *underperformed* Linear Regression — a real, useful signal of overfitting, not a modeling mistake. A small hyperparameter sweep across `max_depth` and `min_samples_leaf` confirmed the hypothesis: shallower trees generalized better up to a point (`max_depth=6`), after which performance degraded again (`max_depth=4`) — a clean empirical demonstration of the bias-variance tradeoff. Gradient Boosting was tuned with equal effort but didn't surpass the tuned Random Forest.

**Feature importance:** `quantity_lag_1` (65%) and `quantity_rolling_7` (34%) account for ~99% of the trained model's decision-making; explicit calendar features (`is_festival_season`, `month`) contributed under 1% combined. This makes sense on reflection — since lag features are built from a product's own recent actual sales, they implicitly absorb seasonal and trend shifts as they happen, without needing an explicit calendar signal to tell the model "this is festival season."

**Model persistence:** the final tuned Random Forest is saved via `joblib` (`ml/models/demand_model.joblib`), alongside its exact feature column order, so it can be reloaded for inference without retraining.

---

## Inventory Recommendation Engine

Combines the trained model's predictions with current stock to generate restock recommendations, following an (s, Q) reorder-point policy:

- **Reorder point (s):** `predicted_daily_demand × 7 days`, computed per product from that product's own latest model prediction — so the threshold is naturally personality-aware (a high-volume steady product gets a higher threshold than a low-volume erratic one) without any hardcoded lookup table.
- **Order quantity (Q), once triggered:** sized to cover 30 days of predicted demand minus current stock, rounded to the nearest practical purchase unit.
- **Erratic-demand flag:** products with a non-zero `zero_order_prob` (intermittent, spiky demand) are explicitly flagged in the output — an honest acknowledgment that averaging-based forecasts are known to be less reliable for intermittent demand, and such recommendations warrant manual review rather than blind trust.

Cross-validated against the independent Phase 5 SQL-based low-stock analysis: both approaches — one purely statistical, one ML-driven — independently flagged the same two products (Jaggery, Rajma) as highest-risk, both correctly tied to their designed winter-seasonal demand spike outpacing a static randomly-assigned stock level.

---

## Testing Strategy

17 automated tests (`pytest`), organized by concern rather than by file count for its own sake:

- **`test_generate_demand.py`** (3 tests) — non-negative output under heavy noise, guaranteed-zero behavior at `zero_order_prob=1.0`, measurable seasonal multiplier effect.
- **`test_split_quantity.py`** (4 tests) — parts always sum to the original total, all parts always positive, correct `ValueError` on invalid input, buyer count never exceeds the configured maximum.
- **`test_ml_pipeline.py`** (3 tests) — train/test dates never overlap, lag features exactly match actual prior-day values (not just "close"), the target column is never present among the features.
- **`test_db_integrity.py`** (3 tests) — an invalid foreign key insert is rejected by the database, every product references a real category, every order item references a real order.
- **`test_analytics.py`** (4 tests) — correct row counts per aggregation level, all revenue values positive, and a cross-check that product-level and category-level revenue totals reconcile exactly (catching a broken JOIN in either query).

```bash
python3 -m pytest tests/ -v
# 17 passed
```

---

## Ground-Truth Validation

Because the dataset was generated with known, deliberate demand parameters, every later phase's findings could be checked against a known answer — not just assumed correct:

| Product | Designed (Phase 2) | Found in Analytics (Phase 5) |
|---|---|---|
| Basmati Rice | trend +0.4 | Q1→Q4 quantity +32.4% |
| Cashew Nuts | trend +0.5 | Q1→Q4 quantity +39.1% |
| Groundnut Oil | trend −0.3 | Q1→Q4 quantity −21.3% |
| Iodized Salt | trend −0.2 | Q1→Q4 quantity −14.3% |
| Ghee / Almonds / Biryani Masala | seasonal ×3.5, Oct–Nov | Oct–Nov revenue +~30% overall |
| Steady products (Rice, Dal, Oil, etc.) | trend 0.0 | Q1→Q4 within ±3% |

Every non-seasonal product's measured direction and rough magnitude matched its designed trend parameter. This gave real confidence that later ML findings reflected genuine signal in the pipeline, not artifacts of a broken data path.

---

## Known Limitations

- **Recursive forecasting compounds error over the horizon.** Multi-day-ahead predictions feed each day's prediction into the next day's lag features; small errors can accumulate. Appropriate for the 7-day lead time used here, but not validated for much longer horizons.
- **Erratic/intermittent-demand products are poorly served by averaging-based forecasting.** A product like Rock Salt alternates between zero-demand days and demand spikes; a smoothed daily average doesn't describe any real day. A specialized method (e.g., Croston's method) would be more appropriate — flagged in the output rather than implemented, given project scope.
- **7-day lead time and 30-day order coverage are placeholder assumptions**, not derived from real supplier delivery data (which the dataset doesn't model). A production system would calibrate these per supplier/category.
- **Revenue scale reflects 20 products carrying the volume a real store would spread across hundreds of SKUs** — a known simplification of concentrating full-category demand into one representative product per category, rather than a data error.