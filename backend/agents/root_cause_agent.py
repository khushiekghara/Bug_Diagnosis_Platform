"""
Milestone 3 -- Task 1: Root Cause Agent
Reasons about the probable root cause of a submitted bug using RAG
retrieval over the Historical Defect Knowledge Base built in Milestone 1.

Design:
- Retrieves the most semantically similar historical bug chunks for the
  submitted bug's text (title + description + stack trace + error log),
  narrowed with the exception type / affected component already
  identified by the Triage Agent and Log Analysis Agent (so it consumes
  their outputs, as required by M3.1).
- Builds a root cause hypothesis grounded in what those historical bugs
  describe, rather than inventing an explanation.
- Clearly separates "evidence" (what was retrieved from the knowledge
  base) from "reasoning" (the agent's own inference connecting that
  evidence to the current bug) via distinct output fields.
- No external LLM/API required -- retrieval + rule-based synthesis.
"""
from typing import Dict

from agents.retriever import get_retriever

DISTANCE_HIGH_CONFIDENCE = 0.6
DISTANCE_MEDIUM_CONFIDENCE = 1.0


def _build_query_text(shared_context: Dict) -> str:
    bug = shared_context.get("bug_report", {})
    triage = shared_context.get("triage", {})
    log = shared_context.get("log_analysis", {})

    parts = [
        bug.get("title", "") or "",
        bug.get("description", "") or "",
        bug.get("stack_trace", "") or "",
        bug.get("error_log", "") or "",
    ]

    if log.get("exception_type"):
        parts.append(f"Exception type: {log['exception_type']}")
    if triage.get("affected_component"):
        parts.append(f"Affected component: {triage['affected_component']}")

    return " ".join(p for p in parts if p)


def _distance_to_confidence(distance: float) -> float:
    if distance <= DISTANCE_HIGH_CONFIDENCE:
        return round(0.85 - (distance / DISTANCE_HIGH_CONFIDENCE) * 0.1, 2)
    if distance <= DISTANCE_MEDIUM_CONFIDENCE:
        span = DISTANCE_MEDIUM_CONFIDENCE - DISTANCE_HIGH_CONFIDENCE
        progress = (distance - DISTANCE_HIGH_CONFIDENCE) / span
        return round(0.75 - progress * 0.35, 2)
    return 0.3


def _snippet(text: str, length: int = 220) -> str:
    text = " ".join(text.split())
    return text[:length] + ("..." if len(text) > length else "")


class RootCauseAgent:
    def run(self, shared_context: Dict, top_k: int = 8, max_evidence: int = 3) -> Dict:
        query_text = _build_query_text(shared_context)

        if not query_text.strip():
            return {
                "agent": "RootCauseAgent",
                "root_cause_hypothesis": "Insufficient information to determine a root cause.",
                "confidence": 0.3,
                "supporting_evidence": [],
                "reasoning": "No bug text, stack trace, or error log was available to retrieve context from.",
            }

        retriever = get_retriever()
        matches = retriever.query_unique_bugs(query_text, top_k=top_k, max_bugs=max_evidence)

        if not matches:
            return {
                "agent": "RootCauseAgent",
                "root_cause_hypothesis": "No sufficiently similar historical defects were found to ground a hypothesis.",
                "confidence": 0.3,
                "supporting_evidence": [],
                "reasoning": "The retrieval pipeline returned no matches from the historical defect knowledge base.",
            }

        top_match = matches[0]
        confidence = _distance_to_confidence(top_match["distance"])

        log = shared_context.get("log_analysis", {})
        triage = shared_context.get("triage", {})

        hypothesis_parts = []
        if log.get("exception_type"):
            hypothesis_parts.append(f"The bug is likely caused by a {log['exception_type']}")
        else:
            hypothesis_parts.append("The bug's likely cause")

        if triage.get("affected_component"):
            hypothesis_parts.append(f"in the {triage['affected_component']} component")

        hypothesis_parts.append(
            f"consistent with {len(matches)} similar historical defect(s) retrieved from the "
            f"{top_match.get('source_repo', 'historical')} dataset, the closest of which describes: "
            f"\"{_snippet(top_match['text'], 160)}\""
        )
        hypothesis = " ".join(hypothesis_parts) + "."

        supporting_evidence = [
            {
                "bug_id": m["bug_id"],
                "source_repo": m.get("source_repo"),
                "similarity_distance": round(m["distance"], 4),
                "excerpt": _snippet(m["text"]),
            }
            for m in matches
        ]

        reasoning = (
            f"Retrieved {len(matches)} unique historical defect(s) via semantic similarity search "
            f"over the historical defect knowledge base, using the bug's description"
            + (f", detected exception type '{log['exception_type']}'" if log.get("exception_type") else "")
            + (f", and affected component '{triage['affected_component']}'" if triage.get("affected_component") else "")
            + f" as the query. The closest match had a distance of {round(top_match['distance'], 4)}, "
            f"which maps to a confidence of {confidence}. The hypothesis above is the agent's own "
            f"inference connecting this evidence to the current bug -- it is not a guarantee, and "
            f"should be verified against the actual code."
        )

        return {
            "agent": "RootCauseAgent",
            "root_cause_hypothesis": hypothesis,
            "confidence": confidence,
            "supporting_evidence": supporting_evidence,
            "reasoning": reasoning,
        }


if __name__ == "__main__":
    import json

    sample_context = {
        "bug_report": {
            "id": 1,
            "title": "Application crashes on tab close with video playing",
            "description": "The browser crashes intermittently when closing a tab while a video plays in the background.",
            "stack_trace": "nsIFrame::Destroy() called from nsCSSFrameConstructor::ContentRemoved",
            "error_log": "",
        },
        "triage": {"affected_component": "UI/Frontend", "severity": "Critical"},
        "log_analysis": {"exception_type": None},
    }

    agent = RootCauseAgent()
    result = agent.run(sample_context)
    print(json.dumps(result, indent=2))