"""
Deterministic quantitative tools for financial valuation.

All math is executed in pure Python — no LLM guessing.
These functions receive structured parameters and return structured results.
"""

from __future__ import annotations
from typing import Any


def compute_wacc(params: dict) -> dict:
    """
    Compute Weighted Average Cost of Capital.

    Required params:
        cost_of_equity  (decimal, e.g. 0.10)
        cost_of_debt    (decimal)
        tax_rate        (decimal)
        equity_weight   (decimal, e.g. 0.70)
        debt_weight     (decimal, e.g. 0.30)
    """
    ke = float(params.get("cost_of_equity", 0.10))
    kd = float(params.get("cost_of_debt", 0.05))
    tax = float(params.get("tax_rate", 0.21))
    we = float(params.get("equity_weight", 0.7))
    wd = float(params.get("debt_weight", 0.3))

    wacc = (we * ke) + (wd * kd * (1 - tax))

    return {
        "wacc": round(wacc, 6),
        "wacc_pct": f"{wacc * 100:.2f}%",
        "breakdown": {
            "equity_component": round(we * ke, 6),
            "debt_component": round(wd * kd * (1 - tax), 6),
            "cost_of_equity": ke,
            "cost_of_debt": kd,
            "tax_rate": tax,
            "equity_weight": we,
            "debt_weight": wd,
        },
    }


def execute_dcf(params: dict) -> dict:
    """
    Deterministic Discounted Cash Flow valuation.

    Required params:
        free_cash_flows      list of projected FCFs (5 years)
        terminal_growth_rate decimal
        wacc                 decimal
        shares_outstanding   int
        net_debt             number (positive = debt exceeds cash)
    """
    fcfs = [float(x) for x in params.get("free_cash_flows", [])]
    tgr = float(params.get("terminal_growth_rate", 0.025))
    wacc = float(params.get("wacc", 0.10))
    shares = float(params.get("shares_outstanding", 1))
    net_debt = float(params.get("net_debt", 0))

    if not fcfs:
        return {"error": "No free cash flows provided"}
    if wacc <= tgr:
        return {"error": f"WACC ({wacc}) must exceed terminal growth rate ({tgr})"}

    # Discount projected FCFs
    pv_fcfs = []
    for i, fcf in enumerate(fcfs, start=1):
        pv = fcf / ((1 + wacc) ** i)
        pv_fcfs.append(round(pv, 2))

    # Terminal value (Gordon Growth Model)
    last_fcf = fcfs[-1]
    terminal_value = (last_fcf * (1 + tgr)) / (wacc - tgr)
    n = len(fcfs)
    pv_terminal = terminal_value / ((1 + wacc) ** n)

    # Enterprise value
    enterprise_value = sum(pv_fcfs) + pv_terminal

    # Equity value
    equity_value = enterprise_value - net_debt

    # Per-share value
    per_share = equity_value / shares if shares > 0 else 0

    return {
        "pv_of_fcfs": pv_fcfs,
        "terminal_value": round(terminal_value, 2),
        "pv_terminal_value": round(pv_terminal, 2),
        "enterprise_value": round(enterprise_value, 2),
        "net_debt": round(net_debt, 2),
        "equity_value": round(equity_value, 2),
        "implied_share_price": round(per_share, 2),
        "shares_outstanding": shares,
        "assumptions": {
            "wacc": wacc,
            "terminal_growth_rate": tgr,
            "projection_years": n,
        },
    }


def run_sensitivity_analysis(
    dcf_params: dict,
    wacc_range: list[float] | None = None,
    tgr_range: list[float] | None = None,
) -> dict:
    """
    Sensitivity analysis: varies WACC and terminal growth rate to produce a
    matrix of implied share prices.
    """
    base_wacc = float(dcf_params.get("wacc", 0.10))
    base_tgr = float(dcf_params.get("terminal_growth_rate", 0.025))

    if wacc_range is None:
        wacc_range = [
            round(base_wacc - 0.02, 4),
            round(base_wacc - 0.01, 4),
            round(base_wacc, 4),
            round(base_wacc + 0.01, 4),
            round(base_wacc + 0.02, 4),
        ]
    if tgr_range is None:
        tgr_range = [
            round(base_tgr - 0.01, 4),
            round(base_tgr - 0.005, 4),
            round(base_tgr, 4),
            round(base_tgr + 0.005, 4),
            round(base_tgr + 0.01, 4),
        ]

    matrix = {}
    for w in wacc_range:
        row = {}
        for g in tgr_range:
            if w <= g:
                row[f"{g:.3%}"] = "N/A"
                continue
            params_copy = {**dcf_params, "wacc": w, "terminal_growth_rate": g}
            result = execute_dcf(params_copy)
            row[f"{g:.3%}"] = result.get("implied_share_price", "ERR")
        matrix[f"{w:.2%}"] = row

    return {
        "wacc_values": [f"{w:.2%}" for w in wacc_range],
        "tgr_values": [f"{g:.3%}" for g in tgr_range],
        "implied_prices": matrix,
        "base_case": {
            "wacc": f"{base_wacc:.2%}",
            "terminal_growth": f"{base_tgr:.3%}",
        },
    }
