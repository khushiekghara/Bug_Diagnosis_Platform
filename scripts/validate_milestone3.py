"""
Milestone 3 -- Validation
Validates the Root Cause Agent (M3.1), Duplicate Detection Agent (M3.2),
and Remediation Agent (M3.3) against real historical bugs plus a
synthetic unrelated case.

Approach:
- Self-retrieval test: take a real historical bug's own text and query
  the pipeline with it. The agent should retrieve that same bug as its
  closest match (a "known duplicate" case), which is the strongest
  ground-truth check available without hand-labeling the whole dataset.
- Partial-text test: query with only part of a known bug's text (its
  title/first sentence). Should still rank as Duplicate or Related, since
  it's genuinely the same underlying issue with less context.
- Unrelated test: query with a synthetic bug about a completely different
  domain. Should be classified as New/Unmatched with low similarity.
- Full pipeline test: runs the whole orchestrator (5 agents) on one real
  bug and confirms Remediation produces at least one recommendation.

Run from the project root:
    python scripts/validate_milestone3.py

Requires kb/chroma_store to exist -- run the Milestone 1 kb/ pipeline
first if it doesn't.
"""
import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

CLEANED_CSV = os.path.join(PROJECT_ROOT, "kb", "data", "cleaned_historical_bugs.csv")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "kb", "chroma_store")


def _check_prereqs():
    if not os.path.exists(CHROMA_DIR):
        print(f"ERROR: {CHROMA_DIR} not found.")
        print("Run the kb/ pipeline first (clean_data.py, chunking.py, "
              "embeddings.py, build_vector_store.py) before validating Milestone 3.")
        sys.exit(1)
    if not os.path.exists(CLEANED_CSV):
        print(f"ERROR: {CLEANED_CSV} not found. Run kb/clean_data.py first.")
        sys.exit(1)


def _make_shared_context(bug_id, title, description):
    return {
        "bug_report": {
            "id": bug_id,
            "title": title,
            "description": description,
            "stack_trace": "",
            "error_log": "",
        },
        "triage": {"affected_component": "Unknown/General", "severity": "Medium"},
        "log_analysis": {"exception_type": None},
    }


def validate_duplicate_detection(sample_bugs):
    from agents.duplicate_detection_agent import DuplicateDetectionAgent

    print("=" * 78)
    print("PART 1 -- DUPLICATE DETECTION AGENT (M3.2)")
    print("=" * 78)

    agent = DuplicateDetectionAgent()
    results = {"self_retrieval": [], "partial_text": [], "unrelated": []}

    # --- Self-retrieval: full known bug text should match itself ---
    print("\n[Self-retrieval test -- known duplicate]")
    for bug in sample_bugs[:5]:
        ctx = _make_shared_context(bug["id"], bug["title"], bug["description"])
        result = agent.run(ctx)
        top_match_id = result["matches"][0]["bug_id"] if result["matches"] else None
        matched_self = str(top_match_id) == str(bug["id"])
        results["self_retrieval"].append(matched_self)
        print(f"  bug_id={bug['id']}: status={result['duplicate_status']}, "
              f"top_match={top_match_id}, matched_self={matched_self}")

    # --- Partial text: title only should still rank as duplicate/related ---
    print("\n[Partial-text test -- title only, should still match]")
    for bug in sample_bugs[:5]:
        ctx = _make_shared_context(bug["id"], bug["title"], "")
        result = agent.run(ctx)
        is_dup_or_related = result["duplicate_status"] in ("Likely Duplicate", "Related Issue")
        results["partial_text"].append(is_dup_or_related)
        print(f"  bug_id={bug['id']}: status={result['duplicate_status']}, "
              f"dup_or_related={is_dup_or_related}")

    # --- Unrelated synthetic bug ---
    print("\n[Unrelated test -- synthetic unrelated bug]")
    unrelated_ctx = _make_shared_context(
        "SYNTH1",
        "Cafeteria menu changed today",
        "The lunch menu in the office cafeteria switched from Italian to Mexican food this week.",
    )
    unrelated_result = agent.run(unrelated_ctx)
    is_unmatched = unrelated_result["duplicate_status"] == "New/Unmatched Issue"
    results["unrelated"].append(is_unmatched)
    print(f"  status={unrelated_result['duplicate_status']}, correctly_unmatched={is_unmatched}")
    if unrelated_result["matches"]:
        print(f"  closest distance found: {unrelated_result['matches'][0]['distance']}")

    self_rate = sum(results["self_retrieval"]) / len(results["self_retrieval"])
    partial_rate = sum(results["partial_text"]) / len(results["partial_text"])
    unrelated_rate = sum(results["unrelated"]) / len(results["unrelated"])

    print("\n" + "-" * 78)
    print(f"  Self-retrieval accuracy : {sum(results['self_retrieval'])}/{len(results['self_retrieval'])} = {self_rate:.0%}")
    print(f"  Partial-text match rate : {sum(results['partial_text'])}/{len(results['partial_text'])} = {partial_rate:.0%}")
    print(f"  Unrelated correctly flagged : {sum(results['unrelated'])}/{len(results['unrelated'])} = {unrelated_rate:.0%}")

    return {"self_retrieval": self_rate, "partial_text": partial_rate, "unrelated": unrelated_rate}


def validate_root_cause(sample_bugs):
    from agents.root_cause_agent import RootCauseAgent

    print("\n" + "=" * 78)
    print("PART 2 -- ROOT CAUSE AGENT (M3.1)")
    print("=" * 78)

    agent = RootCauseAgent()
    has_evidence_count = 0
    has_hypothesis_count = 0

    for bug in sample_bugs[:5]:
        ctx = _make_shared_context(bug["id"], bug["title"], bug["description"])
        result = agent.run(ctx)
        has_hypothesis = bool(result["root_cause_hypothesis"]) and "Insufficient" not in result["root_cause_hypothesis"] and "No sufficiently" not in result["root_cause_hypothesis"]
        has_evidence = len(result["supporting_evidence"]) > 0

        has_hypothesis_count += int(has_hypothesis)
        has_evidence_count += int(has_evidence)

        print(f"\n  bug_id={bug['id']}")
        print(f"    confidence: {result['confidence']}")
        print(f"    evidence_count: {len(result['supporting_evidence'])}")
        print(f"    hypothesis: {result['root_cause_hypothesis'][:150]}...")

    total = min(5, len(sample_bugs))
    print("\n" + "-" * 78)
    print(f"  Hypotheses generated : {has_hypothesis_count}/{total}")
    print(f"  Evidence retrieved   : {has_evidence_count}/{total}")

    print("\n[Unrelated test -- should show low confidence]")
    unrelated_ctx = _make_shared_context(
        "SYNTH1",
        "Cafeteria menu changed today",
        "The lunch menu in the office cafeteria switched from Italian to Mexican food this week.",
    )
    unrelated_result = agent.run(unrelated_ctx)
    print(f"  confidence: {unrelated_result['confidence']} (expected: low, <= 0.5)")

    return {"hypothesis_rate": has_hypothesis_count / total, "evidence_rate": has_evidence_count / total}


def validate_remediation(sample_bugs):
    from agents.orchestrator import AgentOrchestrator

    print("\n" + "=" * 78)
    print("PART 3 -- REMEDIATION AGENT (M3.3) + FULL PIPELINE")
    print("=" * 78)

    orchestrator = AgentOrchestrator()
    bug = sample_bugs[0]

    full_bug_report = {
        "id": bug["id"],
        "title": bug["title"],
        "description": bug["description"],
        "stack_trace": "",
        "error_log": "",
    }

    result = orchestrator.run(full_bug_report)
    remediation = result["agent_outputs"].get("RemediationAgent", {})

    print(f"\n  Ran full pipeline on bug_id={bug['id']}")
    print(f"  Agents run: {result['agents_run']}")
    print(f"  Recommendations generated: {len(remediation.get('recommendations', []))}")

    for rec in remediation.get("recommendations", []):
        print(f"    - [{rec['basis']}] confidence={rec['confidence']}: {rec['recommendation'][:120]}...")

    print(f"\n  Summary: {result['summary'][:300]}...")

    has_recommendations = len(remediation.get("recommendations", [])) > 0
    return {"has_recommendations": has_recommendations}


if __name__ == "__main__":
    _check_prereqs()

    import pandas as pd
    df = pd.read_csv(CLEANED_CSV, nrows=200)
    # Pick a handful of records with substantial description text, so the
    # self-retrieval test has real content to match against.
    df = df[df["description"].astype(str).str.len() > 80].head(6)
    sample_bugs = df.to_dict("records")

    if len(sample_bugs) < 2:
        print("Not enough usable records in the cleaned dataset to validate. Exiting.")
        sys.exit(1)

    dup_results = validate_duplicate_detection(sample_bugs)
    rc_results = validate_root_cause(sample_bugs)
    rem_results = validate_remediation(sample_bugs)

    print("\n" + "=" * 78)
    print("MILESTONE 3 VALIDATION COMPLETE")
    print("=" * 78)
    print("Duplicate Detection self-retrieval rate:", f"{dup_results['self_retrieval']:.0%}")
    print("Root Cause hypothesis generation rate:", f"{rc_results['hypothesis_rate']:.0%}")
    print("Remediation produced recommendations:", rem_results["has_recommendations"])
    print("\nNote: self-retrieval accuracy validates that the RAG pipeline")
    print("correctly finds a known bug's own record -- the strongest available")
    print("ground-truth check without a hand-labeled duplicate/root-cause dataset.")