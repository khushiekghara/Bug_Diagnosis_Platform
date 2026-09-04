"""
M1.4 — Embedding Generation
Loads the chunked bug data and generates a vector embedding for each chunk
using a free, local sentence-transformers model (no API key needed).
Run this AFTER chunking.py.
"""
import os
import json
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = os.path.join(os.path.dirname(__file__), "data", "bug_chunks.jsonl")
EMBEDDED_PATH = os.path.join(os.path.dirname(__file__), "data", "bug_chunks_embedded.jsonl")

MODEL_NAME = "all-MiniLM-L6-v2"


def load_chunks(path: str = CHUNKS_PATH):
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def generate_embeddings(input_path: str = CHUNKS_PATH, output_path: str = EMBEDDED_PATH):
    chunks = load_chunks(input_path)
    if not chunks:
        print("No chunks found — run chunking.py first.")
        return []

    print(f"Loading embedding model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    vectors = model.encode(texts, show_progress_bar=True, batch_size=32)

    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector.tolist()

    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")

    print(f"Saved {len(chunks)} embedded chunks -> {output_path}")
    return chunks


if __name__ == "__main__":
    generate_embeddings()