"""Day 8: verify the dashboard and save a repeatable QA report.

Run from the inner project folder: python scripts/verify_dashboard.py
Uses the existing Streamlit, pandas, and Plotly dependencies. Does not alter data.
"""

import argparse
import csv
import hashlib
import io
import runpy
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def verify(app_path, output_dir):
    app_path, output_dir = Path(app_path).resolve(), Path(output_dir)
    checks = []

    def check(condition, description):
        if not condition:
            raise AssertionError(description)
        checks.append(description)
        print(f"PASS: {description}")

    source = app_path.parent / "data" / "sales_profitability.csv"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    app = runpy.run_path(str(app_path))
    data = app["load_data"](source)
    expected = {"revenue_cents": 38528635, "cost_of_goods_sold_cents": 30530359,
                "gross_profit_cents": 7998276}
    check(len(data) == 1000 and all(int(data[field].sum()) == value for field, value in expected.items()),
          "Full dataset: 1,000 orders; revenue $385,286.35; cost $305,303.59; gross profit $79,982.76")
    for dimension in ["month", "category", "region"]:
        grouped = app["grouped_totals"](data, dimension)
        check(all(int(grouped[field].sum()) == value for field, value in expected.items()),
              f"{dimension.title()} chart totals reconcile to source")

    start, end = date(2025, 1, 1), date(2025, 3, 31)
    filtered = app["filter_transactions"](data, start, end, ["East"], ["Furniture"])
    check(len(filtered) == 18 and int(filtered.revenue_cents.sum()) == 1238350
          and int(filtered.cost_of_goods_sold_cents.sum()) == 959814
          and int(filtered.gross_profit_cents.sum()) == 278536,
          "Q1 + East + Furniture: 18 orders, revenue $12,383.50, cost $9,598.14, gross profit $2,785.36")
    products = app["product_summary"](filtered)
    check(int(products.transactions.sum()) == 18
          and int(products.revenue_cents.sum()) == 1238350
          and int(products.gross_profit_cents.sum()) == 278536,
          "Filtered product table reconciles to filtered transactions")
    expected_margins = [None if row.revenue_cents == 0 else float(
        Decimal(int(row.gross_profit_cents)) / Decimal(int(row.revenue_cents)) * 100
    ) for row in products.itertuples()]
    check(list(products.gross_margin_pct) == expected_margins,
          "Product margins use aggregate profit divided by aggregate revenue")

    downloaded = list(csv.DictReader(io.StringIO(app["transaction_csv"](filtered).decode("utf-8"))))
    check(len(downloaded) == 18
          and {row["order_id"] for row in downloaded} == set(filtered.order_id)
          and sum(Decimal(row["revenue"]) for row in downloaded) == Decimal("12383.50")
          and all(row["region"] == "East" and row["category"] == "Furniture"
                  and start <= date.fromisoformat(row["date"]) <= end for row in downloaded),
          "CSV export contains exactly the filtered 18 orders and matching revenue")
    check(not any(field == "month" or field.endswith("_cents") for field in downloaded[0]),
          "CSV export excludes internal calculation columns")
    day = date(2025, 1, 1)
    single_day = app["filter_transactions"](data, day, day, sorted(data.region.unique()), sorted(data.category.unique()))
    check(len(single_day) == int((data.date.dt.date == day).sum()) and len(single_day) > 0,
          "Date range includes both endpoints, including a one-day range")

    at = AppTest.from_file(str(app_path)).run(timeout=60)
    check(not at.exception, "Dashboard starts without a Streamlit exception")
    check([metric.value for metric in at.metric] == ["$385,286.35", "$305,303.59", "$79,982.76", "20.76%"],
          "All four default metric cards match the verified financial results")
    check(len(at.get("plotly_chart")) == 3 and len(at.dataframe) == 1
          and len(at.get("download_button")) == 1,
          "Dashboard contains three charts, a product table, and a download button")
    at.multiselect(key="region_filter").set_value(["East"])
    at.multiselect(key="category_filter").set_value(["Furniture"])
    at.date_input(key="date_filter").set_value((start, end))
    at.run(timeout=30)
    check(not at.exception and [metric.value for metric in at.metric]
          == ["$12,383.50", "$9,598.14", "$2,785.36", "22.49%"],
          "Changing all three sidebar filters updates the displayed metric cards")
    check(set(at.dataframe[0].value["product"]) == set(products["product"]),
          "Displayed product table follows the sidebar filters")
    at.multiselect(key="region_filter").set_value([])
    at.run(timeout=30)
    check(not at.exception and len(at.info) == 1 and len(at.metric) == 0
          and len(at.get("plotly_chart")) == 0 and len(at.get("download_button")) == 0,
          "Empty selection shows guidance and removes stale metrics, charts, and download")
    at.multiselect(key="region_filter").set_value(["East"])
    at.date_input(key="date_filter").set_value((start,))
    at.run(timeout=30)
    check(not at.exception and len(at.info) == 1 and len(at.metric) == 0,
          "Incomplete date selection is handled without an exception")
    check(hashlib.sha256(source.read_bytes()).hexdigest() == before,
          "QA run leaves the source transaction file unchanged")

    output_dir.mkdir(parents=True, exist_ok=True)
    report = ["# Dashboard QA report", "",
              f"Run time (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
              f"App SHA-256: {hashlib.sha256(app_path.read_bytes()).hexdigest()}",
              f"Source data SHA-256: {before}", "",
              f"All {len(checks)} automated checks passed.", ""]
    report += [f"- PASS: {description}" for description in checks]
    report += ["", "## Browser checks still required", "",
               "- Confirm chart labels, legends, and colors are readable at your browser size.",
               "- Click Download filtered transactions (CSV) and open the downloaded file.",
               "- Save screenshots of the full dashboard and the Q1/East/Furniture selection.",
               "", "Automated checks validate exported CSV content and button presence. They do not click a real browser download or verify visual layout.", ""]
    path = output_dir / "dashboard_qa.md"
    path.write_text("\n".join(report), encoding="utf-8")
    print(f"\nAll {len(checks)} automated checks passed. Report: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=ROOT / "app.py")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    try:
        verify(args.app, args.output_dir)
    except Exception as error:
        parser.exit(1, f"Dashboard verification failed: {error}\nNo new PASS report was written.\n")
