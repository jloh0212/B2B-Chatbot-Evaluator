"""
rules/p7_handoff.py — Human Handoff rule checks.
"""

from __future__ import annotations
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validator import _mentions_internal_systems

from dataclasses import dataclass


@dataclass
class RuleViolation:
    code: str
    message: str
    severity: str
    evidence: str
    principle: str


_HANDOFF_PHRASES = re.compile(
    r'\b(connect(ing)? you (to|with)|transfer(ring)? (you|this)|'
    r'hand(ing)? (you )?off|escalat(ing)?|routing (you|this)|'
    r'pass(ing)? (you|this) (to|over to)|speak(ing)? with (a|our|the) (specialist|agent|human|rep|team))\b',
    re.IGNORECASE,
)

_CONTEXT_SUMMARY_SIGNALS = [
    r"(summary|context|details|captured so far|to recap|as discussed|confirmed items?|"
    r"(your|the) (request|order|query|issue|case|items?)(\s+so far)?)",
]

_FORCE_HANDOFF_SIGNALS = [
    r"(you (need|should|must|have) to (call|contact|speak|talk) (to|with))",
    r"(only a (human|specialist|agent|rep) can|please (call|contact|email))",
    r"(i cannot handle|beyond (my|agent) (capabilities|scope|ability))",
]


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lower = response_text.lower()

    handoff_triggered = bool(_HANDOFF_PHRASES.search(response_text))

    if handoff_triggered:
        # P7_HANDOFF_WITHOUT_VERIFY — hands off without showing agent paths exhausted
        exhausted_signals = [
            r"(exhausted|tried|attempted|verified|confirmed|checked)",
            r"(i('ve| have) (checked|tried|verified|confirmed|looked into|explored))",
            r"(agent (paths|options|capabilities) (are |have been )?(exhausted|tried))",
            r"(beyond (what i can|my ability to) (verify|confirm|resolve))",
        ]
        exhausted = any(re.search(p, lower) for p in exhausted_signals)
        if not exhausted:
            violations.append(RuleViolation(
                code="P7_HANDOFF_WITHOUT_VERIFY",
                message="Handoff triggered without demonstrating that agent paths were exhausted first.",
                severity="major",
                evidence="Handoff without verification of exhaustion",
                principle="P7",
            ))

        # P7_DROPS_CONTEXT_AT_HANDOFF — no context summary passed with handoff
        has_summary = any(re.search(p, lower) for p in _CONTEXT_SUMMARY_SIGNALS)
        if not has_summary:
            violations.append(RuleViolation(
                code="P7_DROPS_CONTEXT_AT_HANDOFF",
                message="Handoff does not include context summary for the specialist.",
                severity="major",
                evidence="No context summary before handoff",
                principle="P7",
            ))

    # P7_INTERNAL_SYSTEM_NAME — exposes internal system names
    internal_hits = _mentions_internal_systems(response_text)
    if internal_hits:
        violations.append(RuleViolation(
            code="P7_INTERNAL_SYSTEM_NAME",
            message=f"Internal system name exposed: {', '.join(internal_hits)}",
            severity="critical",
            evidence=str(internal_hits),
            principle="P7",
        ))

    # P7_FORCE_HANDOFF — forces handoff when agent could handle it
    for pattern in _FORCE_HANDOFF_SIGNALS:
        if re.search(pattern, lower):
            # Allow if handoff is clearly a last resort (exhausted mentioned)
            if not re.search(r"exhausted|tried all|no (other|further) option", lower):
                violations.append(RuleViolation(
                    code="P7_FORCE_HANDOFF",
                    message="Response forces handoff to human without attempting agent resolution first.",
                    severity="minor",
                    evidence=pattern[:50],
                    principle="P7",
                ))
            break

    return violations
