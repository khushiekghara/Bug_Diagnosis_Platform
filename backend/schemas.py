from pydantic import BaseModel, Field
from typing import Optional
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