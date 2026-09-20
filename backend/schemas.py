from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BugReportCreate(BaseModel):
    """Used for the direct-paste submission path."""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    stack_trace: Optional[str] = None
    error_log: Optional[str] = None


class BugReportOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    stack_trace: Optional[str]
    error_log: Optional[str]
    source_type: str
    original_filename: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DiagnosisOut(BaseModel):
    """Milestone 2: structured agent pipeline output returned to the client."""
    id: int
    bug_id: int

    severity: Optional[str]
    priority: Optional[str]
    affected_component: Optional[str]
    confidence: Optional[float]
    triage_reasoning: Optional[str]

    exception_type: Optional[str]
    failure_point: Optional[str]
    affected_code_path: Optional[str]
    log_reasoning: Optional[str]

    summary: Optional[str]
    analyzed_at: datetime

    class Config:
        from_attributes = True


class DiagnosisFullOut(BaseModel):
    """Full pipeline output including raw agent JSON — useful for demos
    and for validating agent behaviour."""
    bug_id: Optional[int]
    analyzed_at: str
    agents_run: List[str]
    agent_outputs: Dict[str, Any]
    shared_context: Dict[str, Any]
    summary: str