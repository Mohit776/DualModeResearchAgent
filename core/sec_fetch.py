import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from .observability import logfire

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
    text = soup.get_text(separator=" ", strip=True)
    text_lower = text.lower()

    # Find all occurrences of "item 1a"
    starts = []
    i = 0
    while True:
        idx = text_lower.find("item 1a", i)
        if idx == -1:
            break
        starts.append(idx)
        i = idx + 1

    if not starts:
        logfire.warn("Could not find Item 1A, falling back to full document prefix")
        return text[:50000]

    # Find the largest block between an "item 1a" and the next "item 1b" or "item 2"
    best_text = ""
    for start in starts:
        end = text_lower.find("item 1b", start)
        if end == -1:
            end = text_lower.find("item 2", start)
        
        if end != -1 and end > start:
            chunk = text[start:end]
            if len(chunk) > len(best_text):
                best_text = chunk

    if len(best_text) < 1000:
        # If the best we found is still suspiciously small, fallback
        logfire.warn("Best Item 1A match was too small, falling back to 50k chars from last known start")
        return text[starts[-1]:starts[-1]+50000]

    return best_text


def fetch_latest_10k_risks(ticker):
    """Fetch the latest 10-K risk factors from SEC EDGAR for a given ticker.

    Returns:
        tuple: (risk_text: str, filing_year: int)
    """
    with logfire.span("📄 sec.fetch_10k", ticker=ticker):
        cik = get_cik(ticker)
        accession, document, filing_year = get_latest_10k_metadata(cik)
        html = download_10k(cik, accession, document)
        risk_text = extract_risk_factors(html)
        logfire.info("📄 Fetched 10-K for {ticker} ({year}), {n_chars} chars",
                     ticker=ticker, year=filing_year, n_chars=len(risk_text))
        return risk_text, filing_year

