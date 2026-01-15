import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SELECTORS = {
    "product_name": ".spotlight__head-title",
    "product_sub_name": ".spotlight__head-latin-title",
    "product_image_url": "img.spotlight__head-img",
    "product_description": ".spotlight__head-copy p",
    "brand_lifestyle_title": ".product-benefits__title",
    "brand_lifestyle_description": ".product-benefits__copy",
    "product_uses_list_item1": ".product-uses__block-list ul li:nth-child(1)",
    "product_uses_list_item2": ".product-uses__block-list ul li:nth-child(2)",
    "product_uses_list_item3": ".product-uses__block-list ul li:nth-child(3)",
    "product_uses_directions_text1": ".product-uses__directions-for-use-copy",
    "product_uses_cautions_text": ".product-uses__cautions-body p",
    "product_howitworks_location": ".product-sourcingalt__info-title",
}


def scrape_product_page(url, headers=HEADERS):
    """Scrape a single doTERRA product page."""
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        out = {"url": url, "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        for key, selector in SELECTORS.items():
            element = soup.select_one(selector)
            if element:
                if key == "product_image_url":
                    out[key] = element.get("src")
                else:
                    out[key] = element.get_text(separator=" ", strip=True)
            else:
                out[key] = None

        return out
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {"url": url, "error": str(e)}


def main():
    root = Path(__file__).resolve().parent
    url = "https://shop.doterra.com/DE/de_DE/shop/copaiba-oil/"

    data = scrape_product_page(url)

    # Write JSON
    out_path = root / "copaiba.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", out_path)


if __name__ == "__main__":
    main()
