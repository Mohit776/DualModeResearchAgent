import requests
from .config import POLYGON_API_KEY

BASE = "https://api.polygon.io"


def get_us_financials(ticker, filing_year=None):
    url = (
        f"https://api.polygon.io/vX/reference/financials"
        f"?ticker={ticker}&limit=2&timeframe=annual"
        f"&sort=period_of_report_date&order=desc"
        f"&include_sources=true"
    )
    if filing_year:
        url += f"&period_of_report_date.lte={filing_year}-12-31"
    url += f"&apiKey={POLYGON_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data.get("status") == "ERROR" or "error" in data:
        error_msg = data.get('error', 'Unknown Error')
        raise ValueError(f"Polygon API Error: {error_msg}")
        
    return data


def get_financials(ticker, filing_year=None):
    """Fetch US financials."""
    sym = ticker.upper()
    if sym.endswith(".NS") or sym.endswith(".BO"):
        raise ValueError(f"Indian stocks ({sym}) are not supported in this lightweight version.")
    
    return get_us_financials(sym, filing_year=filing_year)


def _extract_period(result):
    """Extract the fiscal period label from a result, trying multiple fields."""
    # Try Polygon fields in order of preference
    for field in ("period_of_report_date", "end_date"):
        val = result.get(field)
        if val:
            return str(val)
    # Try fiscal_year (Polygon returns this as a string like "2024")
    fy = result.get("fiscal_year")
    if fy:
        return str(fy)
    return None


def compute_kpis(data, filing_year=None):
    results = data.get("results", [])
    if len(results) < 2:
        raise ValueError("Not enough financial data (need 2 periods)")

    result_a = results[0]
    result_b = results[1]

    # Extract period strings for ordering
    date_a = _extract_period(result_a) or ""
    date_b = _extract_period(result_b) or ""

    # Ensure correct ordering: latest (curr year) first, previous (prev year) second
    if date_a and date_b and date_a < date_b:
        result_a, result_b = result_b, result_a
        date_a, date_b = date_b, date_a

    latest_result = result_a
    previous_result = result_b

    latest = latest_result["financials"]["income_statement"]
    previous = previous_result["financials"]["income_statement"]

    # Extract period dates — use multiple fallbacks
    latest_period = _extract_period(latest_result)
    prev_period = _extract_period(previous_result)

    # Final fallback: derive from user-supplied filing_year
    if not latest_period and filing_year:
        latest_period = str(filing_year)
    if not prev_period and filing_year:
        prev_period = str(int(filing_year) - 1)
    # If still nothing, show the filing year positions
    latest_period = latest_period or "Current"
    prev_period = prev_period or "Previous"

    revenue_latest = latest["revenues"]["value"]
    revenue_prev = previous["revenues"]["value"]

    op_income_latest = latest.get("operating_income_loss", {}).get("value", 0)
    op_income_prev = previous.get("operating_income_loss", {}).get("value", 0)

    # YoY Growth = (Current Year Revenue - Previous Year Revenue) / Previous Year Revenue
    yoy_growth = (revenue_latest - revenue_prev) / revenue_prev if revenue_prev else 0

    op_margin_latest = op_income_latest / revenue_latest if revenue_latest else 0
    op_margin_prev = op_income_prev / revenue_prev if revenue_prev else 0

    kpis = {
        "revenue_latest": revenue_latest,
        "revenue_prev": revenue_prev,
        "yoy_growth": round(yoy_growth, 4),
        "op_income_latest": op_income_latest,
        "op_income_prev": op_income_prev,
        "op_margin_latest": round(op_margin_latest, 4),
        "op_margin_prev": round(op_margin_prev, 4),
        "latest_period": latest_period,
        "prev_period": prev_period,
    }

    # Extract real shares outstanding and net debt for DCF
    # From Polygon: balance_sheet is nested inside each result
    market_data = data.get("_market_data", {})
    if market_data:
        kpis["shares_outstanding"] = market_data.get("shares_outstanding", 0)
        kpis["net_debt"] = market_data.get("net_debt", 0)
    else:
        # Try to extract from Polygon balance sheet data
        try:
            bal = latest_result["financials"].get("balance_sheet", {})
            # Polygon uses basic/diluted weighted average shares
            shares = (
                latest_result["financials"]
                .get("income_statement", {})
                .get("basic_average_shares", {})
                .get("value", 0)
            )
            total_debt = (
                bal.get("long_term_debt", {}).get("value", 0)
                + bal.get("current_debt", {}).get("value", 0)
            )
            cash = bal.get("cash", {}).get("value", 0)
            kpis["shares_outstanding"] = shares
            kpis["net_debt"] = total_debt - cash
        except Exception:
            kpis["shares_outstanding"] = 0
            kpis["net_debt"] = 0

    return kpis


def get_company_sic(ticker):
    """Return the SIC code and company name."""
    sym = ticker.upper()
    if sym.endswith(".NS") or sym.endswith(".BO"):
        return None, sym

    # US (Polygon)
    url = f"{BASE}/v3/reference/tickers/{sym}?apiKey={POLYGON_API_KEY}"
    try:
        data = requests.get(url).json()
        result = data.get("results", {})
        sic_code = result.get("sic_code")
        name = result.get("name", sym)
        return sic_code, name
    except Exception:
        return None, sym


def get_peers(ticker, max_peers=2):
    """
    Dynamically discover related companies.
    Indian stocks fallback to sector-based static peers or empty due to lack of a direct peer API.
    """
    sym = ticker.upper()
    
    if sym.endswith(".NS") or sym.endswith(".BO"):
        # For India, finding direct peers programmatically via Yahoo is hard without heavy scraping.
        # Fallback to an empty list or predefined sector maps if you want.
        # Here we just return empty list so the peer agent skips it gracefully instead of crashing.
        return []

    # US (Polygon)
    try:
        url = f"{BASE}/v1/related-companies/{sym}?apiKey={POLYGON_API_KEY}"
        data = requests.get(url).json()
        candidates = [
            item["ticker"]
            for item in data.get("results", [])
            if item["ticker"].upper() != sym
        ]

        valid_peers = []
        for candidate in candidates:
            if len(valid_peers) >= max_peers:
                break
            try:
                fin_data = get_financials(candidate)
                if len(fin_data.get("results", [])) >= 2:
                    valid_peers.append(candidate)
            except Exception:
                continue

        return valid_peers
    except Exception:
        return []
