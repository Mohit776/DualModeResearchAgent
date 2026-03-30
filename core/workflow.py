import json
from typing import TypedDict, Dict, Any, List, Optional

from langgraph.graph import StateGraph, END
from .financials import get_financials, compute_kpis, get_peers
from .llm import (
    explain_kpis, summarize_risks, generate_thesis,
    generate_dcf_params, generate_confidence_score,
)
from .rag import retrieve_risks
from .quant_tools import compute_wacc, execute_dcf, run_sensitivity_analysis
from .reflection import reflect


# ── State ─────────────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    ticker: str
    mode: str                              # "quick" or "deep"
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


# ── Nodes ─────────────────────────────────────────────────────────────────────

def fetch_financials_node(state: AgentState) -> AgentState:
    filing_year = state.get("filing_year")
    data = get_financials(state["ticker"], filing_year=filing_year)
    state["financials"] = compute_kpis(data, filing_year=filing_year)
    return state


def analyze_financials_node(state: AgentState) -> AgentState:
    mode = state.get("mode", "quick")
    result = explain_kpis(state["ticker"], state["financials"], mode=mode)
    state["financial_analysis"] = json.loads(result) if isinstance(result, str) else result
    return state


def retrieve_risks_node(state: AgentState) -> AgentState:
    year = state.get("filing_year", 2023)
    risk_results = retrieve_risks(
        "Summarize key risk factors disclosed in the 10-K filing",
        state["ticker"],
        year,
    )
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
    mode = state.get("mode", "quick")
    result = summarize_risks(state["risks"], mode=mode)
    state["risk_summary"] = json.loads(result) if isinstance(result, str) else result
    return state


def peer_comparison_node(state: AgentState) -> AgentState:
    filing_year = state.get("filing_year")
    peers = get_peers(state["ticker"])
    if not peers:
        return state

    peer_margins = {}
    for peer_ticker in peers:
        try:
            peer_data = get_financials(peer_ticker, filing_year=filing_year)
            peer_kpis = compute_kpis(peer_data)
            peer_margins[peer_ticker] = peer_kpis["op_margin_latest"]
        except Exception:
            continue

    if not peer_margins:
        return state

    avg_peer_margin = sum(peer_margins.values()) / len(peer_margins)

    state["peer_comparison"] = {
        "peers": list(peer_margins.keys()),
        "peer_margins": {k: round(v, 4) for k, v in peer_margins.items()},
        "avg_peer_operating_margin": round(avg_peer_margin, 4),
        "company_operating_margin": state["financials"]["op_margin_latest"],
    }
    return state


def quant_analysis_node(state: AgentState) -> AgentState:
    """Run deterministic DCF + WACC using Python — no LLM math guessing."""
    mode = state.get("mode", "deep")

    # Ask the LLM to generate reasonable DCF parameters from financials
    try:
        dcf_params = generate_dcf_params(state["ticker"], state["financials"], mode=mode)
    except Exception:
        state["dcf_result"] = {"error": "Failed to generate DCF parameters"}
        state["wacc_result"] = {}
        state["sensitivity"] = {}
        return state

    # Compute WACC deterministically
    wacc_result = compute_wacc(dcf_params)
    state["wacc_result"] = wacc_result

    # Override the LLM's WACC estimate with our computed value
    dcf_params["wacc"] = wacc_result["wacc"]

    # Run DCF deterministically
    dcf_result = execute_dcf(dcf_params)
    state["dcf_result"] = dcf_result

    # Sensitivity analysis
    if "error" not in dcf_result:
        sensitivity = run_sensitivity_analysis(dcf_params)
        state["sensitivity"] = sensitivity
    else:
        state["sensitivity"] = {}

    return state


def thesis_node(state: AgentState) -> AgentState:
    mode = state.get("mode", "deep")
    state["thesis"] = generate_thesis(
        state["ticker"],
        state["financials"],
        state["risk_summary"],
        mode=mode,
    )
    return state


def reflection_node(state: AgentState) -> AgentState:
    """Senior Analyst reviews the report for contradictions and hallucinations."""
    revision_count = state.get("revision_count", 0)

    # Build partial report for review
    partial_report = {
        "ticker": state["ticker"],
        "financial_overview": state.get("financial_analysis", {}),
        "risk_assessment": state.get("risk_summary", {}),
        "peer_comparison": state.get("peer_comparison", {}),
        "thesis": state.get("thesis", {}),
        "dcf_valuation": state.get("dcf_result", {}),
    }

    result = reflect(partial_report, state["financials"], revision_count, mode="deep")
    state["reflection"] = result
    state["revision_count"] = result.get("revision_count", revision_count + 1)
    return state


def confidence_scoring_node(state: AgentState) -> AgentState:
    """Generate confidence-weighted conclusion for the investment memo."""
    partial_report = {
        "ticker": state["ticker"],
        "financial_overview": state.get("financial_analysis", {}),
        "risk_assessment": state.get("risk_summary", {}),
        "thesis": state.get("thesis", {}),
        "dcf_valuation": state.get("dcf_result", {}),
    }
    reflection = state.get("reflection", {})

    try:
        confidence = generate_confidence_score(partial_report, reflection, mode="deep")
    except Exception:
        confidence = {
            "overall_confidence": "MEDIUM",
            "confidence_score": 0.5,
            "conclusion": "Confidence scoring unavailable.",
            "recommended_action": "FURTHER_RESEARCH",
        }

    state["confidence"] = confidence
    return state


def assemble_report_node(state: AgentState) -> AgentState:
    """Assemble the final structured investment memo."""
    report = {
        "ticker": state["ticker"],
        "mode": state.get("mode", "quick"),
        "financial_overview": state.get("financial_analysis", {}),
        "risk_assessment": state.get("risk_summary", {}),
    }

    # Deep mode additions
    if state.get("peer_comparison"):
        report["peer_comparison"] = state["peer_comparison"]
    if state.get("thesis"):
        report["thesis"] = state["thesis"]
    if state.get("dcf_result"):
        report["dcf_valuation"] = state["dcf_result"]
    if state.get("wacc_result"):
        report["wacc_analysis"] = state["wacc_result"]
    if state.get("sensitivity"):
        report["sensitivity_analysis"] = state["sensitivity"]
    if state.get("reflection"):
        report["senior_analyst_review"] = {
            "approved": state["reflection"].get("approved", True),
            "feedback": state["reflection"].get("feedback", ""),
            "revision_cycles": state.get("revision_count", 0),
        }
    if state.get("confidence"):
        report["investment_conclusion"] = state["confidence"]
    if state.get("citations"):
        report["citations"] = state["citations"]

    state["report"] = report
    return state


# ── Routing ───────────────────────────────────────────────────────────────────

def route_mode(state: AgentState) -> str:
    """Route to peer_comparison for 'deep' mode, else go straight to report."""
    if state.get("mode") == "deep":
        return "peer_comparison"
    return "assemble_report"


def route_reflection(state: AgentState) -> str:
    """
    After reflection, either loop back to thesis (if rejected and under max)
    or proceed to confidence scoring.
    """
    reflection = state.get("reflection", {})
    approved = reflection.get("approved", True)
    revision_count = state.get("revision_count", 0)

    if not approved and revision_count < 2:
        # Loop back — the thesis node will regenerate with the feedback context
        return "thesis"
    return "confidence_scoring"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    # All nodes
    graph.add_node("fetch_financials",    fetch_financials_node)
    graph.add_node("analyze_financials",  analyze_financials_node)
    graph.add_node("retrieve_risks",      retrieve_risks_node)
    graph.add_node("summarize_risks",     summarize_risks_node)
    graph.add_node("peer_comparison",     peer_comparison_node)
    graph.add_node("quant_analysis",      quant_analysis_node)
    graph.add_node("thesis",              thesis_node)
    graph.add_node("reflection",          reflection_node)
    graph.add_node("confidence_scoring",  confidence_scoring_node)
    graph.add_node("assemble_report",     assemble_report_node)

    # Entry point
    graph.set_entry_point("fetch_financials")

    # Linear chain (both modes)
    graph.add_edge("fetch_financials",    "analyze_financials")
    graph.add_edge("analyze_financials",  "retrieve_risks")
    graph.add_edge("retrieve_risks",      "summarize_risks")

    # Mode branch after summarize_risks
    graph.add_conditional_edges(
        "summarize_risks",
        route_mode,
        {
            "peer_comparison": "peer_comparison",
            "assemble_report": "assemble_report",
        },
    )

    # Deep mode chain: peers → quant → thesis → reflection → (loop or confidence)
    graph.add_edge("peer_comparison",   "quant_analysis")
    graph.add_edge("quant_analysis",    "thesis")
    graph.add_edge("thesis",            "reflection")

    # Cyclical reflection: approved → confidence, rejected → back to thesis
    graph.add_conditional_edges(
        "reflection",
        route_reflection,
        {
            "thesis": "thesis",
            "confidence_scoring": "confidence_scoring",
        },
    )

    graph.add_edge("confidence_scoring", "assemble_report")
    graph.add_edge("assemble_report",    END)

    return graph.compile()