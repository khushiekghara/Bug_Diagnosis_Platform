# Intelligent Bug Diagnosis Platform with Fix Recommendation Assistance

Infosys Springboard Internship Project (Batch 3, 26-27)
Milestone 1: Foundation & Bug Understanding

## Overview

This project builds an AI-assisted platform that helps developers diagnose
software bugs faster by combining a bug submission system with a
Retrieval-Augmented Generation (RAG) pipeline over a historical defect
knowledge base. Given a new bug report, the system retrieves semantically
similar historical bugs and their resolutions to assist diagnosis and fix
recommendation.

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
- System architecture and agent design (Triage, Log Analysis, Root Cause,
  Duplicate Detection, Remediation agents) documented in `docs/architecture.md`.
  Agent implementation itself is planned for Milestone 2.

## Project Structure

bug-diagnosis-platform/
backend/ Bug Submission Module (FastAPI + SQLite)
frontend/ Simple HTML submission form
kb/ Historical Defect Knowledge Base pipeline
data/ Datasets (not committed to git, see below)
chroma_store/ Vector database (not committed to git)
scripts/ Standalone test/utility scripts
docs/ Architecture and design documentation


## Dataset

The historical defect knowledge base is seeded using the DeepTriage bug
report dataset (Mozilla Bugzilla bug reports), sourced from Kaggle. Apache
and Eclipse sources are planned additions for a later milestone. See
`docs/architecture.md` section 8 for known limitations.

Because the raw dataset files and generated embeddings are large, they are
excluded from this repository via `.gitignore`. To reproduce the knowledge
base locally, download the dataset and place the files inside `kb/data/`,
then follow the setup steps below.

## Setup

### 1. Create a virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

### 2. Run the Bug Submission Module (backend)
cd backend
uvicorn main:app --reload

The API will be available at `http://localhost:8000`, with interactive
docs at `http://localhost:8000/docs`.

Open `frontend/index.html` in a browser to use the submission form.

### 3. Build the Historical Defect Knowledge Base

Place your dataset CSV (e.g. `fix.csv`) inside `kb/data/`, then run each
step in order:
Your .gitignore file looks correct — good content, saved properly as .gitignore. Now let's run the actual git commands.

Run these one at a time in the terminal (make sure you're in the project root, not kb/)
bash
cd C:\Users\kriti\OneDrive\Desktop\bug-diagnosis-platform
rm -r -force .git

Then:

bash
git init
git add .
git status

Paste me the full output of git status before you commit anything. I need to see the list of files it's about to track — specifically confirm it does NOT include:

kb/data/fix.csv, sev.csv, fix_train.csv, sev_train.csv, etc.
kb/data/bug_chunks_embedded.jsonl, bug_chunks.jsonl
kb/data/corpus_fixsev.txt, embedding.npy, vocab.lst
kb/chroma_store/...
backend/bug_reports.db

If git status shows those files staged anyway, it usually means one of two things:

You're running git status from inside kb/ instead of the project root (paths in .gitignore are relative to root)
There's a stray __pycache__ still floating around

Run it and paste the output — once it's clean, we commit and push in one go.

(.venv) PS C:\Users\kriti\OneDrive\Desktop\bug-diagnosis-platform> git init
Initialized empty Git repository in C:/Users/kriti/OneDrive/Desktop/bug-diagnosis-platform/.git/
(.venv) PS C:\Users\kriti\OneDrive\Desktop\bug-diagnosis-platform> git add .
(.venv) PS C:\Users\kriti\OneDrive\Desktop\bug-diagnosis-platform> git status
On branch master
No commits yet
Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   README.md
        new file:   backend/database.py
        new file:   backend/main.py
        new file:   backend/models.py
        new file:   backend/schemas.py
        new file:   docs/architecture.md
        new file:   frontend/index.html
        new file:   kb/build_vector_store.py
        new file:   kb/chunking.py
        new file:   kb/clean_data.py
        new file:   kb/data_historical_bugs.csv
        new file:   kb/embeddings.py
        new file:   kb/inspect_dataset.py
        new file:   requirements.txt
        new file:   scripts/query_kb.py
(.venv) PS C:\Users\kriti\OneDrive\Desktop\bug-diagnosis-platform>

Checking gitignore rules against a stray tracked file.

This is clean — no large data files, no chroma_store, no .db file. Only code and docs. The one small thing: kb/data_historical_bugs.csv is being tracked — that's the leftover empty, unused file sitting directly in kb/ (not kb/data/, so your .gitignore rule didn't catch it since it's a different path). It's harmless size-wise (it's empty), but let's remove it since it's dead weight we don't use anymore:

bash
git rm --cached kb/data_historical_bugs.csv
del kb\data_historical_bugs.csv

Now commit and push:

bash
git commit -m "Milestone 1: Bug Submission Module + Historical Defect KB with RAG"
git remote add origin https://github.com/khushiekghara/Bug_Diagnosis_Platform.git
git branch -M main
git push -u origin main

This should go through cleanly and fast this time — it's just code (no 60MB+ datasets). Paste the output once it's done, and if it succeeds, Milestone 1 is fully submittable: repo link + docs/architecture.md + the tech stack table.

plzz create readme file don't use so many emoji's

Here's the complete README.md — copy this into your file (replace whatever's there):

markdown
# Intelligent Bug Diagnosis Platform with Fix Recommendation Assistance

Infosys Springboard Internship Project (Batch 3, 26-27)
Milestone 1: Foundation & Bug Understanding

## Overview

This project builds an AI-assisted platform that helps developers diagnose
software bugs faster by combining a bug submission system with a
Retrieval-Augmented Generation (RAG) pipeline over a historical defect
knowledge base. Given a new bug report, the system retrieves semantically
similar historical bugs and their resolutions to assist diagnosis and fix
recommendation.

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
- System architecture and agent design (Triage, Log Analysis, Root Cause,
  Duplicate Detection, Remediation agents) documented in `docs/architecture.md`.
  Agent implementation itself is planned for Milestone 2.

## Project Structure

bug-diagnosis-platform/
backend/ Bug Submission Module (FastAPI + SQLite)
frontend/ Simple HTML submission form
kb/ Historical Defect Knowledge Base pipeline
data/ Datasets (not committed to git, see below)
chroma_store/ Vector database (not committed to git)
scripts/ Standalone test/utility scripts
docs/ Architecture and design documentation


## Dataset

The historical defect knowledge base is seeded using the DeepTriage bug
report dataset (Mozilla Bugzilla bug reports), sourced from Kaggle. Apache
and Eclipse sources are planned additions for a later milestone. See
`docs/architecture.md` section 8 for known limitations.

Because the raw dataset files and generated embeddings are large, they are
excluded from this repository via `.gitignore`. To reproduce the knowledge
base locally, download the dataset and place the files inside `kb/data/`,
then follow the setup steps below.

## Setup

### 1. Create a virtual environment and install dependencies

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt


### 2. Run the Bug Submission Module (backend)

cd backend
uvicorn main:app --reload


The API will be available at `http://localhost:8000`, with interactive
docs at `http://localhost:8000/docs`.

Open `frontend/index.html` in a browser to use the submission form.

### 3. Build the Historical Defect Knowledge Base

Place your dataset CSV (e.g. `fix.csv`) inside `kb/data/`, then run each
step in order:

cd kb
python clean_data.py
python chunking.py
python embeddings.py
python build_vector_store.py

### 4. Test semantic retrieval
cd ..
python scripts/query_kb.py

This runs a sample query against the vector store and prints the top
matching historical bugs, confirming the RAG pipeline works end to end.

## Tech Stack

- Backend / API: FastAPI (Python)
- Database: SQLite (development), PostgreSQL planned
- Frontend: HTML/JavaScript (Milestone 1), React planned
- Chunking: LangChain text splitters
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- Vector Store: ChromaDB
- Historical Dataset: Mozilla Bugzilla bug reports (Kaggle DeepTriage dataset)

Full details are in `docs/architecture.md`.

## Author

Khushi
Infosys Springboard Internship, Batch 3 (26-27)
