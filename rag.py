import os
import json
import numpy as np

from llama_index.embeddings.nvidia import NVIDIAEmbedding
from config import NVIDIA_API_KEY, EMAILS_PATH, EMBED_MODEL


def _load_emails() -> list[dict]:
    emails = []
    if not os.path.isdir(EMAILS_PATH):
        return emails
    for fname in sorted(os.listdir(EMAILS_PATH)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(EMAILS_PATH, fname), encoding="utf-8") as f:
            emails.append(json.load(f))
    return emails


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def build_index():
    emails = _load_emails()
    if not emails:
        return emails, np.array([])

    embed_model = NVIDIAEmbedding(model=EMBED_MODEL, api_key=NVIDIA_API_KEY)
    texts = [f"{e.get('subject', '')}\n{e.get('body', '')}" for e in emails]
    embeddings = embed_model.get_text_embedding_batch(texts, show_progress=False)
    return emails, np.array(embeddings)


def retrieve_examples(emails: list[dict], embeddings: np.ndarray, niche: str, recipient_type: str, language: str, top_k: int = 3) -> list[dict]:
    if not emails or embeddings.size == 0:
        return []

    embed_model = NVIDIAEmbedding(model=EMBED_MODEL, api_key=NVIDIA_API_KEY)
    query_vec = np.array(embed_model.get_text_embedding(niche or "холодное письмо"))

    filtered = [(i, e) for i, e in enumerate(emails)
                if e.get("recipient_type") == recipient_type and e.get("language") == language]

    if len(filtered) >= top_k:
        indices = [i for i, _ in filtered]
        sims = [_cosine_similarity(query_vec, embeddings[i]) for i in indices]
        ranked = sorted(zip(sims, [e for _, e in filtered]), reverse=True)
        return [e for _, e in ranked[:top_k]]

    sims = [_cosine_similarity(query_vec, emb) for emb in embeddings]
    ranked = sorted(zip(sims, emails), reverse=True)
    return [e for _, e in ranked[:top_k]]
