"""
Milestone 3 -- Shared Retrieval Utility
Provides a single reusable interface for querying the historical defect
vector store built in Milestone 1 (kb/build_vector_store.py). Used by the
Root Cause Agent and Duplicate Detection Agent so the embedding model and
ChromaDB client are loaded only once and reused across queries -- this is
the "same embedding strategy established for the RAG pipeline" reuse
required by M3.2.
"""
import os
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer

# backend/agents/retriever.py -> backend/agents -> backend -> project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "kb", "chroma_store")
COLLECTION_NAME = "historical_bugs"
MODEL_NAME = "all-MiniLM-L6-v2"


class HistoricalBugRetriever:
    """
    Loads the embedding model and ChromaDB collection once, and exposes a
    simple query() method that returns similar historical bug chunks.
    """

    _instance = None  # simple singleton so the model loads only once per process

    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_collection(COLLECTION_NAME)

    @classmethod
    def get_instance(cls) -> "HistoricalBugRetriever":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def query(self, text: str, top_k: int = 8) -> List[Dict]:
        """
        Returns up to top_k matching chunks as a list of dicts:
        {chunk_id, bug_id, source_repo, severity, status, text, distance}
        Lower distance = more similar (this store uses default L2 distance).
        """
        if not text or not text.strip():
            return []

        query_embedding = self.model.encode([text])[0].tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        matches = []
        ids = results.get("ids", [[]])[0]
        for i in range(len(ids)):
            matches.append({
                "chunk_id": ids[i],
                "bug_id": results["metadatas"][0][i].get("bug_id"),
                "source_repo": results["metadatas"][0][i].get("source_repo"),
                "severity": results["metadatas"][0][i].get("severity"),
                "status": results["metadatas"][0][i].get("status"),
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i],
            })
        return matches

    def query_unique_bugs(self, text: str, top_k: int = 8, max_bugs: int = 5) -> List[Dict]:
        """
        Same as query(), but deduplicated by bug_id -- a single historical
        bug may have multiple chunks match; this keeps only the
        best-scoring (lowest distance) chunk per bug_id.
        Returns at most max_bugs results, sorted by distance ascending.
        """
        raw_matches = self.query(text, top_k=top_k)
        best_per_bug: Dict[str, Dict] = {}

        for match in raw_matches:
            bug_id = match["bug_id"]
            if bug_id not in best_per_bug or match["distance"] < best_per_bug[bug_id]["distance"]:
                best_per_bug[bug_id] = match

        unique_matches = sorted(best_per_bug.values(), key=lambda m: m["distance"])
        return unique_matches[:max_bugs]


def get_retriever() -> HistoricalBugRetriever:
    """Convenience accessor used by agents."""
    return HistoricalBugRetriever.get_instance()


if __name__ == "__main__":
    import json
    retriever = get_retriever()
    results = retriever.query_unique_bugs(
        "Application crashes when closing multiple tabs while a video is "
        "playing, null pointer in frame destructor.",
        top_k=10,
        max_bugs=5,
    )
    print(json.dumps(results, indent=2)[:2000])