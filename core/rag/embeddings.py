import re
import math
import hashlib
from collections import Counter
from qdrant_client.models import SparseVector

import requests
from ..config import GEMINI_API, GEMINI_EMBED_MODEL, FALLBACK_EMBED_MODEL, EMBEDDING_DIM
from ..observability import logfire

_model = None

def get_model():
    """Lazy-load fastembed TextEmbedding model."""
    global _model
    if _model is None:
        from fastembed import TextEmbedding 
        _model = TextEmbedding(FALLBACK_EMBED_MODEL)
    return _model

def _embed_texts_fastembed(texts: list[str]) -> list[list[float]]:
    """Batch-encode texts via fastembed (returns plain Python lists)."""
    with logfire.span("✨ rag.embed", provider="fastembed", n_texts=len(texts), model=FALLBACK_EMBED_MODEL):
        return [vec.tolist() for vec in get_model().embed(texts)]

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-encode texts using Gemini with fallback to fastembed."""
    if not GEMINI_API:
        return _embed_texts_fastembed(texts)
        
    with logfire.span("✨ rag.embed", provider="gemini", n_texts=len(texts), model=GEMINI_EMBED_MODEL) as span:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_EMBED_MODEL}:batchEmbedContents?key={GEMINI_API}"
            
            all_embeddings = []
            batch_size = 50
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                requests_payload = [
                    {
                        "model": GEMINI_EMBED_MODEL,
                        "content": {"parts": [{"text": text}]},
                        "outputDimensionality": EMBEDDING_DIM
                    }
                    for text in batch_texts
                ]
                
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={"requests": requests_payload},
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"Gemini API error: {response.text}")
                    raise ValueError("Gemini API request failed")
                    
                data = response.json()
                embeddings = [item["values"] for item in data["embeddings"]]
                
                # Check dimensions to prevent Qdrant 400 Bad Request
                if embeddings and len(embeddings[0]) != EMBEDDING_DIM:
                    raise ValueError(f"Dimension mismatch: got {len(embeddings[0])}, expected {EMBEDDING_DIM}")

                all_embeddings.extend(embeddings)

            span.set_attribute("total_embeddings", len(all_embeddings))
            return all_embeddings
            
        except Exception as e:
            logfire.warn("⚠️ Gemini embed failed, falling back to fastembed", error=str(e))
            return _embed_texts_fastembed(texts)

def embed_single(text: str) -> list[float]:
    return embed_texts([text])[0]

# ── Sparse vector helpers (simple BM25-style tokenisation) ───────────────────
_TOKENISE_RE = re.compile(r"[a-zA-Z0-9]+")

def _tokenise(text: str) -> list[str]:
    return [t.lower() for t in _TOKENISE_RE.findall(text)]

def build_sparse_vector(text: str) -> SparseVector:
    """Build a sparse vector from term frequencies (BM25-lite)."""
    tokens = _tokenise(text)
    if not tokens:
        return SparseVector(indices=[0], values=[0.0])

    freq = Counter(tokens)
    indices = []
    values = []
    for token, count in freq.items():
        idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % (2**31)
        tf = 1 + math.log(count)
        indices.append(idx)
        values.append(round(tf, 4))
    return SparseVector(indices=indices, values=values)
