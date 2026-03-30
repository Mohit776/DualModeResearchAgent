import re
import uuid
import math
from collections import Counter

from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    VectorParams, SparseVectorParams, SparseIndexParams,
    Distance, PointStruct, NamedVector, NamedSparseVector,
    SparseVector,
)
from fastembed import TextEmbedding 
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── Singleton Qdrant client — persistent local storage ───────────────────────

_client = None
_model = None

COLLECTION_NAME = "financial_docs"
DB_PATH = "./db"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"   # 384-dim, ONNX — no torch needed


def get_model():
    """Lazy-load fastembed TextEmbedding model."""
    global _model
    if _model is None:
        _model = TextEmbedding(EMBED_MODEL)
    return _model


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-encode texts via fastembed (returns plain Python lists)."""
    return [vec.tolist() for vec in get_model().embed(texts)]


def _embed_single(text: str) -> list[float]:
    return _embed_texts([text])[0]


def get_client():
    global _client
    if _client is None:
        _client = QdrantClient(path=DB_PATH)
    return _client


# ── Sparse vector helpers (simple BM25-style tokenisation) ───────────────────

_TOKENISE_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenise(text: str) -> list[str]:
    return [t.lower() for t in _TOKENISE_RE.findall(text)]


def _build_sparse_vector(text: str) -> SparseVector:
    """Build a sparse vector from term frequencies (BM25-lite)."""
    tokens = _tokenise(text)
    if not tokens:
        return SparseVector(indices=[0], values=[0.0])

    freq = Counter(tokens)
    indices = []
    values = []
    for token, count in freq.items():
        idx = abs(hash(token)) % (2**31)
        tf = 1 + math.log(count)
        indices.append(idx)
        values.append(round(tf, 4))
    return SparseVector(indices=indices, values=values)


# ── Collection management ────────────────────────────────────────────────────

def create_collection():
    client = get_client()
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(size=384, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
            ),
        },
    )


# ── Ingestion ────────────────────────────────────────────────────────────────

def ingest_document(text: str, ticker: str, year: int, doc_type: str = "10-K"):
    """Ingest a text document with both dense and sparse vectors + rich metadata."""
    client = get_client()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_text(text)

    # Batch encode all chunks at once (faster than one-by-one)
    dense_vecs = _embed_texts(chunks)

    points = []
    for i, chunk in enumerate(chunks):
        sparse_vec = _build_sparse_vector(chunk)

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": dense_vecs[i],
                    "sparse": sparse_vec,
                },
                payload={
                    "ticker": ticker,
                    "year": year,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "text": chunk,
                },
            )
        )

    # Batch upsert for performance
    BATCH = 64
    for start in range(0, len(points), BATCH):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[start : start + BATCH],
        )


# ── Hybrid retrieval ─────────────────────────────────────────────────────────

def retrieve_risks(
    query: str,
    ticker: str,
    year: int,
    doc_type: str | None = None,
    limit: int = 8,
) -> list[dict]:
    """
    Hybrid retrieval: dense + sparse vectors with metadata hard-filters.

    Returns a list of dicts with 'text', 'chunk_index', and 'score' for
    traceable citations.
    """
    client = get_client()

    # Dense query vector
    dense_vec = _embed_single(query)
    # Sparse query vector
    sparse_vec = _build_sparse_vector(query)

    # Hard metadata filters — prevents cross-contamination across tickers/years
    must_conditions = [
        models.FieldCondition(key="ticker", match=models.MatchValue(value=ticker)),
        models.FieldCondition(key="year", match=models.MatchValue(value=year)),
    ]
    if doc_type:
        must_conditions.append(
            models.FieldCondition(key="doc_type", match=models.MatchValue(value=doc_type))
        )
    qfilter = models.Filter(must=must_conditions)

    # Use prefetch for hybrid search with RRF fusion
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=dense_vec,
                using="dense",
                limit=limit * 2,
                filter=qfilter,
            ),
            models.Prefetch(
                query=sparse_vec,
                using="sparse",
                limit=limit * 2,
                filter=qfilter,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
    )

    return [
        {
            "text": hit.payload["text"],
            "chunk_index": hit.payload.get("chunk_index", -1),
            "score": round(hit.score, 4),
        }
        for hit in results.points
    ]