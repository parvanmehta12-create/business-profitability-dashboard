"""Generate the synthetic Day 2 dataset with Python's standard library.

Run from anywhere: python scripts/generate_data.py
This replaces data/sales.csv with the same seeded sample each time.
"""

import calendar
import csv
import json
import random
import sys
from pathlib import Path

SEED = 42
FIELDS = [
    "order_id", "date", "product", "category", "region", "customer_segment",
    "quantity", "unit_price", "unit_cost", "discount_pct",
]
# Product, category, list price in USD, base cost as a fraction of list price.
PRODUCTS = [
    ("Office Chair", "Furniture", 150, 0.65),
    ("Standing Desk", "Furniture", 350, 0.72),
    ("Bookshelf", "Furniture", 120, 0.68),
    ("Filing Cabinet", "Furniture", 180, 0.78),
    ("Monitor", "Technology", 240, 0.76),
    ("Keyboard", "Technology", 45, 0.48),
    ("Wireless Mouse", "Technology", 30, 0.42),
    ("Printer", "Technology", 200, 0.84),
    ("Notebook Pack", "Office Supplies", 18, 0.38),
    ("Pen Set", "Office Supplies", 12, 0.30),
    ("Paper Ream", "Office Supplies", 9, 0.60),
    ("Desk Organizer", "Office Supplies", 25, 0.45),
]
REGIONS = ["East", "West", "Central", "South"]
SEGMENTS = ["Consumer", "Small Business", "Corporate"]
MONTH_COUNTS = [65, 60, 70, 70, 75, 80, 80, 85, 90, 95, 110, 120]


def generate_rows():
    rng = random.Random(SEED)
    rows = []
    for month, count in enumerate(MONTH_COUNTS, start=1):
        for _ in range(count):
            product, category, price, cost_ratio = rng.choice(PRODUCTS)
            region = rng.choices(REGIONS, weights=[30, 28, 24, 18])[0]
            segment = rng.choices(SEGMENTS, weights=[45, 35, 20])[0]
            day = rng.randint(1, calendar.monthrange(2025, month)[1])
            quantity = rng.randint(1, {"Consumer": 4, "Small Business": 7, "Corporate": 12}[segment])
            discounts = [0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
            weights = [35, 20, 18, 10, 8, 6, 3]
            discount = rng.choices(discounts, weights=weights)[0]
            if month in (11, 12):
                discount = min(0.40, round(discount + 0.05, 2))
            cost = round(price * cost_ratio * rng.uniform(0.95, 1.05), 2)
            rows.append({
                "order_id": "", "date": f"2025-{month:02d}-{day:02d}",
                "product": product, "category": category, "region": region,
                "customer_segment": segment, "quantity": quantity,
                "unit_price": float(price), "unit_cost": cost,
                "discount_pct": discount,
            })
    rows.sort(key=lambda row: row["date"])
    for index, row in enumerate(rows, start=1):
        row["order_id"] = f"ORD{index:05d}"
    return rows


if __name__ == "__main__":
    rows = generate_rows()
    if "--json" in sys.argv:
        print(json.dumps({"fields": FIELDS, "rows": rows}))
    else:
        output = Path(__file__).resolve().parents[1] / "data" / "sales.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {len(rows):,} synthetic transactions to {output}")
