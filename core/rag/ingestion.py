import uuid
from qdrant_client import models
from qdrant_client.models import (
    VectorParams, SparseVectorParams, SparseIndexParams,
    Distance, PointStruct
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import EMBEDDING_DIM
from ..observability import logfire
from .client import get_client, COLLECTION_NAME
from .embeddings import embed_texts, build_sparse_vector

# ── Collection management ────────────────────────────────────────────────────
def create_collection():
    client = get_client()
    if client.collection_exists(COLLECTION_NAME):
        logfire.info(f"Collection {COLLECTION_NAME} already exists, skipping creation.")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
            ),
        },
    )
    
    # Create payload indexes for fast filtering
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="ticker",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="year",
        field_schema=models.PayloadSchemaType.INTEGER,
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="doc_type",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )

# ── Ingestion ────────────────────────────────────────────────────────────────
def ingest_document(text: str, ticker: str, year: int, doc_type: str = "10-K"):
    """Ingest a text document with both dense and sparse vectors + rich metadata."""
    with logfire.span("📥 rag.ingest", ticker=ticker, year=year, doc_type=doc_type):
        client = get_client()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = splitter.split_text(text)
        logfire.info("📄 Ingesting {n_chunks} chunks for {ticker}", n_chunks=len(chunks), ticker=ticker)

        # Batch encode all chunks at once (faster than one-by-one)
        dense_vecs = embed_texts(chunks)

        points = []
        for i, chunk in enumerate(chunks):
            sparse_vec = build_sparse_vector(chunk)

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
        logfire.info("✅ Upserted {n_points} points to Qdrant", n_points=len(points))
