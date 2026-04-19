import os
import json
import hashlib
import chromadb

from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter

from config import NVIDIA_API_KEY, CHROMA_PATH, EMAILS_PATH, COLLECTION_NAME, INDEX_STATE_FILE, EMBED_MODEL


def _compute_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _load_state() -> dict:
    if os.path.exists(INDEX_STATE_FILE):
        with open(INDEX_STATE_FILE) as f:
            return json.load(f)
    return {}


def _save_state(state: dict) -> None:
    with open(INDEX_STATE_FILE, "w") as f:
        json.dump(state, f)


def build_index():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    embed_model = NVIDIAEmbedding(model=EMBED_MODEL, api_key=NVIDIA_API_KEY)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    saved_state = _load_state()
    new_state = {}
    new_docs = []

    if not os.path.isdir(EMAILS_PATH):
        return VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model), chroma_collection

    for fname in sorted(os.listdir(EMAILS_PATH)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(EMAILS_PATH, fname)
        file_hash = _compute_hash(fpath)
        new_state[fname] = file_hash

        if saved_state.get(fname) == file_hash:
            continue

        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        text = f"{data.get('subject', '')}\n{data.get('body', '')}"
        doc = Document(
            text=text,
            metadata={
                "id": data.get("id", fname),
                "niche": data.get("niche", ""),
                "recipient_type": data.get("recipient_type", ""),
                "language": data.get("language", ""),
                "subject": data.get("subject", ""),
                "why_it_works": data.get("why_it_works", ""),
            },
            excluded_llm_metadata_keys=["why_it_works"],
            excluded_embed_metadata_keys=["id", "why_it_works"],
        )
        new_docs.append(doc)

    if new_docs:
        VectorStoreIndex.from_documents(
            new_docs,
            storage_context=storage_context,
            embed_model=embed_model,
        )

    _save_state(new_state)

    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    return index, chroma_collection


def retrieve_examples(index, niche: str, recipient_type: str, language: str, top_k: int = 3) -> list[dict]:
    query = niche or "холодное письмо"

    filters = MetadataFilters(filters=[
        MetadataFilter(key="recipient_type", value=recipient_type),
        MetadataFilter(key="language", value=language),
    ])
    retriever = index.as_retriever(similarity_top_k=top_k, filters=filters)
    results = retriever.retrieve(query)

    if len(results) < top_k:
        retriever_no_filter = index.as_retriever(similarity_top_k=top_k)
        results = retriever_no_filter.retrieve(query)

    examples = []
    for node in results:
        meta = node.metadata or {}
        examples.append({
            "id": meta.get("id", ""),
            "niche": meta.get("niche", ""),
            "recipient_type": meta.get("recipient_type", ""),
            "language": meta.get("language", ""),
            "subject": meta.get("subject", ""),
            "body": node.get_content(),
            "why_it_works": meta.get("why_it_works", ""),
        })
    return examples
