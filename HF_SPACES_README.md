---
title: dōTERRA Essential Oils Discovery Engine
emoji: 🌿
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
---

# dōTERRA Essential Oils Discovery Engine

FastAPI backend for semantic search and recommendations of essential oils.

## Features

- Vector-based semantic search using Qdrant
- Recommendation engine using embeddings
- CORS-enabled for frontend integration
- Langfuse tracing support (optional)

## Environment Variables

Required:
- `QDRANT_HOST`: Qdrant server hostname
- `QDRANT_PORT`: Qdrant server port
- `QDRANT_COLLECTION`: Qdrant collection name
- `QDRANT_API_KEY`: Qdrant API key

Optional:
- `MODEL_NAME`: Embedding model name (default: jinaai/jina-embeddings-v2-base-de)
- `ALLOWED_ORIGINS`: CORS allowed origins
- `PERPLEXITY_API_KEY`: For alternative search
- `OPENAI_API_KEY`: For LLM features
- `LANGFUSE_PUBLIC_KEY`: For tracing
- `LANGFUSE_SECRET_KEY`: For tracing
- `LANGFUSE_HOST`: Langfuse host

## API Endpoints

- `GET /`: Health check
- `POST /search`: Semantic search
- `POST /recommendations`: Get recommendations based on likes/dislikes
- `POST /perplexity_search`: Alternative search via Perplexity

## Documentation

See [HF_SPACES_DEPLOYMENT.md](https://github.com/aaronspring/doTERRA_essential_oils_recos/blob/main/HF_SPACES_DEPLOYMENT.md) for full setup instructions.
