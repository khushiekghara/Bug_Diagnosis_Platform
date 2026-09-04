"""
M1.4 — Test semantic retrieval of similar historical bugs.
Takes a sample new bug description, embeds it, and returns the
top-k most similar historical bugs from the vector store.

This is your proof that the RAG retrieval pipeline works end-to-end.
"""
import os
import sys
import chromadb
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "kb"))

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "kb", "chroma_store")
COLLECTION_NAME = "historical_bugs"
MODEL_NAME = "all-MiniLM-L6-v2"


def query_similar_bugs(query_text: str, top_k: int = 5):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query_text])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    print(f"\nQuery: {query_text}\n")
    print(f"Top {top_k} similar historical bugs:\n")
    for i in range(len(results["ids"][0])):
        print(f"{i + 1}. [{results['metadatas'][0][i]['source_repo']}] "
              f"bug_id={results['metadatas'][0][i]['bug_id']} "
              f"(distance={results['distances'][0][i]:.4f})")
        print(f"   {results['documents'][0][i][:200]}...")
        print()

    return results


if __name__ == "__main__":
    sample_query = (
        "Application crashes when closing multiple tabs while a video "
        "is playing in the background, null pointer in frame destructor."
    )
    query_similar_bugs(sample_query, top_k=3)