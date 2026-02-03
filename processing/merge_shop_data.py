#!/usr/bin/env python3
"""Merge shop URLs and images with filtered_oils.csv"""

import csv
from pathlib import Path

# Read shop data
shop_data = {}
with open("oils_with_shop_urls.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        shop_data[row["name"]] = {
            "shop_url": row["shop_url"],
            "image_url": row["image_url"],
            "status": row["status"],
        }

print(f"Loaded {len(shop_data)} products from oils_with_shop_urls.csv\n")

# Read and merge filtered oils
output_rows = []
matched = 0
missing = []

with open("filtered_oils.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames + ["shop_url", "image_url"]

    for row in reader:
        name = row["name"]
        if name in shop_data:
            row["shop_url"] = shop_data[name]["shop_url"]
            row["image_url"] = shop_data[name]["image_url"]
            matched += 1
        else:
            row["shop_url"] = ""
            row["image_url"] = ""
            missing.append(name)

        output_rows.append(row)

# Save merged file
output_path = Path("filtered_oils_with_shop_urls.csv")
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"✅ Merged: {matched} products matched")
print(f"⚠️  Unmatched: {len(missing)} products")
if missing:
    print("\nUnmatched products:")
    for name in missing[:5]:
        print(f"  • {name}")
    if len(missing) > 5:
        print(f"  ... and {len(missing) - 5} more")

print(f"\n{'=' * 70}")
print(f"✅ Saved to: {output_path}")
print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
print(f"   Rows: {len(output_rows)}")
print(f"{'=' * 70}")
