from pathlib import Path

import pandas as pd


def serialize_row(row):
    """Serialize a row into a flat string for LLM embeddings."""
    columns_to_include = {
        "product_name": "Produktname",
        "product_sub_name": "Untername",
        "product_description": "Beschreibung",
        "brand_lifestyle_title": "Lifestyle-Titel",
        "brand_lifestyle_description": "Lifestyle-Beschreibung",
        "product_uses_list_item1": "-",
        "product_uses_list_item2": "-",
        "product_uses_list_item3": "-",
        "product_uses_directions_text1": "Anwendungshinweise",
        "product_uses_cautions_text": "Vorsichtshinweise",
    }

    parts = []
    for col, label in columns_to_include.items():
        if col in row and pd.notna(row[col]):
            value = str(row[col]).strip()
            if value:
                parts.append(f"{label}: {value}")

    return "\n".join(parts)


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Serialize dōTERRA oil data for embeddings.")
    script_dir = Path(__file__).parent
    parser.add_argument(
        "--input", default=str(script_dir / "doterra_oils_sitemap.csv"), help="Input CSV file"
    )
    parser.add_argument(
        "--output", default=str(script_dir / "single_oil.csv"), help="Output CSV file"
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        return

    print(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)

    # 1. Categorization logic from EDA
    print("Processing and filtering data...")
    df["type"] = "Single Oil"
    df.loc[df["product_name"].str.contains("Touch", na=False), "type"] = "Touch"
    df.loc[df["product_name"].str.contains("Roll-On|Mischung", na=False), "type"] = "Blend/Roll-On"

    # 2. Mischung detection (as seen in EDA)
    if "product_sub_name" in df.columns:
        df["Mischung"] = df.product_sub_name.str.contains("Mischung", na=False).fillna(True)

    # 3. Apply serialization
    print("Applying serialization...")
    df["serialized_text"] = df.apply(serialize_row, axis=1)

    # 4. Filter for Single Oils as per notebook requirements
    single_oil_df = df[df.type == "Single Oil"]
    # Filter out base oils like Fractionated Coconut Oil
    single_oil_df = single_oil_df[single_oil_df.product_name != "Fraktioniertes Kokosöl"]
    # Ensure product name is present
    single_oil_df = single_oil_df[single_oil_df.product_name.notnull()].reset_index(drop=True)
    # show last 5 rows
    print("Last 5 rows:")
    print(single_oil_df.tail())

    # 5. Save output
    print(f"Saving {len(single_oil_df)} rows to {args.output}...")
    single_oil_df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print("Done!")


if __name__ == "__main__":
    main()
