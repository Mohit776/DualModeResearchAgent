import json
from groq import Groq
from openai import OpenAI
from .config import (
    GROQ_API_KEY, ZHIPU_API_KEY, ZHIPU_BASE_URL,
    QUICK_MODEL, DEEP_MODEL,
)

# ── LLM Clients ──────────────────────────────────────────────────────────────

_groq_client = Groq(api_key=GROQ_API_KEY)
_zhipu_client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)


def _chat(mode: str, messages: list, temperature: float = 0.2, json_mode: bool = True):
    """Unified chat helper that routes to the correct LLM based on mode."""
    if mode == "deep":
        client, model = _zhipu_client, DEEP_MODEL
    else:
        client, model = _groq_client, QUICK_MODEL

    kwargs = dict(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


# ── Public API ────────────────────────────────────────────────────────────────

def explain_kpis(ticker: str, kpis: dict, mode: str = "quick") -> str:
    latest_period = kpis.get('latest_period', 'unknown')
    prev_period = kpis.get('prev_period', 'unknown')
    prompt = f"""
    You are a financial analyst.

    Company: {ticker}

    Fiscal Period (Latest): {latest_period}
    Fiscal Period (Previous): {prev_period}

    Financial Data:
    Revenue ({latest_period}): {kpis['revenue_latest']}
    Revenue ({prev_period}): {kpis['revenue_prev']}
    YoY Growth: {kpis['yoy_growth'] * 100:.2f}%
    Operating Income ({latest_period}): {kpis['op_income_latest']}
    Operating Income ({prev_period}): {kpis['op_income_prev']}
    Operating Margin ({latest_period}): {kpis['op_margin_latest'] * 100:.2f}%
    Operating Margin ({prev_period}): {kpis['op_margin_prev'] * 100:.2f}%

    Explain what this means in simple financial terms.
    Use the exact fiscal period dates above, do NOT guess or swap them.
    Provide the output exactly as JSON:
    {{
      "revenue_growth": "short string explaining revenue YoY growth between {prev_period} and {latest_period}",
      "operating_margin_trend": "short string explaining operating margin trend between {prev_period} and {latest_period}"
    }}
    """
    return _chat(mode, [{"role": "user", "content": prompt}], temperature=0.2)


def summarize_risks(chunks: list, mode: str = "quick") -> str:
    context = "\n\n".join(chunks)
    max_chars = 8000
    if len(context) > max_chars:
        context = context[:max_chars] + "\n\n[...truncated]"

    prompt = f"""
You are a financial analyst.

Below are extracted sections from a company's 10-K.

{context}

Summarize the key risk factors strictly using the provided text.

Return the output exactly as JSON:

{{
  "industry_risks": ["short bullet", "short bullet"],
  "operational_risks": ["short bullet", "short bullet"],
  "regulatory_risks": ["short bullet", "short bullet"]
}}

Do not include anything outside the JSON.
"""
    return _chat(mode, [{"role": "user", "content": prompt}], temperature=0.2)


def generate_thesis(ticker: str, financials: dict, risks: dict, mode: str = "deep") -> dict:
    prompt = f"""
    You are an equity research analyst.

    Company: {ticker}

    Financial Summary:
    {json.dumps(financials, indent=2)}

    Risk Summary:
    {json.dumps(risks, indent=2)}

    Provide output as JSON:
    {{
      "bull_case": "short paragraph",
      "bear_case": "short paragraph"
    }}
    """
    result = _chat(mode, [{"role": "user", "content": prompt}], temperature=0.3)
    return json.loads(result)


def generate_dcf_params(ticker: str, financials: dict, mode: str = "deep") -> dict:
    """Ask the LLM to estimate reasonable DCF input parameters from financials."""
    # Use real shares outstanding and net debt from actual data
    real_shares = financials.get("shares_outstanding", 0)
    real_net_debt = financials.get("net_debt", 0)

    shares_instruction = ""
    if real_shares and real_shares > 0:
        shares_instruction = f"""\n    IMPORTANT: Use these REAL values from the company's filings:
    - shares_outstanding: {real_shares}
    - net_debt: {real_net_debt}
    Do NOT estimate or guess these values. Use the exact numbers above."""

    prompt = f"""
    You are a senior financial analyst doing a DCF valuation.

    Company: {ticker}

    Financial Data:
    {json.dumps(financials, indent=2)}
    {shares_instruction}

    Based on this data, estimate reasonable DCF input parameters.
    Return the output exactly as JSON:
    {{
      "free_cash_flows": [number, number, number, number, number],
      "growth_rates": [decimal, decimal, decimal, decimal, decimal],
      "terminal_growth_rate": decimal,
      "wacc": decimal,
      "cost_of_equity": decimal,
      "cost_of_debt": decimal,
      "tax_rate": decimal,
      "debt_weight": decimal,
      "equity_weight": decimal,
      "shares_outstanding": {real_shares if real_shares and real_shares > 0 else 'number'},
      "net_debt": {real_net_debt if real_shares and real_shares > 0 else 'number'},
      "reasoning": "Brief explanation of key assumptions"
    }}

    Use realistic estimates. All decimals should be ratios (e.g. 0.10 for 10%).
    """
    result = _chat(mode, [{"role": "user", "content": prompt}], temperature=0.2)
    parsed = json.loads(result)

    # Force override with real data if available (don't trust the LLM for these)
    if real_shares and real_shares > 0:
        parsed["shares_outstanding"] = real_shares
        parsed["net_debt"] = real_net_debt

    return parsed


def review_report(report: dict, financials: dict, mode: str = "deep") -> dict:
    """Senior Analyst reflection — checks for contradictions and hallucinations."""
    prompt = f"""
    You are a Senior Equity Analyst reviewing a junior analyst's report.

    ORIGINAL FINANCIAL DATA (ground truth):
    {json.dumps(financials, indent=2)}

    JUNIOR ANALYST REPORT:
    {json.dumps(report, indent=2)}

    Your job:
    1. Check for FINANCIAL CONTRADICTIONS — does the report contradict the data?
    2. Check for DATA HALLUCINATIONS — does the report claim data not present?
    3. Check for MATH ERRORS — are computed metrics consistent?
    4. Check for MISSING RISK FACTORS — any obvious omissions?

    Return the output exactly as JSON:
    {{
      "approved": true or false,
      "issues_found": ["issue 1", "issue 2"],
      "corrections": ["correction 1", "correction 2"],
      "feedback": "overall feedback string"
    }}

    If the report is accurate and complete, set approved to true and leave
    issues_found and corrections as empty arrays.
    """
    result = _chat(mode, [{"role": "user", "content": prompt}], temperature=0.1)
    return json.loads(result)


def generate_confidence_score(report: dict, reflection: dict, mode: str = "deep") -> dict:
    """Generate a confidence-weighted conclusion for the investment memo."""
    prompt = f"""
    You are a senior portfolio strategist.

    INVESTMENT REPORT:
    {json.dumps(report, indent=2)}

    QUALITY REVIEW:
    {json.dumps(reflection, indent=2)}

    Based on the quality of data, consistency of analysis, and review feedback,
    generate a confidence-weighted investment conclusion.

    Return the output exactly as JSON:
    {{
      "overall_confidence": "HIGH" or "MEDIUM" or "LOW",
      "confidence_score": decimal between 0 and 1,
      "data_quality": "HIGH" or "MEDIUM" or "LOW",
      "analysis_consistency": "HIGH" or "MEDIUM" or "LOW",
      "conclusion": "2-3 sentence investment conclusion with confidence weighting",
      "key_assumptions": ["assumption 1", "assumption 2"],
      "recommended_action": "BUY" or "HOLD" or "SELL" or "FURTHER_RESEARCH"
    }}
    """
    result = _chat(mode, [{"role": "user", "content": prompt}], temperature=0.2)
    return json.loads(result)