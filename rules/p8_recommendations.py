"""
rules/p8_recommendations.py — Proactive Recommendations rule checks.
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


_BROAD_REQUEST_SIGNALS = [
    r"(any brand|any model|something|anything|whatever|whichever)",
    r"(we need|i need|looking for) (a|some|any) (chair|laptop|dress|milk|product)",
]

_BEST_FOR_PATTERN = re.compile(r'\bbest for\b', re.IGNORECASE)

_UNIT_PRICE_ONLY = re.compile(
    r'\$[\d,]+(?:\.\d{2})?\s*/\s*unit|\$[\d,]+(?:\.\d{2})?\s*per unit',
    re.IGNORECASE,
)

_TOTAL_PRICE_PATTERN = re.compile(
    r'(total|subtotal|extended|grand total)[\s:]*\$[\d,]+|\$[\d,]+\s*(total|subtotal)',
    re.IGNORECASE,
)


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lower = response_text.lower()

    # Count SKU/product mentions in the response (proxy for number of recommendations)
    sku_mentions = re.findall(r'\b[A-Z0-9]{2,}-[A-Z0-9-]{2,}\b', response_text)
    named_options = re.findall(
        r'(?:^|\n)\s*[-*•]\s+([A-Z][^\n]+)',
        response_text,
    )

    # P8_NO_QUALIFY_FIRST — broad request with ≥2 SKUs without clarifying question
    is_broad = any(re.search(p, lower) for p in _BROAD_REQUEST_SIGNALS)
    conversation = context.get("conversation", [])
    last_user_message = ""
    if conversation:
        for turn in reversed(conversation):
            if turn.get("role") == "user":
                last_user_message = turn.get("content", "").lower()
                break

    is_broad_user = any(re.search(p, last_user_message) for p in _BROAD_REQUEST_SIGNALS)
    has_clarifying_q = '?' in response_text and not re.search(r'proceed\?|confirm\?|adjust\?', lower)

    if is_broad_user and len(sku_mentions) >= 2 and not has_clarifying_q:
        violations.append(RuleViolation(
            code="P8_NO_QUALIFY_FIRST",
            message="Broad request met with ≥2 SKU recommendations without qualifying question first.",
            severity="major",
            evidence=f"Broad request, {len(sku_mentions)} SKUs recommended without clarifier",
            principle="P8",
        ))

    # P8_MISSING_BEST_FOR — recommendations without "best for" labels
    if len(named_options) >= 2 or len(sku_mentions) >= 2:
        best_for_count = len(_BEST_FOR_PATTERN.findall(response_text))
        option_count = max(len(named_options), len(sku_mentions))
        if best_for_count == 0:
            violations.append(RuleViolation(
                code="P8_MISSING_BEST_FOR",
                message="Multiple recommendations provided without 'best for' labels.",
                severity="minor",
                evidence=f"{option_count} options, 0 'best for' labels",
                principle="P8",
            ))

    # P8_OPTION_COUNT_EXCESS — more than 4 options
    if len(sku_mentions) > 4 or len(named_options) > 4:
        count = max(len(sku_mentions), len(named_options))
        violations.append(RuleViolation(
            code="P8_OPTION_COUNT_EXCESS",
            message=f"Response presents {count} options — exceeds the 4-option maximum.",
            severity="minor",
            evidence=f"{count} options detected",
            principle="P8",
        ))

    # P8_UNIT_PRICE_ONLY — shows unit price but no total for multi-unit orders
    has_qty = re.search(r'\b(\d+)\s+(units?|cases?|chairs?|dresses?|laptops?)\b', last_user_message)
    if has_qty:
        qty = int(has_qty.group(1))
        if qty > 1 and _UNIT_PRICE_ONLY.search(response_text):
            if not _TOTAL_PRICE_PATTERN.search(response_text):
                violations.append(RuleViolation(
                    code="P8_UNIT_PRICE_ONLY",
                    message="Multi-unit order shows unit price only, no total/subtotal provided.",
                    severity="minor",
                    evidence=f"Qty {qty} order, unit price only",
                    principle="P8",
                ))

    return violations
