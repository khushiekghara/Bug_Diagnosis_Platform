from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base


class BugReport(Base):
    """
    Schema for a submitted bug report (M1.2 / M1.3).
    Covers pasted descriptions, stack traces, error logs, and uploaded files.
    """
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    error_log = Column(Text, nullable=True)
    source_type = Column(String(20), nullable=False, default="paste")  # "paste" or "file"
    original_filename = Column(String(255), nullable=True)
    status = Column(String(30), nullable=False, default="submitted")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DiagnosisResult(Base):
    """
    Milestone 2: stores the combined output of the agent pipeline for a
    given bug report. Full agent JSON is kept in agent_outputs_json so
    nothing is lost, while key fields are also stored as columns for
    easy querying and reporting.
    """
    __tablename__ = "diagnosis_results"

    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bug_reports.id"), nullable=False, index=True)

    # Triage Agent output
    severity = Column(String(20), nullable=True)
    priority = Column(String(30), nullable=True)
    affected_component = Column(String(60), nullable=True)
    confidence = Column(Float, nullable=True)
    triage_reasoning = Column(Text, nullable=True)

    # Log Analysis Agent output
    exception_type = Column(String(120), nullable=True)
    failure_point = Column(String(255), nullable=True)
    affected_code_path = Column(Text, nullable=True)   # stored as comma-separated
    log_reasoning = Column(Text, nullable=True)

    # Combined
    summary = Column(Text, nullable=True)
    agent_outputs_json = Column(Text, nullable=True)   # full raw JSON
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())