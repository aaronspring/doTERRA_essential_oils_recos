import os
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd  # noqa: E402
import torch  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402
from qdrant_client.models import Distance, PointStruct, VectorParams  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402
from tqdm import tqdm  # noqa: E402

from config import (  # noqa: E402
    MODEL_NAME,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_HOST,
    QDRANT_PORT,
    VECTOR_NAME,
)


def main():
    # 1. Configuration
    script_dir = Path(__file__).parent
    csv_path = os.getenv("CSV_PATH", str(script_dir / "single_oil.csv"))
    collection_name = QDRANT_COLLECTION

    # Qdrant connection settings
    qdrant_host = QDRANT_HOST
    qdrant_port = QDRANT_PORT

    # qdrant payload columns to include
    payload_cols = [
        "product_name",
        "product_sub_name",
        "product_image_url",
        "product_description",
        "brand_lifestyle_title",
        "brand_lifestyle_description",
        "url",
    ]

    print("--- Starting Embeddings Generation and Upload (Local Docker) ---")

    # 2. Load data
    print(f"Loading data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: {csv_path} not found.")
        return

    if "serialized_text" not in df.columns:
        print("Error: 'serialized_text' column not found in CSV.")
        return

    model_name = MODEL_NAME
    vector_name = VECTOR_NAME

    print(f"Initializing model: {model_name}...")

    # Use CUDA if available, else CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and torch.backends.mps.is_available():
        device = "mps"

    print(f"Using device: {device}")

    # Jina embeddings v2 needs trust_remote_code=True
    model = SentenceTransformer(model_name, device=device, trust_remote_code=True)

    # 4. Generate Embeddings
    print("Generating embeddings for 'serialized_text'...")
    zero_len_count = (df["serialized_text"].fillna("").str.len() == 0).sum()
    if zero_len_count > 0:
        print(f"Found {zero_len_count} zero-length serialized texts. Setting them to empty string.")
    sentences = df["serialized_text"].fillna("").tolist()

    # Generate embeddings
    embeddings = model.encode(sentences, show_progress_bar=True, convert_to_numpy=True)

    vector_size = embeddings.shape[1]
    print(f"Generated {len(embeddings)} embeddings with dimension {vector_size}.")

    # 5. Connect to Qdrant (Cloud or Local)
    print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    try:
        if QDRANT_API_KEY:
            # Cloud connection
            client = QdrantClient(
                url=qdrant_host,
                api_key=QDRANT_API_KEY,
                prefer_grpc=False,
            )
        else:
            # Local connection
            client = QdrantClient(host=qdrant_host, port=qdrant_port)
        # Test connection
        client.get_collections()
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        print("Check Qdrant URL, port, and API key in .env file")
        return

    # 6. Create collection
    print(
        f"Creating (or recreating) collection '{collection_name}' "
        f"with named vector '{vector_name}'..."
    )
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config={vector_name: VectorParams(size=vector_size, distance=Distance.COSINE)},
    )

    # 7. Prepare and Upload Points
    print("Uploading points to Qdrant...")
    points = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Preparing Points"):
        # Build payload
        payload = {col: row[col] for col in payload_cols if col in df.columns}

        # Rename url to product_url for consistency
        if "url" in payload:
            payload["product_url"] = payload.pop("url")

        # Clean up NaN values for Qdrant compatibility (it doesn't like NaNs)
        payload = {k: (v if pd.notna(v) else "") for k, v in payload.items()}

        points.append(
            PointStruct(id=i, vector={vector_name: embeddings[i].tolist()}, payload=payload)
        )

    # Batch upsert
    # Breaking into chunks if list is very large, but for ~1000 items direct upsert is fine
    chunk_size = 100
    for i in range(0, len(points), chunk_size):
        chunk = points[i : i + chunk_size]
        client.upsert(collection_name=collection_name, points=chunk)
        print(f"Uploaded batch {i} - {i + len(chunk)}")

    print("--- Finished ---")
    print(f"Successfully uploaded {len(points)} points to collection '{collection_name}'.")

    # Verify count
    info = client.get_collection(collection_name)
    print(f"Collection status: {info.status}")
    print(f"Total points: {info.points_count}")


if __name__ == "__main__":
    main()
