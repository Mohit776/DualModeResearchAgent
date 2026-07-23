import json
import os

# Disable Ragas telemetry BEFORE importing ragas (it phones home to explodinggradients.com on import)
os.environ["RAGAS_DO_NOT_TRACK"] = "true"

import math
from pathlib import Path
from typing import Dict, Any

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import Faithfulness, ResponseRelevancy

# We use the existing graph and LLM settings
from core.workflow import build_graph
from core.llm import _groq_client, _groq_fallback_client
from core.observability import logfire

from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from core.config import GROQ_API_KEY, DEEP_MODEL


def get_ragas_llm():
    """Return a ChatGroq LLM for Ragas evaluation."""
    return ChatGroq(api_key=GROQ_API_KEY, model=DEEP_MODEL)


def get_ragas_embeddings():
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")


def _sanitize_score(score) -> dict:
    """Convert Ragas EvaluationResult to a flat JSON-safe dict of metric scores (NaN -> None)."""
    df = score.to_pandas()

    # These are data columns — not metric scores
    skip_cols = {"user_input", "retrieved_contexts", "response", "reference",
                 "question", "answer", "contexts", "ground_truth"}

    result = {}
    for col in df.columns:
        if col in skip_cols:
            continue
        try:
            val = float(df[col].mean())
            result[col] = None if (math.isnan(val) or math.isinf(val)) else round(val, 4)
        except Exception:
            result[col] = None
    return result


def run_evaluation(ticker: str = None) -> Dict[str, Any]:
    """
    Run evaluation for a specific ticker, or all tickers in dataset.json if none provided.
    """
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path, "r") as f:
        data = json.load(f)

    if ticker:
        data = [d for d in data if d["ticker"].upper() == ticker.upper()]
        if not data:
            raise ValueError(f"Ticker {ticker} not found in dataset.json")

    results = []
    graph = build_graph()
    llm = get_ragas_llm()
    embeddings = get_ragas_embeddings()

    # Instantiate metrics with our LLM/embeddings so Ragas doesn't default to OpenAI
    faithfulness_metric = Faithfulness(llm=llm)
    relevancy_metric = ResponseRelevancy(llm=llm, embeddings=embeddings)

    for item in data:
        t = item["ticker"]
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        filing_year = item.get("filing_year", 2024)

        # Run the agent graph
        print(f"Running evaluation for {t} ({filing_year})...")
        with logfire.span("🚀 langgraph.invoke", ticker=t, filing_year=filing_year):
            final_state = graph.invoke({"ticker": t, "filing_year": filing_year})

        # Extract RAG contexts and final answer
        contexts = final_state.get("risks", [])

        # The final report might be a dict, convert to string
        report = final_state.get("report", {})
        answer = json.dumps(report, indent=2) if isinstance(report, dict) else str(report)

        # Build Ragas v0.4 SingleTurnSample with correct column names
        sample = SingleTurnSample(
            user_input=question,
            response=answer,
            retrieved_contexts=[str(c) for c in contexts],
            reference=ground_truth,
        )
        eval_dataset = EvaluationDataset(samples=[sample])

        # Run Ragas evaluation
        with logfire.span("🧪 ragas.evaluate", ticker=t):
            score = evaluate(
                dataset=eval_dataset,
                metrics=[faithfulness_metric, relevancy_metric],
                raise_exceptions=False,
            )

        results.append({
            "ticker": t,
            "metrics": _sanitize_score(score)
        })

    return {"status": "success", "evaluations": results}


if __name__ == "__main__":
    res = run_evaluation()
    print(json.dumps(res, indent=2))
