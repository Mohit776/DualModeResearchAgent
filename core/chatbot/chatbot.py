import json
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from core.config import GROQ_API_KEY, GROQ_FALLBACK_API_KEY
from core.llm import _chat
from core.observability import logfire

class ChatRequest(BaseModel):
    message: str
    ticker: Optional[str] = None
    report_context: Optional[Any] = None
    history: Optional[list] = []

def chat(req: ChatRequest):
    if not GROQ_API_KEY and not GROQ_FALLBACK_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API keys are not configured")

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

    try:
        messages = [{"role": "system", "content": system_prompt}]
        if req.history:
            messages.extend(req.history)
        messages.append({"role": "user", "content": req.message})

        with logfire.span("💬 chatbot.chat", ticker=req.ticker):
            reply = _chat(messages, temperature=0.1, json_mode=False, model="openai/gpt-oss-20b")
        return {"success": True, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))