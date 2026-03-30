import json
import streamlit as st
from core.rag import create_collection, ingest_document, get_client, COLLECTION_NAME
from core.workflow import build_graph
from core.sec_fetch import fetch_latest_10k_risks, fetch_indian_stock_risks

# Single accessor — the global singleton in rag.py ensures one instance per process
def get_qdrant_client():
    return get_client()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quant  Agent · Financial Intelligence",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Dark gradient background */
  .stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 50%, #0f1117 100%);
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12151f 0%, #1a1d2e 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
  }

  /* Hero banner */
  .hero {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 60%);
    animation: shimmer 4s ease-in-out infinite;
  }
  @keyframes shimmer {
    0%, 100% { transform: translate(0,0); }
    50%       { transform: translate(10px, 10px); }
  }
  .hero h1 { color: #fff; font-size: 2.2rem; font-weight: 700; margin: 0; }
  .hero p  { color: rgba(255,255,255,0.8); font-size: 1rem; margin-top: 0.4rem; }

  /* Metric cards */
  .metric-card {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    transition: transform 0.2s, border-color 0.2s;
  }
  .metric-card:hover {
    transform: translateY(-3px);
    border-color: rgba(99,102,241,0.55);
  }
  .metric-label { color: #94a3b8; font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
  .metric-value { color: #e2e8f0; font-size: 1.6rem; font-weight: 700; margin-top: 0.25rem; }
  .metric-delta-pos { color: #34d399; font-size: 0.85rem; font-weight: 600; }
  .metric-delta-neg { color: #f87171; font-size: 0.85rem; font-weight: 600; }

  /* Section headers */
  .section-header {
    display: flex; align-items: center; gap: 0.6rem;
    margin: 1.8rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(99,102,241,0.2);
  }
  .section-header h2 { color: #c4b5fd; font-size: 1.15rem; font-weight: 600; margin: 0; }

  /* Risk pills */
  .risk-tag {
    display: inline-block;
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3);
    color: #fca5a5;
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    font-size: 0.8rem;
    margin: 0.25rem;
  }

  /* Thesis cards */
  .bull-card {
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.25);
    border-radius: 12px; padding: 1.2rem;
  }
  .bear-card {
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.25);
    border-radius: 12px; padding: 1.2rem;
  }
  .bull-card h4 { color: #34d399; margin-top: 0; }
  .bear-card h4 { color: #f87171; margin-top: 0; }
  .bull-card p, .bear-card p { color: #cbd5e1; font-size: 0.9rem; margin: 0; line-height: 1.6; }

  /* Peer badge */
  .peer-badge {
    background: rgba(6,182,212,0.1);
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 8px; padding: 1rem;
    text-align: center;
  }
  .peer-badge .label { color: #67e8f9; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; }
  .peer-badge .value { color: #e2e8f0; font-size: 1.4rem; font-weight: 700; }

  /* Confidence badge */
  .confidence-badge {
    border-radius: 12px; padding: 1.2rem;
    text-align: center;
  }
  .confidence-high {
    background: rgba(52,211,153,0.12);
    border: 1px solid rgba(52,211,153,0.35);
  }
  .confidence-medium {
    background: rgba(251,191,36,0.12);
    border: 1px solid rgba(251,191,36,0.35);
  }
  .confidence-low {
    background: rgba(248,113,113,0.12);
    border: 1px solid rgba(248,113,113,0.35);
  }
  .confidence-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
  .confidence-score { font-size: 2rem; font-weight: 700; margin: 0.3rem 0; }

  /* DCF card */
  .dcf-card {
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.25);
    border-radius: 12px; padding: 1.2rem 1.4rem;
  }
  .dcf-card .label { color: #a78bfa; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
  .dcf-card .value { color: #e2e8f0; font-size: 1.4rem; font-weight: 700; margin-top: 0.2rem; }

  /* Reflection card */
  .reflection-card {
    border-radius: 12px; padding: 1.2rem;
  }
  .reflection-approved {
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.25);
  }
  .reflection-rejected {
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.25);
  }

  /* Citation */
  .citation-item {
    background: rgba(99,102,241,0.06);
    border-left: 3px solid rgba(99,102,241,0.4);
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
    color: #94a3b8;
  }
  .citation-item .cite-meta { color: #6366f1; font-weight: 600; font-size: 0.75rem; }

  /* Status step */
  .step-item {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.5rem 0;
    color: #94a3b8; font-size: 0.88rem;
  }
  .step-done  { color: #34d399; }
  .step-active { color: #818cf8; }

  /* Run button override */
  div.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; border: none; border-radius: 10px;
    font-weight: 600; font-size: 1rem;
    padding: 0.65rem 2rem; width: 100%;
    transition: opacity 0.2s, transform 0.15s;
  }
  div.stButton > button:hover { opacity: 0.88; transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_billions(v):
    """Format a raw dollar value into a readable string."""
    if abs(v) >= 1e9:
        return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"

def delta_html(value_pct):
    arrow = "▲" if value_pct >= 0 else "▼"
    cls = "metric-delta-pos" if value_pct >= 0 else "metric-delta-neg"
    return f'<span class="{cls}">{arrow} {abs(value_pct):.1f}%</span>'

def confidence_color(level):
    colors = {"HIGH": "#34d399", "MEDIUM": "#fbbf24", "LOW": "#f87171"}
    return colors.get(level, "#94a3b8")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌳 Quant  Agent")
    st.markdown("<p style='color:#64748b;font-size:0.8rem;margin-top:-10px;'>Financial Intelligence Platform</p>", unsafe_allow_html=True)
    st.divider()

    ticker = st.text_input(
        "Ticker Symbol",
        value="NVDA",
        placeholder="e.g. AAPL, TSLA…",
        help="NYSE / NASDAQ ticker symbol"
    ).upper().strip()

    mode = st.radio(
        "Analysis Mode",
        options=["quick", "deep"],
        format_func=lambda m: "⚡ Quick (Groq)" if m == "quick" else "🔬 Deep (GLM-4.7 + DCF + Thesis)",
        index=1,
    )

    st.divider()

    st.markdown("**Upload Risk & MD&A Document** *(overrides SEC auto-fetch)*")
    st.caption("Supports US 10-K extracts or Indian Annual Report text")
    uploaded = st.file_uploader(
        "Drop a .txt extract here",
        type=["txt"],
        label_visibility="collapsed"
    )
    ingest_year = st.number_input("Filing Year (if uploading)", min_value=2000, max_value=2030, value=2023, step=1)

    run_btn = st.button("🚀  Run Analysis", use_container_width=True)

    st.divider()
    st.markdown("<p style='color:#475569;font-size:0.75rem;'>Powered by Groq · GLM-4.7 · Qdrant · LangGraph</p>", unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
  <h1>🌳 Quant  Agent · Financial Intelligence</h1>
  <p>AI-powered equity research · KPI analysis · RAG risk assessment · DCF valuation · Investment thesis</p>
</div>
""", unsafe_allow_html=True)


# ── Main logic ────────────────────────────────────────────────────────────────

if run_btn:
    if not ticker:
        st.error("Please enter a valid ticker symbol.")
        st.stop()

    # ── Resolve filing year & ingest if needed ─────────────────────────────
    filing_year = None

    if uploaded is not None:
        with st.spinner("Ingesting uploaded document into Qdrant…"):
            text = uploaded.read().decode("utf-8")
            filing_year = int(ingest_year)
            if not get_qdrant_client().collection_exists(COLLECTION_NAME):
                create_collection()
            ingest_document(text, ticker, filing_year)
        st.success(f"✅ Uploaded document ingested for **{ticker} ({filing_year})**")
    else:
        already_ingested = False
        if get_qdrant_client().collection_exists(COLLECTION_NAME):
            from qdrant_client import models as qdrant_models
            results = get_qdrant_client().scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=qdrant_models.Filter(
                    must=[qdrant_models.FieldCondition(
                        key="ticker",
                        match=qdrant_models.MatchValue(value=ticker)
                    )]
                ),
                limit=1,
                with_payload=True
            )
            if results[0]:
                filing_year = results[0][0].payload.get("year", int(ingest_year))
                already_ingested = True
                st.info(f"ℹ️ Using cached document data for **{ticker} ({filing_year})** already in Qdrant.")

        if not already_ingested:
            # For Indian stocks, auto-fetch from yfinance instead of SEC EDGAR
            if ticker.endswith(".NS") or ticker.endswith(".BO"):
                with st.spinner(f"🌐 Fetching risk & business data for **{ticker}** from Yahoo Finance…"):
                    try:
                        risk_text, filing_year = fetch_indian_stock_risks(ticker, filing_year=int(ingest_year))
                        if not risk_text or len(risk_text) < 100:
                            st.warning("⚠️ Very limited data available from Yahoo Finance. Results may be limited.")
                    except Exception as e:
                        st.error(f"❌ Yahoo Finance fetch failed: {e}")
                        st.stop()

                with st.spinner("📥 Ingesting risk data into Qdrant…"):
                    if not get_qdrant_client().collection_exists(COLLECTION_NAME):
                        create_collection()
                    ingest_document(risk_text, ticker, filing_year)
                st.success(f"✅ Yahoo Finance data ingested for **{ticker} ({filing_year})**")
            else:
                with st.spinner(f"🌐 Fetching latest 10-K for **{ticker}** from SEC EDGAR…"):
                    try:
                        risk_text, filing_year = fetch_latest_10k_risks(ticker)
                        if not risk_text or len(risk_text) < 200:
                            st.warning("⚠️ Risk section was very short or not found in the 10-K. Results may be limited.")
                    except Exception as e:
                        st.error(f"❌ SEC EDGAR fetch failed: {e}")
                        st.stop()

                with st.spinner("📥 Ingesting 10-K risk text into Qdrant…"):
                    if not get_qdrant_client().collection_exists(COLLECTION_NAME):
                        create_collection()
                    ingest_document(risk_text, ticker, filing_year)
                st.success(f"✅ SEC 10-K ingested for **{ticker} ({filing_year})**")

    # -- Run the agent graph --
    filing_year = filing_year or int(ingest_year)

    steps_quick = [
        ("fetch_financials",   "Fetching financial data from Polygon…"),
        ("analyze_financials", "Analyzing KPIs with Groq LLM…"),
        ("retrieve_risks",     "Retrieving relevant 10-K excerpts (hybrid search)…"),
        ("summarize_risks",    "Summarizing risk factors…"),
        ("assemble_report",    "Assembling final report…"),
    ]
    steps_deep = [
        ("fetch_financials",   "Fetching financial data from Polygon…"),
        ("analyze_financials", "Analyzing KPIs with GLM-4.7…"),
        ("retrieve_risks",     "Retrieving relevant 10-K excerpts (hybrid search)…"),
        ("summarize_risks",    "Summarizing risk factors…"),
        ("peer_comparison",    "Discovering & comparing industry peers…"),
        ("quant_analysis",     "Running DCF / WACC valuation (deterministic)…"),
        ("thesis",             "Generating investment thesis…"),
        ("reflection",         "Senior Analyst reviewing report…"),
        ("confidence_scoring", "Computing confidence-weighted conclusion…"),
        ("assemble_report",    "Assembling final investment memo…"),
    ]
    steps = steps_deep if mode == "deep" else steps_quick

    progress_placeholder = st.empty()

    def render_status(current_step_idx):
        html = ""
        for i, (_, label) in enumerate(steps):
            if i < current_step_idx:
                html += f'<div class="step-item step-done">✔ {label}</div>'
            elif i == current_step_idx:
                html += f'<div class="step-item step-active">⟳ {label}</div>'
            else:
                html += f'<div class="step-item">○ {label}</div>'
        progress_placeholder.markdown(html, unsafe_allow_html=True)

    render_status(0)

    graph = build_graph()

    try:
        model_label = "GLM-4.7 Deep" if mode == "deep" else "Groq Quick"
        with st.spinner(f"Running **{mode.upper()}** analysis for **{ticker}** via {model_label}…"):
            final_state = graph.invoke({"ticker": ticker, "mode": mode, "filing_year": filing_year})
    except Exception as e:
        progress_placeholder.empty()
        st.error(f"❌ Analysis failed: {e}")
        st.stop()

    progress_placeholder.empty()
    report = final_state.get("report", {})
    financials = final_state.get("financials", {})
    fin_analysis = report.get("financial_overview", {})
    risk_data = report.get("risk_assessment", {})
    peer = report.get("peer_comparison", {})
    thesis = report.get("thesis", {})
    dcf = report.get("dcf_valuation", {})
    wacc = report.get("wacc_analysis", {})
    sensitivity = report.get("sensitivity_analysis", {})
    reflection = report.get("senior_analyst_review", {})
    confidence = report.get("investment_conclusion", {})
    citations = report.get("citations", [])

    st.success(f"✅ Analysis complete for **{ticker}** ({mode} mode)")

    # ── Confidence Score Banner (deep mode) ───────────────────────────────
    if confidence:
        conf_level = confidence.get("overall_confidence", "MEDIUM")
        conf_score = confidence.get("confidence_score", 0.5)
        conf_color = confidence_color(conf_level)
        conf_css = f"confidence-{conf_level.lower()}" if conf_level in ("HIGH", "MEDIUM", "LOW") else "confidence-medium"
        action = confidence.get("recommended_action", "HOLD")

       
    # ── KPI Metrics row ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header"><h2>📊 Financial KPIs</h2></div>', unsafe_allow_html=True)

    rev_latest = financials.get("revenue_latest", 0)
    rev_prev   = financials.get("revenue_prev", 0)
    yoy        = financials.get("yoy_growth", 0) * 100
    opm_latest = financials.get("op_margin_latest", 0) * 100
    opm_prev   = financials.get("op_margin_prev", 0) * 100
    opm_delta  = opm_latest - opm_prev
    oi_latest  = financials.get("op_income_latest", 0)

    # Extract fiscal year labels from period dates
    latest_period = financials.get("latest_period", "Latest")
    prev_period   = financials.get("prev_period", "Previous")
    # Show just the year portion if it's a full date string like "2024-12-31"
    latest_year = latest_period[:4] if len(str(latest_period)) >= 4 else latest_period
    prev_year   = prev_period[:4] if len(str(prev_period)) >= 4 else prev_period

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Revenue ({latest_year})</div>
          <div class="metric-value">{fmt_billions(rev_latest)}</div>
          {delta_html(yoy)} YoY ({prev_year} → {latest_year})
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Revenue ({prev_year})</div>
          <div class="metric-value">{fmt_billions(rev_prev)}</div>
          <span style="color:#64748b;font-size:0.8rem;">Prior year</span>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Operating Income ({latest_year})</div>
          <div class="metric-value">{fmt_billions(oi_latest)}</div>
          <span style="color:#64748b;font-size:0.8rem;">{latest_year}</span>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Operating Margin ({latest_year})</div>
          <div class="metric-value">{opm_latest:.1f}%</div>
          {delta_html(opm_delta)} vs {prev_year}
        </div>""", unsafe_allow_html=True)

    # ── LLM Financial Analysis ────────────────────────────────────────────────
    st.markdown('<div class="section-header"><h2>🤖 AI Financial Analysis</h2></div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("**📈 Revenue Growth**")
            st.write(fin_analysis.get("revenue_growth", "—"))
    with col_b:
        with st.container(border=True):
            st.markdown("**📉 Operating Margin Trend**")
            st.write(fin_analysis.get("operating_margin_trend", "—"))

    # ── Risk Assessment ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header"><h2>⚠️ Risk Assessment</h2></div>', unsafe_allow_html=True)

    risk_cols = st.columns(3)
    risk_categories = {
        "🏭 Industry Risks":    risk_data.get("industry_risks", []),
        "⚙️ Operational Risks": risk_data.get("operational_risks", []),
        "📋 Regulatory Risks":  risk_data.get("regulatory_risks", []),
    }
    for col, (cat, items) in zip(risk_cols, risk_categories.items()):
        with col:
            st.markdown(f"**{cat}**")
            if items:
                for item in items:
                    st.markdown(f'<span class="risk-tag">• {item}</span>', unsafe_allow_html=True)
            else:
                st.caption("No data available.")

    # ── Peer Comparison (deep mode) ───────────────────────────────────────────
    if peer:
        peer_tickers  = peer.get("peers", [])
        peer_margins  = peer.get("peer_margins", {})
        avg_peer_m    = peer.get("avg_peer_operating_margin", 0)
        company_m     = peer.get("company_operating_margin", 0)
        diff          = (company_m - avg_peer_m) * 100
        sign          = "+" if diff >= 0 else ""
        adv_color     = "#34d399" if diff >= 0 else "#f87171"

        peers_label = " · ".join(peer_tickers) if peer_tickers else "Peers"
        st.markdown(
            f'<div class="section-header"><h2>🔬 Peer Comparison &nbsp;'
            f'<span style="color:#67e8f9;font-size:0.85rem;font-weight:400;">vs {peers_label}</span>'
            f'</h2></div>',
            unsafe_allow_html=True
        )

        num_cols = 2 + len(peer_tickers)
        peer_cols = st.columns(num_cols)

        with peer_cols[0]:
            st.markdown(f"""
            <div class="peer-badge">
              <div class="label">{ticker} Op. Margin</div>
              <div class="value">{company_m*100:.1f}%</div>
            </div>""", unsafe_allow_html=True)

        with peer_cols[1]:
            st.markdown(f"""
            <div class="peer-badge">
              <div class="label">vs Peer Avg</div>
              <div class="value" style="color:{adv_color};">{sign}{diff:.1f}pp</div>
            </div>""", unsafe_allow_html=True)

        for i, pt in enumerate(peer_tickers):
            pm = peer_margins.get(pt, 0) * 100
            with peer_cols[2 + i]:
                st.markdown(f"""
                <div class="peer-badge">
                  <div class="label">{pt} Op. Margin</div>
                  <div class="value">{pm:.1f}%</div>
                </div>""", unsafe_allow_html=True)

    # ── DCF Valuation (deep mode) ─────────────────────────────────────────────
    if dcf and "error" not in dcf:
        st.markdown('<div class="section-header"><h2>📐 DCF Valuation</h2></div>', unsafe_allow_html=True)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown(f"""
            <div class="dcf-card">
              <div class="label">Enterprise Value</div>
              <div class="value">{fmt_billions(dcf.get('enterprise_value', 0))}</div>
            </div>""", unsafe_allow_html=True)
        with d2:
            st.markdown(f"""
            <div class="dcf-card">
              <div class="label">Equity Value</div>
              <div class="value">{fmt_billions(dcf.get('equity_value', 0))}</div>
            </div>""", unsafe_allow_html=True)
        with d3:
            st.markdown(f"""
            <div class="dcf-card">
              <div class="label">Implied Share Price</div>
              <div class="value">${dcf.get('implied_share_price', 0):,.2f}</div>
            </div>""", unsafe_allow_html=True)
        with d4:
            wacc_pct = wacc.get("wacc_pct", "N/A") if wacc else "N/A"
            st.markdown(f"""
            <div class="dcf-card">
              <div class="label">WACC</div>
              <div class="value">{wacc_pct}</div>
            </div>""", unsafe_allow_html=True)

        # WACC breakdown
        if wacc and wacc.get("breakdown"):
            wb = wacc["breakdown"]
            with st.expander("📊 WACC Breakdown", expanded=False):
                wc1, wc2, wc3, wc4 = st.columns(4)
                wc1.metric("Cost of Equity", f"{wb.get('cost_of_equity', 0)*100:.1f}%")
                wc2.metric("Cost of Debt", f"{wb.get('cost_of_debt', 0)*100:.1f}%")
                wc3.metric("Equity Weight", f"{wb.get('equity_weight', 0)*100:.0f}%")
                wc4.metric("Debt Weight", f"{wb.get('debt_weight', 0)*100:.0f}%")

    # ── Sensitivity Analysis (deep mode) ──────────────────────────────────────
    if sensitivity and sensitivity.get("implied_prices"):
        st.markdown('<div class="section-header"><h2>📊 Sensitivity Analysis</h2></div>', unsafe_allow_html=True)
        st.caption("Implied share price across WACC (rows) × Terminal Growth Rate (columns)")

        import pandas as pd
        matrix = sensitivity["implied_prices"]
        df = pd.DataFrame(matrix).T
        df.index.name = "Terminal Growth"
        df.columns.name = "WACC"
        st.dataframe(df, use_container_width=True)

        base = sensitivity.get("base_case", {})
        st.caption(f"Base case: WACC = {base.get('wacc', 'N/A')}, Terminal Growth = {base.get('terminal_growth', 'N/A')}")

    # ── Investment Thesis (deep mode) ─────────────────────────────────────────
    if thesis:
        st.markdown('<div class="section-header"><h2>💡 Investment Thesis</h2></div>', unsafe_allow_html=True)
        th1, th2 = st.columns(2)
        with th1:
            st.markdown(f"""
            <div class="bull-card">
              <h4>🟢 Bull Case</h4>
              <p>{thesis.get('bull_case', '—')}</p>
            </div>""", unsafe_allow_html=True)
        with th2:
            st.markdown(f"""
            <div class="bear-card">
              <h4>🔴 Bear Case</h4>
              <p>{thesis.get('bear_case', '—')}</p>
            </div>""", unsafe_allow_html=True)

    # ── Senior Analyst Review (deep mode) ─────────────────────────────────────
    if reflection:
        approved = reflection.get("approved", True)
        rev_cycles = reflection.get("revision_cycles", 0)
        feedback = reflection.get("feedback", "No feedback.")

        css_class = "reflection-approved" if approved else "reflection-rejected"
        status_icon = "✅" if approved else "⚠️"
        status_text = "Approved" if approved else "Flagged for Review"
        status_color = "#34d399" if approved else "#fbbf24"

        st.markdown(f'<div class="section-header"><h2>🔍 Senior Analyst Review</h2></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="reflection-card {css_class}">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
            <span style="font-size:1.3rem;">{status_icon}</span>
            <span style="color:{status_color};font-weight:600;font-size:1rem;">{status_text}</span>
            <span style="color:#64748b;font-size:0.8rem;margin-left:auto;">Revision cycles: {rev_cycles}</span>
          </div>
          <p style="color:#cbd5e1;font-size:0.9rem;margin:0;line-height:1.6;">{feedback}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Citations (traceable sources) ─────────────────────────────────────────
    if citations:
        st.markdown('<div class="section-header"><h2>📌 Source Citations</h2></div>', unsafe_allow_html=True)
        with st.expander(f"View {len(citations)} source citations", expanded=False):
            for i, cite in enumerate(citations, 1):
                score = cite.get("relevance_score", 0)
                src = cite.get("source", "Unknown")
                chunk_idx = cite.get("chunk_index", "?")
                excerpt = cite.get("excerpt", "")
                st.markdown(f"""
                <div class="citation-item">
                  <div class="cite-meta">[{i}] {src} — Chunk #{chunk_idx} — Relevance: {score:.3f}</div>
                  <div style="margin-top:0.3rem;">{excerpt}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Raw JSON expander ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header"><h2>📄 Raw Report JSON</h2></div>', unsafe_allow_html=True)
    with st.expander("View full structured report", expanded=False):
        st.json(report)

    st.divider()
    st.caption("Quant Agent · Financial Intelligence Platform · Powered by Groq, GLM-4.7, Qdrant, LangGraph")

else:
    # ── Landing placeholder ────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0; color: #475569;">
      <div style="font-size:4rem;">📈</div>
      <h3 style="color:#94a3b8; margin-top:1rem;">Enter a ticker and click <em>Run Analysis</em></h3>
      <p style="max-width:480px; margin: 0.5rem auto; font-size:0.9rem; line-height:1.6;">
        The AI agent will fetch live financials, retrieve risk sections from the vector store,
        run DCF valuation, and generate a structured equity research report — all in seconds.<br/><br/>
        <em>Supports both US and Indian Stocks (.NS / .BO).</em> US stocks auto-fetch from SEC EDGAR; Indian stocks auto-fetch from Yahoo Finance.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    features = [
        ("⚡", "Dual-Model AI", "Groq for speed, GLM-4.7 for deep reasoning. Automatic routing based on analysis mode."),
        ("🧠", "Hybrid RAG", "Dense + sparse vectors in Qdrant with metadata grounding. Zero cross-contamination."),
        ("📐", "DCF Valuation", "Deterministic DCF, WACC, and sensitivity analysis. No LLM math guessing."),
    ]
    for col, (icon, title, desc) in zip([col1, col2, col3], features):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="text-align:center; padding:1.5rem;">
              <div style="font-size:2rem;">{icon}</div>
              <div style="color:#c4b5fd; font-weight:600; margin:0.5rem 0;">{title}</div>
              <div style="color:#64748b; font-size:0.85rem; line-height:1.5;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    features2 = [
        ("🔍", "Reflection Loop", "Senior Analyst AI reviews for data contradictions and hallucinations before finalizing."),
        ("💡", "Investment Thesis", "Bull & bear cases with confidence-weighted conclusions and traceable citations."),
        ("📊", "Sensitivity Tables", "See how valuations shift across WACC and growth rate scenarios."),
    ]
    for col, (icon, title, desc) in zip([col4, col5, col6], features2):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="text-align:center; padding:1.5rem;">
              <div style="font-size:2rem;">{icon}</div>
              <div style="color:#c4b5fd; font-weight:600; margin:0.5rem 0;">{title}</div>
              <div style="color:#64748b; font-size:0.85rem; line-height:1.5;">{desc}</div>
            </div>""", unsafe_allow_html=True)
