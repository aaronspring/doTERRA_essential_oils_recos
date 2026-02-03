#!/usr/bin/env python3
"""Fetch shop URLs and images using correct dōTERRA shop structure."""

import csv
import re
from pathlib import Path

import httpx

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

print(f"Found {len(oils)} oils\n")

results = []
client = httpx.Client(follow_redirects=True, timeout=10)

for oil in oils:
    name = oil["name"]
    code = oil["produktcode"]
    pdf_url = oil["url"]

    # Extract product slug from PDF URL
    # e.g., https://media.doterra.com/eu/de/pips/wild-orange-oil.pdf -> wild-orange-oil
    match = re.search(r"pips/([^/]+)\.pdf", pdf_url)
    slug = match.group(1) if match else None

    if not slug:
        print(f"✗ {name:40} -> NO SLUG FOUND")
        continue

    # Correct shop URL format for German dōTERRA shop
    shop_url = f"https://shop.doterra.com/de/de_de/shop/{slug}/"
    image_url = None

    try:
        resp = client.get(shop_url, follow_redirects=True)
        # Check if page loaded correctly (content > 10KB, no error markers)
        is_valid_page = (
            resp.status_code == 200
            and len(resp.text) > 10000
            and "Error" not in resp.text
            and "404" not in resp.text
        )

        if is_valid_page:
            # Try to extract image URL - look for large product images
            img_patterns = [
                r'https://[^\s"\'<>]*essential-oils/single-oils/[^\s"\'<>]*large-500x1350[^\s"\'<>]*\.(?:png|jpg|webp)',
                r'https://[^\s"\'<>]*prd-evo-content\.doterra\.com/europe/images/products[^\s"\'<>]*\.(?:png|jpg|webp)',
            ]

            for pattern in img_patterns:
                img_match = re.search(pattern, resp.text, re.IGNORECASE)
                if img_match:
                    image_url = img_match.group(0)
                    break

            results.append(
                {
                    "name": name,
                    "produktcode": code,
                    "pdf_url": pdf_url,
                    "shop_url": shop_url,
                    "image_url": image_url or "",
                    "status": "VALID" if image_url else "VALID_NO_IMAGE",
                }
            )
            print(f"✓ {name:40} -> OK" + (" + IMG" if image_url else " (no img)"))
        else:
            results.append(
                {
                    "name": name,
                    "produktcode": code,
                    "pdf_url": pdf_url,
                    "shop_url": shop_url,
                    "image_url": "",
                    "status": "ERROR_PAGE",
                }
            )
            print(f"✗ {name:40} -> ERROR PAGE")
    except Exception as e:
        results.append(
            {
                "name": name,
                "produktcode": code,
                "pdf_url": pdf_url,
                "shop_url": shop_url,
                "image_url": "",
                "status": f"EXCEPTION: {type(e).__name__}",
            }
        )
        print(f"✗ {name:40} -> {type(e).__name__}")

client.close()

# Save results
output_path = Path("oils_with_shop_urls.csv")
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=["name", "produktcode", "pdf_url", "shop_url", "image_url", "status"]
    )
    writer.writeheader()
    writer.writerows(results)

print(f"\n✅ Saved to {output_path}")

# Summary
valid = sum(1 for r in results if r["status"] in ["VALID", "VALID_NO_IMAGE"])
with_images = sum(1 for r in results if r["image_url"])
print(f"Summary: {valid}/{len(results)} valid shop URLs, {with_images} with images")
