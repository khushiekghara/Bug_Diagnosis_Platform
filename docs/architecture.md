# Intelligent Bug Diagnosis Platform — System Architecture (Milestone 1)

## 1. Overview

This document describes the system architecture, agent responsibilities,
orchestration flow, and data model for the Intelligent Bug Diagnosis
Platform with Fix Recommendation Assistance.

## 2. High-Level Component Diagram
[Bug Submission UI] --> [Backend / API Layer] --> [Bug Report Processing]
|
v
[Bug Report Database]

[Historical Defect Knowledge Base]
Data Cleaning & Chunking Pipeline
--> Embedding Generation Module
--> Vector Database (ChromaDB)
--> RAG Retrieval Pipeline
|
v
[Agent Orchestrator] --> Triage Agent
--> Log Analysis Agent
--> Root Cause Agent
--> Duplicate Detection Agent
--> Remediation Agent
|
v
[Structured Findings / Diagnosis Module]
|
v
[Results & Recommendations Interface]
|
v
[Knowledge Base Update Module] --> feeds back into Historical Defect KB


## 3. Agent Responsibilities

| Agent | Input | Responsibility | Output |
|---|---|---|---|
| **Triage Agent** | New bug report | Classifies bug type/severity, routes to the right downstream agent | Triage category, priority label |
| **Log Analysis Agent** | Stack trace / error log | Parses logs, extracts error signatures and stack frames | Structured log summary |
| **Root Cause Agent** | Bug report + retrieved similar historical bugs | Uses RAG context to reason about likely root cause | Root cause hypothesis |
| **Duplicate Detection Agent** | New bug report + vector search results | Checks semantic similarity against historical/open bugs to flag duplicates | Duplicate match (if any) + confidence score |
| **Remediation Agent** | Root cause hypothesis + historical resolutions | Suggests a fix based on how similar historical bugs were resolved | Recommended fix / next steps |

## 4. Orchestration Flow

1. User submits a bug report (paste or file upload) via the Bug Submission Module.
2. Backend validates and stores the report in the Bug Report Database.
3. The Agent Orchestrator is triggered and calls the **Triage Agent** first.
4. In parallel/sequence, the **Log Analysis Agent** parses any stack trace/log content.
5. The **RAG Retrieval Pipeline** queries the Vector Database for semantically similar historical bugs.
6. The **Duplicate Detection Agent** and **Root Cause Agent** both consume this retrieved context.
7. The **Remediation Agent** produces a final fix recommendation using retrieved historical resolutions.
8. All agent outputs are merged into the Structured Findings / Diagnosis Module.
9. Results are displayed via the Results & Recommendations Interface.
10. Confirmed diagnoses can be pushed back into the Historical Defect Knowledge Base via the Knowledge Base Update Module (future milestone).

## 5. Data Model

### Bug Report (submitted by user)
```json
{
  "id": "integer",
  "title": "string",
  "description": "text",
  "stack_trace": "text (nullable)",
  "error_log": "text (nullable)",
  "source_type": "paste | file",
  "original_filename": "string (nullable)",
  "status": "string",
  "created_at": "datetime"
}
```

### Historical Defect (from knowledge base)
```json
{
  "id": "string/integer",
  "source_repo": "string (e.g. mozilla, apache, eclipse)",
  "title": "string",
  "description": "text",
  "stack_trace": "text (nullable)",
  "resolution": "text (nullable)",
  "severity": "string",
  "status": "string"
}
```

### Bug Chunk (post-chunking, used for embedding/retrieval)
```json
{
  "chunk_id": "string",
  "bug_id": "string/integer",
  "source_repo": "string",
  "severity": "string",
  "status": "string",
  "text": "string (chunked content)",
  "embedding": "vector[384]"
}
```

## 6. Data Flow Summary

Bug Submission --> Processing/Validation --> Storage
|
Historical Data (Kaggle) --> Cleaning --> Chunking --> Embedding --> Vector Index
|
Query-time similarity search
|
Agent Pipeline --> Results UI


## 7. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend / API | FastAPI (Python) | Async, fast, pairs naturally with the RAG/ML pipeline |
| Bug Report DB | SQLite (dev) → PostgreSQL (planned) | Simple to start, easy migration path |
| Frontend | HTML/JS (M1) → React (planned) | Fast to build for M1 submission deadline |
| Chunking | LangChain Text Splitters | Standard, well-tested recursive chunking |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Free, local, no API key required, fast on CPU |
| Vector Store | ChromaDB | Lightweight, embedded, no separate server needed |
| Historical Dataset | Mozilla Bugzilla bug reports (Kaggle: DeepTriage dataset) | Real, large-scale, publicly available bug report corpus |
| Agent Layer | Planned: LangChain/custom orchestrator + LLM (model TBD) | To be implemented in Milestone 2 |

## 8. Known Limitations (to address in later milestones)

- Historical Defect Knowledge Base is currently seeded with **Mozilla** bug reports only (from the DeepTriage Kaggle dataset). Apache and Eclipse sources are planned additions for a future milestone.
- Agent Layer (Triage, Log Analysis, Root Cause, Duplicate Detection, Remediation) is architecturally defined here but not yet implemented — this is the primary scope for Milestone 2.
- Currently using a representative sample (3,000 records / ~18,400 chunks) of the full historical dataset for faster iteration; full-dataset indexing can be run later by removing the row cap in `clean_data.py`.