import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from scrape_single import HEADERS, scrape_product_page


def get_urls_from_sitemap(sitemap_url):
    print(f"Fetching sitemap from {sitemap_url}...")
    resp = requests.get(sitemap_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # Parse XML
    root = ET.fromstring(resp.content)
    # Namespaces are often present in sitemaps
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    locs = [loc.text for loc in root.findall(".//ns:loc", ns)]

    # Filter for products (contain /p/) and oils (contain 'oil')
    oil_urls = []
    for url in locs:
        if "/DE/de_DE/p/" in url and "oil" in url.lower():
            # Exclude accessories
            if any(
                x in url.lower()
                for x in [
                    "sticker",
                    "vial-keychain",
                    "diffuser",
                    "kit-english",
                    "kit-german",
                    "introductory-pack",
                ]
            ):
                continue

            slug = url.rstrip("/").split("/")[-1]
            shop_url = f"https://shop.doterra.com/DE/de_DE/shop/{slug}/"
            oil_urls.append(shop_url)

    # Remove duplicates
    return sorted(list(set(oil_urls)))


def main():
    root = Path(__file__).resolve().parent
    output_csv = root / "doterra_oils_sitemap.csv"
    sitemap_url = "https://www.doterra.com/sitemaps/de_de_sitemap.xml"

    urls = get_urls_from_sitemap(sitemap_url)
    print(f"Found {len(urls)} oil products in sitemap.")

    test = False
    if test:
        urls = urls[:3]

    all_data = []
    for i, url in enumerate(urls):
        print(f"[{i + 1}/{len(urls)}] Scraping: {url}")
        data = scrape_product_page(url)
        all_data.append(data)
        time.sleep(0.25)

        # Intermediate save every 10 items
        if (i + 1) % 10 == 0:
            pd.DataFrame(all_data).to_csv(output_csv, index=False, encoding="utf-8-sig")

    df = pd.DataFrame(all_data)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"Done! Saved {len(all_data)} products to {output_csv}")


if __name__ == "__main__":
    main()
