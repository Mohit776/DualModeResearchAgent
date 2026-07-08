import json
from .state import AgentState
from ..observability import logfire
from ..rag import retrieve_risks
from ..llm import summarize_risks

def retrieve_risks_node(state: AgentState) -> AgentState:
    year = state.get("filing_year")
    if year is None:
        raise ValueError("filing_year is required in state for risk retrieval")
        
    with logfire.span("🛡️ node.retrieve_risks", ticker=state["ticker"], year=year):
        risk_results = retrieve_risks(
            "Summarize key risk factors disclosed in the 10-K filing",
            state["ticker"],
            year,
        )
        
        if not risk_results:
            state["risk_chunks"] = []
            state["risks"] = []
            state["citations"] = []
            return state

        # risk_results is a list of dicts with text, chunk_index, score
        state["risk_chunks"] = risk_results
        state["risks"] = [r["text"] for r in risk_results]

        # Build citations
        state["citations"] = [
            {
                "source": f"10-K {state['ticker']} ({year})",
                "chunk_index": r.get("chunk_index", -1),
                "relevance_score": r.get("score", 0),
                "excerpt": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
            }
            for r in risk_results
        ]
    return state

def summarize_risks_node(state: AgentState) -> AgentState:
    with logfire.span("⚠️ node.summarize_risks", ticker=state["ticker"]):
        if not state.get("risks"):
            state["risk_summary"] = {"industry_risks": [], "operational_risks": [], "regulatory_risks": []}
            return state
            
        result = summarize_risks(state["risks"])
        state["risk_summary"] = json.loads(result) if isinstance(result, str) else result
    return state
