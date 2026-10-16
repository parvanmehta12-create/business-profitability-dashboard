"""Day 4: calculate gross profitability from validated single-product orders.

Run: python scripts/calculate_profitability.py
Money uses Decimal, with revenue rounded to cents per transaction (half up).
Margin percentages use 0–100 units: 25.00 means 25%, not 0.25.
Original and cleaned input files are never overwritten.
"""

import argparse
import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENT = Decimal("0.01")
HUNDRED = Decimal("100")
REQUIRED = {"order_id", "quantity", "unit_price", "unit_cost", "discount_pct"}
ADDED = ["revenue", "cost_of_goods_sold", "gross_profit", "gross_margin_pct"]


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def number(value, field, row_number):
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"CSV row {row_number}: invalid {field}") from None
    if not result.is_finite():
        raise ValueError(f"CSV row {row_number}: non-finite {field}")
    return result


def calculate(input_path, output_dir):
    input_path, output_dir = Path(input_path), Path(output_dir)
    targets = [output_dir / name for name in (
        "sales_profitability.csv", "profitability_summary.json", "profitability_spot_checks.csv"
    )]
    if input_path.resolve() in [path.resolve() for path in targets]:
        raise ValueError("Input must differ from output files.")
    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if not REQUIRED.issubset(fields):
            raise ValueError(f"Missing columns: {sorted(REQUIRED - set(fields))}")
        if set(ADDED) & set(fields):
            raise ValueError("Input already includes profitability columns. Use sales_clean.csv.")
        rows = list(reader)
    if not rows:
        raise ValueError("Input contains no transactions.")

    total_revenue = Decimal(0)
    total_cost = Decimal(0)
    total_profit = Decimal(0)
    order_ids = set()
    losses = 0
    zero_revenue = 0
    for row_number, row in enumerate(rows, start=2):
        order_id = row["order_id"]
        if not order_id or order_id in order_ids:
            raise ValueError(f"CSV row {row_number}: missing or duplicate order ID.")
        order_ids.add(order_id)
        quantity, price, cost, discount = [
            number(row[field], field, row_number)
            for field in ("quantity", "unit_price", "unit_cost", "discount_pct")
        ]
        if quantity <= 0 or quantity != quantity.to_integral_value():
            raise ValueError(f"CSV row {row_number}: quantity must be a positive integer.")
        if price <= 0 or cost < 0 or not 0 <= discount <= 1:
            raise ValueError(f"CSV row {row_number}: invalid price, cost, or discount range.")
        revenue = money(quantity * price * (1 - discount))
        cogs = money(quantity * cost)
        profit = revenue - cogs
        margin = "" if revenue == 0 else str(money(profit / revenue * HUNDRED))
        row.update(revenue=str(revenue), cost_of_goods_sold=str(cogs),
                   gross_profit=str(profit), gross_margin_pct=margin)
        total_revenue += revenue
        total_cost += cogs
        total_profit += profit
        losses += profit < 0
        zero_revenue += revenue == 0
    if total_revenue - total_cost != total_profit:
        raise ValueError("Revenue less cost does not reconcile to gross profit.")
    overall_margin = None if total_revenue == 0 else str(money(total_profit / total_revenue * HUNDRED))
    summary = {
        "source": input_path.name,
        "data_type": "synthetic",
        "currency": "USD",
        "transaction_count": len(rows),
        "total_revenue": str(total_revenue),
        "total_cost_of_goods_sold": str(total_cost),
        "total_gross_profit": str(total_profit),
        "overall_gross_margin_pct": overall_margin,
        "loss_making_transactions": losses,
        "zero_revenue_transactions": zero_revenue,
        "totals_reconcile": True,
        "rounding": "Revenue and COGS rounded per transaction to USD cents, half up. Gross profit is their difference.",
        "margin_definition": "Gross profit / revenue * 100. Overall margin uses totals, not average row margins. Blank CSV or null JSON margin means zero revenue.",
        "scope": "Gross profit excludes operating expenses, interest, and taxes. USD amounts are exact decimal strings in JSON.",
    }
    # Include first, middle, last, a discounted, and a loss-making transaction.
    picks = []
    candidates = [0, len(rows)//2, len(rows)-1]
    candidates += [next((i for i, row in enumerate(rows) if Decimal(row['discount_pct']) > 0), 0)]
    candidates += [next((i for i, row in enumerate(rows) if Decimal(row['gross_profit']) < 0), 0)]
    for index in candidates + list(range(min(5, len(rows)))):
        if index not in picks and len(picks) < min(5, len(rows)):
            picks.append(index)
    output_dir.mkdir(parents=True, exist_ok=True)
    for target, records in ((targets[0], rows), (targets[2], [rows[i] for i in picks])):
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields + ADDED, lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    targets[1].write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "sales_clean.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        summary = calculate(args.input, args.output_dir)
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(1, f"Profitability calculation failed: {error}\n")
    print(json.dumps(summary, indent=2))
    print(f"Saved profitability data, summary, and five spot checks in {args.output_dir}")


if __name__ == "__main__":
    main()
