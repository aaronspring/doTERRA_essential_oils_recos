import os

from dotenv import load_dotenv

load_dotenv()

# Qdrant configuration: local
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")

# Qdrant configuration: remote
# QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant url")
# QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
# QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")

# Embedding model configuration
# Using smaller model to fit within Vercel's 8GB build environment
# all-MiniLM-L6-v2: ~90MB, 384-dim embeddings
# Previous: jinaai/jina-embeddings-v2-base-de (~500MB)
MODEL_NAME = "all-MiniLM-L6-v2"

# The vector name in Qdrant is derived from the model name (the slug after /)
VECTOR_NAME = MODEL_NAME.split("/")[-1]

# Perplexity API Configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
