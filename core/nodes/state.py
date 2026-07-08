from typing import TypedDict, Dict, Any, List

class AgentState(TypedDict, total=False):
    ticker: str
    filing_year: int                       # year of the 10-K used for RAG
    financials: Dict[str, Any]
    financial_analysis: Dict[str, Any]
    risk_chunks: List[Dict[str, Any]]      # raw retrieval results with citations
    risks: List[str]                       # text-only for backward compat
    risk_summary: Dict[str, Any]
    peer_comparison: Dict[str, Any]
    thesis: Dict[str, Any]
    dcf_result: Dict[str, Any]             # DCF valuation
    wacc_result: Dict[str, Any]            # WACC computation
    sensitivity: Dict[str, Any]            # Sensitivity analysis matrix
    citations: List[Dict[str, str]]        # Traceable source citations
    reflection: Dict[str, Any]            # Senior Analyst review
    confidence: Dict[str, Any]             # Confidence-weighted conclusion
    revision_count: int                    # Reflection loop counter
    report: Dict[str, Any]
