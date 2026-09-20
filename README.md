Intelligent Bug Diagnosis Platform with Fix Recommendation Assistance

Infosys Springboard Internship Project (Batch 3, 26-27) Milestone 1: Foundation & Bug Understanding

Overview

This project builds an AI-assisted platform that helps developers diagnose software bugs faster by combining a bug submission system with a Retrieval-Augmented Generation (RAG) pipeline over a historical defect knowledge base. Given a new bug report, the system retrieves semantically similar historical bugs and their resolutions to assist diagnosis and fix recommendation.

See docs/architecture.md for the full system architecture, agent responsibilities, data model, and tech stack.

What is implemented in Milestone 1
Bug Submission Module: a web form and API that accepts bug reports either by direct paste or by file upload (stack traces, error logs), validates them, and stores them in a database.
Historical Defect Knowledge Base: a RAG pipeline that cleans a historical bug report dataset, chunks it, generates embeddings, indexes them in a vector database, and retrieves semantically similar historical bugs for a given query.
System architecture and agent design (Triage, Log Analysis, Root Cause, Duplicate Detection, Remediation agents) documented in docs/architecture.md. Agent implementation itself is planned for Milestone 2.
Project Structure
bug-diagnosis-platform/
  backend/            Bug Submission Module (FastAPI + SQLite)
  frontend/           Simple HTML submission form
  kb/                 Historical Defect Knowledge Base pipeline
    data/             Datasets (not committed to git, see below)
    chroma_store/     Vector database (not committed to git)
  scripts/            Standalone test/utility scripts
  docs/               Architecture and design documentation
Dataset

The historical defect knowledge base is seeded using the DeepTriage bug report dataset (Mozilla Bugzilla bug reports), sourced from Kaggle. Apache and Eclipse sources are planned additions for a later milestone. See docs/architecture.md section 8 for known limitations.

Because the raw dataset files and generated embeddings are large, they are excluded from this repository via .gitignore. To reproduce the knowledge base locally, download the dataset and place the files inside kb/data/, then follow the setup steps below.

Setup
1. Create a virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
2. Run the Bug Submission Module (backend)
cd backend
uvicorn main:app --reload

The API will be available at http://localhost:8000, with interactive docs at http://localhost:8000/docs.

Open frontend/index.html in a browser to use the submission form.

3. Build the Historical Defect Knowledge Base

Place your dataset CSV (e.g. fix.csv) inside kb/data/, then run each step in order:

cd kb
python clean_data.py
python chunking.py
python embeddings.py
python build_vector_store.py
4. Test semantic retrieval
cd ..
python scripts/query_kb.py

This runs a sample query against the vector store and prints the top matching historical bugs, confirming the RAG pipeline works end to end.

Tech Stack
Backend / API: FastAPI (Python)
Database: SQLite (development), PostgreSQL planned
Frontend: HTML/JavaScript (Milestone 1), React planned
Chunking: LangChain text splitters
Embeddings: sentence-transformers (all-MiniLM-L6-v2)
Vector Store: ChromaDB
Historical Dataset: Mozilla Bugzilla bug reports (Kaggle DeepTriage dataset)

Full details are in docs/architecture.md.

Author

Khushi Infosys Springboard Internship, Batch 3 (26-27)
