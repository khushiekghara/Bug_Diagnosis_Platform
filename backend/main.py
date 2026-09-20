import json
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List

import models
import schemas
from database import engine, get_db
from agents.orchestrator import AgentOrchestrator

# Create tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bug Diagnosis Platform — Submission + Agent Pipeline")

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
    """Runs the agent pipeline on a bug and persists the result."""
    result = orchestrator.run(_bug_to_dict(bug))

    triage = result["agent_outputs"].get("TriageAgent", {})
    log = result["agent_outputs"].get("LogAnalysisAgent", {})

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
        summary=result.get("summary"),
        agent_outputs_json=json.dumps(result["agent_outputs"]),
    )
    db.add(diagnosis)

    # Mark the bug as analyzed
    bug.status = "analyzed"
    db.commit()
    db.refresh(diagnosis)

    return result


@app.get("/")
def health_check():
    return {"status": "ok", "service": "bug-diagnosis-platform"}


@app.post("/bugs/paste", response_model=schemas.BugReportOut)
def submit_pasted_bug(payload: schemas.BugReportCreate, db: Session = Depends(get_db)):
    """Direct-paste submission. Agents run automatically after storage."""
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

    # Milestone 2: run the agent pipeline on submission
    _run_and_store_diagnosis(bug, db)
    db.refresh(bug)
    return bug


@app.post("/bugs/upload", response_model=schemas.BugReportOut)
async def submit_bug_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """File-upload submission. Agents run automatically after storage."""
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
    """Milestone 2: fetch the stored agent diagnosis for a bug."""
    diagnosis = (
        db.query(models.DiagnosisResult)
        .filter(models.DiagnosisResult.bug_id == bug_id)
        .order_by(models.DiagnosisResult.analyzed_at.desc())
        .first()
    )
    if not diagnosis:
        raise HTTPException(status_code=404, detail="No diagnosis found for this bug")
    return diagnosis


@app.post("/bugs/{bug_id}/diagnose", response_model=schemas.DiagnosisFullOut)
def rerun_diagnosis(bug_id: int, db: Session = Depends(get_db)):
    """Milestone 2: manually re-run the agent pipeline on an existing bug.
    Returns the full pipeline output including raw agent JSON."""
    bug = db.query(models.BugReport).filter(models.BugReport.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug report not found")

    result = _run_and_store_diagnosis(bug, db)
    return result