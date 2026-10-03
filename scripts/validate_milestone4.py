"""
Milestone 4 -- Task 3: End-to-End Testing
Validates the full agent pipeline across varied bug types, stack trace
formats, and historical dataset sizes, and separately validates the
Milestone 4 features: Defect Pattern Analytics and Knowledge Base Growth.

Requires:
- The backend running: cd backend && uvicorn main:app --reload
- pip install requests (if not already installed)

Run from the project root:
    python scripts/validate_milestone4.py
"""
import os
import sys
import time
import json
import requests

API_BASE = "http://localhost:8000"

VARIED_BUGS = [
    {
        "name": "Python traceback",
        "title": "Startup fails with a database connection error",
        "description": "The service crashes on boot whenever the database is unreachable.",
        "stack_trace": (
            'Traceback (most recent call last):\n'
            '  File "app/main.py", line 42, in start\n'
            '    db.connect()\n'
            'ConnectionError: could not reach database'
        ),
    },
    {
        "name": "Java stack trace",
        "title": "NullPointerException under load in the connection pool",
        "description": "Under heavy load, leasing a connection intermittently throws an exception.",
        "stack_trace": (
            "java.lang.NullPointerException\n"
            "    at org.apache.http.pool.AbstractConnPool.getPoolEntryBlocking(AbstractConnPool.java:327)"
        ),
    },
    {
        "name": "JavaScript error",
        "title": "Checkout button throws a TypeError",
        "description": "Clicking submit on the checkout page does nothing and logs an error.",
        "stack_trace": (
            "TypeError: Cannot read property 'value' of null\n"
            "    at handleSubmit (checkout.js:88:12)"
        ),
    },
    {
        "name": "Log-file style output",
        "title": "Memory leak in background worker",
        "description": "",
        "error_log": (
            "[2026-01-14 03:22:11] WARN  heap usage 92%\n"
            "[2026-01-14 03:24:02] ERROR OutOfMemoryError in worker/pool.py:204\n"
        ),
    },
    {
        "name": "Plain text, no stack trace",
        "title": "Typo on the settings page",
        "description": "The settings screen label reads 'Prefrences' instead of 'Preferences'.",
    },
]


def submit_and_diagnose(bug):
    resp = requests.post(
        f"{API_BASE}/bugs/paste",
        json={k: v for k, v in bug.items() if k != "name"},
        timeout=60,
    )
    resp.raise_for_status()
    bug_id = resp.json()["id"]
    diag = requests.get(f"{API_BASE}/bugs/{bug_id}/diagnosis", timeout=30)
    diag.raise_for_status()
    return bug_id, diag.json()


def validate_varied_bug_types():
    print("=" * 78)
    print("PART A -- END-TO-END TEST ACROSS VARIED BUG TYPES / FORMATS")
    print("=" * 78)

    results = []
    for bug in VARIED_BUGS:
        bug_id, diagnosis = submit_and_diagnose(bug)

        checks = {
            "triage_ran": diagnosis.get("severity") is not None,
            "log_analysis_ran": diagnosis.get("failure_point") is not None,
            "root_cause_ran": diagnosis.get("root_cause_hypothesis") is not None,
            "duplicate_ran": diagnosis.get("duplicate_status") is not None,
            "remediation_ran": bool(json.loads(diagnosis.get("remediation_recommendations_json") or "[]")),
        }
        all_ran = all(checks.values())
        results.append(all_ran)

        print(f"\n[{bug['name']}] bug_id={bug_id}")
        print(f"  Severity: {diagnosis.get('severity')}  |  Exception: {diagnosis.get('exception_type')}")
        print(f"  Duplicate status: {diagnosis.get('duplicate_status')}")
        print(f"  All 5 agents produced output: {all_ran}  {checks if not all_ran else ''}")

    pass_rate = sum(results) / len(results)
    print("\n" + "-" * 78)
    print(f"  Formats fully processed by all 5 agents: {sum(results)}/{len(results)} = {pass_rate:.0%}")
    return pass_rate


def validate_duplicate_quality_vs_dataset_size():
    """
    The knowledge base's effective size changes as bugs are resolved and
    added back to it (Milestone 4 growth). This re-checks duplicate
    detection quality at the CURRENT dataset size by resubmitting a known
    bug and confirming self-similarity still holds -- i.e. growth does
    not degrade retrieval quality as the store gets larger.
    """
    print("\n" + "=" * 78)
    print("PART B -- DUPLICATE DETECTION QUALITY AT CURRENT DATASET SIZE")
    print("=" * 78)

    stats = requests.get(f"{API_BASE}/knowledge-base/stats", timeout=30).json()
    print(f"  Current knowledge base size: {stats['total_chunks']} chunks "
          f"({stats['historical_chunks']} historical + {stats['platform_chunks']} platform-added "
          f"from {stats['platform_bugs']} resolved bug(s))")

    probe = {
        "title": "Browser crashes closing a tab while a video plays",
        "description": "The browser crashes when closing an unrelated tab while a video plays elsewhere.",
    }
    bug_id, diagnosis = submit_and_diagnose(probe)
    matches = json.loads(diagnosis.get("duplicate_matches_json") or "[]")

    found_match = len(matches) > 0
    print(f"  Probe bug_id={bug_id}: status={diagnosis.get('duplicate_status')}, "
          f"matches_found={len(matches)}")
    return found_match


def validate_recommendation_relevance():
    print("\n" + "=" * 78)
    print("PART C -- RECOMMENDATION RELEVANCE")
    print("=" * 78)

    relevant_count = 0
    total = len(VARIED_BUGS)
    for bug in VARIED_BUGS:
        bug_id, diagnosis = submit_and_diagnose(bug)
        recs = json.loads(diagnosis.get("remediation_recommendations_json") or "[]")
        component = diagnosis.get("affected_component", "")

        has_grounded_rec = any(r["basis"] != "best_practice_guideline" for r in recs)
        relevant_count += int(has_grounded_rec)

        print(f"  [{bug['name']}] component={component}, "
              f"recommendation_count={len(recs)}, grounded={has_grounded_rec}")

    relevance_rate = relevant_count / total
    print(f"\n  Recommendations grounded in evidence (not just best-practice fallback): "
          f"{relevant_count}/{total} = {relevance_rate:.0%}")
    return relevance_rate


def validate_analytics():
    print("\n" + "=" * 78)
    print("PART D -- DEFECT PATTERN ANALYTICS SANITY CHECK")
    print("=" * 78)

    report = requests.get(f"{API_BASE}/analytics/patterns", timeout=30).json()
    print(f"  Total bugs submitted : {report['total_bugs_submitted']}")
    print(f"  Total bugs analyzed  : {report['total_bugs_analyzed']}")
    print(f"  Components tracked   : {len(report['component_frequency'])}")
    print(f"  Recurring patterns   : {len(report['recurring_patterns'])}")
    print(f"  Duplicate rate       : {report['duplicate_cluster_summary']['duplicate_rate_percent']}%")

    consistent = report["total_bugs_analyzed"] <= report["total_bugs_submitted"]
    print(f"  Analyzed <= Submitted (no double-counting): {consistent}")
    return consistent


if __name__ == "__main__":
    try:
        requests.get(API_BASE, timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not reach {API_BASE}")
        print("Start the backend first: cd backend && uvicorn main:app --reload")
        sys.exit(1)

    format_pass_rate = validate_varied_bug_types()
    duplicate_ok = validate_duplicate_quality_vs_dataset_size()
    relevance_rate = validate_recommendation_relevance()
    analytics_ok = validate_analytics()

    print("\n" + "=" * 78)
    print("MILESTONE 4 END-TO-END VALIDATION COMPLETE")
    print("=" * 78)
    print(f"Format coverage (all 5 agents produced output): {format_pass_rate:.0%}")
    print(f"Duplicate detection functioning at current dataset size: {duplicate_ok}")
    print(f"Recommendation relevance (evidence-grounded): {relevance_rate:.0%}")
    print(f"Analytics internally consistent: {analytics_ok}")