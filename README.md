# Intelligent Bug Diagnosis Platform with Fix Recommendation Assistance
 
Infosys Springboard Internship Project (Batch 3, 26-27)
Milestone 1: Foundation & Bug Understanding
Milestone 2: Triage and Log Analysis Agents
 
## Overview
 
This project builds an AI-assisted platform that helps developers diagnose
software bugs faster. It combines a bug submission system with a
Retrieval-Augmented Generation (RAG) pipeline over a historical defect
knowledge base, and a multi-agent pipeline that automatically classifies
and analyzes each submitted bug.
 
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
- System architecture and agent design documented in `docs/architecture.md`.
## What is implemented in Milestone 2
 
- Triage Agent: classifies a submitted bug by severity (Critical, High,
  Medium, Low), priority, and affected component, with a confidence score
  and human-readable reasoning. Rule-based keyword matching, no external
  API required.
- Log Analysis Agent: parses stack traces and error logs to identify the
  exception type, the failure point (file and line), and the affected code
  path, with structured output. Works across Python, Java, and JavaScript
  style traces.
- Multi-Agent Orchestration: both agents run automatically when a bug is
  submitted. Their outputs are combined into a single shared context object,
  stored in the database, and returned to the client. The orchestrator is
  built to accept additional downstream agents (Root Cause, Duplicate
  Detection, Remediation) in a later milestone.
- Validation: a dedicated script tests both agents against a hand-labeled
  set of bug reports covering different formats (Python traceback, Java
  stack trace, JavaScript error, plain text with no trace, log-file style
  output), and separately runs the full pipeline across a sample of the
  real seeded historical dataset to confirm it handles real-world, messy
  text without failing.
## Project Structure
 
```
bug-diagnosis-platform/
  backend/                     Bug Submission Module and Agent Pipeline
    agents/
      triage_agent.py          Milestone 2: Triage Agent
      log_analysis_agent.py    Milestone 2: Log Analysis Agent
      orchestrator.py          Milestone 2: Multi-agent orchestration
    database.py                 Database connection setup
    models.py                   Bug report and diagnosis result schema
    schemas.py                  API request/response validation
    main.py                     FastAPI app and endpoints
  frontend/
    index.html                  Bug submission form
  kb/                            Historical Defect Knowledge Base pipeline
    data/                        Datasets (not committed to git, see below)
    chroma_store/                 Vector database (not committed to git)
    clean_data.py
    chunking.py
    embeddings.py
    build_vector_store.py
  scripts/
    query_kb.py                  Tests semantic retrieval from the knowledge base
    validate_agents.py           Milestone 2: agent accuracy and coverage validation
  docs/
    architecture.md               Architecture, agent design, data model, tech stack
```
 
## Dataset
 
The historical defect knowledge base is seeded using the DeepTriage bug
report dataset (Mozilla Bugzilla bug reports), sourced from Kaggle. Apache
and Eclipse sources are planned additions for a later milestone. See
`docs/architecture.md` for known limitations.
 
Because the raw dataset files and generated embeddings are large, they are
excluded from this repository via `.gitignore`. To reproduce the knowledge
base locally, download the dataset and place the files inside `kb/data/`,
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
 
The API is available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.
 
Open `frontend/index.html` in a browser to use the submission form. When a
bug is submitted, the Triage Agent and Log Analysis Agent run automatically.
 
Key endpoints:
- `POST /bugs/paste` - submit a bug report by pasting text
- `POST /bugs/upload` - submit a bug report by file upload
- `GET /bugs` - list all submitted bug reports
- `GET /bugs/{id}` - get one bug report
- `GET /bugs/{id}/diagnosis` - get the stored agent diagnosis for a bug
- `POST /bugs/{id}/diagnose` - re-run the agent pipeline and return the full result
### 3. Build the Historical Defect Knowledge Base
 
Place your dataset CSV (e.g. `fix.csv`) inside `kb/data/`, then run each
step in order:
 
```
cd kb
python clean_data.py
python chunking.py
python embeddings.py
python build_vector_store.py
```
 
### 4. Test semantic retrieval
 
```
cd ..
python scripts/query_kb.py
```
 
This runs a sample query against the vector store and prints the top
matching historical bugs, confirming the RAG pipeline works end to end.
 
### 5. Validate the Triage and Log Analysis Agents
 
```
python scripts/validate_agents.py
```
 
This prints accuracy on a labeled test suite (varied bug report formats)
and a coverage report on a sample of the real seeded dataset.
 
## Tech Stack
 
- Backend / API: FastAPI (Python)
- Database: SQLite (development), PostgreSQL planned
- Frontend: HTML/JavaScript (Milestone 1), React planned
- Agent Layer: rule-based Triage Agent and Log Analysis Agent (Python,
  keyword matching and regex), Agent Orchestrator
- Chunking: LangChain text splitters
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- Vector Store: ChromaDB
- Historical Dataset: Mozilla Bugzilla bug reports (Kaggle DeepTriage dataset)
Full details are in `docs/architecture.md`.
 
## Planned for Milestone 3
 
- Root Cause Agent, Duplicate Detection Agent, and Remediation Agent
- LLM-based reasoning over retrieved historical context
- Results and recommendations interface
- Expanding the historical dataset to include Apache and Eclipse sources
## Author
 
Khushi
Infosys Springboard Internship, Batch 3 (26-27)

 
