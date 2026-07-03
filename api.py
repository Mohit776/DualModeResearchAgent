import os
from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import uvicorn
import json
from groq import Groq

from core.rag import create_collection, ingest_document, get_client, COLLECTION_NAME
from core.workflow import build_graph
from core.sec_fetch import fetch_latest_10k_risks, fetch_indian_stock_risks
from core.config import GROQ_API_KEY

app = FastAPI(title="Quant Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}


class AnalyzeRequest(BaseModel):
    ticker: str
    mode: str = "deep" # "quick" or "deep"
    filing_year: int = 2023

@app.post("/api/analyze")
async def analyze_stock(req: AnalyzeRequest):
    ticker = req.ticker.upper().strip()
    filing_year = req.filing_year
    mode = req.mode

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
        
    client = get_client()

    already_ingested = False
    if client.collection_exists(COLLECTION_NAME):
        from qdrant_client import models as qdrant_models
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=qdrant_models.Filter(
                must=[qdrant_models.FieldCondition(key="ticker", match=qdrant_models.MatchValue(value=ticker))]
            ),
            limit=1,
            with_payload=True
        )
        if results[0]:
            filing_year = results[0][0].payload.get("year", filing_year)
            already_ingested = True

    if not already_ingested:
        # Auto-fetch logic mirrored from frontend.py
        if ticker.endswith(".NS") or ticker.endswith(".BO"):
            try:
                risk_text, fetched_year = fetch_indian_stock_risks(ticker, filing_year=filing_year)
                if not client.collection_exists(COLLECTION_NAME):
                    create_collection()
                ingest_document(risk_text, ticker, fetched_year)
                filing_year = fetched_year
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Yahoo Finance fetch failed: {e}")
        else:
            try:
                risk_text, fetched_year = fetch_latest_10k_risks(ticker)
                if not client.collection_exists(COLLECTION_NAME):
                    create_collection()
                ingest_document(risk_text, ticker, fetched_year)
                filing_year = fetched_year
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"SEC EDGAR fetch failed: {e}")

    # Run LangGraph
    try:
        graph = build_graph()
        final_state = graph.invoke({"ticker": ticker, "mode": mode, "filing_year": filing_year})
        
        # We also want the financials object inside final_state, and the report object
        return {
            "success": True,
            "ticker": ticker,
            "mode": mode,
            "filing_year": filing_year,
            "report": final_state.get("report", {}),
            "financials": final_state.get("financials", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_document(
    file: UploadFile,
    ticker: str = Form(...),
    year: int = Form(2023)
):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        ticker = ticker.upper().strip()
        
        client = get_client()
        if not client.collection_exists(COLLECTION_NAME):
            create_collection()
            
        ingest_document(text, ticker, year)
        
        return {"success": True, "message": f"Successfully ingested document for {ticker} ({year})"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
class ChatRequest(BaseModel):
    message: str
    ticker: Optional[str] = None
    report_context: Optional[Any] = None

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")

    system_prompt = (
        "You are QuantBot, an expert AI stock market and equity research assistant. "
        "Answer the user's questions clearly, concisely, and accurately. "
        "Use bullet points for readability where appropriate."
    )

    if req.ticker and req.report_context:
        report_str = json.dumps(req.report_context)
        system_prompt += (
            f"\n\nContext: The user is currently viewing a financial report for {req.ticker}. "
            f"Here is the report data: {report_str}\n"
            "If the user asks about the current stock or report, use this data to answer."
        )

    client = Groq(api_key=GROQ_API_KEY)
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1024,
        )
        return {"success": True, "reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
