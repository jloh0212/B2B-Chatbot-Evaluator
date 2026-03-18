"""
rules/p3_efficiency.py — Efficiency and Real-Time Response rule checks.
"""

from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class RuleViolation:
    code: str
    message: str
    severity: str
    evidence: str
    principle: str


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []

    # Count question marks — each line with a ? is a clarifying question
    lines = response_text.split('\n')
    question_lines = [l for l in lines if '?' in l and len(l.strip()) > 3]
    q_count = len(question_lines)

    # P3_CLARIFIER_EXCESS — more than 5 clarifying questions
    if q_count > 5:
        violations.append(RuleViolation(
            code="P3_CLARIFIER_EXCESS",
            message=f"Response contains {q_count} question lines — exceeds the 5-question limit.",
            severity="major",
            evidence=f"{q_count} question lines found",
            principle="P3",
        ))

    # P3_INTERROGATION — 7+ consecutive question lines
    consecutive = 0
    max_consecutive = 0
    for line in lines:
        if '?' in line and len(line.strip()) > 3:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0
    if max_consecutive >= 7:
        violations.append(RuleViolation(
            code="P3_INTERROGATION",
            message=f"{max_consecutive} consecutive question lines detected — interrogation pattern.",
            severity="major",
            evidence=f"{max_consecutive} consecutive questions",
            principle="P3",
        ))

    # P3_OPTION_EXCESS — more than 4 bullet options without grouping
    bullet_lines = [l for l in lines if re.match(r'^\s*[-*•]\s+', l)]
    if len(bullet_lines) > 4:
        # Check if they're grouped (headers between bullets)
        header_lines = [l for l in lines if re.match(r'^#{1,3}\s+|^[A-Z][^:]+:', l) and '?' not in l]
        if len(header_lines) == 0:
            violations.append(RuleViolation(
                code="P3_OPTION_EXCESS",
                message=f"Response contains {len(bullet_lines)} bullet options without grouping headers.",
                severity="minor",
                evidence=f"{len(bullet_lines)} bullets",
                principle="P3",
            ))

    # P3_NO_ANSWER_FIRST — answer is buried; response starts with questions instead of info
    non_empty = [l.strip() for l in lines if l.strip()]
    if non_empty:
        first_content_lines = non_empty[:3]
        first_has_question = any('?' in l for l in first_content_lines)
        first_has_answer = any(
            re.search(r'(stock:|price:|verified|here are|got it|summary|option)', l, re.IGNORECASE)
            for l in first_content_lines
        )
        # Only flag if response is substantial (> 5 lines) and starts with questions
        if first_has_question and not first_has_answer and len(non_empty) > 5:
            violations.append(RuleViolation(
                code="P3_NO_ANSWER_FIRST",
                message="Response opens with clarifying questions before providing any information.",
                severity="minor",
                evidence=str(first_content_lines[:2]),
                principle="P3",
            ))

    return violations
