# Business Profitability Dashboard

A retail analytics portfolio project exploring revenue, cost of goods sold, gross profit, and gross margin by month, product, region, and customer segment.

## Business questions

- Which products and categories generate the most gross profit?
- Which regions and customer segments have the strongest margins?
- How do revenue and gross profit change over time?
- Where are discounts associated with low margins or losses?

## Scope

The first version will include four metric cards, monthly trends, category and region charts, date and category filters, a product profitability table, and a CSV download.

Planned tools: Python, pandas, Plotly, Streamlit, GitHub, and Streamlit Community Cloud.

## Status

Day 1 setup is prepared. The starter app only displays the project scope; data preparation and analytics are scheduled for later days.

## Data plan

Use 500–1,000 clearly labeled synthetic retail transactions covering 12 months, in USD. No business findings have been calculated yet.

Expected columns: `order_id`, `date`, `product`, `category`, `region`, `customer_segment`, `quantity`, `unit_price`, `unit_cost`, `discount_pct`.

Each row will represent one product line within an order. Discounts use decimals, for example `0.10` for 10%. Order IDs may repeat across product lines.

## Metric definitions

- Revenue = quantity × unit price × (1 − discount_pct)
- Cost of goods sold = quantity × unit cost
- Gross profit = revenue − cost of goods sold
- Gross margin = total gross profit ÷ total revenue × 100

Show margin as unavailable when total revenue is zero. Aggregate margin is calculated from totals, not by averaging row margins. Gross profit excludes operating expenses, interest, and taxes. Discount associations do not establish causation.

## Run the starter app

In a Python environment, including GitHub Codespaces, open a terminal in this repository and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

In Codespaces, open port 8501 from the Ports tab. To stop the app, press Ctrl+C in its terminal.

## Project structure

```text
app.py                  Starter app; dashboard added on Day 6
requirements.txt        Python dependencies
data/README.md          Dataset specification
scripts/clean_data.py    Reserved cleaning-script entrypoint
screenshots/            Dashboard images added on Day 8
docs/10-day-plan.md      Daily milestones and completion checklist
```

## Findings and limitations

Findings will be added after data preparation and validation. Synthetic data supports a demonstration, not conclusions about a real company.
