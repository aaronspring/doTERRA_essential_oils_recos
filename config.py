import os

from dotenv import load_dotenv

load_dotenv()

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils_paddle")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Embedding model configuration
# Must match the model used during data ingestion into Qdrant
# all-MiniLM-L6-v2: ~90MB, 384-dim embeddings
MODEL_NAME = os.getenv("MODEL_NAME", "jinaai/jina-embeddings-v2-base-de")

# The vector name in Qdrant is derived from the model name (the slug after /)
# Prefixed with "full_" to match the ingestion script's naming convention
VECTOR_NAME = f"full_{MODEL_NAME.split('/')[-1]}"

# Perplexity API Configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
