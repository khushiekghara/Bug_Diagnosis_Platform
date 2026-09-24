# Intelligent Bug Diagnosis Platform with Fix Recommendation Assistance
 
Infosys Springboard Internship Project (Batch 3, 26-27)
Milestone 1: Foundation & Bug Understanding
Milestone 2: Triage and Log Analysis Agents
Milestone 3: Root Cause Analysis, Duplicate Detection, Remediation & Findings Display
 
## Overview
 
This project builds an AI-assisted platform that helps developers diagnose
software bugs faster. It combines a bug submission system with a
Retrieval-Augmented Generation (RAG) pipeline over a historical defect
knowledge base, and a five-agent pipeline that automatically classifies,
analyzes, and recommends fixes for each submitted bug.
 
See `docs/architecture.md` for the full system architecture, agent
responsibilities, data model, and tech stack.
 
## What is implemented in Milestone 1
 
- Bug Submission Module: a web form and API that accepts bug reports either
  by direct paste or by file upload (stack traces, error logs), validates
  them, and stores them in a database.
- Historical Defect Knowledge Base: a RAG pipeline that cleans a historical
  bug report dataset, chunks it, generates embeddings, indexes them in a
  vector database, and retrieves semantically similar historical bugs for
  a given query.
## What is implemented in Milestone 2
 
- Triage Agent: classifies a submitted bug by severity (Critical, High,
  Medium, Low), priority, and affected component, with a confidence score
  and human-readable reasoning.
- Log Analysis Agent: parses stack traces and error logs to identify the
  exception type, the failure point (file and line), and the affected code
  path, with structured output.
- Multi-Agent Orchestration: both agents run automatically when a bug is
  submitted, and their outputs are combined into a shared context object.
- Validation: scripts/validate_agents.py tests both agents against
  labeled bug reports covering different formats, and against the real
  seeded historical dataset.
## What is implemented in Milestone 3
 
- Root Cause Agent: uses RAG retrieval over the historical defect
  knowledge base to generate a root cause hypothesis for a submitted bug,
  with a confidence score and supporting evidence drawn from the closest
  matching historical defects. Evidence and reasoning are returned as
  separate fields so retrieved facts are never confused with the agent's
  own inference.
- Duplicate Detection Agent: performs semantic similarity search over the
  historical defect knowledge base (reusing the same embedding model and
  vector store as the Root Cause Agent) to classify a submitted bug as a
  Likely Duplicate, a Related Issue, or a New/Unmatched Issue, with
  similarity scores and summaries for each matching historical bug.
- Remediation Agent: generates fix recommendations grounded in the Root
  Cause Agent's hypothesis, the Duplicate Detection Agent's matches, and
  general best-practice guidance where historical evidence is not
  available. Every recommendation is labeled by basis (historical
  evidence, root cause analysis, or best-practice guideline) so
  speculative guidance is never presented as a confirmed fix.
- Structured Findings Display: the frontend's Diagnosis page shows all
  five agents' output together -- Triage, Log Analysis, Root Cause,
  Duplicate Detection, and Remediation -- in clearly separated sections,
  with an explicit "Insufficient Evidence" state when an agent cannot
  produce a reliable result.
- Validation: scripts/validate_milestone3.py tests the Root Cause and
  Duplicate Detection agents using self-retrieval (a known historical bug
  should match itself), partial-text matching, and a synthetic unrelated
  case, plus a full pipeline run to confirm Remediation produces
  recommendations.
## Project Structure
 
```
bug-diagnosis-platform/
  backend/                     Bug Submission Module and Agent Pipeline
    agents/
      triage_agent.py          Milestone 2: Triage Agent
      log_analysis_agent.py    Milestone 2: Log Analysis Agent
      retriever.py             Milestone 3: shared RAG retrieval utility
      root_cause_agent.py      Milestone 3: Root Cause Agent
      duplicate_detection_agent.py  Milestone 3: Duplicate Detection Agent
      remediation_agent.py     Milestone 3: Remediation Agent
      orchestrator.py          Runs all 5 agents in the correct order
    database.py                 Database connection setup
    models.py                   Bug report and diagnosis result schema
    schemas.py                  API request/response validation
    main.py                     FastAPI app and endpoints
  frontend/                     React (Vite) frontend
    src/
      components/               Layout, Sidebar, Topbar, BugTable, StatCard, StatusBadge
      context/                  ThemeContext.jsx
      pages/                    Dashboard, BugReports, BugDetails, Diagnosis, SubmitBug
      services/                 api.js - calls to the backend API
      utils/                    helpers.js
      App.jsx, main.jsx, index.css
    index.html
    package.json
    vite.config.js
  kb/                            Historical Defect Knowledge Base pipeline
    data/                        Datasets (not committed to git, see below)
    chroma_store/                 Vector database (not committed to git)
    clean_data.py
    chunking.py
    embeddings.py
    build_vector_store.py
  scripts/
    query_kb.py                  Tests semantic retrieval from the knowledge base
    validate_agents.py           Milestone 2: Triage/Log Analysis accuracy validation
    validate_milestone3.py       Milestone 3: Root Cause/Duplicate/Remediation validation
  docs/
    architecture.md               Architecture, agent design, data model, tech stack
```
 
## Dataset
 
The historical defect knowledge base is seeded using the DeepTriage bug
report dataset (Mozilla Bugzilla bug reports), sourced from Kaggle. Apache
and Eclipse sources are planned additions for a later milestone. See
docs/architecture.md for known limitations.
 
Because the raw dataset files and generated embeddings are large, they are
excluded from this repository via .gitignore. To reproduce the knowledge
base locally, download the dataset and place the files inside kb/data/,
then follow the setup steps below.
 
## Setup
 
### 1. Create a virtual environment and install dependencies
 
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
 
### 2. Run the Bug Submission Module and Agent Pipeline (backend)
 
```
cd backend
uvicorn main:app --reload
```
 
The API is available at http://localhost:8000, with interactive docs at
http://localhost:8000/docs.
 
When a bug is submitted, all five agents run automatically: Triage, Log
Analysis, Root Cause, Duplicate Detection, and Remediation.
 
Key endpoints:
- POST /bugs/paste - submit a bug report by pasting text
- POST /bugs/upload - submit a bug report by file upload
- GET /bugs - list all submitted bug reports
- GET /bugs/{id} - get one bug report
- GET /bugs/{id}/diagnosis - get the stored agent diagnosis for a bug
- POST /bugs/{id}/diagnose - re-run the full agent pipeline and return the full result
### 3. Run the frontend
 
```
cd frontend
npm install
npm run dev
```
 
This starts a local dev server (Vite prints the URL, typically
http://localhost:5173). Make sure the backend (step 2) is running first.
 
### 4. Build the Historical Defect Knowledge Base
 
Place your dataset CSV (e.g. fix.csv) inside kb/data/, then run each
step in order:
 
```
cd kb
python clean_data.py
python chunking.py
python embeddings.py
python build_vector_store.py
```
 
### 5. Test semantic retrieval
 
```
cd ..
python scripts/query_kb.py
```
 
### 6. Validate the agents
 
```
python scripts/validate_agents.py
python scripts/validate_milestone3.py
```
 
The first validates Triage and Log Analysis accuracy on labeled test
cases; the second validates Root Cause, Duplicate Detection, and
Remediation using self-retrieval and a synthetic unrelated case.
 
## Tech Stack
 
- Backend / API: FastAPI (Python)
- Database: SQLite (development), PostgreSQL planned
- Frontend: React (Vite)
- Agent Layer: five agents (Triage, Log Analysis, Root Cause, Duplicate
  Detection, Remediation), rule-based and RAG-based, coordinated by an
  Agent Orchestrator -- no external LLM/API required
- Chunking: LangChain text splitters
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- Vector Store: ChromaDB
- Historical Dataset: Mozilla Bugzilla bug reports (Kaggle DeepTriage dataset)
Full details are in docs/architecture.md.

## Author
 
Khushi
Infosys Springboard Internship, Batch 3 (26-27)

 
