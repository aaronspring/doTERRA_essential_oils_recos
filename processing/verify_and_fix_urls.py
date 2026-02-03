#!/usr/bin/env python3
"""Verify and fix shop URLs using actual dōTERRA shop structure."""

import csv
import re
from pathlib import Path

import httpx

csv_path = Path("oils_with_shop_urls.csv")
results = []

# Read existing CSV
existing_urls = {}
with open(csv_path, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing_urls[row["name"]] = row

print(f"Loaded {len(existing_urls)} existing entries\n")

# Sample validation - check 10 random URLs
client = httpx.Client(follow_redirects=True, timeout=10)

print("=" * 80)
print("VALIDATION REPORT")
print("=" * 80)

count = 0
valid = 0
invalid = 0

for name, data in list(existing_urls.items())[:10]:
    shop_url = data["shop_url"]
    image_url = data["image_url"]
    code = data["produktcode"]

    print(f"\n{name}")
    print(f"  Product Code: {code}")
    print(f"  Shop URL: {shop_url}")

    # Check if shop URL exists
    try:
        resp = client.get(shop_url, follow_redirects=True)
        status = resp.status_code
        is_error = "Error" in resp.text or "404" in resp.text or status >= 400
        print(f"  Status: {status} {'✓' if status == 200 and not is_error else '✗ ERROR'}")

        if status == 200 and not is_error:
            valid += 1
            # Try to find image in page
            imgs = re.findall(r'src=["\']([^"\']*\.(?:jpg|jpeg|png|webp))["\']', resp.text)
            if imgs:
                print(f"  Found {len(imgs)} images in page")
                print(f"    First: {imgs[0][:80]}...")
        else:
            invalid += 1

    except Exception as e:
        print(f"  Status: ✗ {type(e).__name__}: {str(e)[:60]}")
        invalid += 1

    count += 1

client.close()

print("\n" + "=" * 80)
print(f"SUMMARY: {valid} valid, {invalid} invalid out of {count} checked")
print("=" * 80)
