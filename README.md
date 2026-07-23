# 📈 Quant Agent — Production-Grade AI Financial Research & RAG System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agents-FF6F00?style=flat)](https://langchain-ai.github.io/langgraph/)
[![Next.js](https://img.shields.io/badge/Next.js-16.2-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-Cloud_Vector_DB-C9252B?style=flat&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Groq](https://img.shields.io/badge/Groq-GPT--OSS_120B-F05032?style=flat)](https://groq.com)
[![Logfire](https://img.shields.io/badge/Logfire-Pydantic_Observability-76ABAE?style=flat)](https://logfire.pydantic.dev)

**Quant Agent** is an autonomous equity research assistant combining **LangGraph** multi-agent workflows, a production-grade **Hybrid RAG Pipeline** (Gemini Embeddings + Qdrant Cloud + FlashRank Re-ranking), deterministic **DCF & WACC Valuation engines**, and an interactive **Next.js 16 frontend** with a context-aware chatbot (**QuantBot**).

It ingests SEC EDGAR 10-K filings and financial market data to generate institutional-grade investment memos complete with confidence scoring and traceable source citations.

---

## 💡 System Architecture

```mermaid
flowchart TD
    User([User / Ticker Input]) --> API[FastAPI Server]

    subgraph RAG & Data Engine
        API --> SEC[SEC EDGAR 10-K Fetcher]
        API --> Polygon[Polygon.io Financials API]
        SEC --> Chunk[Semantic Text Splitter]
        Chunk --> Dense[Gemini Dense Embeddings]
        Chunk --> Sparse[BM25 Sparse Encoder]
        Dense & Sparse --> Qdrant[(Qdrant Cloud DB)]
        Qdrant --> Hybrid[Hybrid Query + Metadata Filters]
        Hybrid --> Rerank[FlashRank Cross-Encoder]
    end

    subgraph LangGraph Multi-Agent Reasoning Loop
        Rerank --> Node1[1. Fetch Financials]
        Node1 --> Node2[2. Analyze Financial KPIs]
        Node2 --> Node3[3. Retrieve SEC Risks]
        Node3 --> Node4[4. Summarize Risks]
        Node4 --> Node5[5. Discover & Compare Peers]
        Node5 --> Node6[6. Deterministic DCF / WACC Valuation]
        Node6 --> Node7[7. Investment Thesis]
        Node7 --> Node8{8. Senior Analyst Reflection}
        Node8 -- Rejected --> Node7
        Node8 -- Approved --> Node9[9. Confidence Scoring]
        Node9 --> Node10[10. Final Memo Assembly]
    end

    Node10 --> UI[Next.js 16 Dashboard]
    UI --> QuantBot[QuantBot Memory-Augmented Chatbot]
```

---

## ✨ Key System Capabilities

- 🔍 **Hybrid RAG Pipeline**: Combines Google Gemini dense vector embeddings (`models/gemini-embedding-2`) and BM25 sparse vectors in Qdrant Cloud DB with strict payload metadata filtering (`ticker`, `year`) to eliminate cross-stock contamination.
- 🎯 **Neural Cross-Encoder Re-Ranking**: Integrates FlashRank (`ms-marco-TinyBERT-L-2-v2`) for second-pass context re-ranking, maximizing retrieval precision.
- 🧮 **Deterministic Valuation Engine**: Computes Gordon Growth DCF, WACC, and a $5 \times 5$ sensitivity matrix in pure Python without LLM arithmetic guessing.
- 🔄 **Self-Reflecting Senior Analyst Loop**: LangGraph reflection node reviews draft reports for financial contradictions and hallucinations, automatically cycling back for revisions.
- 💬 **Context-Aware QuantBot Chatbot**: Next.js floating chatbot with active report memory and suggested questions.
- 🔭 **Full Observability & Evals**: Pydantic Logfire tracing for latency/tokens and built-in Ragas evaluation suite (`Faithfulness` & `Response Relevancy`).

---

## 🛠️ Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Backend API** | Python 3.11, FastAPI, Uvicorn, Pydantic |
| **Agent Orchestration** | LangGraph, LangChain, Groq SDK (`openai/gpt-oss-120b`) |
| **RAG & Search** | Qdrant Cloud DB, Gemini Embeddings, FastEmbed, FlashRank Cross-Encoder |
| **Data Sources** | SEC EDGAR 10-K (BeautifulSoup), Polygon.io API, `yfinance` |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 |
| **Observability & Evals** | Pydantic Logfire, Ragas Framework |

---


## ⚡ Quickstart

### 1. Environment Configuration
Create a `.env` file in the root folder:
```env
GROQ_API_KEY="your-groq-api-key"
GEMINI_KEY="your-gemini-api-key"
POLYGON_API_KEY="your-polygon-api-key"
QDRANT_API="your-qdrant-api-key"
QDRANT_CLUSTER="your-qdrant-cluster-url"
LOGFIRE_TOKEN="your-logfire-token" # Optional
```

### 2. Backend Setup (FastAPI)
```bash
python -m venv venv
# Linux/macOS: source venv/bin/activate | Windows: venv\Scripts\activate
pip install -r requirements.txt
python api.py
```
*Runs on `http://localhost:8000`*

### 3. Frontend Setup (Next.js)
```bash
cd web
npm install
npm run dev
```
*Runs on `http://localhost:3000`*

### 4. Run Ragas Evals
```bash
python -m core.evals.runner
```

---

## 👤 Author
Developed by **Mohit Aggarwal** as a demonstration of production-grade AI engineering, multi-agent systems, and financial RAG architectures.

