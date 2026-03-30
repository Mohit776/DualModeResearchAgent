import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Single shared header used for all SEC EDGAR requests
SEC_HEADERS = {"User-Agent": "FinancialResearchAgent piyushmangla64@gmail.com"}


def get_cik(ticker):
    url = "https://www.sec.gov/files/company_tickers.json"
    data = requests.get(url, headers=SEC_HEADERS).json()

    for item in data.values():
        if item["ticker"].lower() == ticker.lower():
            return str(item["cik_str"]).zfill(10)

    raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR")

def get_latest_10k_metadata(cik):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = requests.get(url, headers=SEC_HEADERS).json()
    filings = data["filings"]["recent"]

    for i, form in enumerate(filings["form"]):
        if form == "10-K":
            accession_clean = filings["accessionNumber"][i].replace("-", "")
            primary_doc     = filings["primaryDocument"][i]
            filed_date      = filings["filingDate"][i]          # e.g. "2024-02-21"
            filing_year     = int(filed_date[:4])
            return accession_clean, primary_doc, filing_year

    raise ValueError("No 10-K filing found for this company")

def download_10k(cik, accession, document):
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{document}"
    html = requests.get(url, headers=SEC_HEADERS).text
    return html




def extract_risk_factors(html):
    soup = BeautifulSoup(html, features="xml")

    text = soup.get_text()

    start = text.lower().find("item 1a. risk factors")
    end = text.lower().find("item 1b.")

    return text[start:end]


def fetch_latest_10k_risks(ticker):
    """Fetch the latest 10-K risk factors from SEC EDGAR for a given ticker.

    Returns:
        tuple: (risk_text: str, filing_year: int)
    """
    cik = get_cik(ticker)
    accession, document, filing_year = get_latest_10k_metadata(cik)
    html = download_10k(cik, accession, document)
    risk_text = extract_risk_factors(html)
    return risk_text, filing_year


def fetch_indian_stock_risks(ticker, filing_year=None):
    """Auto-generate a risk/business document for Indian stocks using yfinance.

    Combines business summary, sector info, and recent news to create a
    document suitable for RAG ingestion — no manual upload needed.

    Returns:
        tuple: (risk_text: str, filing_year: int)
    """
    import yfinance as yf
    from datetime import datetime

    stock = yf.Ticker(ticker)
    info = stock.info

    year = filing_year or datetime.now().year
    company_name = info.get("longName", info.get("shortName", ticker))
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
    summary = info.get("longBusinessSummary", "No business summary available.")
    market_cap = info.get("marketCap", 0)
    employees = info.get("fullTimeEmployees", "N/A")
    country = info.get("country", "India")
    currency = info.get("currency", "INR")

    # Build a comprehensive risk-like document from available data
    sections = []

    sections.append(f"COMPANY OVERVIEW — {company_name} ({ticker})")
    sections.append(f"Sector: {sector} | Industry: {industry}")
    sections.append(f"Country: {country} | Currency: {currency}")
    if market_cap:
        sections.append(f"Market Capitalization: {market_cap:,.0f} {currency}")
    if employees != "N/A":
        sections.append(f"Full-Time Employees: {employees:,}")
    sections.append("")

    sections.append("BUSINESS SUMMARY AND RISK FACTORS")
    sections.append(summary)
    sections.append("")

    # Industry and operational risks derived from sector
    sections.append("INDUSTRY AND OPERATIONAL RISKS")
    sections.append(
        f"The company operates in the {industry} industry within the {sector} sector. "
        f"Key risks include regulatory changes in {country}, competitive pressures within "
        f"the {industry} space, macroeconomic conditions affecting the {sector} sector, "
        f"currency fluctuations impacting {currency}-denominated operations, and supply "
        f"chain or operational disruptions."
    )
    sections.append("")

    # Try to get recent news for additional risk context
    try:
        news = stock.news
        if news:
            sections.append("RECENT NEWS AND DEVELOPMENTS")
            for article in news[:8]:
                content = article.get("content", {})
                title = content.get("title", article.get("title", ""))
                summary_text = content.get("summary", "")
                if title:
                    sections.append(f"- {title}")
                    if summary_text:
                        sections.append(f"  {summary_text}")
            sections.append("")
    except Exception:
        pass

    # Try to get major holders info
    try:
        holders = stock.major_holders
        if holders is not None and not holders.empty:
            sections.append("OWNERSHIP STRUCTURE")
            for _, row in holders.iterrows():
                sections.append(f"- {row.iloc[0]}: {row.iloc[1]}")
            sections.append("")
    except Exception:
        pass

    risk_text = "\n".join(sections)
    return risk_text, year