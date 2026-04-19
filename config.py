import os
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
CHROMA_PATH = "./chroma_db"
EMAILS_PATH = "./data/emails"
COLLECTION_NAME = "cold_emails"
INDEX_STATE_FILE = ".index_state.json"

EMBED_MODEL = "nvidia/nv-embedqa-e5-v5"
LLM_MODEL = "meta/llama-3.3-70b-instruct"
