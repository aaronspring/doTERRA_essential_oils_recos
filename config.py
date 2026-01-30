import os

from dotenv import load_dotenv

load_dotenv()

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Embedding model configuration
# Must match the model used during data ingestion into Qdrant
# all-MiniLM-L6-v2: ~90MB, 384-dim embeddings
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# The vector name in Qdrant is derived from the model name (the slug after /)
VECTOR_NAME = MODEL_NAME.split("/")[-1]

# Perplexity API Configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online")

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
