from .state import AgentState
from ..observability import logfire
from ..llm import generate_dcf_params
from ..quant_tools import compute_wacc, execute_dcf, run_sensitivity_analysis

def quant_analysis_node(state: AgentState) -> AgentState:
    """Run deterministic DCF + WACC using Python — no LLM math guessing."""
    with logfire.span("🧮 node.quant_analysis", ticker=state["ticker"]):
        # Ask the LLM to generate reasonable DCF parameters from financials
        try:
            dcf_params = generate_dcf_params(state["ticker"], state["financials"])
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
