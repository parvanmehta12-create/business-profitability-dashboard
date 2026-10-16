"""Validate synthetic retail orders without changing the original sales.csv.

Run from the inner project folder: python scripts/clean_data.py
Optional: python scripts/clean_data.py --input other.csv --output-dir other_folder
"""

import argparse
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "order_id", "date", "product", "category", "region", "customer_segment",
    "quantity", "unit_price", "unit_cost", "discount_pct",
]
NUMERIC = ["quantity", "unit_price", "unit_cost", "discount_pct"]
TEXT = ["order_id", "product", "category", "region", "customer_segment"]
PRODUCT_CATEGORY = {
    "Office Chair": "Furniture", "Standing Desk": "Furniture",
    "Bookshelf": "Furniture", "Filing Cabinet": "Furniture",
    "Monitor": "Technology", "Keyboard": "Technology",
    "Wireless Mouse": "Technology", "Printer": "Technology",
    "Notebook Pack": "Office Supplies", "Pen Set": "Office Supplies",
    "Paper Ream": "Office Supplies", "Desk Organizer": "Office Supplies",
}


def clean_sales(input_path, output_dir):
    """Clean this project's single-product orders and report every exclusion."""
    input_path, output_dir = Path(input_path), Path(output_dir)
    targets = [output_dir / name for name in (
        "sales_clean.csv", "rejected_rows.csv", "validation_report.json"
    )]
    if input_path.resolve() in [path.resolve() for path in targets]:
        raise ValueError("Input must differ from all output files.")
    raw = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    if set(raw.columns) != set(FIELDS):
        raise ValueError(
            f"Column mismatch. Missing: {sorted(set(FIELDS) - set(raw.columns))}; "
            f"unexpected: {sorted(set(raw.columns) - set(FIELDS))}"
        )
    if raw.empty:
        raise ValueError("Input has no transactions. No outputs were written.")
    data = raw[FIELDS].copy()
    data = data.apply(lambda column: column.str.strip())
    trimmed = int((raw[FIELDS] != data).any(axis=1).sum())
    reasons = [[] for _ in range(len(data))]

    def flag(mask, message):
        for index in data.index[mask]:
            reasons[index].append(message)

    for field in TEXT:
        flag(data[field].eq(""), f"Missing {field}")
    # Strict ISO dates prevent ambiguous month/day conversions.
    dates = pd.to_datetime(data["date"], format="%Y-%m-%d", errors="coerce")
    flag(~data["date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}") | dates.isna(), "Invalid ISO date")
    flag(dates.notna() & dates.dt.year.ne(2025), "Date outside the 2025 sample period")
    data["date"] = dates.dt.strftime("%Y-%m-%d")
    for field in NUMERIC:
        values = pd.to_numeric(data[field], errors="coerce")
        finite = values.map(lambda value: pd.notna(value) and math.isfinite(value))
        flag(~finite, f"Missing or invalid {field}")
        data[field] = values
    flag(data["quantity"].le(0) | data["quantity"].mod(1).ne(0), "Quantity must be a positive integer")
    flag(data["unit_price"].le(0), "Unit price must be positive")
    flag(data["unit_cost"].lt(0), "Unit cost cannot be negative")
    flag(data["discount_pct"].lt(0) | data["discount_pct"].gt(1), "Discount must be between 0 and 1")
    flag(~data["region"].isin(["East", "West", "Central", "South"]), "Unknown region")
    flag(~data["customer_segment"].isin(["Consumer", "Small Business", "Corporate"]), "Unknown customer segment")
    flag(~data["product"].isin(PRODUCT_CATEGORY), "Unknown product")
    flag(data["product"].map(PRODUCT_CATEGORY).ne(data["category"]), "Product/category mismatch")

    invalid = pd.Series([bool(reason) for reason in reasons], index=data.index)
    valid = data.loc[~invalid].copy()
    # Normalize first, then keep one copy of an otherwise identical transaction.
    duplicate_mask = valid.duplicated(subset=FIELDS, keep="first")
    duplicate_indices = valid.index[duplicate_mask]
    for index in duplicate_indices:
        reasons[index].append("Duplicate transaction; first copy retained")
    valid = valid.loc[~duplicate_mask]
    # Unique order IDs are a rule of this sample, not all retail datasets.
    conflict_mask = valid.duplicated(subset=["order_id"], keep=False)
    conflict_indices = valid.index[conflict_mask]
    for index in conflict_indices:
        reasons[index].append("Conflicting order ID; all conflicting rows excluded")
    cleaned = valid.loc[~conflict_mask].copy()
    cleaned["quantity"] = cleaned["quantity"].astype("int64")
    cleaned = cleaned.sort_values(["date", "order_id"]).reset_index(drop=True)
    excluded = [index for index, reason in enumerate(reasons) if reason]
    rejected = raw.loc[excluded].copy()
    rejected.insert(0, "source_csv_row", [index + 2 for index in excluded])
    rejected["rejection_reason"] = ["; ".join(reasons[index]) for index in excluded]
    report = {
        "source": input_path.name,
        "input_rows": len(raw),
        "rows_with_whitespace_trimmed": trimmed,
        "invalid_rows": int(invalid.sum()),
        "duplicate_rows_removed": len(duplicate_indices),
        "conflicting_order_rows": len(conflict_indices),
        "rejected_rows": len(rejected),
        "output_rows": len(cleaned),
        "row_count_reconciles": len(raw) == len(cleaned) + len(rejected),
        "date_min": None if cleaned.empty else cleaned["date"].min(),
        "date_max": None if cleaned.empty else cleaned["date"].max(),
        "notes": "Synthetic 2025 data. Negative gross profit is not a rejection rule. Original input preserved.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(targets[0], index=False, lineterminator="\n")
    rejected.to_csv(targets[1], index=False, lineterminator="\n")
    targets[2].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "sales.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        report = clean_sales(args.input, args.output_dir)
    except (ValueError, OSError, pd.errors.ParserError) as error:
        parser.exit(1, f"Data check failed: {error}\n")
    print(json.dumps(report, indent=2))
    print(f"Saved cleaned data, rejected rows, and validation report in {args.output_dir}")
    if report["output_rows"] == 0:
        parser.exit(1, "No valid transactions remain. Review rejected_rows.csv.\n")


if __name__ == "__main__":
    main()
