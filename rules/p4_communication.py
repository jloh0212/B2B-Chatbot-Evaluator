"""
rules/p4_communication.py — Natural Communication rule checks.
"""

from __future__ import annotations
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validator import check_hype

from dataclasses import dataclass


@dataclass
class RuleViolation:
    code: str
    message: str
    severity: str
    evidence: str
    principle: str


_JARGON_TERMS = [
    "synergies", "synergistic", "omnichannel", "holistic", "leverage",
    "touchpoints", "please be advised", "pursuant to", "as per our",
    "utilize", "utilize the", "per your request", "kindly note",
    "as discussed", "moving forward", "going forward", "circle back",
    "paradigm", "disruptive", "value-add", "thought leader",
]

_ROBOTIC_OPENERS = [
    r"^(hello|hi|greetings)[,!.]?\s+(i am|i'm)\s+(an?\s+)?(ai|artificial intelligence|language model|bot|assistant)",
    r"^as an (ai|artificial intelligence|language model|bot|assistant)",
    r"^i am (an?\s+)?(ai|artificial intelligence|language model|bot|chatbot)",
    r"^certainly[,!]?\s+i('d| would) be (happy|glad|pleased) to",
    r"^of course[,!]?\s+i('d| would) be (happy|glad|pleased) to",
    r"^absolutely[,!]?\s+i('d| would) be (happy|glad|pleased) to",
]


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lower = response_text.lower()

    # P4_JARGON — contains business jargon
    found_jargon = [term for term in _JARGON_TERMS if term in lower]
    if found_jargon:
        violations.append(RuleViolation(
            code="P4_JARGON",
            message=f"Jargon detected: {', '.join(found_jargon[:3])}",
            severity="minor",
            evidence=str(found_jargon[:3]),
            principle="P4",
        ))

    # P4_ROBOTIC_OPENER — starts with a robotic AI self-identification
    for pattern in _ROBOTIC_OPENERS:
        if re.match(pattern, lower.strip()):
            violations.append(RuleViolation(
                code="P4_ROBOTIC_OPENER",
                message="Response opens with a robotic AI self-identification.",
                severity="minor",
                evidence=response_text[:80],
                principle="P4",
            ))
            break

    # P4_DENSE_PARAGRAPH — paragraph > 120 words with no line break
    paragraphs = re.split(r'\n\s*\n', response_text)
    for para in paragraphs:
        # Remove bullet lines to focus on prose
        prose = ' '.join(
            l for l in para.split('\n')
            if not re.match(r'^\s*[-*•]', l) and not re.match(r'^\s*[A-C]\s*[—-]', l)
        )
        word_count = len(prose.split())
        if word_count > 120:
            violations.append(RuleViolation(
                code="P4_DENSE_PARAGRAPH",
                message=f"Dense paragraph detected: {word_count} words without a break.",
                severity="minor",
                evidence=prose[:100] + "...",
                principle="P4",
            ))
            break

    # P4_ANSWER_LAST — answer buried at end (response > 5 lines and no meaningful info in first 3)
    lines = [l.strip() for l in response_text.split('\n') if l.strip()]
    if len(lines) > 5:
        first_three = ' '.join(lines[:3]).lower()
        answer_signals = ['got it', 'here are', 'verified', 'stock:', 'price:', 'option', 'summary']
        if not any(sig in first_three for sig in answer_signals):
            # Check if questions dominate the start
            first_question_at = next(
                (i for i, l in enumerate(lines) if '?' not in l and len(l) > 20), None
            )
            if first_question_at and first_question_at > 3:
                violations.append(RuleViolation(
                    code="P4_ANSWER_LAST",
                    message="Substantive answer does not appear until late in the response.",
                    severity="minor",
                    evidence=f"First substantive line at position {first_question_at}",
                    principle="P4",
                ))

    return violations
