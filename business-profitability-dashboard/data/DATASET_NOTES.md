# Synthetic retail sales dataset

## Source and scope

`sales.csv` is generated sample data for this portfolio project, not records from a real company or an external dataset. All prices, costs, distributions, and patterns are invented assumptions. Currency is USD. The reporting period is January–December 2025.

There are exactly 1,000 rows, 12 products, 3 categories, 4 regions, and 3 customer segments. Each row represents a single-product order in this first dataset. The unique order IDs simplify Day 3 validation. Future multi-product datasets may repeat order IDs and will require line identifiers for duplicate checks.

## Data dictionary

| Column | Type | Definition |
| --- | --- | --- |
| order_id | Text | Unique order ID, ORD00001 through ORD01000 |
| date | Date text | Order date in YYYY-MM-DD format |
| product | Text | One of 12 products defined in the generator |
| category | Text | Furniture, Technology, or Office Supplies |
| region | Text | East, West, Central, or South |
| customer_segment | Text | Consumer, Small Business, or Corporate |
| quantity | Integer | Units sold, always positive |
| unit_price | Decimal | USD per unit before discount |
| unit_cost | Decimal | USD cost of goods sold per unit |
| discount_pct | Decimal | Fraction of price discounted: 0.10 means 10% |

## Generation assumptions

- Reproducible Python generator: `scripts/generate_data.py`, random seed 42. Uses only the standard library. Running it overwrites `data/sales.csv` with the same sample under the same Python runtime.
- Orders per month: 65, 60, 70, 70, 75, 80, 80, 85, 90, 95, 110, 120. Higher late-year activity is deliberately built in and must not be presented as a discovered market trend.
- Products are sampled uniformly from the 12-product catalog in the generator. Product list prices remain fixed. Unit costs vary by ±5% around each product's assumed base cost, then round to cents.
- Region sampling weights: East 30%, West 28%, Central 24%, South 18%. Segment weights: Consumer 45%, Small Business 35%, Corporate 20%. Actual sample shares may differ.
- Quantities are uniformly sampled from 1–4 units for Consumers, 1–7 for Small Businesses, and 1–12 for Corporate buyers.
- Base discounts of 0%, 5%, 10%, 15%, 20%, 30%, and 40% use weights of 35%, 20%, 18%, 10%, 8%, 6%, and 3%. November and December add 5 percentage points, capped at 40%.
- Some high-discount sales have negative gross profit. These are valid transactions to analyze, not data errors.
- Dates are sampled within each month, then rows are sorted chronologically and assigned unique IDs.
- No missing values, duplicate orders, returns, taxes, shipping, operating expenses, or inflation are intentionally included. Day 3 will still validate the data. Do not invent cleaning corrections when none are required.

## Profitability calculations for Day 4

Revenue = quantity × unit_price × (1 − discount_pct).

Cost of goods sold = quantity × unit_cost.

Gross profit = revenue − cost of goods sold.

Overall gross margin = total gross profit ÷ total revenue × 100. Do not average row margins. A zero revenue denominator makes margin unavailable.

Discount effects are partly mechanical in this generated data. The sample cannot establish causal effects on demand, estimate price elasticity, or support real-company recommendations.
