import os
import traceback
from contextlib import asynccontextmanager

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

try:
    from config import MODEL_NAME, QDRANT_COLLECTION, QDRANT_HOST, QDRANT_PORT, VECTOR_NAME
except ImportError:
    # Fallback for different execution contexts
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")
    MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"
    VECTOR_NAME = MODEL_NAME.split("/")[-1]

# Global variables for model and client
model = None
qdrant_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, qdrant_client

    # Load Model
    print(f"Loading model: {MODEL_NAME}...")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Using device: {device}")

    try:
        model = SentenceTransformer(MODEL_NAME, device=device, trust_remote_code=True)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e

    # Initialize Qdrant Client
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # Check if collection exists
        collections = qdrant_client.get_collections()
        exists = any(c.name == QDRANT_COLLECTION for c in collections.collections)
        if not exists:
            print(
                f"Warning: Collection '{QDRANT_COLLECTION}' "
                "does not exist yet. Please run ingestion."
            )
        else:
            print(f"Collection '{QDRANT_COLLECTION}' found.")

    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        # We don't raise here to allow app to start even if qdrant is temporarily down

    yield

    # Cleanup
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class RecommendRequest(BaseModel):
    positive: list[int]  # List of point IDs
    negative: list[int] = []
    limit: int = 10


class ProductPayload(BaseModel):
    product_name: str
    product_sub_name: str | None = None
    product_image_url: str | None = None
    product_description: str | None = None
    brand_lifestyle_title: str | None = None
    brand_lifestyle_description: str | None = None
    product_url: str | None = None


class SearchResult(BaseModel):
    id: int
    score: float
    payload: ProductPayload


# --- Endpoints ---


@app.get("/")
def read_root():
    return {"status": "ok", "service": "essential-oils-discovery-backend"}


@app.post("/search", response_model=list[SearchResult])
async def search_oils(request: SearchRequest):
    if not model or not qdrant_client:
        raise HTTPException(status_code=503, detail="Service not ready (model or db missing)")

    # 1. Vectorize query
    # Standard ST encode
    query_vector = model.encode([request.query])[0].tolist()

    # 2. Search Qdrant (using new query_points API)
    try:
        search_result = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            using=VECTOR_NAME,
            limit=request.limit,
            with_payload=True,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Qdrant search failed: {str(e)}")

    # 3. Format results
    results = []
    # query_points returns QueryResponse containing points
    for hit in search_result.points:
        results.append(SearchResult(id=hit.id, score=hit.score, payload=hit.payload))

    return results


@app.post("/recommend", response_model=list[SearchResult])
async def recommend_oils(request: RecommendRequest):
    """
    Recommend items based on positive (liked) and negative (disliked) item IDs.
    Does NOT require a text query. Uses Qdrant's internal recommendation API
    which uses the stored vectors of the referenced IDs.
    """
    if not qdrant_client:
        raise HTTPException(status_code=503, detail="Database connection missing")

    if not request.positive:
        raise HTTPException(
            status_code=400, detail="At least one positive ID is required for recommendation."
        )

    try:
        recommend_input = models.RecommendInput(
            positive=request.positive, negative=request.negative
        )
        recommend_query = models.RecommendQuery(recommend=recommend_input)

        recommend_result = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=recommend_query,
            using=VECTOR_NAME,
            limit=request.limit,
            with_payload=True,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Qdrant recommendation failed: {str(e)}")

    results = []
    for hit in recommend_result.points:
        results.append(SearchResult(id=hit.id, score=hit.score, payload=hit.payload))

    return results


@app.get("/random", response_model=list[SearchResult])
async def get_random_oils(limit: int = 5):
    """Returns random items for initial discovery"""
    if not qdrant_client:
        raise HTTPException(status_code=503, detail="Database connection missing")

    # Qdrant scroll API or random sampling
    # Ideally use a random vector or scroll.
    # Simple scroll for now.

    try:
        # We scroll with a random offset? No easy way to random offset.
        # We can search with a random vector.

        # Default dim
        dim = 384

        if model:
            dim = model.get_sentence_embedding_dimension()

        random_vector = np.random.rand(dim).tolist()

        search_result = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=random_vector,
            using=VECTOR_NAME,
            limit=limit,
            with_payload=True,
        )

        # Format
        results = []
        for hit in search_result.points:
            results.append(SearchResult(id=hit.id, score=hit.score, payload=hit.payload))
        return results

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Random fetch failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
