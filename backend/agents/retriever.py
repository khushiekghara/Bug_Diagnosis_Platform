"""
Shared Retrieval Utility (Milestone 3) + Knowledge Base Growth (Milestone 4)

Provides one reusable interface for the historical defect vector store
built in Milestone 1 (kb/build_vector_store.py):

- query() / query_unique_bugs(): semantic search used by the Root Cause
  and Duplicate Detection agents (Milestone 3).
- add_resolved_bug(): Milestone 4 knowledge base growth. When a submitted
  bug gets a confirmed fix, it is chunked, embedded with the SAME model,
  and written back into the SAME collection, so future searches can find
  it and the Remediation Agent can recommend its confirmed fix.
- get_stats(): size of the knowledge base, split into original historical
  data versus bugs added by this platform.

The embedding model and ChromaDB client are loaded once and reused.
"""
import os
from typing import Dict, List, Optional, Set

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# backend/agents/retriever.py -> backend/agents -> backend -> project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "kb", "chroma_store")
COLLECTION_NAME = "historical_bugs"
MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)

MAX_FIELD_CHARS = 3000
MAX_RESOLUTION_CHARS = 2000

PLATFORM_ID_PREFIX = "PLAT-"
PLATFORM_SOURCE = "platform"
PLATFORM_ORIGIN = "platform_confirmed"
HISTORICAL_ORIGIN = "historical_dataset"


def platform_bug_id(bug_id) -> str:
    """Knowledge-base id for a bug submitted through this platform."""
    return f"{PLATFORM_ID_PREFIX}{bug_id}"


class HistoricalBugRetriever:
    _instance = None

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
            meta = results["metadatas"][0][i] or {}
            matches.append({
                "chunk_id": ids[i],
                "bug_id": meta.get("bug_id"),
                "source_repo": meta.get("source_repo"),
                "severity": meta.get("severity"),
                "status": meta.get("status"),
                "resolution": meta.get("resolution") or None,
                "origin": meta.get("origin", HISTORICAL_ORIGIN),
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i],
            })
        return matches

    def query_unique_bugs(
        self,
        text: str,
        top_k: int = 8,
        max_bugs: int = 5,
        exclude_bug_ids: Optional[Set[str]] = None,
    ) -> List[Dict]:
        exclude_bug_ids = exclude_bug_ids or set()
        fetch_k = top_k + (8 if exclude_bug_ids else 0)
        raw_matches = self.query(text, top_k=fetch_k)

        best_per_bug: Dict[str, Dict] = {}
        for match in raw_matches:
            bug_id = match["bug_id"]
            if bug_id in exclude_bug_ids:
                continue
            if bug_id not in best_per_bug or match["distance"] < best_per_bug[bug_id]["distance"]:
                best_per_bug[bug_id] = match

        unique_matches = sorted(best_per_bug.values(), key=lambda m: m["distance"])
        return unique_matches[:max_bugs]

    def add_resolved_bug(
        self,
        bug_id,
        title: str,
        description: Optional[str],
        stack_trace: Optional[str],
        error_log: Optional[str],
        severity: Optional[str],
        resolution: str,
    ) -> int:
        """
        Adds a resolved bug (with its confirmed fix) to the knowledge base.
        Safe to call again for the same bug: its earlier chunks are
        removed first, so nothing goes stale. Returns chunks written.
        """
        resolution = (resolution or "").strip()[:MAX_RESOLUTION_CHARS]
        if not resolution:
            raise ValueError("A non-empty resolution is required to add a bug to the knowledge base.")

        kb_bug_id = platform_bug_id(bug_id)

        parts = [f"Title: {(title or '').strip()}"]
        if description:
            parts.append(f"Description: {description.strip()[:MAX_FIELD_CHARS]}")
        parts.append(f"Resolution: {resolution}")
        if stack_trace:
            parts.append(f"Stack Trace: {stack_trace.strip()[:MAX_FIELD_CHARS]}")
        if error_log:
            parts.append(f"Error Log: {error_log.strip()[:MAX_FIELD_CHARS]}")
        pieces = _splitter.split_text("\n".join(parts))

        self.collection.delete(where={"bug_id": kb_bug_id})

        metadata = {
            "bug_id": kb_bug_id,
            "source_repo": PLATFORM_SOURCE,
            "severity": severity or "unknown",
            "status": "resolved",
            "resolution": resolution,
            "origin": PLATFORM_ORIGIN,
        }
        embeddings = self.model.encode(pieces).tolist()
        self.collection.add(
            ids=[f"{kb_bug_id}_chunk{i}" for i in range(len(pieces))],
            embeddings=embeddings,
            documents=pieces,
            metadatas=[dict(metadata) for _ in pieces],
        )
        return len(pieces)

    def get_stats(self) -> Dict:
        """Knowledge base size, split into original vs platform-added data."""
        total_chunks = self.collection.count()
        added = self.collection.get(
            where={"origin": PLATFORM_ORIGIN},
            include=["metadatas"],
        )
        platform_chunks = len(added["ids"])
        platform_bugs = len({m.get("bug_id") for m in (added["metadatas"] or [])})
        return {
            "total_chunks": total_chunks,
            "historical_chunks": total_chunks - platform_chunks,
            "platform_chunks": platform_chunks,
            "platform_bugs": platform_bugs,
        }


def get_retriever() -> HistoricalBugRetriever:
    """Convenience accessor used by agents and the API."""
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
    print(retriever.get_stats())