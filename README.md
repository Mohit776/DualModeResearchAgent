# oops_Tree — AI-Powered Equity Research Agent

An agentic financial analysis pipeline that fetches live financial data, retrieves risk factors from SEC 10-K filings via RAG, and generates a structured investment report — powered by **LangGraph**, **Groq LLMs**, **Qdrant**, and the **Polygon.io** API.

---

## What It Does

Given a stock ticker (e.g. `NVDA`), the system:

1. **Fetches live financials** from Polygon.io (revenue, operating income, margins)
2. **Analyzes KPIs** using an LLM and formats the output as structured JSON
3. **Retrieves relevant risk chunks** from an embedded SEC 10-K filing using semantic search (RAG)
4. **Summarizes risk factors** into categorized buckets (industry / operational / regulatory)
5. *(Deep mode)* **Compares against a peer** (AMD) on operating margin
6. *(Deep mode)* **Generates an investment thesis** — bull case and bear case
7. **Assembles a final structured report** emitted as clean JSON

---

## Project Structure

```
oops_Tree/
├── app.py              # Entrypoint — ingestion check + graph execution
├── workflow.py         # LangGraph graph definition, nodes, and routing logic
├── financials.py       # Polygon.io API calls + KPI computation
├── llm.py              # Groq LLM calls (explain KPIs, summarize risks, generate thesis)
├── rag.py              # Qdrant vector store — ingest and retrieve 10-K chunks
├── config.py           # Loads API keys from .env
├── data/
│   └── NVDA_2023_10K_risks.txt   # Raw 10-K risk section text
├── qdrant_storage/     # Persistent local Qdrant vector DB
├── .env                # API keys (not committed)
└── requirements.txt
```

---

## Agent Flow (LangGraph)

```
                    ┌─────────────────────┐
                    │  fetch_financials   │  ← Polygon.io API
                    └────────┬────────────┘
                             │
                    ┌────────▼────────────┐
                    │ analyze_financials  │  ← Groq LLM (JSON)
                    └────────┬────────────┘
                             │
                    ┌────────▼────────────┐
                    │  retrieve_risks     │  ← Qdrant semantic search
                    └────────┬────────────┘
                             │
                    ┌────────▼────────────┐
                    │  summarize_risks    │  ← Groq LLM (JSON)
                    └────────┬────────────┘
                             │
               mode == "deep"│mode == "quick"
               ┌─────────────┘             └──────────────┐
      ┌────────▼────────────┐                    ┌────────▼──────────────┐
      │  peer_comparison    │  ← Polygon.io       │    assemble_report    │
      └────────┬────────────┘                    └───────────────────────┘
               │
      ┌────────▼────────────┐
      │      thesis         │  ← Groq LLM (JSON)
      └────────┬────────────┘
               │
      ┌────────▼────────────┐
      │   assemble_report   │
      └─────────────────────┘
```

### Modes
| Mode | Nodes Run | Use Case |
|------|-----------|----------|
| `"quick"` | fetch → analyze → risks → summarize → assemble | Fast overview |
| `"deep"` | + peer comparison + investment thesis | Full equity research |

---

## Output Schema

```json
{
    "ticker": "NVDA",
    "financial_overview": {
        "revenue_growth": "...",
        "operating_margin_trend": "..."
    },
    "risk_assessment": {
        "industry_risks": ["...", "..."],
        "operational_risks": ["...", "..."],
        "regulatory_risks": ["...", "..."]
    },
    "peer_comparison": {
        "peer": "AMD",
        "peer_operating_margin": 0.1066,
        "company_operating_margin": 0.6038
    },
    "thesis": {
        "bull_case": "...",
        "bear_case": "..."
    }
}
```

---

## Setup

### 1. Clone & create a virtual environment
```bash
git clone <repo-url>
cd oops_Tree
python -m venv venv
venv\Scripts\activate      # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
pip install langgraph langchain-text-splitters
```

### 3. Configure API keys

Create a `.env` file in the project root:
```env
GROQ_API_KEY="your_groq_api_key"
POLYGON_API_KEY="your_polygon_api_key"
```

- **Groq API key** → [console.groq.com](https://console.groq.com)
- **Polygon.io key** → [polygon.io](https://polygon.io)

### 4. Add 10-K data

Place raw SEC 10-K risk section text in:
```
data/NVDA_2023_10K_risks.txt
```

### 5. Run

```bash
python app.py
```

The first run ingests the 10-K into the local Qdrant vector store. Subsequent runs skip ingestion and go straight to the graph.

To switch modes, change `"mode"` in `app.py`:
```python
final_state = graph.invoke({"ticker": "NVDA", "mode": "deep"})   # full report
final_state = graph.invoke({"ticker": "NVDA", "mode": "quick"})  # KPIs + risks only
```

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM inference | [Groq](https://groq.com) (`llama-3.1-8b-instant`) |
| Financial data | [Polygon.io](https://polygon.io) |
| Vector store | [Qdrant](https://qdrant.tech) (local) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Text chunking | `langchain-text-splitters` |
