# Intelligent Bug Diagnosis Platform with Fix Recommendation Assistance

## Project Report

**Infosys Springboard Internship — Batch 3 (26-27)**
**Author:** Khushi
**Mentor:** springboardmentor556
**Repository:** https://github.com/khushiekghara/Bug_Diagnosis_Platform
**Report covers:** Milestones 1-4

---

## 1. Problem Statement

Developers spend a significant amount of time manually triaging and diagnosing
bug reports, often re-solving problems that are functionally identical to bugs
resolved before. This project builds an AI-assisted platform that shortens
that process: a developer submits a bug report, and the system automatically
classifies it, analyzes its technical details, retrieves similar historical
defects, identifies a probable root cause, flags duplicates, and recommends a
fix — all grounded in real historical data rather than guesswork.

## 2. Solution Overview

The platform combines three building blocks:

1. **A Bug Submission system** — a web form and API for reporting bugs
   (paste or file upload).
2. **A Retrieval-Augmented Generation (RAG) pipeline** over a historical
   defect knowledge base, built from a real public dataset of Mozilla
   Bugzilla bug reports.
3. **A five-agent diagnosis pipeline** that runs automatically on every
   submission, using rule-based reasoning and the RAG pipeline — no external
   LLM or paid API required.

The platform also **learns over time**: when a bug's fix is confirmed, it is
added back into the knowledge base, so future similar bugs can be matched
against real, confirmed fixes instead of just historical (unverified) data.

## 3. System Architecture
[Bug Submission UI] --> [Backend / API Layer] --> [Bug Report Processing]
|
v
[Bug Report Database]

[Historical Defect Knowledge Base]
Data Cleaning & Chunking Pipeline
--> Embedding Generation Module
--> Vector Database (ChromaDB)
--> RAG Retrieval Pipeline <---------------------+
| |
v |
[Agent Orchestrator] |
Stage 1: Triage Agent, Log Analysis Agent |
Stage 2: Root Cause Agent, Duplicate Detection Agent, |
Remediation Agent |
| |
v |
[Structured Findings / Diagnosis Module] --> stored in DB |
| |
v |
[Results & Recommendations Interface] (React frontend) |
| |
"Mark Resolved" (confirmed fix) |
| |
v |
[Knowledge Base Update Module] ------------------------------+
(chunks + embeds the resolved bug, writes it back
into the same vector store)

[Defect Pattern Analytics Module]
Aggregates across all diagnosed bugs: component frequency,
severity distribution, recurring exception types, systemic
(component, exception) patterns, recurring keyword themes.


## 4. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend / API | FastAPI (Python) | Async, fast, integrates naturally with the RAG/agent pipeline |
| Database | SQLite (dev), PostgreSQL planned | Simple to start, clear migration path |
| Frontend | React (Vite) | Component-based dashboard, bug list, diagnosis, analytics pages |
| Chunking | LangChain Text Splitters | Standard recursive chunking, reused for both historical and platform-grown data |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Free, local, no API key, fast on CPU |
| Vector Store | ChromaDB | Lightweight, embedded, no separate server |
| Historical Dataset | Mozilla Bugzilla bug reports (Kaggle DeepTriage dataset) | Real, large-scale, public bug report corpus |
| Agent Layer | 5 custom agents (rule-based + RAG), Python | No external LLM/API cost; fully explainable |

## 5. Agent Design

| Agent | Milestone | Input | Technique | Output |
|---|---|---|---|---|
| **Triage Agent** | M2 | Bug title/description/trace | Keyword matching | Severity, priority, affected component, confidence, reasoning |
| **Log Analysis Agent** | M2 | Stack trace / error log | Regex pattern matching | Exception type, failure point, affected code path |
| **Root Cause Agent** | M3 | Bug text + Triage/Log output | RAG retrieval over knowledge base | Root cause hypothesis, confidence, supporting evidence |
| **Duplicate Detection Agent** | M3 | Bug text | Semantic similarity search (same embedding model/store) | Duplicate status, matching bugs, similarity scores |
| **Remediation Agent** | M3 | Root Cause + Duplicate Detection + Triage output | Resolution-text extraction + rule-based synthesis | Fix recommendations, each labeled by evidence basis |

All five agents are coordinated by an **Agent Orchestrator**, which runs
Stage 1 (Triage, Log Analysis) first, then Stage 2 (Root Cause, Duplicate
Detection, Remediation) in order — each Stage 2 agent's output is folded
into a shared context so Remediation can use Root Cause's and Duplicate
Detection's findings.

## 6. Milestone-by-Milestone Summary

### Milestone 1 — Foundation & Bug Understanding
- Researched defect analysis workflows, RAG architecture, semantic similarity, and bug report structures.
- Designed the system architecture and data model.
- Built the Bug Submission Module (paste + file upload, validation, storage).
- Built the Historical Defect Knowledge Base: cleaned a real Mozilla Bugzilla dataset, chunked it, generated embeddings, and indexed it in ChromaDB. Verified semantic retrieval works end to end.

### Milestone 2 — Triage and Log Analysis Agents
- Built the Triage Agent (severity/priority/component classification with confidence and reasoning).
- Built the Log Analysis Agent (exception type, failure point, affected code path extraction).
- Implemented multi-agent orchestration: both agents run automatically on submission.
- Validated both agents against a labeled, format-varied test suite and against the real seeded dataset.

### Milestone 3 — Root Cause Analysis, Duplicate Detection, Remediation & Findings Display
- Built the Root Cause Agent: RAG-grounded hypothesis generation with separate evidence/reasoning fields.
- Built the Duplicate Detection Agent: semantic similarity search classifying bugs as Likely Duplicate / Related Issue / New.
- Built the Remediation Agent: fix recommendations labeled by evidence basis, never presenting speculation as a confirmed fix.
- Built the Structured Findings Display (frontend Diagnosis page) showing all 5 agents' output in clearly separated sections, with an explicit "Insufficient Evidence" state.
- Validated all three new agents using self-retrieval (a known bug correctly matches itself), partial-text matching, and a synthetic unrelated case.

### Milestone 4 — Pattern Analytics, Knowledge Base Growth, End-to-End Testing & Documentation
- Built the Defect Pattern Analytics Module: aggregates component frequency, severity distribution, recurring exception types, systemic (component, exception) patterns, and recurring keyword themes across every submitted bug.
- Implemented the Knowledge Base growth mechanism: a confirmed fix (via "Mark Resolved") is chunked and embedded the same way as the original dataset and written back into the same ChromaDB collection, with safeguards so a bug never matches itself and re-resolving a bug replaces (not duplicates) its chunks.
- Verified the Remediation Agent correctly prioritizes a `confirmed_fix` (from a resolved platform bug) above text-mined historical evidence, root-cause-based reasoning, and generic best practices.
- Conducted end-to-end testing across five distinct bug formats (Python, Java, JavaScript, log-file style, plain text), confirming all 5 agents produce output for every format, and validating duplicate detection and recommendation relevance.
- Generated a final demonstration report (`docs/demo_report.md`) with five distinct bug submissions and their complete agent pipeline output.

## 7. Data Model (Key Tables)

**BugReport**

id, title, description, stack_trace, error_log, source_type,
original_filename, status, created_at,
resolution_text, resolved_at, kb_chunks_added (added in Milestone 4)


**DiagnosisResult**

id, bug_id,
severity, priority, affected_component, confidence, triage_reasoning,
exception_type, failure_point, affected_code_path, log_reasoning,
root_cause_hypothesis, root_cause_confidence, root_cause_evidence_json, root_cause_reasoning,
duplicate_status, duplicate_matches_json, duplicate_reasoning,
remediation_recommendations_json, remediation_confidence, remediation_reasoning,
summary, agent_outputs_json, analyzed_at


## 8. API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/bugs/paste` | POST | Submit a bug report by pasting text (runs full pipeline) |
| `/bugs/upload` | POST | Submit a bug report by file upload (runs full pipeline) |
| `/bugs` | GET | List all submitted bugs |
| `/bugs/{id}` | GET | Get one bug report |
| `/bugs/{id}/diagnosis` | GET | Get the stored diagnosis for a bug |
| `/bugs/{id}/diagnose` | POST | Re-run the full agent pipeline, return raw output |
| `/bugs/{id}/resolve` | POST | Record a confirmed fix; adds the bug to the knowledge base |
| `/analytics/patterns` | GET | Defect pattern analytics report |
| `/knowledge-base/stats` | GET | Knowledge base size (historical vs platform-added) |

## 9. Validation Summary

| Validation | Script | Result |
|---|---|---|
| Triage/Log Analysis accuracy | `scripts/validate_agents.py` | Labeled test suite + real-dataset coverage test |
| Root Cause / Duplicate Detection / Remediation | `scripts/validate_milestone3.py` | 100% self-retrieval accuracy; confidence correctly scales with match quality |
| End-to-end across formats, knowledge base growth, analytics | `scripts/validate_milestone4.py` | All 5 agents produce output across 5 distinct bug formats |
| Final demonstration | `scripts/generate_demo_report.py` | 5 distinct bugs with complete pipeline output, written to `docs/demo_report.md` |

## 10. Known Limitations

- The historical knowledge base is currently seeded with **Mozilla** bug
  reports only; Apache and Eclipse sources were planned but not included due
  to dataset availability constraints.
- Agents use rule-based keyword matching and RAG retrieval rather than an
  LLM; this keeps the system fast, free, and fully explainable, at the cost
  of reasoning depth an LLM could provide.
- The Remediation Agent's `historical_evidence` recommendation (text-mined
  resolution language) is not currently gated by match closeness the same
  way `confirmed_fix` is — a refinement planned for a future milestone.
- The platform-added knowledge base entries are stored alongside the
  original historical dataset in the same ChromaDB collection; a production
  system would likely separate these for easier auditing.

## 11. Planned Future Work

- Introduce an LLM for deeper reasoning on top of the existing RAG
  foundation, improving hypothesis and recommendation quality.
- Expand the historical dataset with Apache and Eclipse bug reports.
- Gate `historical_evidence` recommendations by match closeness, matching
  the `confirmed_fix` logic.
- Add authentication and multi-user support for team usage.

## 12. How to Reproduce

See `README.md` in the repository root for full setup instructions
(environment setup, running the backend/frontend, building the knowledge
base, and running every validation script).