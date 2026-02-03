#!/usr/bin/env python3
"""Fetch shop URLs and product images from dōTERRA German shop."""

import csv
import re
import urllib.error
import urllib.request
from pathlib import Path

csv_path = Path("filtered_oils.csv")
oils = []

with open(csv_path, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        oils.append(
            {
                "url": row["url"],
                "name": row["name"],
                "produktcode": row.get("produktcode", ""),
            }
        )

print(f"Processing {len(oils)} oils...\n")

results = []
valid_count = 0
image_count = 0

for i, oil in enumerate(oils, 1):
    name = oil["name"]
    code = oil["produktcode"]
    pdf_url = oil["url"]

    # Extract product slug from PDF URL
    match = re.search(r"pips/([^/]+)\.pdf", pdf_url)
    slug = match.group(1) if match else None

    if not slug:
        print(f"[{i:3d}] ✗ {name:40} -> NO SLUG")
        results.append(
            {
                "name": name,
                "produktcode": code,
                "pdf_url": pdf_url,
                "shop_url": "",
                "image_url": "",
                "status": "NO_SLUG",
            }
        )
        continue

    # Build shop URL
    shop_url = f"https://shop.doterra.com/de/de_de/shop/{slug}/"
    image_url = ""
    status = "ERROR"

    try:
        with urllib.request.urlopen(shop_url, timeout=10) as resp:
            if resp.status == 200:
                content = resp.read().decode("utf-8")

                # Look for large product image
                img_match = re.search(
                    r'https://[^\s"\'<>]*essential-oils/single-oils/[^\s"\'<>]*large-500x1350[^\s"\'<>]*\.(?:png|jpg|webp)',
                    content,
                    re.IGNORECASE,
                )

                if img_match:
                    image_url = img_match.group(0)
                    status = "OK_WITH_IMAGE"
                    image_count += 1
                else:
                    status = "OK_NO_IMAGE"

                valid_count += 1
                print(f"[{i:3d}] ✓ {name:40} -> {status}")
            else:
                print(f"[{i:3d}] ✗ {name:40} -> HTTP {resp.status}")
                status = f"HTTP_{resp.status}"

    except urllib.error.HTTPError as e:
        print(f"[{i:3d}] ✗ {name:40} -> HTTP {e.code}")
        status = f"HTTP_{e.code}"
    except Exception as e:
        print(f"[{i:3d}] ✗ {name:40} -> {type(e).__name__}")
        status = type(e).__name__

    results.append(
        {
            "name": name,
            "produktcode": code,
            "pdf_url": pdf_url,
            "shop_url": shop_url,
            "image_url": image_url,
            "status": status,
        }
    )

# Save results
output_path = Path("oils_with_shop_urls.csv")
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=["name", "produktcode", "pdf_url", "shop_url", "image_url", "status"]
    )
    writer.writeheader()
    writer.writerows(results)

print(f"\n{'=' * 70}")
print(f"✅ Saved to {output_path}")
print(f"Summary: {valid_count}/{len(results)} valid shop URLs")
print(f"         {image_count}/{len(results)} with product images")
print(f"{'=' * 70}")
