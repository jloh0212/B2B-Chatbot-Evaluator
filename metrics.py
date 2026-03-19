"""
metrics.py — METRICS registry and M4/M5 compute functions.

M1, M2, M3 rule checks + LLM prompt templates are defined here but
executed by EvaluationEngine._compute_m1/m2/m3() in evaluator.py
(because they need the Anthropic client).

M4 and M5 are pure functions and can be called directly.
"""

from __future__ import annotations

import re
import sys
import os
from statistics import mean
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))

from metric_types import MetricResult, metric_score_label

# ---------------------------------------------------------------------------
# METRICS registry
# ---------------------------------------------------------------------------

METRICS: dict[str, dict[str, str]] = {
    "M1": {
        "name": "Faithfulness",
        "description": "Response facts are grounded in the provided agent context (no hallucinated SKUs/prices).",
        "default_method": "combined",
    },
    "M2": {
        "name": "Answer Relevance",
        "description": "Response directly addresses the user's intent (price/stock/delivery/order/general).",
        "default_method": "combined",
    },
    "M3": {
        "name": "Groundedness",
        "description": "Response content lexically overlaps with agent context; no invented claims.",
        "default_method": "combined",
    },
    "M4": {
        "name": "Instruction Following",
        "description": "Response follows B2B formatting and communication rules (ABC options, labels, no UI refs).",
        "default_method": "rule",
    },
    "M5": {
        "name": "Calibration",
        "description": "Rule-check scores agree with LLM judge scores across P1-P10 (meta-metric).",
        "default_method": "meta",
    },
}

# ---------------------------------------------------------------------------
# LLM prompt templates (used by evaluator._compute_m1/m2/m3)
# ---------------------------------------------------------------------------

M1_FAITHFULNESS_PROMPT = """You are evaluating whether a B2B chatbot response is faithful to the provided context.

Agent Context (ground truth):
{agent_context}

User Message:
{user_message}

Chatbot Response to Evaluate:
{response_text}

Pre-detected rule flags:
{rule_flags}

Task: Score how well the response sticks to facts in the agent context. Penalize invented SKUs, prices, or claims not supported by the context.

Respond ONLY with valid JSON:
{{"faithfulness_score": <0.0-1.0>, "rationale": "<1-2 sentences>", "unsupported_claims": ["<claim1>", "<claim2>"]}}"""


M2_RELEVANCE_PROMPT = """You are evaluating whether a B2B chatbot response answers the user's actual question.

Detected user intent: {detected_intent}

User Message:
{user_message}

Chatbot Response to Evaluate:
{response_text}

Pre-detected rule flags:
{rule_flags}

Task: Score how directly the response addresses the user's intent. A response that deflects, ignores the main question, or answers a different question scores low.

Respond ONLY with valid JSON:
{{"relevance_score": <0.0-1.0>, "rationale": "<1-2 sentences>", "intent_addressed": <true|false>}}"""


M3_GROUNDEDNESS_PROMPT = """You are evaluating whether a B2B chatbot response is grounded in the provided context.

Agent Context (ground truth):
{agent_context}

User Message:
{user_message}

Chatbot Response to Evaluate:
{response_text}

Pre-detected rule flags:
{rule_flags}

Task: Score how well the response is anchored to the provided context. A grounded response only states things that can be traced back to the context. Penalize invented details.

Respond ONLY with valid JSON:
{{"groundedness_score": <0.0-1.0>, "rationale": "<1-2 sentences>", "grounded_claims": <count>, "ungrounded_claims": <count>}}"""


# ---------------------------------------------------------------------------
# M4: Instruction Following (rule-only, pure function)
# ---------------------------------------------------------------------------

# Jargon list (same as P4 rule)
_JARGON = re.compile(
    r'\b(synergies|omnichannel|holistic|leverage|touchpoints|please\s+be\s+advised)\b',
    re.IGNORECASE,
)
# UI references (same as P5 rule)
_UI_REFS = re.compile(
    r'\b(click|button|menu|page|dropdown|navigate|scroll)\b',
    re.IGNORECASE,
)
# Price pattern: dollar/euro amounts
_PRICE_PATTERN = re.compile(r'(USD|EUR|\$|€)\s*[\d,]+(\.\d+)?')
# "Indicative" label near price
_INDICATIVE = re.compile(r'\bindicative\b', re.IGNORECASE)
# A/B/C options detector (reuse from validator pattern)
_ABC_PATTERN = re.compile(r'\b[ABC]\s*[):.]\s+\S', re.MULTILINE)


def _has_abc_options(text: str) -> bool:
    """True if response contains labelled A/B/C options."""
    return bool(_ABC_PATTERN.search(text))


def _skus_in_text(text: str) -> list[str]:
    """Extract potential SKU-like tokens (alphanumeric with hyphens, 5+ chars)."""
    return re.findall(r'\b[A-Z][A-Z0-9\-]{4,}\b', text)


def compute_m4_instruction_following(response_text: str, scenario: Any) -> MetricResult:
    """
    Rule-only checklist for B2B instruction-following.

    Checks:
    1. ABC options present when ≥2 SKUs mentioned
    2. Indicative label near price pattern
    3. No UI references
    4. No jargon
    5. Answer not buried (first 3 lines not all questions)
    """
    flags: list[str] = []
    checks_passed = 0
    total_checks = 5

    # Check 1: ABC options when ≥2 SKUs mentioned
    skus = _skus_in_text(response_text)
    if len(skus) >= 2:
        if _has_abc_options(response_text):
            checks_passed += 1
        else:
            flags.append("M4_MISSING_ABC_OPTIONS")
    else:
        checks_passed += 1  # Not applicable — pass

    # Check 2: Indicative label near price
    has_price = bool(_PRICE_PATTERN.search(response_text))
    if has_price:
        if _INDICATIVE.search(response_text):
            checks_passed += 1
        else:
            flags.append("M4_PRICE_NOT_LABELED")
    else:
        checks_passed += 1  # No price mentioned — pass

    # Check 3: No UI references
    if not _UI_REFS.search(response_text):
        checks_passed += 1
    else:
        flags.append("M4_UI_REFERENCE")

    # Check 4: No jargon
    if not _JARGON.search(response_text):
        checks_passed += 1
    else:
        flags.append("M4_JARGON_PRESENT")

    # Check 5: Answer not buried — first 3 lines shouldn't all be questions
    lines = [l.strip() for l in response_text.strip().split('\n') if l.strip()]
    first_three = lines[:3] if lines else []
    if first_three:
        question_count = sum(1 for l in first_three if l.endswith('?'))
        if question_count == len(first_three) and len(first_three) > 0:
            flags.append("M4_ANSWER_BURIED")
        else:
            checks_passed += 1
    else:
        checks_passed += 1

    score = checks_passed / total_checks
    label = metric_score_label(score)

    rationale_parts = []
    if flags:
        rationale_parts.append(f"Failed checks: {', '.join(flags)}.")
    else:
        rationale_parts.append("All instruction-following checks passed.")

    rationale = " ".join(rationale_parts)
    evidence = f"{checks_passed}/{total_checks} checks passed"

    return MetricResult(
        metric_id="M4",
        name=METRICS["M4"]["name"],
        score=round(score, 3),
        score_label=label,
        method="rule",
        rationale=rationale,
        evidence=evidence,
        raw_flags=flags,
    )


# ---------------------------------------------------------------------------
# M5: Calibration (meta-computation, pure function)
# ---------------------------------------------------------------------------

def compute_m5_calibration(principle_results: dict) -> MetricResult:
    """
    Meta-metric: agreement between rule-based scores and LLM judge scores.

    For each principle:
      agreement = 1.0 - abs(pr.score - pr.llm_score) / 4.0

    Skips principles where both sides used default (llm_score == 3 and no violations).
    Returns score=None if LLM judge was not run at all.
    """
    # Detect if LLM judge was actually run
    # If ALL principles have llm_score == 3, assume LLM was not run
    all_llm_scores = [pr.llm_score for pr in principle_results.values()]
    if all(s == 3 for s in all_llm_scores):
        return MetricResult(
            metric_id="M5",
            name=METRICS["M5"]["name"],
            score=None,
            score_label="N/A",
            method="unavailable",
            rationale="LLM judge was not run — calibration requires LLM scores.",
            evidence="All LLM scores defaulted to 3",
            raw_flags=[],
        )

    agreements: list[float] = []
    divergent_principles: list[str] = []

    for p_id, pr in principle_results.items():
        rule_score = pr.score
        llm_score = pr.llm_score

        # Skip if both sides produced no signal (llm=3, no violations → default values)
        has_violations = len(getattr(pr, 'rule_violations', [])) > 0
        if llm_score == 3 and not has_violations:
            continue  # No signal on either side — skip

        delta = abs(rule_score - llm_score)
        agreement = 1.0 - delta / 4.0
        agreements.append(agreement)

        if delta >= 2:
            divergent_principles.append(p_id)

    if not agreements:
        return MetricResult(
            metric_id="M5",
            name=METRICS["M5"]["name"],
            score=None,
            score_label="N/A",
            method="unavailable",
            rationale="No principles with both rule and LLM signal available.",
            evidence="Insufficient data",
            raw_flags=[],
        )

    calibration_score = mean(agreements)
    label = metric_score_label(calibration_score)

    if divergent_principles:
        rationale = (
            f"Rule and LLM scores diverge ≥2 points on: {', '.join(divergent_principles)}. "
            f"Mean agreement: {calibration_score:.0%}."
        )
    else:
        rationale = f"Rule and LLM scores agree well across principles. Mean agreement: {calibration_score:.0%}."

    evidence = f"{len(agreements)} principles compared, {len(divergent_principles)} divergent"

    return MetricResult(
        metric_id="M5",
        name=METRICS["M5"]["name"],
        score=round(calibration_score, 3),
        score_label=label,
        method="meta",
        rationale=rationale,
        evidence=evidence,
        raw_flags=divergent_principles,
    )
