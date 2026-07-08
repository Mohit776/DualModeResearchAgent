from langgraph.graph import StateGraph, END

from .nodes.state import AgentState
from .nodes import (
    fetch_financials_node,
    analyze_financials_node,
    retrieve_risks_node,
    summarize_risks_node,
    peer_comparison_node,
    quant_analysis_node,
    thesis_node,
    reflection_node,
    confidence_scoring_node,
    assemble_report_node,
)


# ── Routing ───────────────────────────────────────────────────────────────────

def route_mode(state: AgentState) -> str:
    """Route to peer_comparison."""
    return "peer_comparison"


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