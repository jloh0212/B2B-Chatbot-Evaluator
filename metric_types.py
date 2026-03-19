"""
metric_types.py — MetricResult dataclass for M1-M5 quality metrics.

Kept in its own file to avoid circular imports between metrics.py and evaluator.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def metric_score_label(score: float | None) -> str:
    """Map 0.0–1.0 score to High/Medium/Low/N/A label."""
    if score is None:
        return "N/A"
    if score >= 0.75:
        return "High"
    if score >= 0.50:
        return "Medium"
    return "Low"


@dataclass
class MetricResult:
    metric_id: str        # "M1"–"M5"
    name: str
    score: float | None   # 0.0–1.0 normalized, or None if unavailable
    score_label: str      # "High" | "Medium" | "Low" | "N/A"
    method: str           # "rule" | "llm" | "combined" | "unavailable" | "meta"
    rationale: str
    evidence: str
    raw_flags: list[str] = field(default_factory=list)
