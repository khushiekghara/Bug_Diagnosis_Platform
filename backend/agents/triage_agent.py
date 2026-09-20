"""
Milestone 2 - Task 1: Triage Agent

Classifies a submitted bug by:
- Severity
- Priority
- Affected component
- Confidence score
- Reasoning

This implementation uses rule-based keyword matching.
No API key or external LLM is required.
"""

from typing import Dict, List


# ---------------------------------------------------------
# 1. SEVERITY KEYWORDS
# ---------------------------------------------------------

SEVERITY_KEYWORDS = {
    "Critical": [
        "data loss",
        "data corruption",
        "corruption",
        "security vulnerability",
        "vulnerability",
        "exploit",
        "breach",
        "deadlock",
        "system down",
        "outage",
        "cannot start",
        "won't start",
        "fatal",
        "segmentation fault",
        "segfault",
        "unrecoverable",
        "production down",
        "service unavailable",
    ],

    "High": [
        "crash",
        "crashes",
        "crashed",
        "failure",
        "failed",
        "exception",
        "error",
        "broken",
        "not working",
        "doesn't work",
        "regression",
        "blocks",
        "blocking",
        "null pointer",
        "nullpointerexception",
        "timeout",
        "freeze",
        "freezes",
        "hangs",
        "unresponsive",
    ],

    "Medium": [
        "incorrect",
        "wrong",
        "unexpected",
        "inconsistent",
        "slow",
        "performance",
        "delay",
        "mismatch",
        "warning",
        "deprecated",
    ],

    "Low": [
        "cosmetic",
        "typo",
        "spelling",
        "minor",
        "ui glitch",
        "alignment",
        "color",
        "spacing",
        "enhancement",
        "suggestion",
        "nice to have",
    ],
}


# ---------------------------------------------------------
# 2. COMPONENT KEYWORDS
# ---------------------------------------------------------

COMPONENT_KEYWORDS = {
    "Database": [
        "database",
        "sql",
        "query",
        "db ",
        "table",
        "schema",
        "index",
        "postgres",
        "mysql",
        "sqlite",
        "connection pool",
    ],

    "Authentication": [
        "login",
        "log in",
        "auth",
        "password",
        "token",
        "session",
        "permission",
        "unauthorized",
        "credential",
        "authentication",
    ],

    "UI/Frontend": [
        "button",
        "page",
        "screen",
        "display",
        "render",
        "css",
        "layout",
        "click",
        "form",
        "ui ",
        "frontend",
        "browser",
        "javascript",
    ],

    "API/Backend": [
        "endpoint",
        "api",
        "request",
        "response",
        "server",
        "route",
        "controller",
        "service",
        "backend",
        "fastapi",
        "rest",
    ],

    "Network": [
        "network",
        "connection",
        "socket",
        "proxy",
        "dns",
        "timeout",
        "http",
        "tcp",
        "connection refused",
        "connectionerror",
    ],

    "Memory/Performance": [
        "memory",
        "leak",
        "cpu",
        "performance",
        "slow",
        "latency",
        "resource",
        "out of memory",
        "oom",
    ],

    "File/Storage": [
        "file",
        "upload",
        "download",
        "disk",
        "storage",
        "path",
        "directory",
        "filesystem",
    ],
}


# ---------------------------------------------------------
# 3. SEVERITY → PRIORITY
# ---------------------------------------------------------

SEVERITY_TO_PRIORITY = {
    "Critical": "P1 - Immediate",
    "High": "P2 - High",
    "Medium": "P3 - Normal",
    "Low": "P4 - Low",
}


# ---------------------------------------------------------
# 4. SEVERITY WEIGHT
# ---------------------------------------------------------

SEVERITY_WEIGHT = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


# ---------------------------------------------------------
# 5. COUNT KEYWORD MATCHES
# ---------------------------------------------------------

def _count_matches(text: str, keywords: List[str]) -> List[str]:

    text_lower = text.lower()

    return [
        keyword
        for keyword in keywords
        if keyword.lower() in text_lower
    ]


# ---------------------------------------------------------
# 6. CLASSIFY SEVERITY
# ---------------------------------------------------------

def classify_severity(text: str) -> Dict:

    matches = {
        level: _count_matches(text, keywords)
        for level, keywords in SEVERITY_KEYWORDS.items()
    }

    scores = {
        level: len(values) * SEVERITY_WEIGHT[level]
        for level, values in matches.items()
    }

    best_level = max(scores, key=scores.get)

    # No keyword found
    if scores[best_level] == 0:

        return {
            "severity": "Medium",
            "matched_keywords": [],
            "matched_count": 0,
            "score": 0,
        }

    return {
        "severity": best_level,
        "matched_keywords": matches[best_level],
        "matched_count": len(matches[best_level]),
        "score": scores[best_level],
    }


# ---------------------------------------------------------
# 7. CLASSIFY COMPONENT
# ---------------------------------------------------------

def classify_component(text: str) -> Dict:

    matches = {
        component: _count_matches(text, keywords)
        for component, keywords in COMPONENT_KEYWORDS.items()
    }

    best_component = max(
        matches,
        key=lambda component: len(matches[component])
    )

    best_matches = matches[best_component]

    # No component keyword found
    if not best_matches:

        return {
            "component": "Unknown/General",
            "matched_keywords": [],
        }

    return {
        "component": best_component,
        "matched_keywords": best_matches,
    }


# ---------------------------------------------------------
# 8. CALCULATE CONFIDENCE
# ---------------------------------------------------------

def compute_confidence(
    severity_result: Dict,
    component_result: Dict
) -> float:

    severity_score = min(
        severity_result["matched_count"] / 3.0,
        1.0
    )

    component_score = min(
        len(component_result["matched_keywords"]) / 2.0,
        1.0
    )

    confidence = round(
        (0.7 * severity_score) +
        (0.3 * component_score),
        2
    )

    return max(confidence, 0.30)


# ---------------------------------------------------------
# 9. TRIAGE AGENT
# ---------------------------------------------------------

class TriageAgent:

    """
    Triage Agent classifies:
    - Severity
    - Priority
    - Affected component
    - Confidence
    - Reasoning
    """

    def run(self, bug_report: Dict) -> Dict:

        # Combine all available bug information
        combined_text = " ".join(
            [
                bug_report.get("title", "") or "",
                bug_report.get("description", "") or "",
                bug_report.get("stack_trace", "") or "",
                bug_report.get("error_log", "") or "",
            ]
        )

        # Classify severity
        severity_result = classify_severity(
            combined_text
        )

        # Classify component
        component_result = classify_component(
            combined_text
        )

        # Calculate confidence
        confidence = compute_confidence(
            severity_result,
            component_result
        )

        # Convert severity to priority
        priority = SEVERITY_TO_PRIORITY[
            severity_result["severity"]
        ]

        # -------------------------------------------------
        # REASONING
        # -------------------------------------------------

        reasoning_parts = []

        # Severity reasoning
        if severity_result["matched_keywords"]:

            reasoning_parts.append(
                f"Severity '{severity_result['severity']}' "
                f"was inferred from the signal(s): "
                f"{', '.join(severity_result['matched_keywords'][:5])}."
            )

        else:

            reasoning_parts.append(
                "No strong severity signal was found, "
                "so severity defaulted to Medium."
            )

        # Component reasoning
        if component_result["matched_keywords"]:

            reasoning_parts.append(
                f"Component "
                f"'{component_result['component']}' "
                f"was inferred from the signal(s): "
                f"{', '.join(component_result['matched_keywords'][:5])}."
            )

        else:

            reasoning_parts.append(
                "No component-specific signal was found; "
                "component is Unknown/General."
            )

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        return {

            "agent": "TriageAgent",

            "severity": severity_result[
                "severity"
            ],

            "priority": priority,

            "affected_component":
                component_result["component"],

            "confidence": confidence,

            "matched_severity_keywords":
                severity_result["matched_keywords"],

            "matched_component_keywords":
                component_result["matched_keywords"],

            "reasoning":
                " ".join(reasoning_parts),
        }


# ---------------------------------------------------------
# 10. TEST THE AGENT DIRECTLY
# ---------------------------------------------------------

if __name__ == "__main__":

    sample_bug = {

        "title":
            "Application crashes on login",

        "description":
            "The application crashes with a "
            "segmentation fault after password reset.",

        "stack_trace":
            "",

        "error_log":
            "",
    }

    agent = TriageAgent()

    result = agent.run(sample_bug)

    import json

    print(
        json.dumps(
            result,
            indent=2
        )
    )