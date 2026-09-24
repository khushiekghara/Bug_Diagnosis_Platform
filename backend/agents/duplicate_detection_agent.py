"""
Milestone 3 -- Task 2: Duplicate Detection Agent
Performs semantic similarity search over historical bug submissions to
identify whether a newly submitted bug is a likely duplicate, a related
issue, or a new/unmatched issue.

Reuses the same embedding model and vector store as the Root Cause Agent
(via agents/retriever.py) -- same embedding strategy across the whole RAG
pipeline, as required by M3.2.
"""
from typing import Dict

from agents.retriever import get_retriever

DUPLICATE_THRESHOLD = 0.6   # distance below this -> likely duplicate
RELATED_THRESHOLD = 1.0     # distance below this (but above duplicate) -> related


def _snippet(text: str, length: int = 200) -> str:
    text = " ".join(text.split())
    return text[:length] + ("..." if len(text) > length else "")


def _distance_to_similarity_score(distance: float) -> float:
    normalized = max(0.0, 1.0 - (distance / 1.5))
    return round(min(normalized, 1.0), 3)


def _classify_status(top_distance: float) -> str:
    if top_distance <= DUPLICATE_THRESHOLD:
        return "Likely Duplicate"
    if top_distance <= RELATED_THRESHOLD:
        return "Related Issue"
    return "New/Unmatched Issue"


class DuplicateDetectionAgent:
    def run(self, shared_context: Dict, top_k: int = 10, max_matches: int = 5) -> Dict:
        bug = shared_context.get("bug_report", {})
        query_text = " ".join([
            bug.get("title", "") or "",
            bug.get("description", "") or "",
            bug.get("stack_trace", "") or "",
            bug.get("error_log", "") or "",
        ]).strip()

        if not query_text:
            return {
                "agent": "DuplicateDetectionAgent",
                "duplicate_status": "New/Unmatched Issue",
                "matches": [],
                "reasoning": "No bug text was available to search against the knowledge base.",
            }

        retriever = get_retriever()
        matches = retriever.query_unique_bugs(query_text, top_k=top_k, max_bugs=max_matches)

        if not matches:
            return {
                "agent": "DuplicateDetectionAgent",
                "duplicate_status": "New/Unmatched Issue",
                "matches": [],
                "reasoning": "No historical bugs were found via semantic search, or the knowledge base is empty.",
            }

        top_distance = matches[0]["distance"]
        duplicate_status = _classify_status(top_distance)

        structured_matches = []
        for m in matches:
            similarity_score = _distance_to_similarity_score(m["distance"])
            match_status = _classify_status(m["distance"])
            structured_matches.append({
                "bug_id": m["bug_id"],
                "source_repo": m.get("source_repo"),
                "severity": m.get("severity"),
                "status": m.get("status"),
                "similarity_score": similarity_score,
                "distance": round(m["distance"], 4),
                "match_status": match_status,
                "summary": _snippet(m["text"]),
                "explanation": (
                    f"This historical bug was retrieved because its description is semantically "
                    f"similar to the submitted bug (similarity score {similarity_score}), based on "
                    f"shared error patterns and/or affected component."
                ),
            })

        reasoning = (
            f"Searched the historical defect knowledge base using the submitted bug's text as the "
            f"query. Found {len(matches)} unique candidate match(es); the closest had a distance of "
            f"{round(top_distance, 4)}, which is classified as '{duplicate_status}' under the "
            f"configured thresholds (duplicate <= {DUPLICATE_THRESHOLD}, related <= {RELATED_THRESHOLD})."
        )

        return {
            "agent": "DuplicateDetectionAgent",
            "duplicate_status": duplicate_status,
            "matches": structured_matches,
            "reasoning": reasoning,
        }


if __name__ == "__main__":
    import json

    sample_context = {
        "bug_report": {
            "id": 2,
            "title": "Tab closing crashes browser during video playback",
            "description": "When I close a tab while a video is playing in another tab, the whole browser crashes.",
            "stack_trace": "",
            "error_log": "",
        }
    }

    agent = DuplicateDetectionAgent()
    result = agent.run(sample_context)
    print(json.dumps(result, indent=2))