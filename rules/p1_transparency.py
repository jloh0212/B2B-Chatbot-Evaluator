"""
rules/p1_transparency.py — Transparency and Trust rule checks.
"""

from __future__ import annotations
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validator import check_forbidden_phrases, check_hype

from dataclasses import dataclass


@dataclass
class RuleViolation:
    code: str
    message: str
    severity: str  # "critical" | "major" | "minor"
    evidence: str
    principle: str


# Patterns that suggest fabricated or unverified commitment
_COMMIT_PHRASES = [
    r"i('ll| will) (add|place|finalize|submit|confirm|process|complete|order)",
    r"(added|placed|finalized|submitted|confirmed|processed|completed|ordered)\s+(the\s+)?(order|request|items?)",
    r"order (has been|is) (placed|confirmed|processed|finalized)",
]

# Price patterns — a number that looks like a price
_PRICE_PATTERN = re.compile(r"\$\s*[\d,]+(?:\.\d{2})?|\b[\d,]+(?:\.\d{2})?\s*(USD|usd)")
_INDICATIVE_NEARBY = re.compile(r"indicative|estimate|estimated|approximate|approx|~|pending|not yet confirmed", re.IGNORECASE)


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lower = response_text.lower()

    # P1_FORBIDDEN_PHRASE — uses phrases like "check other retailers" / "outside our platform"
    fp_violations = check_forbidden_phrases(response_text)
    for v in fp_violations:
        violations.append(RuleViolation(
            code="P1_FORBIDDEN_PHRASE",
            message=v.message,
            severity="major",
            evidence=v.message,
            principle="P1",
        ))

    # P1_HYPE_UNGATED — uses hype adjectives without evidence gating
    hype_violations = check_hype(response_text, marketing_enabled=False)
    for v in hype_violations:
        violations.append(RuleViolation(
            code="P1_HYPE_UNGATED",
            message=v.message,
            severity="minor",
            evidence=v.message,
            principle="P1",
        ))

    # P1_FABRICATED_SKU — mentions a SKU that does not exist in catalog context
    agent_context = context.get("agent_context", "")
    sku_mentions = re.findall(r'\b([A-Z0-9]{2,}-[A-Z0-9-]{2,})\b', response_text)
    catalog_skus = re.findall(r'\b([A-Z0-9]{2,}-[A-Z0-9-]{2,})\b', agent_context)
    catalog_sku_set = set(catalog_skus)
    if catalog_sku_set:
        for sku in sku_mentions:
            if sku not in catalog_sku_set:
                violations.append(RuleViolation(
                    code="P1_FABRICATED_SKU",
                    message=f"SKU '{sku}' mentioned in response not found in agent context catalog.",
                    severity="critical",
                    evidence=sku,
                    principle="P1",
                ))

    # P1_MISSING_INDICATIVE — price presented without "indicative" label nearby
    price_matches = list(_PRICE_PATTERN.finditer(response_text))
    for m in price_matches:
        start = max(0, m.start() - 80)
        end = min(len(response_text), m.end() + 80)
        surrounding = response_text[start:end]
        if not _INDICATIVE_NEARBY.search(surrounding):
            # Check if verified in context (total/verification complete sections)
            if not re.search(r"verification (complete|summary|trail)|verified|confirmed", lower):
                violations.append(RuleViolation(
                    code="P1_MISSING_INDICATIVE",
                    message=f"Price '{m.group()}' presented without 'indicative' label or verification confirmation.",
                    severity="minor",
                    evidence=m.group(),
                    principle="P1",
                ))
                break  # Only flag once per response

    # P1_COMMIT_WITHOUT_VERIFY — commits to action without prior verification language
    for pattern in _COMMIT_PHRASES:
        m = re.search(pattern, lower)
        if m:
            # OK if there's clear verification language present
            verify_present = re.search(
                r"(verified|verification complete|confirmed|catalog status|stock:|unit price:)",
                lower,
            )
            if not verify_present:
                violations.append(RuleViolation(
                    code="P1_COMMIT_WITHOUT_VERIFY",
                    message="Response commits to action without prior verification language.",
                    severity="major",
                    evidence=m.group(),
                    principle="P1",
                ))
                break

    return violations
