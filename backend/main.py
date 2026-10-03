import json
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from typing import Optional, List

import models
import schemas
import analytics
from database import engine, get_db
from agents.orchestrator import AgentOrchestrator
from agents.retriever import get_retriever

# Create tables on startup
models.Base.metadata.create_all(bind=engine)


def _ensure_milestone4_columns():
    """
    Lightweight migration: Milestone 4 added three columns to bug_reports.
    create_all() does not alter tables that already exist, so add any
    missing columns here. This keeps existing submitted bugs, so the
    database file does not have to be deleted after upgrading.
    """
    existing = {col["name"] for col in inspect(engine).get_columns("bug_reports")}
    needed = {
        "resolution_text": "TEXT",
        "resolved_at": "DATETIME",
        "kb_chunks_added": "INTEGER",
    }
    with engine.begin() as conn:
        for name, ddl in needed.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE bug_reports ADD COLUMN {name} {ddl}"))


_ensure_milestone4_columns()

app = FastAPI(title="Bug Diagnosis Platform -- Submission + Agent Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".txt", ".log", ".json", ".csv"}
MAX_FILE_SIZE_MB = 5

orchestrator = AgentOrchestrator()


def _bug_to_dict(bug: models.BugReport) -> dict:
    return {
        "id": bug.id,
        "title": bug.title,
        "description": bug.description,
        "stack_trace": bug.stack_trace,
        "error_log": bug.error_log,
    }


def _run_and_store_diagnosis(bug: models.BugReport, db: Session) -> dict:
    """Runs the full agent pipeline (Milestone 2 + Milestone 3) on a bug
    and persists every agent's result."""
    result = orchestrator.run(_bug_to_dict(bug))
    outputs = result["agent_outputs"]

    triage = outputs.get("TriageAgent", {})
    log = outputs.get("LogAnalysisAgent", {})
    root_cause = outputs.get("RootCauseAgent", {})
    duplicates = outputs.get("DuplicateDetectionAgent", {})
    remediation = outputs.get("RemediationAgent", {})

    diagnosis = models.DiagnosisResult(
        bug_id=bug.id,

        severity=triage.get("severity"),
        priority=triage.get("priority"),
        affected_component=triage.get("affected_component"),
        confidence=triage.get("confidence"),
        triage_reasoning=triage.get("reasoning"),

        exception_type=log.get("exception_type"),
        failure_point=log.get("failure_point"),
        affected_code_path=", ".join(log.get("affected_code_path", []) or []),
        log_reasoning=log.get("reasoning"),

        root_cause_hypothesis=root_cause.get("root_cause_hypothesis"),
        root_cause_confidence=root_cause.get("confidence"),
        root_cause_evidence_json=json.dumps(root_cause.get("supporting_evidence", [])),
        root_cause_reasoning=root_cause.get("reasoning"),

        duplicate_status=duplicates.get("duplicate_status"),
        duplicate_matches_json=json.dumps(duplicates.get("matches", [])),
        duplicate_reasoning=duplicates.get("reasoning"),

        remediation_recommendations_json=json.dumps(remediation.get("recommendations", [])),
        remediation_confidence=remediation.get("confidence"),
        remediation_reasoning=remediation.get("reasoning"),

        summary=result.get("summary"),
        agent_outputs_json=json.dumps(outputs),
    )
    db.add(diagnosis)

    bug.status = "analyzed"
    db.commit()
    db.refresh(diagnosis)

    return result


@app.get("/")
def health_check():
    return {"status": "ok", "service": "bug-diagnosis-platform"}


@app.post("/bugs/paste", response_model=schemas.BugReportOut)
def submit_pasted_bug(payload: schemas.BugReportCreate, db: Session = Depends(get_db)):
    """Direct-paste submission. The full agent pipeline runs automatically
    after storage."""
    if not (payload.description or payload.stack_trace or payload.error_log):
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: description, stack_trace, error_log",
        )

    bug = models.BugReport(
        title=payload.title,
        description=payload.description,
        stack_trace=payload.stack_trace,
        error_log=payload.error_log,
        source_type="paste",
        status="submitted",
    )
    db.add(bug)
    db.commit()
    db.refresh(bug)

    _run_and_store_diagnosis(bug, db)
    db.refresh(bug)
    return bug


@app.post("/bugs/upload", response_model=schemas.BugReportOut)
async def submit_bug_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """File-upload submission. The full agent pipeline runs automatically
    after storage."""
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    try:
        text = contents.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode file as text")

    bug = models.BugReport(
        title=title,
        error_log=text,
        source_type="file",
        original_filename=file.filename,
        status="submitted",
    )
    db.add(bug)
    db.commit()
    db.refresh(bug)

    _run_and_store_diagnosis(bug, db)
    db.refresh(bug)
    return bug


@app.get("/bugs", response_model=List[schemas.BugReportOut])
def list_bugs(db: Session = Depends(get_db)):
    return db.query(models.BugReport).order_by(models.BugReport.created_at.desc()).all()


@app.get("/bugs/{bug_id}", response_model=schemas.BugReportOut)
def get_bug(bug_id: int, db: Session = Depends(get_db)):
    bug = db.query(models.BugReport).filter(models.BugReport.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug report not found")
    return bug


@app.get("/bugs/{bug_id}/diagnosis", response_model=schemas.DiagnosisOut)
def get_diagnosis(bug_id: int, db: Session = Depends(get_db)):
    """Fetch the stored agent diagnosis for a bug (all 5 agents' output)."""
    diagnosis = (
        db.query(models.DiagnosisResult)
        .filter(models.DiagnosisResult.bug_id == bug_id)
        .order_by(models.DiagnosisResult.id.desc())
        .first()
    )
    if not diagnosis:
        raise HTTPException(status_code=404, detail="No diagnosis found for this bug")
    return diagnosis


@app.post("/bugs/{bug_id}/diagnose", response_model=schemas.DiagnosisFullOut)
def rerun_diagnosis(bug_id: int, db: Session = Depends(get_db)):
    """Manually re-run the full agent pipeline on an existing bug.
    Returns the full pipeline output including raw agent JSON."""
    bug = db.query(models.BugReport).filter(models.BugReport.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug report not found")

    result = _run_and_store_diagnosis(bug, db)
    return result


@app.get("/analytics/patterns")
def get_defect_pattern_analytics(db: Session = Depends(get_db)):
    """
    Milestone 4 -- Task 1: Defect Pattern Analytics Module.
    Returns component frequency, severity distribution, recurring
    exception types, systemic (component, exception) patterns, recurring
    keyword themes, and a duplicate-cluster summary across every bug
    submitted so far.
    """
    return analytics.get_full_analytics_report(db)


@app.post("/bugs/{bug_id}/resolve", response_model=schemas.ResolveBugOut)
def resolve_bug(bug_id: int, payload: schemas.ResolveBugRequest, db: Session = Depends(get_db)):
    """
    Milestone 4 -- Task 2: Knowledge base growth mechanism.
    Records a confirmed fix for a bug and adds the bug, together with that
    fix, back into the knowledge base. Future submissions that resemble
    this bug can then match it, and the Remediation Agent will recommend
    its confirmed fix.
    """
    bug = db.query(models.BugReport).filter(models.BugReport.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug report not found")

    diagnosis = (
        db.query(models.DiagnosisResult)
        .filter(models.DiagnosisResult.bug_id == bug_id)
        .order_by(models.DiagnosisResult.id.desc())
        .first()
    )
    severity = diagnosis.severity if diagnosis else None
    resolution = payload.resolution.strip()

    try:
        retriever = get_retriever()
        chunks_added = retriever.add_resolved_bug(
            bug_id=bug.id,
            title=bug.title,
            description=bug.description,
            stack_trace=bug.stack_trace,
            error_log=bug.error_log,
            severity=severity,
            resolution=resolution,
        )
        stats = retriever.get_stats()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not add bug to the knowledge base: {exc}")

    was_resolved_before = bug.resolved_at is not None
    bug.resolution_text = resolution
    bug.resolved_at = datetime.now(timezone.utc)
    bug.kb_chunks_added = chunks_added
    db.commit()
    db.refresh(bug)

    return {
        "bug_id": bug.id,
        "resolved_at": bug.resolved_at,
        "kb_chunks_added": chunks_added,
        "knowledge_base": stats,
        "message": (
            "Confirmed fix updated in the knowledge base."
            if was_resolved_before
            else "Confirmed fix recorded and bug added to the knowledge base."
        ),
    }


@app.get("/knowledge-base/stats", response_model=schemas.KnowledgeBaseStatsOut)
def knowledge_base_stats(db: Session = Depends(get_db)):
    """Milestone 4: how large the knowledge base is and how much it has grown."""
    stats = get_retriever().get_stats()
    resolved_bugs = (
        db.query(models.BugReport)
        .filter(models.BugReport.resolved_at.isnot(None))
        .count()
    )
    return {**stats, "resolved_bugs_submitted": resolved_bugs}