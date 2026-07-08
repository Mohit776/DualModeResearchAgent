import os
import sys
import io

# Force stdout to UTF-8 to prevent Windows terminal emoji crashes
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import uvicorn
import json
from groq import Groq

# Bootstrap Logfire FIRST (before any other core imports so instrumentation hooks load)
from core.observability import logfire  # noqa: F401 — side-effect import

from core.rag import create_collection, ingest_document, get_client, COLLECTION_NAME
from core.workflow import build_graph
from core.sec_fetch import fetch_latest_10k_risks
from core.config import GROQ_API_KEY
from core.llm import _chat
from core.chatbot.chatbot import chat, ChatRequest

app = FastAPI(title="Quant Agent API")

# Auto-instrument all FastAPI routes — request/response spans + exceptions
logfire.instrument_fastapi(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}


class AnalyzeRequest(BaseModel):
    ticker: str
    filing_year: Optional[int] = None

@app.post("/api/analyze")
async def analyze_stock(req: AnalyzeRequest):
    ticker = req.ticker.upper().strip()
    filing_year = req.filing_year

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
        
    client = get_client()

    already_ingested = False
    if client.collection_exists(COLLECTION_NAME):
        from qdrant_client import models as qdrant_models
        
        must_conditions = [qdrant_models.FieldCondition(key="ticker", match=qdrant_models.MatchValue(value=ticker))]
        if filing_year is not None:
            must_conditions.append(qdrant_models.FieldCondition(key="year", match=qdrant_models.MatchValue(value=filing_year)))
            
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=qdrant_models.Filter(must=must_conditions),
            limit=1,
            with_payload=True
        )
        if results[0]:
            already_ingested = True
            if filing_year is None:
                # If no year was requested, use the year from the stored document
                filing_year = results[0][0].payload.get("year")

    if not already_ingested:
        # Ensure collection exists with proper indexes
        if not client.collection_exists(COLLECTION_NAME):
            print(f"[RAG] Creating Qdrant collection '{COLLECTION_NAME}'...")
            create_collection()

        # Auto-fetch and ingest
        if ticker.endswith(".NS") or ticker.endswith(".BO"):
            raise HTTPException(status_code=400, detail="Indian stocks are not supported on this lightweight server.")

        try:
            print(f"[RAG] Fetching 10-K risks from SEC for {ticker}...")
            risk_text, fetched_year = fetch_latest_10k_risks(ticker)
            print(f"[RAG] Ingesting {len(risk_text)} chars into Qdrant for {ticker} ({fetched_year})...")
            ingest_document(risk_text, ticker, fetched_year)
            print(f"[RAG] Ingestion complete for {ticker}.")
            filing_year = fetched_year
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"SEC 10-K fetch failed: {e}")

    # Run LangGraph
    try:
        graph = build_graph()
        with logfire.span("🚀 langgraph.invoke", ticker=ticker, filing_year=filing_year):
            final_state = graph.invoke({"ticker": ticker, "filing_year": filing_year})
        
        return {
            "success": True,
            "ticker": ticker,
            "filing_year": filing_year,
            "report": final_state.get("report", {}),
            "financials": final_state.get("financials", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    return chat(req)

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
