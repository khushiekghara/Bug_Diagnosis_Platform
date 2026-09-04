from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List

import models
import schemas
from database import engine, get_db

# Create tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bug Diagnosis Platform — Submission Module")

# Allow the frontend (served separately) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".txt", ".log", ".json", ".csv"}
MAX_FILE_SIZE_MB = 5


@app.get("/")
def health_check():
    return {"status": "ok", "service": "bug-submission-module"}


@app.post("/bugs/paste", response_model=schemas.BugReportOut)
def submit_pasted_bug(payload: schemas.BugReportCreate, db: Session = Depends(get_db)):
    """
    Direct-paste submission path: bug description, stack trace, error log
    typed/pasted straight into the form.
    """
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
    return bug


@app.post("/bugs/upload", response_model=schemas.BugReportOut)
async def submit_bug_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    File-upload submission path: accepts .txt/.log/.json/.csv bug report,
    stack trace, or error log files.
    """
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