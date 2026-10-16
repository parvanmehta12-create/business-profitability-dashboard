# Dashboard QA report

Run time (UTC): 2026-10-16T23:48:59+00:00
App SHA-256: 3ecfe23392df0d4c1efd241fea424a3e9f7db3c911355ef5ac36714f02d1ac7e
Source data SHA-256: 1943f91d553d4411452417b26c8d83de5d3f5d708422c112dbd16229f31571a8

All 18 automated checks passed.

- PASS: Full dataset: 1,000 orders; revenue $385,286.35; cost $305,303.59; gross profit $79,982.76
- PASS: Month chart totals reconcile to source
- PASS: Category chart totals reconcile to source
- PASS: Region chart totals reconcile to source
- PASS: Q1 + East + Furniture: 18 orders, revenue $12,383.50, cost $9,598.14, gross profit $2,785.36
- PASS: Filtered product table reconciles to filtered transactions
- PASS: Product margins use aggregate profit divided by aggregate revenue
- PASS: CSV export contains exactly the filtered 18 orders and matching revenue
- PASS: CSV export excludes internal calculation columns
- PASS: Date range includes both endpoints, including a one-day range
- PASS: Dashboard starts without a Streamlit exception
- PASS: All four default metric cards match the verified financial results
- PASS: Dashboard contains three charts, a product table, and a download button
- PASS: Changing all three sidebar filters updates the displayed metric cards
- PASS: Displayed product table follows the sidebar filters
- PASS: Empty selection shows guidance and removes stale metrics, charts, and download
- PASS: Incomplete date selection is handled without an exception
- PASS: QA run leaves the source transaction file unchanged

## Browser checks still required

- Confirm chart labels, legends, and colors are readable at your browser size.
- Click Download filtered transactions (CSV) and open the downloaded file.
- Save screenshots of the full dashboard and the Q1/East/Furniture selection.

Automated checks validate exported CSV content and button presence. They do not click a real browser download or verify visual layout.
