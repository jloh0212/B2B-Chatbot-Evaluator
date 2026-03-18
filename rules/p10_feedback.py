"""
rules/p10_feedback.py — Customer Reviews and Feedback Integration rule checks.
"""

from __future__ import annotations
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validator import (
    _has_abc_options,
    _has_review_count,
    _has_recency_band,
    _mentions_unapproved_sources,
    _mentions_fallback_unavailable,
    check_hype,
)

from dataclasses import dataclass


@dataclass
class RuleViolation:
    code: str
    message: str
    severity: str
    evidence: str
    principle: str


_REVIEW_TRIGGER = re.compile(r'\b(review|rating|feedback|rated|stars?)\b', re.IGNORECASE)


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []

    # Only check if response involves reviews
    if not _REVIEW_TRIGGER.search(response_text):
        return violations

    # P10_UNAPPROVED_SOURCE — cites unapproved external review source
    unapproved = _mentions_unapproved_sources(response_text)
    if unapproved:
        violations.append(RuleViolation(
            code="P10_UNAPPROVED_SOURCE",
            message=f"Unapproved external review sources cited: {', '.join(unapproved)}",
            severity="major",
            evidence=str(unapproved),
            principle="P10",
        ))

    # If fallback is declared (reviews unavailable), check for A/B/C
    if _mentions_fallback_unavailable(response_text):
        if not _has_abc_options(response_text):
            violations.append(RuleViolation(
                code="P10_FALLBACK_MISSING",
                message="Reviews declared unavailable but no A/B/C fallback options offered.",
                severity="major",
                evidence="Fallback without A/B/C",
                principle="P10",
            ))
        return violations  # Fallback path — no need to check count/recency

    # P10_MISSING_COUNT — review summary missing explicit count
    if not _has_review_count(response_text):
        violations.append(RuleViolation(
            code="P10_MISSING_COUNT",
            message="Review summary does not include an explicit review count (e.g., 'based on 124 reviews').",
            severity="minor",
            evidence="No review count detected",
            principle="P10",
        ))

    # P10_MISSING_RECENCY — review summary missing recency band
    if not _has_recency_band(response_text):
        violations.append(RuleViolation(
            code="P10_MISSING_RECENCY",
            message="Review summary missing recency band (e.g., 'last 90 days', 'recent purchases').",
            severity="minor",
            evidence="No recency band detected",
            principle="P10",
        ))

    # P10_HYPE_IN_REVIEW — hype adjectives in review summary
    hype_violations = check_hype(response_text, marketing_enabled=False)
    if hype_violations:
        violations.append(RuleViolation(
            code="P10_HYPE_IN_REVIEW",
            message="Hype adjectives found in review summary (ungated enthusiasm).",
            severity="minor",
            evidence=str([v.message for v in hype_violations[:2]]),
            principle="P10",
        ))

    return violations
