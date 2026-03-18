"""
rules/p2_personalization.py — Personalization and Context Awareness rule checks.
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


# Pronouns that should not stand alone for product references
_PRODUCT_PRONOUN_PATTERN = re.compile(
    r'\b(this one|that one|these ones|those ones|this product|that product|it)\b',
    re.IGNORECASE,
)

# Emoji detection
_EMOJI_PATTERN = re.compile(
    r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
    r'\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF'
    r'\U00002600-\U000026FF]+'
)

# Gender mislabeling signals
_GENDER_SIGNAL = re.compile(r"\b(men'?s|women'?s|unisex|gender)\b", re.IGNORECASE)

# Small-talk forcing patterns
_SMALL_TALK_PATTERN = re.compile(
    r'\b(let\'?s chat|hey+|heyyy|how are you|hope you\'re|how\'s your day)\b',
    re.IGNORECASE,
)


def check(response_text: str, context: dict) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lower = response_text.lower()

    # P2_PRONOUN_FOR_PRODUCT — uses pronouns when SKU is in context
    agent_context = context.get("agent_context", "")
    conversation = context.get("conversation", [])
    has_sku_in_context = bool(re.search(r'\b[A-Z0-9]{2,}-[A-Z0-9-]{2,}\b', agent_context))

    # Check prior assistant turns for SKU mentions
    for turn in conversation:
        if turn.get("role") == "assistant":
            if re.search(r'\b[A-Z0-9]{2,}-[A-Z0-9-]{2,}\b', turn.get("content", "")):
                has_sku_in_context = True
                break

    if has_sku_in_context:
        for m in _PRODUCT_PRONOUN_PATTERN.finditer(response_text):
            violations.append(RuleViolation(
                code="P2_PRONOUN_FOR_PRODUCT",
                message=f"Pronoun '{m.group()}' used for product reference when SKU is available in context.",
                severity="major",
                evidence=m.group(),
                principle="P2",
            ))
            break  # Flag once

    # P2_SMALL_TALK_FORCED — agent forces small talk or emoji
    emoji_hits = _EMOJI_PATTERN.findall(response_text)
    if emoji_hits:
        violations.append(RuleViolation(
            code="P2_SMALL_TALK_FORCED",
            message="Response contains emojis inappropriate for B2B procurement context.",
            severity="minor",
            evidence=str(emoji_hits[:3]),
            principle="P2",
        ))

    for m in _SMALL_TALK_PATTERN.finditer(response_text):
        violations.append(RuleViolation(
            code="P2_SMALL_TALK_FORCED",
            message=f"Small-talk phrase '{m.group()}' forced in B2B response.",
            severity="minor",
            evidence=m.group(),
            principle="P2",
        ))
        break

    # P2_CONTEXT_DROP — check if key context from prior turns is absent
    # Look for prior turns that established quantity/product; verify response references them
    prior_quantities = []
    prior_products = []
    for turn in conversation[:-1]:  # Exclude the last user turn
        content = turn.get("content", "")
        qty = re.findall(r'\b(\d+)\s+units?\b|\b(\d+)\s+cases?\b|\b(\d+)\s+chairs?\b', content)
        prior_quantities.extend([q for group in qty for q in group if q])
        skus = re.findall(r'\b([A-Z0-9]{2,}-[A-Z0-9-]{2,})\b', content)
        prior_products.extend(skus)

    if prior_products and len(conversation) > 1:
        # At least one prior SKU should appear or be referenced in the response
        referenced = any(sku in response_text for sku in prior_products)
        # Allow if response is very short (just a quick acknowledgment)
        if not referenced and len(response_text) > 100:
            violations.append(RuleViolation(
                code="P2_CONTEXT_DROP",
                message="Response does not reference products/SKUs established in prior turns.",
                severity="major",
                evidence=f"Prior SKUs: {prior_products[:3]}",
                principle="P2",
            ))

    # P2_GENDER_MISLABEL — check for gender labeling in fashion context
    industry = context.get("industry", "")
    if industry.lower() == "fashion":
        # If mixed-gender products are present but no mixed label
        if re.search(r'\b(men|women|female|male)\b', lower):
            if not _GENDER_SIGNAL.search(response_text):
                pass  # Minor: only flag if clear mislabel, skip for now

    return violations
