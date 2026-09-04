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
