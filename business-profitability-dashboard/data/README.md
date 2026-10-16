# Dataset specification

Day 2 will add `sales.csv`: 500–1,000 synthetic retail product-line transactions covering 12 months in USD. Day 3 will generate `sales_clean.csv`. Neither file exists yet.

| Column | Meaning | Example |
| --- | --- | --- |
| order_id | Order identifier; may repeat for different lines | ORD001 |
| date | Transaction date, YYYY-MM-DD | 2025-01-15 |
| product | Product name | Office Chair |
| category | Product category | Furniture |
| region | Sales region | East |
| customer_segment | Customer group | Small Business |
| quantity | Positive integer units | 2 |
| unit_price | Price per unit before discount, USD | 150.00 |
| unit_cost | Cost per unit, USD | 90.00 |
| discount_pct | Discount fraction between 0 and 1 | 0.10 |

Example check: 2 units at $150, with a 10% discount and $90 unit cost, produce $270 revenue, $180 cost of goods sold, $90 gross profit, and 33.33% gross margin.

Document generation assumptions and the random seed when adding synthetic data. Do not upload confidential customer or employer data.
