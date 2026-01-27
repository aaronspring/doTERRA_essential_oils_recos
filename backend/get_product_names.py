"""
Utility script to fetch all product names from Qdrant and generate system prompt.
"""

from qdrant_client import QdrantClient

try:
    from config import QDRANT_COLLECTION, QDRANT_HOST, QDRANT_PORT
except ImportError:
    import os

    from dotenv import load_dotenv

    load_dotenv()
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "essential_oils")


def get_all_product_names() -> list[str]:
    """
    Fetch all product names from Qdrant collection.

    Returns:
        List of unique product names sorted alphabetically
    """
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    product_names = set()

    # Scroll through all points in the collection
    points, _ = client.scroll(collection_name=QDRANT_COLLECTION, limit=1000, with_payload=True)

    while points:
        for point in points:
            if hasattr(point, "payload") and "product_name" in point.payload:
                product_names.add(point.payload["product_name"])

        # Get next batch
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000,
            with_payload=True,
            offset=len(product_names),
        )

    return sorted(list(product_names))


if __name__ == "__main__":
    names = get_all_product_names()
    print(f"Found {len(names)} unique products:")
    for name in names:
        print(f"  - {name}")
