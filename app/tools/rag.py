"""Policy document search using persistent Chroma when available."""
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "policies"
os.environ.setdefault("HF_HOME", str(DATA_DIR.parents[1] / ".model-cache"))

import chromadb
from chromadb.utils import embedding_functions


def rag_search(query: str, k: int = 4) -> list[dict[str, str]]:
    """Retrieve policy passages, lazily creating a persistent local index."""
    files = sorted(DATA_DIR.glob("*.md"))
    if not files:
        return []
    client = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", ".chroma"))
    collection = client.get_or_create_collection("policies", embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2"))
    if collection.count() == 0:
        docs, ids, metas = [], [], []
        for file in files:
            text = file.read_text(encoding="utf-8")
            for index, chunk in enumerate(re.split(r"\n\s*\n", text)):
                if chunk.strip():
                    docs.append(chunk.strip()); ids.append(f"{file.name}:{index}"); metas.append({"source": file.name})
        collection.add(documents=docs, ids=ids, metadatas=metas)
    found = collection.query(query_texts=[query], n_results=min(k, collection.count()))
    return [{"text": doc, "source": meta["source"], "chunk_id": ident}
            for doc, meta, ident in zip(found["documents"][0], found["metadatas"][0], found["ids"][0])]
