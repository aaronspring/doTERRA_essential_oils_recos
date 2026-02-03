#!/usr/bin/env python3
"""
Ingest doTERRA essential oils from paddleOCR CSV into Qdrant vector database.

Uses the serialized text column for embeddings and maps German columns
to English payload fields for the recommendation system.
"""

import os
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config import MODEL_NAME, QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_HOST, QDRANT_PORT

# Column mapping from German CSV columns to English payload fields
# Note: volume, application_methods, and status are excluded from Qdrant payload
COLUMN_MAPPING = {
    "url": "product_url",
    "name": "product_name",
    "lateinischer_name": "product_latin_name",
    "pflanzenteil": "plant_part",
    "extraktionsmethode": "extraction_method",
    "aromabeschreibung": "aroma_description",
    "hauptchemische_bestandteile": "key_chemical_components",
    "hauptnutzen": "primary_benefits",
    "produktbeschreibung": "product_description",
    "anwendungsmoeglichkeiten": "usage_instructions",
    "hinweise_sichere_anwendung": "safety_notes",
    "produktcode": "product_code",
    "sprache": "language",
    "shop_url": "shop_url",
    "image_url": "product_image_url",
    "serialize": "serialize",
}


def create_serialized_text(row: pd.Series) -> str:
    """Create searchable text from oil data for embedding (German format)."""
    parts = []

    name = row.get("name", "")
    latin_name = row.get("lateinischer_name", "") or row.get("latin_name", "")
    description = row.get("produktbeschreibung", "")

    if name:
        parts.append(f"Ätherisches Öl von dōTERRA **{name}**")
    if latin_name:
        parts.append(f"({latin_name})")
    if description:
        parts.append(f"Produktbeschreibung: {description}")

    aroma = row.get("aromabeschreibung", "")
    if aroma and aroma != "[]":
        parts.append(f"Aromabeschreibung: {aroma}")

    benefits = row.get("hauptnutzen_list", "") or row.get("hauptnutzen", "")
    if benefits and benefits != "[]":
        parts.append(f"Hauptnutzen: {benefits}")

    usage = row.get("anwendungsmoeglichkeiten", "")
    if usage and usage != "[]":
        parts.append(f"Anwendungsmöglichkeiten: {usage}")

    safety = row.get("hinweise_sichere_anwendung_list", "") or row.get(
        "hinweise_sichere_anwendung", ""
    )
    if safety and safety != "[]":
        parts.append(f"Hinweise zur sicheren Anwendung: {safety}")

    return "\n".join(parts)


def create_aroma_text(row: pd.Series) -> str:
    """Create aroma-only text for embedding."""
    aroma = row.get("aromabeschreibung", "")
    name = row.get("name", "")
    latin_name = row.get("lateinischer_name", "") or row.get("latin_name", "")

    parts = []
    if name:
        parts.append(f"Ätherisches Öl **{name}**")
    if latin_name:
        parts.append(f"({latin_name})")
    if aroma and aroma != "[]":
        parts.append(f"Aromabeschreibung: {aroma}")

    return "\n".join(parts)


def main():
    script_dir = Path(__file__).parent
    csv_path = os.getenv("CSV_PATH", str(script_dir / "filtered_oils_with_shop_urls.csv"))
    collection_name = QDRANT_COLLECTION
    qdrant_host = QDRANT_HOST
    qdrant_port = QDRANT_PORT

    print("--- Starting doTERRA Essential Oils Ingestion to Qdrant ---")

    # Load data
    print(f"Loading data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: {csv_path} not found.")
        return

    # Filter to working products (optional: exclude discontinued)
    if "status" in df.columns:
        original_count = len(df)
        df = df[df["status"] != "DISCONTINUED"]
        print(f"Filtered {original_count - len(df)} discontinued products. Remaining: {len(df)}")

    # Remove duplicates based on shop_url (keep first occurrence)
    if "shop_url" in df.columns:
        original_count = len(df)
        df = df.drop_duplicates(subset=["shop_url"], keep="first")
        print(f"Removed {original_count - len(df)} duplicate shop_urls. Remaining: {len(df)}")

    # Check for serialized text column, create if missing
    if "serialize" not in df.columns:
        print("Creating 'serialize' column from raw data...")
        df["serialize"] = df.apply(create_serialized_text, axis=1)
    else:
        print("Using existing 'serialize' column.")

    # Create aroma-only text column
    if "serialize_aroma" not in df.columns:
        print("Creating 'serialize_aroma' column from raw data...")
        df["serialize_aroma"] = df.apply(create_aroma_text, axis=1)
    else:
        print("Using existing 'serialize_aroma' column.")

    # Ensure we have text to embed
    if "serialize" not in df.columns or "serialize_aroma" not in df.columns:
        print("Error: Required serialize columns not found.")
        return

    model_name = MODEL_NAME
    model_slug = model_name.split("/")[-1]
    full_vector_name = f"full_{model_slug}"
    aroma_vector_name = f"aroma_{model_slug}"

    print(f"Initializing model: {model_name}...")

    device = "mps"  # knowingg Apple Silicon
    print(f"Using device: {device}")

    model = SentenceTransformer(model_name, device=device, trust_remote_code=True)

    # Generate full embeddings
    print("Generating embeddings for 'serialize' column...")
    zero_len_count = (df["serialize"].fillna("").str.len() == 0).sum()
    if zero_len_count > 0:
        print(f"Found {zero_len_count} zero-length texts. Setting to empty string.")
    sentences = df["serialize"].fillna("").tolist()

    full_embeddings = model.encode(sentences, show_progress_bar=True, convert_to_numpy=True)
    vector_size = full_embeddings.shape[1]
    print(f"Generated {len(full_embeddings)} full embeddings with dimension {vector_size}.")

    # Generate aroma embeddings
    print("Generating embeddings for 'serialize_aroma' column...")
    zero_len_count = (df["serialize_aroma"].fillna("").str.len() == 0).sum()
    if zero_len_count > 0:
        print(f"Found {zero_len_count} zero-length aroma texts. Setting to empty string.")
    aroma_sentences = df["serialize_aroma"].fillna("").tolist()

    aroma_embeddings = model.encode(aroma_sentences, show_progress_bar=True, convert_to_numpy=True)
    print(
        f"Generated {len(aroma_embeddings)} aroma embeddings with dimension {aroma_embeddings.shape[1]}."
    )

    # Connect to Qdrant
    print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    try:
        if QDRANT_API_KEY:
            client = QdrantClient(
                url=qdrant_host,
                api_key=QDRANT_API_KEY,
                prefer_grpc=False,
            )
        else:
            client = QdrantClient(host=qdrant_host, port=qdrant_port)
        client.get_collections()
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        print("Check Qdrant URL, port, and API key in .env file")
        return

    # Create collection with two named vectors
    print(
        f"Creating (or recreating) collection '{collection_name}' with vectors "
        f"'{full_vector_name}' and '{aroma_vector_name}'..."
    )
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config={
            full_vector_name: VectorParams(size=vector_size, distance=Distance.COSINE),
            aroma_vector_name: VectorParams(size=vector_size, distance=Distance.COSINE),
        },
    )

    # Prepare and upload points
    print("Uploading points to Qdrant...")
    points = []
    for idx, (_, row) in enumerate(tqdm(df.iterrows(), total=len(df), desc="Preparing Points")):
        payload = {}

        # Map German columns to English payload fields
        for german_col, english_field in COLUMN_MAPPING.items():
            if german_col in df.columns and pd.notna(row.get(german_col)):
                value = row[german_col]

                # Get scalar value if it's a Series
                if hasattr(value, "item"):
                    value = value.item()

                # Special handling for specific fields
                if german_col == "produktcode":
                    # Convert product_code to int
                    try:
                        value = int(str(value))
                    except (ValueError, TypeError):
                        value = None

                # Transform plant_part and key_chemical_components to lists
                elif german_col in ["pflanzenteil", "hauptchemische_bestandteile"]:
                    if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                        # Already a string representation of a list, parse it
                        try:
                            import ast

                            value = ast.literal_eval(value)
                        except:
                            value = [v.strip() for v in value.strip("[]").split(",")]
                    elif isinstance(value, str):
                        value = [v.strip() for v in value.strip("[]").split(",")]

                    # Filter out null/empty values and convert to proper list
                    if isinstance(value, list):
                        value = [v for v in value if v and v.lower() not in ["null", "none", ""]]

                        # Remove duplicates from plant_part while preserving order
                        if german_col == "pflanzenteil":
                            seen = set()
                            unique_value = []
                            for v in value:
                                if v not in seen:
                                    seen.add(v)
                                    unique_value.append(v)
                            value = unique_value

                        value = value if value else []

                payload[english_field] = value

        # Clean NaN values for Qdrant compatibility
        def clean_value(v):
            if v is None:
                return ""
            if isinstance(v, float) and pd.isna(v):
                return ""
            if isinstance(v, (list, dict)) and len(v) == 0:
                return []
            return v

        payload = {k: clean_value(v) for k, v in payload.items()}

        # Generate point ID from product_name (alphanumeric + underscore only)
        product_name = row.get("name", f"oil_{idx}") or f"oil_{idx}"
        clean_name = "".join(c for c in str(product_name) if c.isalnum() or c == "_")

        # Use hash of cleaned name for integer ID
        point_id = abs(hash(clean_name)) % (10**9)

        points.append(
            PointStruct(
                id=point_id,
                vector={
                    full_vector_name: full_embeddings[idx].tolist(),
                    aroma_vector_name: aroma_embeddings[idx].tolist(),
                },
                payload=payload,
            )
        )

    # Batch upsert
    chunk_size = 100
    for i in range(0, len(points), chunk_size):
        chunk = points[i : i + chunk_size]
        client.upsert(collection_name=collection_name, points=chunk)
        print(f"Uploaded batch {i} - {i + len(chunk)}")

    print("--- Finished ---")
    print(f"Successfully uploaded {len(points)} points to collection '{collection_name}'.")

    # Verify
    info = client.get_collection(collection_name)
    print(f"Collection status: {info.status}")
    print(f"Total points: {info.points_count}")


if __name__ == "__main__":
    main()
