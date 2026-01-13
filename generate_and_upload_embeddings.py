import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
import torch

def main():
    # 1. Configuration
    csv_path = '/Users/aaronspring/coding/dottera_essential_oils_recos/single_oil.csv'
    model_name = 'jinaai/jina-embeddings-v4'
    collection_name = "essential_oils"
    
    # Payload columns to include
    payload_cols = [
        'product_name', 
        'product_sub_name', 
        'product_image_url', 
        'product_description', 
        'brand_lifestyle_title', 
        'brand_lifestyle_description'
    ]

    print(f"--- Starting Embeddings Generation and Upload ---")
    
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

    # 3. Initialize Model
    print(f"Initializing model: {model_name}...")
    print("This may take a while to download the model (approx. 6GB)...")
    
    # Use CUDA if available, else CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and torch.backends.mps.is_available():
        device = "mps"
    
    print(f"Using device: {device}")
    
    # Jina v4 requires trust_remote_code=True
    # For multimodal models in ST, we can use the model name directly
    # Note: Jina v4 has adapters. For pure text embedding, it usually defaults correctly.
    model = SentenceTransformer(
        model_name, 
        trust_remote_code=True, 
        device=device
    )

    # 4. Generate Embeddings
    print("Generating embeddings for 'serialized_text'...")
    sentences = df['serialized_text'].fillna("").tolist()
    
    # Generate embeddings
    embeddings = model.encode(
        sentences, 
        show_progress_bar=True, 
        convert_to_numpy=True,
        task="retrieval"
    )
    
    vector_size = embeddings.shape[1]
    print(f"Generated {len(embeddings)} embeddings with dimension {vector_size}.")

    # 5. Connect to Qdrant (in-memory)
    print("Connecting to Qdrant (in-memory)...")
    client = QdrantClient(":memory:")

    # 6. Create collection
    print(f"Creating collection '{collection_name}'...")
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
        # Clean up NaN values for Qdrant compatibility
        payload = {k: (v if pd.notna(v) else "") for k, v in payload.items()}
        
        points.append(PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload=payload
        ))

    # Batch upsert
    client.upsert(
        collection_name=collection_name,
        points=points
    )

    print(f"--- Finished ---")
    print(f"Successfully uploaded {len(points)} points to collection '{collection_name}'.")
    
    # Optional: Verify search
    print("\nVerifying with a sample search: 'Something for relaxation'")
    query_text = "Something for relaxation"
    query_vector = model.encode([query_text], task="retrieval")[0].tolist()
    
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=3
    )
    
    print("Top results:")
    for hit in search_result:
        print(f" - {hit.payload.get('product_name')} (Score: {hit.score:.4f})")

if __name__ == "__main__":
    main()
