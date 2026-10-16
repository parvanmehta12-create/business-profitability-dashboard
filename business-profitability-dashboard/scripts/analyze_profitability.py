"""Day 5: summarize the Day 4 dataset and write three sample-data findings.

Run: python scripts/analyze_profitability.py
Outputs: reports/*.csv and reports/business_findings.md.
Gross margin uses total gross profit / total revenue, never average row margins.
"""

import argparse
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZERO = Decimal(0)
CENT = Decimal("0.01")
MONEY = ["revenue", "cost_of_goods_sold", "gross_profit"]
GROUPS = ["month", "product", "category", "region", "customer_segment", "discount_band"]
BANDS = ["0%", ">0–10%", ">10–20%", ">20–30%", ">30–40%", ">40–100%"]


def fixed(value):
    return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


def margin(profit, revenue):
    return "" if revenue == 0 else fixed(profit / revenue * 100)


def band(discount):
    if discount == 0:
        return BANDS[0]
    for limit, label in zip(["0.10", "0.20", "0.30", "0.40", "1"], BANDS[1:]):
        if discount <= Decimal(limit):
            return label
    raise ValueError("Discount must lie between 0 and 1.")


def summarize(rows, dimension):
    groups = defaultdict(list)
    for row in rows:
        groups[row[dimension]].append(row)
    result = []
    for label, records in groups.items():
        totals = {key: sum((row[key] for row in records), ZERO) for key in MONEY}
        losses = [row for row in records if row["gross_profit"] < 0]
        result.append({
            dimension: label,
            "transaction_count": len(records),
            "units_sold": sum(row["quantity"] for row in records),
            **{key: fixed(value) for key, value in totals.items()},
            "gross_margin_pct": margin(totals["gross_profit"], totals["revenue"]),
            "loss_making_transactions": len(losses),
            "gross_loss_amount": fixed(-sum((row["gross_profit"] for row in losses), ZERO)),
        })
    if dimension == "month":
        return sorted(result, key=lambda row: row[dimension])
    if dimension == "discount_band":
        return sorted(result, key=lambda row: BANDS.index(row[dimension]))
    return sorted(result, key=lambda row: (-Decimal(row["gross_profit"]), row[dimension]))


def analyze(input_path, output_dir):
    input_path, output_dir = Path(input_path), Path(output_dir)
    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        needed = {"order_id", "date", "quantity", "discount_pct", *MONEY,
                  "product", "category", "region", "customer_segment"}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError("Missing required columns. Use data/sales_profitability.csv from Day 4.")
        rows = list(reader)
    if not rows:
        raise ValueError("Input contains no transactions.")
    from datetime import date
    ids = set()
    for row in rows:
        if not row["order_id"] or row["order_id"] in ids:
            raise ValueError("Missing or duplicate order IDs in this single-product sample.")
        ids.add(row["order_id"])
        row["month"] = date.fromisoformat(row["date"]).strftime("%Y-%m")
        for field in MONEY + ["quantity", "discount_pct"]:
            row[field] = Decimal(row[field])
            if not row[field].is_finite():
                raise ValueError(f"Non-finite {field}.")
        if row["quantity"] <= 0 or row["quantity"] != row["quantity"].to_integral_value():
            raise ValueError("Quantity must be a positive integer.")
        row["quantity"] = int(row["quantity"])
        if not ZERO <= row["discount_pct"] <= 1:
            raise ValueError("Discount must be between 0 and 1.")
        if row["revenue"] < 0 or row["cost_of_goods_sold"] < 0:
            raise ValueError("Negative revenue or cost is outside this sample's scope.")
        if row["revenue"] - row["cost_of_goods_sold"] != row["gross_profit"]:
            raise ValueError("Transaction revenue minus cost does not equal gross profit.")
        for field in ["product", "category", "region", "customer_segment"]:
            if not row[field].strip():
                raise ValueError(f"Missing {field}.")
        row["discount_band"] = band(row["discount_pct"])

    totals = {key: sum((row[key] for row in rows), ZERO) for key in MONEY}
    summaries = {dimension: summarize(rows, dimension) for dimension in GROUPS}
    for dimension, records in summaries.items():
        for field in MONEY:
            if sum((Decimal(record[field]) for record in records), ZERO) != totals[field]:
                raise ValueError(f"{dimension} {field} fails reconciliation.")
        if sum(record["transaction_count"] for record in records) != len(rows):
            raise ValueError(f"{dimension} count fails reconciliation.")

    cash = lambda value: f"${Decimal(value):,.2f}"
    categories = summaries["category"]
    top = categories[0]
    share = "unavailable" if totals["gross_profit"] == 0 else fixed(Decimal(top["gross_profit"]) / totals["gross_profit"] * 100) + "%"
    products = summaries["product"]
    loss_count = sum(row["gross_profit"] < 0 for row in rows)
    gross_loss = -sum((row["gross_profit"] for row in rows if row["gross_profit"] < 0), ZERO)
    regions_with_margin = [row for row in summaries["region"] if row["gross_margin_pct"] != ""]
    strongest = max(regions_with_margin, key=lambda row: Decimal(row["gross_margin_pct"]), default=None)
    region_finding = (
        f"{strongest['region']} has the highest regional gross margin at {strongest['gross_margin_pct']}%, "
        f"on {cash(strongest['revenue'])} of revenue and {cash(strongest['gross_profit'])} of gross profit."
        if strongest else "Regional gross margins are unavailable because revenue is zero."
    )
    text = [
        "# Retail profitability findings", "",
        "Synthetic sample, January–December 2025. Currency: USD. Findings describe generated transactions, not a real business.", "",
        "## Overall results", "",
        f"{len(rows):,} transactions generated {cash(totals['revenue'])} in revenue, {cash(totals['cost_of_goods_sold'])} in cost of goods sold, and {cash(totals['gross_profit'])} in gross profit. Overall gross margin is {margin(totals['gross_profit'], totals['revenue']) or 'unavailable'}%.", "",
        "## Three findings", "",
        f"1. **{top['category']} contributes the most category gross profit:** {cash(top['gross_profit'])}, or {share} of total gross profit. Its margin is {top['gross_margin_pct'] or 'unavailable'}%. Compare category volume and margins before interpreting the ranking.",
        f"2. **{loss_count} transactions make a gross loss:** their combined gross loss is {cash(gross_loss)}. Those losses are already included in overall gross profit and must not be subtracted again. Product totals can remain positive despite individual loss-making orders.",
        f"3. **Regional margin comparison:** {region_finding} This comparison is descriptive and may reflect product, customer, and discount mix.", "",
        "## Top five products by gross profit", "",
        "| Product | Revenue | Gross profit | Gross margin |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in products[:5]:
        text.append(f"| {row['product']} | {cash(row['revenue'])} | {cash(row['gross_profit'])} | {row['gross_margin_pct'] or 'unavailable'}% |")
    text += ["", "## Discount comparison", "",
             "Bands are mutually exclusive: >0–10% excludes 0% and includes 10%. Compare margins and loss counts in discount_summary.csv. Higher discounts mechanically reduce revenue at a fixed price and quantity. This sample cannot estimate demand responses or prove a causal effect.", "",
             "## Interpretation and next steps", "",
             "Inspect loss-making product and discount combinations before proposing changes. A real business would also need operating expenses, returns, customer retention, and demand evidence. Monthly order counts and higher late-year discounts were deliberately built into the generator. Do not present these patterns as discoveries about the retail market.", "",
             "All six summary tables reconcile to source revenue, cost, gross profit, and transaction count. Aggregate margins are recalculated from totals. Gross profit excludes operating expenses, interest, and taxes.", ""]
    output_dir.mkdir(parents=True, exist_ok=True)
    names = {"month": "monthly", "customer_segment": "customer_segment", "discount_band": "discount"}
    for dimension, records in summaries.items():
        path = output_dir / f"{names.get(dimension, dimension)}_summary.csv"
        if path.resolve() == input_path.resolve():
            raise ValueError("Input must differ from output files.")
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    (output_dir / "business_findings.md").write_text("\n".join(text), encoding="utf-8")
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "sales_profitability.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    try:
        summaries = analyze(args.input, args.output_dir)
    except (ValueError, OSError, InvalidOperation, csv.Error) as error:
        parser.exit(1, f"Analysis failed: {error}\n")
    print("Created six summary tables and business_findings.md.")
    print("PASS: all summary counts, revenue, cost, and gross profit reconcile to source.")
    for dimension, records in summaries.items():
        print(f"  {dimension}: {len(records)} groups")
    print(f"Reports saved in {args.output_dir}")


if __name__ == "__main__":
    main()
