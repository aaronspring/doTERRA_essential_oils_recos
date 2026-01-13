import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
import torch
import os

def main():
    # 1. Configuration
    csv_path = os.getenv("CSV_PATH", "single_oil.csv")
    model_name = 'jinaai/jina-embeddings-v3'
    collection_name = "essential_oils"
    
    # Qdrant connection settings (Localhost Docker)
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    
    # Payload columns to include
    payload_cols = [
        'product_name', 
        'product_sub_name', 
        'product_image_url', 
        'product_description', 
        'brand_lifestyle_title', 
        'brand_lifestyle_description',
        'url'
    ]

    print(f"--- Starting Embeddings Generation and Upload (Local Docker) ---")
    
    # 2. Load data
    print(f"Loading data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: {csv_path} not found.")
        return

    if 'serialized_text' not in df.columns:
        print("Error: 'serialized_text' column not found in CSV.")
        return

    # Switch to standard stable model
    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    
    print(f"Initializing model: {model_name}...")
    
    # Use CUDA if available, else CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and torch.backends.mps.is_available():
        device = "mps"
    
    print(f"Using device: {device}")
    
    # Standard SentenceTransformer
    model = SentenceTransformer(model_name, device=device)

    # 4. Generate Embeddings
    print("Generating embeddings for 'serialized_text'...")
    sentences = df['serialized_text'].fillna("").tolist()
    
    # Generate embeddings
    embeddings = model.encode(
        sentences, 
        show_progress_bar=True, 
        convert_to_numpy=True
    )
    
    vector_size = embeddings.shape[1]
    print(f"Generated {len(embeddings)} embeddings with dimension {vector_size}.")

    # 5. Connect to Qdrant (Local Docker)
    print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        # Test connection
        client.get_collections()
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        print("Make sure Docker container is running: 'docker-compose up -d'")
        return

    # 6. Create collection
    print(f"Creating (or recreating) collection '{collection_name}'...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    # 7. Prepare and Upload Points
    print("Uploading points to Qdrant...")
    points = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Preparing Points"):
        # Build payload
        payload = {col: row[col] for col in payload_cols if col in df.columns}
        
        # Rename url to product_url for consistency
        if 'url' in payload:
            payload['product_url'] = payload.pop('url')

        # Clean up NaN values for Qdrant compatibility (it doesn't like NaNs)
        payload = {k: (v if pd.notna(v) else "") for k, v in payload.items()}
        
        points.append(PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload=payload
        ))

    # Batch upsert
    # Breaking into chunks if list is very large, but for ~1000 items direct upsert is fine
    chunk_size = 100
    for i in range(0, len(points), chunk_size):
        chunk = points[i:i+chunk_size]
        client.upsert(
            collection_name=collection_name,
            points=chunk
        )
        print(f"Uploaded batch {i} - {i+len(chunk)}")

    print(f"--- Finished ---")
    print(f"Successfully uploaded {len(points)} points to collection '{collection_name}'.")
    
    # Verify count
    info = client.get_collection(collection_name)
    print(f"Collection status: {info.status}")
    print(f"Total points: {info.points_count}")

if __name__ == "__main__":
    main()
