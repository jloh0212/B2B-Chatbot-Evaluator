"""
rules/p6_error_handling.py — Error Handling and Recovery rule checks.
"""

from __future__ import annotations
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validator import _has_abc_options

from dataclasses import dataclass


@dataclass
class RuleViolation:
    code: str
    message: str
    severity: str
    evidence: str
    principle: str


_DEAD_END_PHRASES = [
    r"i (don't|do not|cannot|can't) (know|help|assist|answer|provide)",
    r"(unfortunately|sorry)[,.]? i (don't|do not|cannot|can't)",
    r"(not available|unavailable|not possible|impossible)",
]

_APOLOGY_PATTERN = re.compile(
    r'\b(sorry|i apologize|my apologies|pardon me|i\'m afraid|regret to inform)\b',
    re.IGNORECASE,
)

_CONTEXT_REQUEST_PATTERNS = [
    r"(please|can you) (provide|share|give me|tell me) (your|the) (sku|product|item|order number)",
    r"(what|which) (product|item|sku|order) (are you|do you)",
    r"(please clarify|can you clarify) (the |your )?(product|item|sku)",
]

_NEXT_STEP_SIGNALS = [
    r"(here are|here is|i can|let me|next step|instead|alternatively|option)",
    r"(a|b|c)\s*[—\-]",
    r"(proceed|adjust|verify|confirm)",
]


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lower = response_text.lower()

    # P6_DEAD_END — "I don't know" with no next step
    dead_end_found = False
    for pattern in _DEAD_END_PHRASES:
        if re.search(pattern, lower):
            dead_end_found = True
            break

    if dead_end_found:
        has_next_step = any(re.search(p, lower) for p in _NEXT_STEP_SIGNALS)
        if not has_next_step:
            violations.append(RuleViolation(
                code="P6_DEAD_END",
                message="Response reaches a dead end ('I don't know') with no recovery path or next step.",
                severity="major",
                evidence="Dead-end phrase without next step",
                principle="P6",
            ))

    # P6_NO_ABC_WHEN_UNCERTAIN — uncertainty without A/B/C options
    uncertainty_signals = [
        "uncertain", "not sure", "can't confirm", "cannot confirm",
        "unverified", "not verified", "may change", "might change",
        "unclear", "don't have access", "do not have access",
    ]
    has_uncertainty = any(sig in lower for sig in uncertainty_signals)
    if has_uncertainty and not _has_abc_options(response_text):
        violations.append(RuleViolation(
            code="P6_NO_ABC_WHEN_UNCERTAIN",
            message="Response expresses uncertainty but does not offer A/B/C recovery options.",
            severity="minor",
            evidence="Uncertainty detected without A/B/C options",
            principle="P6",
        ))

    # P6_OVER_APOLOGY — 3 or more apology phrases
    apology_count = len(_APOLOGY_PATTERN.findall(response_text))
    if apology_count >= 3:
        violations.append(RuleViolation(
            code="P6_OVER_APOLOGY",
            message=f"Response contains {apology_count} apology phrases — excessive for B2B context.",
            severity="minor",
            evidence=f"{apology_count} apologies detected",
            principle="P6",
        ))

    # P6_REPEAT_CONTEXT_REQUEST — asks for the same context that was already provided
    conversation = context.get("conversation", [])
    if len(conversation) > 1:
        last_user_content = ""
        for turn in reversed(conversation):
            if turn.get("role") == "user":
                last_user_content = turn.get("content", "").lower()
                break

        for pattern in _CONTEXT_REQUEST_PATTERNS:
            if re.search(pattern, lower) and last_user_content:
                # Check if the requested context is already in the last user message
                if re.search(r'\b(sku|product|item)\b', last_user_content):
                    violations.append(RuleViolation(
                        code="P6_REPEAT_CONTEXT_REQUEST",
                        message="Response re-asks for context (SKU/product) already provided by user.",
                        severity="minor",
                        evidence="Context re-request detected",
                        principle="P6",
                    ))
                    break

    return violations
