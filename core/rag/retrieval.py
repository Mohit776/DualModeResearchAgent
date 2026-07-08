from qdrant_client import models
from ..observability import logfire
from .client import get_client, COLLECTION_NAME
from .embeddings import embed_single, build_sparse_vector

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
    with logfire.span("🔍 rag.retrieve", ticker=ticker, year=year, limit=limit) as span:
        client = get_client()

        # Dense query vector
        dense_vec = embed_single(query)
        # Sparse query vector
        sparse_vec = build_sparse_vector(query)

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
        with logfire.span("☁️ qdrant.query", collection=COLLECTION_NAME, limit=limit):
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

        hits = [
            {
                "text": hit.payload["text"],
                "chunk_index": hit.payload.get("chunk_index", -1),
                "score": round(hit.score, 4),
            }
            for hit in results.points
        ]
        span.set_attribute("n_results", len(hits))
        return hits
