import os

# Qdrant configuration: local
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")

# Qdrant configuration: remote
# QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant url")
# QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
# QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")

# Embedding model configuration
# We use Jina Embeddings v2 base German model
MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"

# The vector name in Qdrant is derived from the model name (the slug after /)
VECTOR_NAME = MODEL_NAME.split("/")[-1]
