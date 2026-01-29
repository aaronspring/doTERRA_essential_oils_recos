import json
import os
from contextlib import asynccontextmanager

import numpy as np
import torch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

# Optional Langfuse tracing
HAS_LANGFUSE = True
try:
    from langfuse import Langfuse
    from langfuse.openai import OpenAI
except (ImportError, RuntimeError):
    HAS_LANGFUSE = False
    Langfuse = type(None)  # type: ignore
    from openai import OpenAI

try:
    from config import (
        LANGFUSE_HOST,
        LANGFUSE_PUBLIC_KEY,
        LANGFUSE_SECRET_KEY,
        MODEL_NAME,
        PERPLEXITY_API_KEY,
        QDRANT_API_KEY,
        QDRANT_COLLECTION,
        QDRANT_HOST,
        QDRANT_PORT,
        VECTOR_NAME,
    )
except ImportError:
    # Fallback for different execution contexts
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    MODEL_NAME: str = "jinaai/jina-embeddings-v2-base-de"
    VECTOR_NAME = MODEL_NAME.split("/")[-1]
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Global variables for model and client
model = None
qdrant_client = None
langfuse = None


def _init_langfuse():
    """Initialize Langfuse client if credentials are available."""
    global langfuse
    if not HAS_LANGFUSE:
        print("Langfuse not available (Python 3.14+ not supported yet)")
        langfuse = None
        return

    if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
        try:
            langfuse = Langfuse(
                public_key=LANGFUSE_PUBLIC_KEY,
                secret_key=LANGFUSE_SECRET_KEY,
                host=LANGFUSE_HOST,
            )
        except Exception as e:
            print(f"Failed to initialize Langfuse: {e}")
            langfuse = None
    else:
        langfuse = None


def _get_all_product_names() -> list[str]:
    """
    Fetch all product names from Qdrant collection.

    Returns:
        List of unique product names sorted alphabetically
    """
    if not qdrant_client:
        return []

    product_names = set()

    try:
        # Scroll through all points in the collection
        points, _ = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION, limit=1000, with_payload=True
        )

        while points:
            for point in points:
                if hasattr(point, "payload") and "product_name" in point.payload:
                    product_names.add(point.payload["product_name"])

            # Get next batch
            points, _ = qdrant_client.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=1000,
                with_payload=True,
                offset=len(product_names),
            )
    except Exception as e:
        print(f"Error fetching product names: {e}")

    return sorted(list(product_names))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, qdrant_client, langfuse

    # Initialize Langfuse
    _init_langfuse()
    if langfuse:
        print("Langfuse initialized successfully.")
    else:
        print("Langfuse not configured (no credentials provided).")

    # Load Model
    print(f"Loading model: {MODEL_NAME}...")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Using device: {device}")

    # Skip model loading during Vercel build to save memory
    if os.getenv("SKIP_MODEL_LOAD") != "true":
        try:
            model = SentenceTransformer(MODEL_NAME, device=device, trust_remote_code=True)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise e
    else:
        print("Model loading skipped (will be loaded on first request)")

    # Initialize Qdrant Client
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        if QDRANT_API_KEY:
            # Cloud connection
            qdrant_client = QdrantClient(
                url=QDRANT_HOST,
                api_key=QDRANT_API_KEY,
                prefer_grpc=False,
            )
        else:
            # Local connection
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
    if langfuse:
        langfuse.flush()


app = FastAPI(lifespan=lifespan)

# CORS configuration
# In production, restrict to specific origins
# Default includes localhost for development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(
    ","
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---


class SearchRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=500, description="Search query for essential oils"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")
    liked_oils: list[str] = Field(
        default_factory=list, description="List of names of oils the user likes"
    )
    disliked_oils: list[str] = Field(
        default_factory=list, description="List of names of oils the user dislikes"
    )


class RecommendRequest(BaseModel):
    positive: list[int] = Field(
        ..., min_length=1, description="List of point IDs for positive recommendations"
    )
    negative: list[int] = Field(
        default_factory=list, description="List of point IDs for negative recommendations"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")


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
    source: str = "embedding"  # "embedding" or "perplexity"


# --- Endpoints ---


@app.get("/")
def read_root():
    return {"status": "ok", "service": "essential-oils-discovery-backend"}


def _ensure_model_loaded():
    """Lazy load model on first request if skipped during startup."""
    global model
    if model is None:
        print(f"Lazy loading model: {MODEL_NAME}...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            model = SentenceTransformer(MODEL_NAME, device=device, trust_remote_code=True)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise e


@app.post("/search", response_model=list[SearchResult])
async def search_oils(request: SearchRequest):
    _ensure_model_loaded()
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
        print(f"Qdrant search failed: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Search operation failed")

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
        print(f"Qdrant recommendation failed: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Recommendation operation failed")

    results = []
    for hit in recommend_result.points:
        results.append(SearchResult(id=hit.id, score=hit.score, payload=hit.payload))

    return results


@app.post("/search/perplexity", response_model=list[SearchResult])
async def search_oils_perplexity(request: SearchRequest):
    _ensure_model_loaded()
    if not model or not qdrant_client or not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=503, detail="Service not ready")

    oil_names = []

    try:
        # Resolve path to SYSTEM_PROMPT.md
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, "SYSTEM_PROMPT.md")

        # Get all available product names from Qdrant
        available_products = _get_all_product_names()
        products_str = ", ".join(available_products)

        with open(prompt_path) as f:
            system_prompt = f.read()

        # Inject available products into system prompt
        system_prompt = system_prompt.replace("{{ available_products }}", products_str)

        # Prepare formatted user message
        user_feeling = request.query
        liked_str = ", ".join(request.liked_oils) if request.liked_oils else "Keine"
        disliked_str = ", ".join(request.disliked_oils) if request.disliked_oils else "Keine"

        # Resolve path to USER_PROMPT.md
        user_prompt_path = os.path.join(base_dir, "USER_PROMPT.md")
        with open(user_prompt_path) as f:
            user_prompt_template = f.read()

        user_prompt = (
            user_prompt_template.replace("{{ user_feeling }}", user_feeling)
            .replace("{{ liked_str }}", liked_str)
            .replace("{{ disliked_str }}", disliked_str)
        )

        # Langfuse-instrumented OpenAI client
        search_domains = ["doterra.com"]
        client = OpenAI(
            api_key=PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai",
        )

        response = client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            extra_body={"search_domain_filter": search_domains},
            name="essential_oils_recos",
            metadata={
                "user_feeling": user_feeling,
                "liked_oils": liked_str,
                "disliked_oils": disliked_str,
            },
        )

        content = response.choices[0].message.content
        print(f"DEBUG: Perplexity raw response: {content}")

        # Parse JSON list from content
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):  # sometimes it's just ```
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            oil_names = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract lines if JSON fails
            print(f"Perplexity JSON parse failed. Content: {content}")
            oil_names = []

        if not isinstance(oil_names, list):
            oil_names = []

        # Ensure we take at most 5
        oil_names = oil_names[:5]
        print(f"DEBUG: Perplexity parsed oils: {oil_names}")

    except Exception as e:
        print(f"Perplexity search failed: {e}")
        # Continue with empty perplexity results

    perplexity_results = []
    found_ids = set()

    # 2. Search Qdrant for these oils using name matching with fuzzy fallback
    if oil_names:
        product_map = {}  # Map product names to their ids
        product_base_names = {}  # Map base names (before parenthesis) to full names

        # Build map of product names to IDs
        points, _ = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION, limit=1000, with_payload=True
        )
        while points:
            for point in points:
                if hasattr(point, "payload") and "product_name" in point.payload:
                    full_name = point.payload["product_name"]
                    product_map[full_name] = point.id
                    # Also index by base name (before parenthesis)
                    base_name = full_name.split("(")[0].strip()
                    if base_name not in product_base_names:
                        product_base_names[base_name] = full_name
            points, _ = qdrant_client.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=1000,
                with_payload=True,
                offset=len(product_map),
            )

        # Match Perplexity results to products
        for name in oil_names:
            full_name = None

            # Try exact match first
            if name in product_map:
                full_name = name
            # Try base name match (e.g., "Lavender" -> "Lavender (Lavendel)")
            elif name.split("(")[0].strip() in product_base_names:
                full_name = product_base_names[name.split("(")[0].strip()]
            # Fallback: use embedding to find closest match
            else:
                try:
                    name_vector = model.encode([name])[0].tolist()
                    search_res = qdrant_client.query_points(
                        collection_name=QDRANT_COLLECTION,
                        query=name_vector,
                        using=VECTOR_NAME,
                        limit=1,
                        with_payload=True,
                    )
                    if search_res.points and search_res.points[0].score > 0.8:
                        full_name = search_res.points[0].payload["product_name"]
                except Exception as e:
                    print(f"Error embedding search for {name}: {e}")

            # Add to results if found and not duplicate
            if full_name and full_name in product_map:
                product_id = product_map[full_name]
                if product_id not in found_ids:
                    try:
                        points = qdrant_client.retrieve(
                            collection_name=QDRANT_COLLECTION,
                            ids=[product_id],
                            with_payload=True,
                        )
                        if points:
                            hit = points[0]
                            res = SearchResult(
                                id=hit.id,
                                score=0.99,
                                payload=hit.payload,
                                source="perplexity",
                            )
                            perplexity_results.append(res)
                            found_ids.add(product_id)
                    except Exception as e:
                        print(f"Error retrieving product {full_name}: {e}")

    # 3. Regular Embedding Search for the rest
    query_vector = model.encode([request.query])[0].tolist()

    search_result_embedding = qdrant_client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        using=VECTOR_NAME,
        limit=request.limit + 5,  # Fetch extra to account for deduplication
        with_payload=True,
    )

    embedding_results = []
    for hit in search_result_embedding.points:
        if hit.id not in found_ids:
            embedding_results.append(
                SearchResult(id=hit.id, score=hit.score, payload=hit.payload, source="embedding")
            )

    # Combine results
    final_results = perplexity_results + embedding_results

    return final_results[: request.limit]


@app.get("/random", response_model=list[SearchResult])
async def get_random_oils(
    limit: int = Query(
        default=5, ge=1, le=100, description="Maximum number of random items to return"
    ),
):
    """Returns random items for initial discovery"""
    _ensure_model_loaded()
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
        print(f"Random fetch failed: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Random fetch operation failed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
