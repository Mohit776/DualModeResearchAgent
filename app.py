import json
from core.rag import create_collection, ingest_document, get_client
from core.workflow import build_graph


if __name__ == "__main__":
    client = get_client()
    if not client.collection_exists("financial_docs"):
        create_collection()
        with open("data/NVDA_2023_10K_risks.txt", "r", encoding="utf-8") as f:
            text = f.read()
        ingest_document(text, "NVDA", 2023, doc_type="10-K")
        print("Initial ingestion complete.")

    graph = build_graph()

    # Change mode to "quick" to skip peer comparison + thesis + DCF + reflection
    final_state = graph.invoke({"ticker": "NVDA", "mode": "deep", "filing_year": 2023})

    print("\nFinal Structured Report")
    print("------------------------")
    print(json.dumps(final_state["report"], indent=4))