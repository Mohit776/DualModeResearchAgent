import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")

# Zhipu GLM-4 uses an OpenAI-compatible endpoint
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# Model routing
QUICK_MODEL = "llama-3.3-70b-versatile"   # Groq — low latency 
DEEP_MODEL = "glm-4-plus"                 # Zhipu GLM-4.7 — high reasoning