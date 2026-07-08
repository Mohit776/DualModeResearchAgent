import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

DEEP_MODEL = "openai/gpt-oss-120b" 

QDRANT_API_KEY = os.getenv("QDRANT_API")
QDRANT_CLUSTER = os.getenv("QDRANT_CLUSTER")
GEMINI_API = os.getenv("GEMINI_KEY")
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

# RAG Configuration
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-2")
FALLBACK_EMBED_MODEL = os.getenv("FALLBACK_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))

#-------quant config--------------
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "financial_docs")





