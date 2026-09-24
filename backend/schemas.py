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
    """
    Milestone 2 + Milestone 3: structured agent pipeline output returned
    to the client. JSON-string fields (evidence/matches/recommendations)
    are returned as-is; the frontend parses them for display (M3.4).
    """
    id: int
    bug_id: int

    # Triage Agent
    severity: Optional[str]
    priority: Optional[str]
    affected_component: Optional[str]
    confidence: Optional[float]
    triage_reasoning: Optional[str]

    # Log Analysis Agent
    exception_type: Optional[str]
    failure_point: Optional[str]
    affected_code_path: Optional[str]
    log_reasoning: Optional[str]

    # Root Cause Agent (M3.1)
    root_cause_hypothesis: Optional[str]
    root_cause_confidence: Optional[float]
    root_cause_evidence_json: Optional[str]
    root_cause_reasoning: Optional[str]

    # Duplicate Detection Agent (M3.2)
    duplicate_status: Optional[str]
    duplicate_matches_json: Optional[str]
    duplicate_reasoning: Optional[str]

    # Remediation Agent (M3.3)
    remediation_recommendations_json: Optional[str]
    remediation_confidence: Optional[float]
    remediation_reasoning: Optional[str]

    summary: Optional[str]
    analyzed_at: datetime

    class Config:
        from_attributes = True


class DiagnosisFullOut(BaseModel):
    """Full pipeline output including raw agent JSON -- useful for demos
    and for validating agent behaviour."""
    bug_id: Optional[int]
    analyzed_at: str
    agents_run: List[str]
    agent_outputs: Dict[str, Any]
    shared_context: Dict[str, Any]
    summary: str