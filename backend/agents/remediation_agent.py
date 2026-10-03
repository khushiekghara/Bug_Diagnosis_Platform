"""
Milestone 3 -- Task 3: Remediation Agent
Generates specific, actionable fix recommendations for a submitted bug,
grounded in the Root Cause Agent's hypothesis, the Duplicate Detection
Agent's matched historical bugs, and the Triage/Log Analysis findings.

Milestone 4 update: when the Duplicate Detection Agent surfaces a match
that was resolved on this platform (confirmed_on_platform), its exact
confirmed fix is used as the top-ranked, highest-confidence
recommendation -- stronger evidence than text-mined "resolution
language", and clearly labeled as its own basis ("confirmed_fix") so it
is never confused with a speculative guess.
"""
import re
from typing import Dict, Optional


RESOLUTION_MARKERS = [
    r"fixed by[^.]{0,160}\.",
    r"resolved by[^.]{0,160}\.",
    r"patch(?:ed)?[^.]{0,160}\.",
    r"the fix (?:is|was)[^.]{0,160}\.",
    r"workaround[^.]{0,160}\.",
    r"root cause (?:is|was)[^.]{0,160}\.",
    r"marking (?:verified|fixed)[^.]{0,80}",
]

BEST_PRACTICE_GUIDANCE = {
    "Database": "Review query parameters and connection handling; add null/timeout checks around database calls and verify connection pool configuration.",
    "Authentication": "Verify token/session expiry handling and ensure credentials are validated and invalidated correctly on all code paths.",
    "UI/Frontend": "Check for null/undefined element references before DOM manipulation, and verify event handlers are bound after the relevant elements render.",
    "API/Backend": "Add input validation and structured error handling around the affected endpoint; confirm response contracts match what the client expects.",
    "Network": "Add retry/backoff logic and explicit timeout handling around the network call; verify the target service is reachable in the failing environment.",
    "Memory/Performance": "Profile the affected code path for unreleased references or unbounded growth; ensure objects are properly disposed/garbage-collected.",
    "File/Storage": "Validate file size/type before processing, and add explicit error handling for missing files, permission issues, or disk space limits.",
    "Unknown/General": "Reproduce the issue locally with the provided stack trace, add logging around the failure point, and write a regression test once the cause is confirmed.",
}


def _extract_resolution_snippet(text: str) -> Optional[str]:
    for pattern in RESOLUTION_MARKERS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            snippet = match.group(0).strip()
            return snippet[:220]
    return None


class RemediationAgent:
    def run(self, shared_context: Dict) -> Dict:
        triage = shared_context.get("triage", {})
        root_cause = shared_context.get("root_cause", {})
        duplicates = shared_context.get("duplicate_detection", {})

        component = triage.get("affected_component", "Unknown/General")
        matches = duplicates.get("matches", []) if duplicates else []

        recommendations = []

        # --- Highest-quality evidence: a CONFIRMED fix from a bug
        # resolved on this platform (Milestone 4 growth mechanism). Only
        # used when the match is genuinely close -- a confirmed fix for
        # an unrelated bug would be misleading. ---
        confirmed_found = False
        evidence_found = False
        for match in matches[:3]:
            confirmed_fix = (match.get("resolution") or "").strip()
            close_enough = match.get("match_status") in ("Likely Duplicate", "Related Issue")
            if confirmed_fix and close_enough:
                confirmed_found = True
                recommendations.append({
                    "recommendation": (
                        f"A similar bug (bug_id={match['bug_id']}) was resolved with this "
                        f"confirmed fix: \"{confirmed_fix[:400]}\""
                    ),
                    "basis": "confirmed_fix",
                    "source_bug_id": match["bug_id"],
                    "confidence": round(min(match.get("similarity_score", 0.5) + 0.15, 0.95), 2),
                })
                continue

            snippet = _extract_resolution_snippet(match.get("summary", ""))
            if snippet:
                evidence_found = True
                recommendations.append({
                    "recommendation": (
                        f"Apply a fix consistent with how a similar historical bug "
                        f"(bug_id={match['bug_id']}) was resolved: \"{snippet}\""
                    ),
                    "basis": "historical_evidence",
                    "source_bug_id": match["bug_id"],
                    "confidence": round(min(match.get("similarity_score", 0.5) + 0.1, 0.9), 2),
                })

        if root_cause and root_cause.get("root_cause_hypothesis") and root_cause.get("confidence", 0) >= 0.5:
            recommendations.append({
                "recommendation": (
                    f"Address the likely root cause directly: {root_cause['root_cause_hypothesis']}"
                ),
                "basis": "root_cause_analysis",
                "source_bug_id": None,
                "confidence": root_cause.get("confidence", 0.5),
            })

        best_practice = BEST_PRACTICE_GUIDANCE.get(component, BEST_PRACTICE_GUIDANCE["Unknown/General"])
        recommendations.append({
            "recommendation": best_practice,
            "basis": "best_practice_guideline",
            "source_bug_id": None,
            "confidence": 0.4,
        })

        overall_confidence = max((r["confidence"] for r in recommendations), default=0.3)

        reasoning_parts = []
        if confirmed_found:
            reasoning_parts.append(
                "One or more closely matched bugs were previously resolved on this platform with a "
                "confirmed fix; those are ranked first because they are the strongest evidence available."
            )
        if evidence_found:
            reasoning_parts.append(
                "Found resolution-style language in one or more matched historical bugs; "
                "the top evidence-based recommendation is grounded in that historical fix."
            )
        elif not confirmed_found:
            reasoning_parts.append(
                "No explicit resolution language was found in the matched historical bugs; "
                "recommendations rely on root cause analysis and general best practices instead."
            )
        reasoning_parts.append(
            "Recommendations are labeled by basis (confirmed_fix, historical_evidence, "
            "root_cause_analysis, or best_practice_guideline) so speculative guidance is never "
            "presented as a confirmed fix."
        )

        return {
            "agent": "RemediationAgent",
            "recommendations": recommendations,
            "confidence": overall_confidence,
            "reasoning": " ".join(reasoning_parts),
        }


if __name__ == "__main__":
    import json

    sample_context = {
        "triage": {"affected_component": "UI/Frontend"},
        "root_cause": {
            "root_cause_hypothesis": "The bug is likely caused by a null frame reference during tab teardown.",
            "confidence": 0.72,
        },
        "duplicate_detection": {
            "matches": [
                {
                    "bug_id": "236",
                    "similarity_score": 0.62,
                    "match_status": "Likely Duplicate",
                    "resolution": "Added a null-check before frame destruction in nsFrame.cpp.",
                    "summary": "Crash on tab close. Fixed by adding a null-check before frame destruction in nsFrame.cpp.",
                }
            ]
        },
    }

    agent = RemediationAgent()
    result = agent.run(sample_context)
    print(json.dumps(result, indent=2))