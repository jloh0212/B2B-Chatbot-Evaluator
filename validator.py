"""
validator.py — Standalone copy of the helper functions needed by the rule modules.

Originally from scripts/prompt_output_validator.py. Vendored here so the eval/
folder is fully self-contained.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List
import re

FORBIDDEN_GLOBAL = {
    "reach out to a distributor",
    "visit a local store",
    "check other retailers",
    "outside our platform",
}
HYPE_ADJECTIVES = {"amazing", "incredible", "best-in-class", "unbeatable", "ultimate"}
EXTERNAL_REVIEW_SITES = {
    "amazon", "yelp", "reddit", "trustpilot", "google reviews", "google play",
    "app store", "facebook", "instagram", "twitter", "x", "bbb", "glassdoor",
}
INTERNAL_SYSTEM_KEYWORDS = {
    "salesforce", "zendesk", "freshdesk", "cms", "ugc", "crm",
    "snowflake", "bigquery", "data warehouse",
}


@dataclass
class Violation:
    code: str
    message: str
    path: str | None = None
    conflict_ids: List[str] | None = None


def check_forbidden_phrases(text: str) -> List[Violation]:
    lower = text.lower()
    found = [p for p in FORBIDDEN_GLOBAL if p in lower]
    return [Violation("FORBIDDEN_PHRASE", f"Forbidden phrase: {p}") for p in found]


def check_hype(text: str, marketing_enabled: bool) -> List[Violation]:
    if marketing_enabled:
        return []
    lower = text.lower()
    hits = [a for a in HYPE_ADJECTIVES if a in lower]
    return [Violation("UNGATED_HYPE", f"Hype adjective when marketing disabled: {a}") for a in hits]


def check_security_flag(meta: dict, text: str) -> List[Violation]:
    suspicious = re.search(r"ignore\s+previous\s+instructions|system\s+prompt", text.lower())
    flag = meta.get("security_flag", False)
    if suspicious and not flag:
        return [Violation("INJECTION_NOT_FLAGGED", "Suspicious injection pattern not flagged")]
    return []


def _has_abc_options(text: str) -> bool:
    patterns = [
        r"(^|\n)\s*(?:[-*]\s*)?A\s*[—-]",
        r"(^|\n)\s*(?:[-*]\s*)?B\s*[—-]",
        r"(^|\n)\s*(?:[-*]\s*)?C\s*[—-]",
    ]
    return all(re.search(p, text) for p in patterns)


def _has_review_count(text: str) -> bool:
    return (
        bool(re.search(r"based\s+on\s+\d{1,5}\s+.*reviews", text.lower()))
        or bool(re.search(r"\b\d{1,5}\s+(customer\s+)?reviews\b", text.lower()))
    )


def _has_recency_band(text: str) -> bool:
    t = text.lower()
    if "recent purchases" in t or "recent reviews" in t or "recent" in t:
        return True
    return bool(re.search(
        r"last\s+\d+\s+(days|weeks|months|quarters|years)|past\s+\d+\s+(days|weeks|months|quarters|years)",
        t,
    ))


def _mentions_unapproved_sources(text: str) -> List[str]:
    t = text.lower()
    hits: List[str] = []
    for s in EXTERNAL_REVIEW_SITES:
        if re.search(rf"\b{re.escape(s)}\b", t):
            hits.append(s)
    return hits


def _mentions_internal_systems(text: str) -> List[str]:
    t = text.lower()
    return [s for s in INTERNAL_SYSTEM_KEYWORDS if s in t]


def _mentions_fallback_unavailable(text: str) -> bool:
    t = text.lower()
    triggers = [
        "don't have access to recent customer reviews",
        "do not have access to recent customer reviews",
        "no recent customer reviews are available",
        "reviews are not available",
        "reviews are unavailable",
        "cannot access reviews",
        "can't access reviews",
    ]
    return any(s in t for s in triggers)
