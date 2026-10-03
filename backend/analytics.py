"""
Milestone 4 -- Task 1: Defect Pattern Analytics Module
Analyzes all submitted bugs and their diagnosis results to surface
recurring themes, high-frequency affected components, and systemic
issue patterns -- helping identify areas of the codebase that keep
generating bugs, rather than looking at bugs one at a time.

Each bug is counted once, using its most recent diagnosis. A bug that
was re-analyzed has several stored diagnoses; counting all of them would
inflate every number.

No external service required -- pure aggregation over the existing
SQLite tables (BugReport, DiagnosisResult) using SQLAlchemy + Python's
collections.Counter.
"""
import re
from collections import Counter
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import models

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "with", "and", "or", "but", "not",
    "it", "this", "that", "these", "those", "i", "you", "he", "she", "we",
    "they", "my", "your", "his", "her", "its", "our", "their", "when",
    "while", "after", "before", "then", "than", "so", "if", "as", "by",
    "from", "up", "out", "into", "over", "under", "again", "further",
    "here", "there", "all", "any", "both", "each", "more", "most", "some",
    "such", "no", "nor", "only", "own", "same", "too", "very", "can",
    "will", "just", "should", "now", "do", "does", "did", "has", "have",
    "had", "having", "app", "application", "bug", "issue", "error",
}

MIN_PATTERN_COUNT = 2  # occurrences needed for something to count as "recurring"


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def _latest_diagnoses(db: Session) -> List[models.DiagnosisResult]:
    """One diagnosis per bug: the most recent one (highest id)."""
    latest_ids = select(func.max(models.DiagnosisResult.id)).group_by(
        models.DiagnosisResult.bug_id
    )
    return (
        db.query(models.DiagnosisResult)
        .filter(models.DiagnosisResult.id.in_(latest_ids))
        .all()
    )


def get_component_frequency(diagnoses: List[models.DiagnosisResult]) -> List[Dict]:
    """High-frequency affected components across all diagnosed bugs."""
    counter = Counter(d.affected_component for d in diagnoses if d.affected_component)
    total = sum(counter.values()) or 1
    return [
        {"component": comp, "count": count, "percentage": round(count / total * 100, 1)}
        for comp, count in counter.most_common()
    ]


def get_severity_distribution(diagnoses: List[models.DiagnosisResult]) -> List[Dict]:
    counter = Counter(d.severity for d in diagnoses if d.severity)
    total = sum(counter.values()) or 1
    return [
        {"severity": sev, "count": count, "percentage": round(count / total * 100, 1)}
        for sev, count in counter.most_common()
    ]


def get_exception_frequency(diagnoses: List[models.DiagnosisResult]) -> List[Dict]:
    """Recurring exception/error types -- a strong systemic-issue signal:
    the same exception type appearing repeatedly usually points at one
    underlying weak spot in the codebase."""
    counter = Counter(d.exception_type for d in diagnoses if d.exception_type)
    return [{"exception_type": exc, "count": count} for exc, count in counter.most_common(15)]


def get_recurring_component_exception_patterns(diagnoses: List[models.DiagnosisResult]) -> List[Dict]:
    """Systemic issue patterns: a (component, exception_type) pair that
    has occurred more than once is a strong candidate for a systemic
    problem in that part of the codebase, not an isolated incident."""
    pattern_bugs: Dict[tuple, List[int]] = {}
    for d in diagnoses:
        if not d.affected_component or not d.exception_type:
            continue
        pattern_bugs.setdefault((d.affected_component, d.exception_type), []).append(d.bug_id)

    patterns = [
        {
            "component": component,
            "exception_type": exception_type,
            "occurrences": len(bug_ids),
            "bug_ids": sorted(bug_ids),
        }
        for (component, exception_type), bug_ids in pattern_bugs.items()
        if len(bug_ids) >= MIN_PATTERN_COUNT
    ]
    patterns.sort(key=lambda p: p["occurrences"], reverse=True)
    return patterns


def get_recurring_themes(db: Session, top_n: int = 15) -> List[Dict]:
    """Recurring bug themes -- most frequent meaningful keywords across
    all submitted bug titles, as a lightweight stand-in for topic
    clustering (no LLM required)."""
    titles = db.query(models.BugReport.title).all()
    counter = Counter()
    for (title,) in titles:
        if title:
            counter.update(_tokenize(title))

    return [
        {"keyword": word, "count": count}
        for word, count in counter.most_common(top_n)
        if count >= MIN_PATTERN_COUNT
    ]


def get_duplicate_cluster_summary(diagnoses: List[models.DiagnosisResult]) -> Dict:
    """Summarizes how often Duplicate Detection has flagged submissions
    as duplicates or related issues -- a direct systemic-repeat-bug signal."""
    counter = Counter(d.duplicate_status for d in diagnoses if d.duplicate_status)
    total = sum(counter.values()) or 1
    return {
        "total_analyzed": sum(counter.values()),
        "likely_duplicate": counter.get("Likely Duplicate", 0),
        "related_issue": counter.get("Related Issue", 0),
        "new_unmatched": counter.get("New/Unmatched Issue", 0),
        "duplicate_rate_percent": round(
            (counter.get("Likely Duplicate", 0) + counter.get("Related Issue", 0)) / total * 100, 1
        ),
    }


def get_full_analytics_report(db: Session) -> Dict:
    """Assembles the complete Defect Pattern Analytics report."""
    diagnoses = _latest_diagnoses(db)

    return {
        "total_bugs_submitted": db.query(models.BugReport).count(),
        "total_bugs_analyzed": len(diagnoses),
        "component_frequency": get_component_frequency(diagnoses),
        "severity_distribution": get_severity_distribution(diagnoses),
        "exception_frequency": get_exception_frequency(diagnoses),
        "recurring_patterns": get_recurring_component_exception_patterns(diagnoses),
        "recurring_themes": get_recurring_themes(db),
        "duplicate_cluster_summary": get_duplicate_cluster_summary(diagnoses),
    }