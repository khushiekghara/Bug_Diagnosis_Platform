"""
Milestone 2 -- Task 4: Agent Validation
Validates Triage Agent and Log Analysis Agent accuracy across varied bug
report formats and error types.

Two validation sets are used:

1. A hand-labeled test suite covering different formats (Python traceback,
   Java stack trace, JavaScript error, plain-text report with no trace,
   log-file style output). Each case has an expected severity/component/
   exception type, so accuracy can actually be measured.

2. A sample drawn from the seeded historical dataset
   (kb/data/cleaned_historical_bugs.csv). These have no ground-truth
   severity labels, so they are used for coverage testing -- confirming the
   agents produce sensible, non-crashing output on real messy bug text --
   rather than accuracy scoring.

Run from the project root:
    python scripts/validate_agents.py
"""
import os
import sys
import json
from collections import Counter

# Make backend/ importable so we can reuse the real agent classes
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from agents.triage_agent import TriageAgent            # noqa: E402
from agents.log_analysis_agent import LogAnalysisAgent  # noqa: E402
from agents.orchestrator import AgentOrchestrator       # noqa: E402


# ---------------------------------------------------------------------------
# 1. Hand-labeled test cases -- varied formats and error types
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "name": "Python traceback - critical crash",
        "bug": {
            "id": "T1",
            "title": "Application crashes on startup",
            "description": "The service crashes immediately with a fatal error on boot.",
            "stack_trace": (
                'Traceback (most recent call last):\n'
                '  File "app/main.py", line 42, in start\n'
                '    db.connect()\n'
                'ConnectionError: could not reach database'
            ),
            "error_log": "",
        },
        "expected_severity": "Critical",
        "expected_exception": "ConnectionError",
        "expected_component": "Database",
    },
    {
        "name": "Java stack trace - null pointer",
        "bug": {
            "id": "T2",
            "title": "NullPointerException in connection pool",
            "description": "Under load, leasing a connection throws an exception intermittently.",
            "stack_trace": (
                "java.lang.NullPointerException\n"
                "    at org.apache.http.pool.AbstractConnPool.getPoolEntryBlocking(AbstractConnPool.java:327)"
            ),
            "error_log": "",
        },
        "expected_severity": "High",
        "expected_exception": "NullPointerException",
        "expected_component": "Network",
    },
    {
        "name": "JavaScript error - UI issue",
        "bug": {
            "id": "T3",
            "title": "Button click throws TypeError on checkout page",
            "description": "Clicking the submit button on the checkout page does nothing.",
            "stack_trace": (
                "TypeError: Cannot read property 'value' of null\n"
                "    at handleSubmit (checkout.js:88:12)"
            ),
            "error_log": "",
        },
        "expected_severity": "High",
        "expected_exception": "TypeError",
        "expected_component": "UI/Frontend",
    },
    {
        "name": "Plain text report - no stack trace",
        "bug": {
            "id": "T4",
            "title": "Spelling mistake on settings page",
            "description": "There is a typo in the label on the settings screen; it reads 'Prefrences'.",
            "stack_trace": "",
            "error_log": "",
        },
        "expected_severity": "Low",
        "expected_exception": None,
        "expected_component": "UI/Frontend",
    },
    {
        "name": "Log-file style output - memory issue",
        "bug": {
            "id": "T5",
            "title": "Memory leak in background worker",
            "description": "Memory usage grows unbounded over several hours of operation.",
            "stack_trace": "",
            "error_log": (
                "[2026-01-14 03:22:11] WARN  heap usage 92%\n"
                "[2026-01-14 03:24:02] ERROR OutOfMemoryError in worker/pool.py:204\n"
            ),
        },
        "expected_severity": "Critical",
        "expected_exception": "OutOfMemoryError",
        "expected_component": "Memory/Performance",
    },
    {
        "name": "Auth failure - security related",
        "bug": {
            "id": "T6",
            "title": "Security vulnerability allows session token reuse",
            "description": (
                "An expired session token can still be used to authenticate, "
                "which is a serious security vulnerability."
            ),
            "stack_trace": "",
            "error_log": "",
        },
        "expected_severity": "Critical",
        "expected_exception": None,
        "expected_component": "Authentication",
    },
    {
        "name": "Performance complaint - medium severity",
        "bug": {
            "id": "T7",
            "title": "Search results load slowly",
            "description": "Search queries take an unexpectedly long delay to return results.",
            "stack_trace": "",
            "error_log": "",
        },
        "expected_severity": "Medium",
        "expected_exception": None,
        "expected_component": "Memory/Performance",
    },
    {
        "name": "Empty trace - description only",
        "bug": {
            "id": "T8",
            "title": "Upload fails for large files",
            "description": "File upload fails silently when the file is over 50MB.",
            "stack_trace": "",
            "error_log": "",
        },
        "expected_severity": "High",
        "expected_exception": None,
        "expected_component": "File/Storage",
    },
]


def validate_labeled_cases():
    """Runs both agents on labeled cases and reports accuracy."""
    triage_agent = TriageAgent()
    log_agent = LogAnalysisAgent()

    severity_correct = 0
    component_correct = 0
    exception_correct = 0
    total = len(TEST_CASES)

    rows = []

    for case in TEST_CASES:
        triage_result = triage_agent.run(case["bug"])
        log_result = log_agent.run(case["bug"])

        sev_ok = triage_result["severity"] == case["expected_severity"]
        comp_ok = triage_result["affected_component"] == case["expected_component"]
        exc_ok = log_result["exception_type"] == case["expected_exception"]

        severity_correct += int(sev_ok)
        component_correct += int(comp_ok)
        exception_correct += int(exc_ok)

        rows.append({
            "case": case["name"],
            "severity": f"{triage_result['severity']} (exp {case['expected_severity']}) {'OK' if sev_ok else 'MISS'}",
            "component": f"{triage_result['affected_component']} (exp {case['expected_component']}) {'OK' if comp_ok else 'MISS'}",
            "exception": f"{log_result['exception_type']} (exp {case['expected_exception']}) {'OK' if exc_ok else 'MISS'}",
            "confidence": triage_result["confidence"],
        })

    print("=" * 78)
    print("PART 1 -- ACCURACY ON LABELED TEST CASES")
    print("=" * 78)
    for row in rows:
        print(f"\n[{row['case']}]")
        print(f"  Severity  : {row['severity']}")
        print(f"  Component : {row['component']}")
        print(f"  Exception : {row['exception']}")
        print(f"  Confidence: {row['confidence']}")

    print("\n" + "-" * 78)
    print("ACCURACY SUMMARY")
    print("-" * 78)
    print(f"  Severity classification : {severity_correct}/{total} = {severity_correct / total:.0%}")
    print(f"  Component detection     : {component_correct}/{total} = {component_correct / total:.0%}")
    print(f"  Exception extraction    : {exception_correct}/{total} = {exception_correct / total:.0%}")

    overall = (severity_correct + component_correct + exception_correct) / (total * 3)
    print(f"  Overall agent accuracy  : {overall:.0%}")

    return {
        "severity_accuracy": severity_correct / total,
        "component_accuracy": component_correct / total,
        "exception_accuracy": exception_correct / total,
        "overall_accuracy": overall,
    }


# ---------------------------------------------------------------------------
# 2. Coverage test on the seeded historical dataset
# ---------------------------------------------------------------------------

def validate_on_seeded_dataset(sample_size: int = 100):
    """Runs the full orchestrator on real historical bug text to confirm
    the agents handle messy, varied, real-world input without crashing,
    and to see how the classifications distribute."""
    csv_path = os.path.join(PROJECT_ROOT, "kb", "data", "cleaned_historical_bugs.csv")

    print("\n" + "=" * 78)
    print("PART 2 -- COVERAGE TEST ON SEEDED HISTORICAL DATASET")
    print("=" * 78)

    if not os.path.exists(csv_path):
        print(f"  Skipped: {csv_path} not found.")
        print("  Run the kb/ pipeline first (clean_data.py) to generate it.")
        return None

    import pandas as pd
    df = pd.read_csv(csv_path, nrows=sample_size)

    orchestrator = AgentOrchestrator()

    severity_counts = Counter()
    component_counts = Counter()
    exception_counts = Counter()
    failures = 0
    exception_found = 0

    for _, row in df.iterrows():
        bug = {
            "id": row.get("id"),
            "title": str(row.get("title", "") or ""),
            "description": str(row.get("description", "") or ""),
            "stack_trace": str(row.get("stack_trace", "") or ""),
            "error_log": "",
        }
        try:
            result = orchestrator.run(bug)
            triage = result["agent_outputs"]["TriageAgent"]
            log = result["agent_outputs"]["LogAnalysisAgent"]

            severity_counts[triage["severity"]] += 1
            component_counts[triage["affected_component"]] += 1
            if log["exception_type"]:
                exception_counts[log["exception_type"]] += 1
                exception_found += 1
        except Exception as exc:
            failures += 1
            print(f"  FAILURE on bug id={bug['id']}: {exc}")

    processed = len(df)
    print(f"\n  Records processed      : {processed}")
    print(f"  Pipeline failures      : {failures}")
    print(f"  Success rate           : {(processed - failures) / processed:.0%}")
    print(f"  Exception type found   : {exception_found}/{processed} ({exception_found / processed:.0%})")

    print("\n  Severity distribution:")
    for sev, count in severity_counts.most_common():
        print(f"    {sev:<10} {count:>4}  ({count / processed:.0%})")

    print("\n  Component distribution:")
    for comp, count in component_counts.most_common():
        print(f"    {comp:<22} {count:>4}  ({count / processed:.0%})")

    if exception_counts:
        print("\n  Top exception types detected:")
        for exc_type, count in exception_counts.most_common(8):
            print(f"    {exc_type:<32} {count:>4}")

    return {
        "processed": processed,
        "failures": failures,
        "severity_distribution": dict(severity_counts),
        "component_distribution": dict(component_counts),
    }


if __name__ == "__main__":
    accuracy = validate_labeled_cases()
    coverage = validate_on_seeded_dataset(sample_size=100)

    print("\n" + "=" * 78)
    print("VALIDATION COMPLETE")
    print("=" * 78)
    print("Part 1 measures accuracy against known expected values.")
    print("Part 2 confirms the agents handle real, messy historical bug text")
    print("without failures, and shows how classifications distribute.")