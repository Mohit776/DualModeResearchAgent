# Quant Agent: Financial Intelligence Platform

Quant Agent is a production-grade AI financial research assistant. It leverages advanced Retrieval-Augmented Generation (RAG) to process real-time financial data, SEC 10-K filings, and stock market information to generate institutional-grade investment theses. 

Designed for AI engineering and financial analysis, it features stateful memory, multi-stage reasoning workflows, and deep observability.

## 🚀 Key Features

- **Multi-Source Data Ingestion:** Real-time stock data via Yahoo Finance (`yfinance`) and direct risk factor extraction from SEC EDGAR 10-K filings.
- **Production RAG Pipeline:** Uses **Gemini Embeddings** (via direct REST API for minimal footprint) and **Qdrant Vector Database** (Cloud) for hybrid semantic search.
- **Agentic Orchestration:** Powered by **LangGraph** to handle stateful, multi-step financial reasoning (Quant Analysis → Peer Comparison → Thesis Generation → Reflection Loop).
- **High-Performance LLMs:** Utilises open-source models (120B parameters) powered by **Groq** for lightning-fast inference.
- **Self-Reflecting Guardrails:** Includes a "Senior Analyst" reflection node that reviews generated theses for financial contradictions and hallucinations, looping back for corrections if necessary.
- **Full Observability:** Deep integration with **Pydantic Logfire** for tracing LLM latency, retrieval scores, and LangGraph state changes.
- **Memory-Augmented Chatbot:** A responsive Next.js frontend with an interactive chatbot that remembers context across sessions.

## 🛠️ Technology Stack

**Backend:**
- Python 3.11
- FastAPI & Uvicorn
- LangChain & LangGraph
- Groq Python SDK
- Qdrant Vector DB (Cloud)
- FastEmbed (Fallback Embeddings)
- Pydantic Logfire

**Frontend:**
- Next.js 14 (App Router)
- React
- Custom CSS Variables (No Tailwind)

## ⚙️ Local Development Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd DualModeResearchAgent
```

### 2. Environment Variables
Create a `.env` file in the root directory and add the following keys:

```env
GROQ_API_KEY="your-groq-key"
GROQ_FALLBACK_API_KEY="your-fallback-groq-key"
GEMINI_KEY="your-gemini-api-key"
POLYGON_API_KEY="your-polygon-api-key"
HF_TOKEN="your-huggingface-token"
QDRANT_API="your-qdrant-api-key"
QDRANT_CLUSTER="your-qdrant-cluster-url"
LOGFIRE_TOKEN="your-logfire-token"
```

### 3. Start the Backend (FastAPI)
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Run the API server
python api.py
```
*The backend will run on `http://localhost:8000`.*

### 4. Start the Frontend (Next.js)
```bash
cd web

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The frontend will run on `http://localhost:3000`.*

## 🐳 Deployment (Render)

This project is fully configured for deployment on Render's Free Tier.

1. Push your code to a GitHub repository.
2. In Render, select **"Blueprints"** and connect your repository.
3. Render will automatically detect the `render.yaml` and `Dockerfile`.
4. Enter your environment variables when prompted in the Render dashboard.

*Note on Free Tier:* The Render free tier has a 512MB RAM limit. The primary Gemini embeddings run via API (low memory), but if the system falls back to local `fastembed` models, it may temporarily spike memory usage.

## 👤 Author
Developed by **Mohit Aggarwal** as a demonstration of production-ready AI engineering and autonomous financial research architectures.
