"""
Milestone 4 -- Task 4: Final Demonstration Report
Submits five distinct, realistic bug reports through the live API, lets
the full 5-agent pipeline run on each, and writes a single Markdown
report showing the complete pipeline output for every one of them.

This is the artifact for the "minimum five distinct bug submissions with
full agent pipeline output" deliverable -- generate it once everything
is working, and hand the output file to your mentor alongside the repo.

Requires:
- The backend running: cd backend && uvicorn main:app --reload
- pip install requests (if not already installed)

Run from the project root:
    python scripts/generate_demo_report.py
"""
import os
import sys
import json
import datetime
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_BASE = "http://localhost:8000"
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "docs", "demo_report.md")

DEMO_BUGS = [
    {
        "title": "Application crashes on startup when the database is unreachable",
        "description": (
            "The backend service crashes immediately on startup whenever the "
            "configured database host cannot be reached. No graceful error is "
            "shown to the operator -- the process just exits."
        ),
        "stack_trace": (
            'Traceback (most recent call last):\n'
            '  File "app/main.py", line 42, in start\n'
            '    db.connect()\n'
            '  File "app/db.py", line 17, in connect\n'
            '    raise ConnectionError("could not reach database")\n'
            'ConnectionError: could not reach database'
        ),
    },
    {
        "title": "Intermittent NullPointerException leasing connections under load",
        "description": (
            "Under a load test with 500 concurrent threads, leasing a connection "
            "from the pool intermittently throws a NullPointerException."
        ),
        "stack_trace": (
            "java.lang.NullPointerException\n"
            "    at org.apache.http.pool.AbstractConnPool.getPoolEntryBlocking(AbstractConnPool.java:327)\n"
            "    at org.apache.http.impl.conn.CPoolProxy.getPoolEntry(CPoolProxy.java:150)"
        ),
    },
    {
        "title": "Checkout button does nothing and logs a TypeError",
        "description": (
            "On the checkout page, clicking Submit does not advance the order. "
            "The browser console shows a TypeError on click."
        ),
        "stack_trace": (
            "TypeError: Cannot read property 'value' of null\n"
            "    at handleSubmit (checkout.js:88:12)\n"
            "    at HTMLButtonElement.onclick (checkout.js:14:5)"
        ),
    },
    {
        "title": "Background worker memory usage grows unbounded",
        "description": (
            "Memory usage of the background worker process grows continuously "
            "over several hours of operation until it is killed by the OS."
        ),
        "error_log": (
            "[2026-01-14 03:22:11] WARN  heap usage 92%\n"
            "[2026-01-14 03:24:02] ERROR OutOfMemoryError in worker/pool.py:204\n"
            "[2026-01-14 03:24:03] ERROR worker process terminated"
        ),
    },
    {
        "title": "Settings page shows a spelling mistake",
        "description": (
            "The label on the account settings screen reads 'Prefrences' "
            "instead of 'Preferences'."
        ),
    },
]


def submit_and_diagnose(bug):
    resp = requests.post(
        f"{API_BASE}/bugs/paste",
        json={k: v for k, v in bug.items()},
        timeout=60,
    )
    resp.raise_for_status()
    bug_id = resp.json()["id"]

    full = requests.post(f"{API_BASE}/bugs/{bug_id}/diagnose", timeout=60)
    full.raise_for_status()
    return bug_id, full.json()


def fmt_list(items, empty="None"):
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def render_bug_section(index, bug, bug_id, result):
    outputs = result["agent_outputs"]
    triage = outputs.get("TriageAgent", {})
    log = outputs.get("LogAnalysisAgent", {})
    root_cause = outputs.get("RootCauseAgent", {})
    duplicates = outputs.get("DuplicateDetectionAgent", {})
    remediation = outputs.get("RemediationAgent", {})

    lines = []
    lines.append(f"## Bug {index}: {bug['title']}")
    lines.append("")
    lines.append(f"**Bug ID:** {bug_id}  ")
    lines.append(f"**Analyzed at:** {result['analyzed_at']}  ")
    lines.append(f"**Agents run:** {', '.join(result['agents_run'])}")
    lines.append("")
    lines.append("**Submitted report:**")
    lines.append(f"- Description: {bug.get('description', '(none)')}")
    if bug.get("stack_trace"):
        lines.append(f"- Stack trace:\n```\n{bug['stack_trace']}\n```")
    if bug.get("error_log"):
        lines.append(f"- Error log:\n```\n{bug['error_log']}\n```")
    lines.append("")

    lines.append("### Triage Agent")
    lines.append(f"- Severity: **{triage.get('severity')}**")
    lines.append(f"- Priority: {triage.get('priority')}")
    lines.append(f"- Affected component: {triage.get('affected_component')}")
    lines.append(f"- Confidence: {triage.get('confidence')}")
    lines.append(f"- Reasoning: {triage.get('reasoning')}")
    lines.append("")

    lines.append("### Log Analysis Agent")
    lines.append(f"- Exception type: {log.get('exception_type')}")
    lines.append(f"- Failure point: {log.get('failure_point')}")
    lines.append(f"- Affected code path: {', '.join(log.get('affected_code_path', []) or []) or 'None'}")
    lines.append("")

    lines.append("### Root Cause Agent")
    lines.append(f"- Confidence: {root_cause.get('confidence')}")
    lines.append(f"- Hypothesis: {root_cause.get('root_cause_hypothesis')}")
    evidence = root_cause.get("supporting_evidence", [])
    lines.append(f"- Supporting evidence ({len(evidence)} item(s)):")
    for ev in evidence:
        lines.append(f"  - bug_id={ev['bug_id']} (distance={ev['similarity_distance']}): {ev['excerpt']}")
    lines.append("")

    lines.append("### Duplicate Detection Agent")
    lines.append(f"- Status: **{duplicates.get('duplicate_status')}**")
    matches = duplicates.get("matches", [])
    lines.append(f"- Matches found ({len(matches)}):")
    for m in matches:
        lines.append(
            f"  - bug_id={m['bug_id']} similarity={m['similarity_score']} "
            f"status={m['match_status']}{' (confirmed fix on platform)' if m.get('confirmed_on_platform') else ''}"
        )
    lines.append("")

    lines.append("### Remediation Agent")
    recs = remediation.get("recommendations", [])
    for r in recs:
        source = f" (source bug_id={r['source_bug_id']})" if r.get("source_bug_id") else ""
        lines.append(f"- **[{r['basis']}]** confidence={r['confidence']}{source}: {r['recommendation']}")
    lines.append("")

    lines.append("### Summary")
    lines.append(result.get("summary", ""))
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    try:
        requests.get(API_BASE, timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not reach {API_BASE}")
        print("Start the backend first: cd backend && uvicorn main:app --reload")
        sys.exit(1)

    report_lines = [
        "# Bug Diagnosis Platform -- Final Demonstration Report",
        "",
        f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
        "",
        f"This report submits {len(DEMO_BUGS)} distinct bug reports -- spanning Python, "
        "Java, and JavaScript stack traces, a log-file-style error, and a plain-text "
        "report with no trace at all -- through the live API, and records the complete "
        "output of all 5 agents (Triage, Log Analysis, Root Cause, Duplicate Detection, "
        "Remediation) for each one.",
        "",
        "## Summary Table",
        "",
        "| # | Bug ID | Title | Severity | Exception Type | Duplicate Status |",
        "|---|--------|-------|----------|-----------------|-------------------|",
    ]

    sections = []
    for i, bug in enumerate(DEMO_BUGS, start=1):
        bug_id, result = submit_and_diagnose(bug)
        outputs = result["agent_outputs"]
        triage = outputs.get("TriageAgent", {})
        log = outputs.get("LogAnalysisAgent", {})
        duplicates = outputs.get("DuplicateDetectionAgent", {})

        report_lines.append(
            f"| {i} | {bug_id} | {bug['title']} | {triage.get('severity')} | "
            f"{log.get('exception_type')} | {duplicates.get('duplicate_status')} |"
        )
        sections.append(render_bug_section(i, bug, bug_id, result))
        print(f"Processed bug {i}/{len(DEMO_BUGS)}: {bug['title']}")

    report_lines.append("")
    report_lines.extend(sections)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nReport written to: {OUTPUT_PATH}")
    print("This file is your Milestone 4 / M4.4 demonstration artifact.")