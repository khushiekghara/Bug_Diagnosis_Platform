"""
Milestone 4 -- Task 1: Defect Pattern Analytics Module
Analyzes all submitted bugs and their diagnosis results to surface
recurring themes, high-frequency affected components, and systemic
issue patterns -- helping identify areas of the codebase that keep
generating bugs, rather than looking at bugs one at a time.

No external service required -- pure aggregation over the existing
SQLite tables (BugReport, DiagnosisResult) using SQLAlchemy + Python's
collections.Counter.
"""
import re
from collections import Counter
from typing import Dict, List

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

MIN_PATTERN_COUNT = 2


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def get_component_frequency(db: Session) -> List[Dict]:
    rows = db.query(models.DiagnosisResult.affected_component).all()
    counter = Counter(r[0] for r in rows if r[0])
    total = sum(counter.values()) or 1
    return [
        {"component": comp, "count": count, "percentage": round(count / total * 100, 1)}
        for comp, count in counter.most_common()
    ]


def get_severity_distribution(db: Session) -> List[Dict]:
    rows = db.query(models.DiagnosisResult.severity).all()
    counter = Counter(r[0] for r in rows if r[0])
    total = sum(counter.values()) or 1
    return [
        {"severity": sev, "count": count, "percentage": round(count / total * 100, 1)}
        for sev, count in counter.most_common()
    ]


def get_exception_frequency(db: Session) -> List[Dict]:
    rows = db.query(models.DiagnosisResult.exception_type).all()
    counter = Counter(r[0] for r in rows if r[0])
    return [{"exception_type": exc, "count": count} for exc, count in counter.most_common(15)]


def get_recurring_component_exception_patterns(db: Session) -> List[Dict]:
    rows = db.query(
        models.DiagnosisResult.affected_component,
        models.DiagnosisResult.exception_type,
        models.DiagnosisResult.bug_id,
    ).all()

    pattern_bugs: Dict[tuple, List[int]] = {}
    for component, exception_type, bug_id in rows:
        if not component or not exception_type:
            continue
        key = (component, exception_type)
        pattern_bugs.setdefault(key, []).append(bug_id)

    patterns = [
        {
            "component": component,
            "exception_type": exception_type,
            "occurrences": len(bug_ids),
            "bug_ids": bug_ids,
        }
        for (component, exception_type), bug_ids in pattern_bugs.items()
        if len(bug_ids) >= MIN_PATTERN_COUNT
    ]
    patterns.sort(key=lambda p: p["occurrences"], reverse=True)
    return patterns


def get_recurring_themes(db: Session, top_n: int = 15) -> List[Dict]:
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


def get_duplicate_cluster_summary(db: Session) -> Dict:
    rows = db.query(models.DiagnosisResult.duplicate_status).all()
    counter = Counter(r[0] for r in rows if r[0])
    total = sum(counter.values()) or 1
    return {
        "total_analyzed": total,
        "likely_duplicate": counter.get("Likely Duplicate", 0),
        "related_issue": counter.get("Related Issue", 0),
        "new_unmatched": counter.get("New/Unmatched Issue", 0),
        "duplicate_rate_percent": round(
            (counter.get("Likely Duplicate", 0) + counter.get("Related Issue", 0)) / total * 100, 1
        ),
    }


def get_full_analytics_report(db: Session) -> Dict:
    total_bugs = db.query(models.BugReport).count()
    total_analyzed = db.query(models.DiagnosisResult).count()

    return {
        "total_bugs_submitted": total_bugs,
        "total_bugs_analyzed": total_analyzed,
        "component_frequency": get_component_frequency(db),
        "severity_distribution": get_severity_distribution(db),
        "exception_frequency": get_exception_frequency(db),
        "recurring_patterns": get_recurring_component_exception_patterns(db),
        "recurring_themes": get_recurring_themes(db),
        "duplicate_cluster_summary": get_duplicate_cluster_summary(db),
    }