import os
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
EMAILS_PATH = "./data/emails"

EMBED_MODEL = "nvidia/nv-embedqa-e5-v5"
LLM_MODEL = "mistralai/mistral-7b-instruct-v0.3"
