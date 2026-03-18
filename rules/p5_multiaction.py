"""
rules/p5_multiaction.py — Multi-Action Orchestration rule checks.
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


_UI_PATTERNS = re.compile(
    r'\b(click|tap|press|hit|select from|navigate to|go to the|open the menu|'
    r'scroll (down|up|to)|dropdown|button|checkbox|toggle|tab|page|sidebar|'
    r'menu item|open settings|settings page|click here|use the interface)\b',
    re.IGNORECASE,
)

_COMMIT_WITHOUT_CONFIRM = [
    r"i('ve| have) (added|placed|submitted|finalized|processed|completed|ordered)",
    r"(adding|placing|submitting|finalizing|processing|completing|ordering) now",
    r"done[.!]\s*(i|the|your)",
    r"order (is|has been) (placed|confirmed|finalized|submitted)",
]


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lower = response_text.lower()

    # P5_UI_REFERENCE — mentions UI elements (buttons, menus, clicks)
    m = _UI_PATTERNS.search(response_text)
    if m:
        violations.append(RuleViolation(
            code="P5_UI_REFERENCE",
            message=f"UI element reference detected: '{m.group()}'.",
            severity="major",
            evidence=m.group(),
            principle="P5",
        ))

    # P5_NO_CONFIRM_BEFORE_ACT — commits to irreversible action without asking for confirmation
    for pattern in _COMMIT_WITHOUT_CONFIRM:
        m = re.search(pattern, lower)
        if m:
            # Check if there's a confirmation request nearby (within the same response)
            confirm_present = re.search(
                r'(proceed\?|confirm|shall i|would you like|ok to|approve|yes/no|'
                r'proceed as summarized|adjust|next step)',
                lower,
            )
            if not confirm_present:
                violations.append(RuleViolation(
                    code="P5_NO_CONFIRM_BEFORE_ACT",
                    message=f"Commits to action '{m.group()}' without requesting confirmation.",
                    severity="major",
                    evidence=m.group(),
                    principle="P5",
                ))
            break

    # P5_CONTEXT_DROP_ACROSS_TURN — check multi-turn context
    conversation = context.get("conversation", [])
    if len(conversation) > 2:
        # Find cart/order context from prior turns
        prior_cart_items = []
        for turn in conversation[:-1]:
            content = turn.get("content", "")
            skus = re.findall(r'\b([A-Z0-9]{2,}-[A-Z0-9-]{2,})\b', content)
            prior_cart_items.extend(skus)

        if prior_cart_items:
            referenced = any(sku in response_text for sku in prior_cart_items)
            if not referenced and len(response_text) > 100:
                violations.append(RuleViolation(
                    code="P5_CONTEXT_DROP_ACROSS_TURN",
                    message="Cart/order context from prior turns not referenced in response.",
                    severity="major",
                    evidence=f"Missing: {prior_cart_items[:3]}",
                    principle="P5",
                ))

    return violations
