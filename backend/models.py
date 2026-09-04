from sqlalchemy import Column, Integer, String, Text, DateTime
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