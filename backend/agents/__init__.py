"""
Milestone 2 -- Task 1: Triage Agent
Classifies a submitted bug by severity, priority, and affected component,
with a confidence score and human-readable reasoning.

Rule-based (keyword + heuristic) approach -- no LLM/API key required,
fully explainable, and runs instantly.
"""
from typing import Dict, List


# Keywords that signal each severity level. Order matters: checked from
# most severe to least severe, and the first match wins per keyword group.
SEVERITY_KEYWORDS = {
    "Critical": [
        "crash", "crashes", "crashed", "data loss", "corrupt", "corruption",
        "security", "vulnerability", "exploit", "breach", "deadlock",
        "system down", "outage", "cannot start", "won't start", "fatal",
        "segmentation fault", "segfault", "memory leak", "unrecoverable",
    ],
    "High": [
        "fails", "failure", "failed", "exception", "error", "broken",
        "not working", "doesn't work", "regression", "blocks", "blocking",
        "null pointer", "nullpointerexception", "timeout", "freeze", "freezes",
        "hangs", "unresponsive",
    ],
    "Medium": [
        "incorrect", "wrong", "unexpected", "inconsistent", "slow",
        "performance", "delay", "mismatch", "warning", "deprecated",
    ],
    "Low": [
        "cosmetic", "typo", "spelling", "minor", "ui glitch", "alignment",
        "color", "spacing", "enhancement", "suggestion", "nice to have",
    ],
}

# Keywords that hint at which part of the system is affected.
COMPONENT_KEYWORDS = {
    "Database": ["database", "sql", "query", "db ", "table", "schema", "index", "postgres", "mysql", "sqlite"],
    "Authentication": ["login", "auth", "password", "token", "session", "permission", "unauthorized", "credential"],
    "UI/Frontend": ["button", "page", "screen", "display", "render", "css", "layout", "click", "form", "ui "],
    "API/Backend": ["endpoint", "api", "request", "response", "server", "route", "controller", "service"],
    "Network": ["network", "connection", "socket", "proxy", "dns", "timeout", "http", "tcp"],
    "Memory/Performance": ["memory", "leak", "cpu", "performance", "slow", "latency", "resource"],
    "File/Storage": ["file", "upload", "download", "disk", "storage", "path", "directory"],
}

# Priority derived from severity -- kept as an explicit mapping so it's
# easy to see and tune independently of severity wording.
SEVERITY_TO_PRIORITY = {
    "Critical": "P1 - Immediate",
    "High": "P2 - High",
    "Medium": "P3 - Normal",
    "Low": "P4 - Low",
}


def _count_matches(text: str, keywords: List[str]) -> List[str]:
    text_lower = text.lower()
    return [kw for kw in keywords if kw in text_lower]


def classify_severity(text: str) -> Dict:
    """Returns the severity level with the most keyword matches, plus
    which keywords triggered it (used for reasoning + confidence)."""
    matches_per_level = {
        level: _count_matches(text, keywords)
        for level, keywords in SEVERITY_KEYWORDS.items()
    }

    best_level = max(matches_per_level, key=lambda lvl: len(matches_per_level[lvl]))
    best_matches = matches_per_level[best_level]

    if not best_matches:
        return {"severity": "Medium", "matched_keywords": [], "matched_count": 0}

    return {
        "severity": best_level,
        "matched_keywords": best_matches,
        "matched_count": len(best_matches),
    }


def classify_component(text: str) -> Dict:
    matches_per_component = {
        component: _count_matches(text, keywords)
        for component, keywords in COMPONENT_KEYWORDS.items()
    }
    best_component = max(matches_per_component, key=lambda c: len(matches_per_component[c]))
    best_matches = matches_per_component[best_component]

    if not best_matches:
        return {"component": "Unknown/General", "matched_keywords": []}

    return {"component": best_component, "matched_keywords": best_matches}


def compute_confidence(severity_result: Dict, component_result: Dict) -> float:
    """Simple, explainable confidence score in [0, 1] based on how many
    signal keywords were found. More matches = more confidence."""
    sev_score = min(severity_result["matched_count"] / 3, 1.0)
    comp_score = min(len(component_result["matched_keywords"]) / 2, 1.0)
    confidence = round((0.7 * sev_score) + (0.3 * comp_score), 2)
    return max(confidence, 0.3)


class TriageAgent:
    """
    Classifies a bug report's severity, priority, and affected component.
    """

    def run(self, bug_report: Dict) -> Dict:
        combined_text = " ".join([
            bug_report.get("title", "") or "",
            bug_report.get("description", "") or "",
            bug_report.get("stack_trace", "") or "",
            bug_report.get("error_log", "") or "",
        ])

        severity_result = classify_severity(combined_text)
        component_result = classify_component(combined_text)
        confidence = compute_confidence(severity_result, component_result)
        priority = SEVERITY_TO_PRIORITY[severity_result["severity"]]

        reasoning_parts = []
        if severity_result["matched_keywords"]:
            reasoning_parts.append(
                f"Severity '{severity_result['severity']}' inferred from keyword(s): "
                f"{', '.join(severity_result['matched_keywords'][:5])}."
            )
        else:
            reasoning_parts.append(
                "No strong severity keywords found; defaulted to 'Medium'."
            )

        if component_result["matched_keywords"]:
            reasoning_parts.append(
                f"Component '{component_result['component']}' inferred from keyword(s): "
                f"{', '.join(component_result['matched_keywords'][:5])}."
            )
        else:
            reasoning_parts.append(
                "No component-specific keywords found; component marked as 'Unknown/General'."
            )

        return {
            "agent": "TriageAgent",
            "severity": severity_result["severity"],
            "priority": priority,
            "affected_component": component_result["component"],
            "confidence": confidence,
            "reasoning": " ".join(reasoning_parts),
        }


if __name__ == "__main__":
    sample_bug = {
        "title": "Application crashes on login",
        "description": "The app crashes with a segmentation fault whenever a user "
                        "tries to log in after a password reset.",
        "stack_trace": "",
        "error_log": "",
    }
    agent = TriageAgent()
    result = agent.run(sample_bug)
    import json
    print(json.dumps(result, indent=2))