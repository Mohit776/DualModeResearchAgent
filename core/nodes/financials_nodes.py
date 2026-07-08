import json
from .state import AgentState
from ..observability import logfire
from ..financials import get_financials, compute_kpis, get_peers
from ..llm import explain_kpis

def fetch_financials_node(state: AgentState) -> AgentState:
    with logfire.span("📊 node.fetch_financials", ticker=state["ticker"]):
        filing_year = state.get("filing_year")
        data = get_financials(state["ticker"], filing_year=filing_year)
        state["financials"] = compute_kpis(data, filing_year=filing_year)
    return state

def analyze_financials_node(state: AgentState) -> AgentState:
    with logfire.span("📈 node.analyze_financials", ticker=state["ticker"]):
        result = explain_kpis(state["ticker"], state["financials"])
        state["financial_analysis"] = json.loads(result) if isinstance(result, str) else result
    return state

def peer_comparison_node(state: AgentState) -> AgentState:
    with logfire.span("👥 node.peer_comparison", ticker=state["ticker"]):
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
