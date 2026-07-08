from .state import AgentState
from ..observability import logfire
from ..llm import generate_thesis, generate_confidence_score
from ..reflection import reflect

def thesis_node(state: AgentState) -> AgentState:
    with logfire.span("📜 node.thesis", ticker=state["ticker"]):
        state["thesis"] = generate_thesis(
            state["ticker"],
            state["financials"],
            state["risk_summary"],
        )
    return state


def reflection_node(state: AgentState) -> AgentState:
    """Senior Analyst reviews the report for contradictions and hallucinations."""
    with logfire.span("🤔 node.reflection", ticker=state["ticker"], revision=state.get("revision_count", 0)):
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

        result = reflect(partial_report, state["financials"], revision_count)
        state["reflection"] = result
        state["revision_count"] = result.get("revision_count", revision_count + 1)
    return state


def confidence_scoring_node(state: AgentState) -> AgentState:
    """Generate confidence-weighted conclusion for the investment memo."""
    with logfire.span("⭐ node.confidence_scoring", ticker=state["ticker"]):
        partial_report = {
            "ticker": state["ticker"],
            "financial_overview": state.get("financial_analysis", {}),
            "risk_assessment": state.get("risk_summary", {}),
            "thesis": state.get("thesis", {}),
            "dcf_valuation": state.get("dcf_result", {}),
        }
        reflection = state.get("reflection", {})

        try:
            confidence = generate_confidence_score(partial_report, reflection)
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
    with logfire.span("📋 node.assemble_report", ticker=state["ticker"]):
        report = {
            "ticker": state["ticker"],
            "financial_overview": state.get("financial_analysis", {}),
            "risk_assessment": state.get("risk_summary", {}),
        }

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
