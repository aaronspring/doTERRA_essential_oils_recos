#!/usr/bin/env python3
"""
Extract essential oil data from random URLs and save to CSV.
Uses seed 42 for reproducibility.
"""

import argparse
import json
import random

import pandas as pd
import tqdm
from extract_essential_oil_v2 import (
    extract_from_images,
    prepare_images,
)


def main(n=None):
    # Load URLs from JSON
    with open("doterra_eu_de_pips.json") as f:
        data = json.load(f)

    urls = data["urls"]

    # Determine number of URLs to select
    num_to_select = n if n is not None else len(urls)

    # Select random URLs with seed 42
    random.seed(42)
    selected_urls = random.sample(urls, min(num_to_select, len(urls)))

    print(f"Selected {len(selected_urls)} random URLs:")
    for url in selected_urls:
        print(f"  - {url}")

    # Process each URL
    results = []
    for url in tqdm.tqdm(selected_urls):
        print(f"\n{'=' * 70}")
        print(f"Processing: {url}")
        print(f"{'=' * 70}")

        cleanup_files = []
        try:
            # Prepare images from URL
            image_paths, cleanup_files = prepare_images(url)

            # Extract data (auto-detect German since these are DE URLs)
            data = extract_from_images(image_paths, output_format="auto")

            # Add URL to data
            data["url"] = url
            results.append(data)

            print(f"\nExtracted: {data.get('name', 'N/A')}")

        except Exception as e:
            print(f"Error processing {url}: {e}")
            # Add error entry
            results.append(
                {
                    "url": url,
                    "error": str(e),
                    "name": "",
                    "latin_name": "",
                }
            )
        finally:
            import os

            for f in cleanup_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except OSError:
                    pass

    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)

    # Ensure URL is first column
    cols = ["url"] + [col for col in df.columns if col != "url"]
    df = df[cols]

    # Save to CSV
    output_file = "extracted_oils.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"\n{'=' * 70}")
    print("RESULTS SAVED")
    print(f"{'=' * 70}")
    print(f"CSV file: {output_file}")
    print(f"Total rows: {len(df)}")
    print("\nPreview:")
    print(df[["url", "name", "lateinischer_name", "produktbeschreibung"]].to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract essential oil data from URLs")
    parser.add_argument(
        "-n", "--num", type=int, default=None, help="Number of oils to select (default: all)"
    )
    args = parser.parse_args()
    main(n=args.num)
