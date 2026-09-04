"""
M1.4 — Vector Store Indexing
Loads embedded chunks and indexes them into a local ChromaDB collection,
storing bug metadata alongside each vector for retrieval.
Run this AFTER embeddings.py.
"""
import os
import json
import chromadb

EMBEDDED_PATH = os.path.join(os.path.dirname(__file__), "data", "bug_chunks_embedded.jsonl")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_store")
COLLECTION_NAME = "historical_bugs"


def load_embedded_chunks(path: str = EMBEDDED_PATH):
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def build_index(input_path: str = EMBEDDED_PATH):
    chunks = load_embedded_chunks(input_path)
    if not chunks:
        print("No embedded chunks found — run embeddings.py first.")
        return

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    ids = [c["chunk_id"] for c in chunks]
    embeddings = [c["embedding"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "bug_id": str(c["bug_id"]),
            "source_repo": c.get("source_repo", "unknown"),
            "severity": c.get("severity", "unknown"),
            "status": c.get("status", "unknown"),
        }
        for c in chunks
    ]

    batch = 500
    for i in range(0, len(ids), batch):
        collection.add(
            ids=ids[i:i + batch],
            embeddings=embeddings[i:i + batch],
            documents=documents[i:i + batch],
            metadatas=metadatas[i:i + batch],
        )

    print(f"Indexed {len(ids)} chunks into ChromaDB collection '{COLLECTION_NAME}' at {CHROMA_DIR}")


if __name__ == "__main__":
    build_index()