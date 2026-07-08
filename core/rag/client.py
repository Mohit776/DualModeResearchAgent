from qdrant_client import QdrantClient
from ..config import QDRANT_API_KEY, QDRANT_CLUSTER, COLLECTION_NAME

# ── Singleton Qdrant client ──────────────────────────────────────────────────
_client = None
DB_PATH = "./db"

def get_client():
    global _client
    if _client is None:
        try:
            if QDRANT_CLUSTER and QDRANT_API_KEY:
                _client = QdrantClient(url=QDRANT_CLUSTER, api_key=QDRANT_API_KEY)
            else:
                _client = QdrantClient(path=DB_PATH)
            
            # Simple health check
            _client.get_collections()
        except Exception as e:
            from ..observability import logfire
            logfire.error("Failed to connect to Qdrant", error=str(e))
            raise ConnectionError(f"Failed to connect to Qdrant: {e}")
    return _client
