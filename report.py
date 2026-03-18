"""
report.py — JSON report and markdown display summary generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from evaluator import EvaluationResult, GapItem, score_label, BUSINESS_IMPACT


# ---------------------------------------------------------------------------
# Score label thresholds
# ---------------------------------------------------------------------------

def _score_emoji(score: float) -> str:
    if score >= 4:
        return "🟢"
    elif score >= 3:
        return "🟡"
    else:
        return "🔴"


def _gap_rank_score(gap: GapItem) -> int:
    severity_weight = {"critical": 10, "major": 4, "minor": 1}
    type_weight = {"C": 3, "B": 2, "A": 1}
    return severity_weight.get(gap.severity, 0) + type_weight.get(gap.type, 1)


# ---------------------------------------------------------------------------
# JSON Report
# ---------------------------------------------------------------------------

def generate_json_report(result: EvaluationResult) -> dict:
    principle_results_json: dict[str, Any] = {}
    for p, pr in result.principle_results.items():
        principle_results_json[p] = {
            "score": pr.score,
            "score_label": pr.score_label,
            "rule_violations": pr.rule_violations,
            "llm_score": pr.llm_score,
            "llm_rationale": pr.llm_rationale,
            "llm_evidence_quote": pr.llm_evidence_quote,
            "improvement_suggestions": pr.improvement_suggestions,
            "business_impact": pr.business_impact,
        }

    top_gaps_json = []
    for rank, gap in enumerate(result.top_gaps[:5], start=1):
        top_gaps_json.append({
            "rank": rank,
            "principle": gap.principle,
            "description": gap.description,
            "type": gap.type,
            "severity": gap.severity,
            "evidence": gap.evidence,
            "fix_example": gap.fix_example,
        })

    return {
        "report_version": "1.0",
        "run_id": result.run_id,
        "timestamp": result.timestamp,
        "version_id": result.version_id,
        "scenario_id": result.scenario.id,
        "industry": result.scenario.industry,
        "composite_score": result.composite_score,
        "weighted_composite_score": result.weighted_composite_score,
        "score_label": result.score_label,
        "risk_flags": result.risk_flags,
        "principle_results": principle_results_json,
        "top_gaps": top_gaps_json,
        "eval_metadata": result.eval_metadata,
    }


# ---------------------------------------------------------------------------
# Markdown Display Summary
# ---------------------------------------------------------------------------

def generate_display_summary(result: EvaluationResult) -> str:
    lines = []

    # Header
    composite = result.weighted_composite_score
    emoji = _score_emoji(composite)
    lines.append(f"## Evaluation Summary — {result.scenario.id}")
    lines.append(f"**Industry:** {result.scenario.industry} | "
                 f"**Version:** {result.version_id} | "
                 f"**Composite Score:** {emoji} {composite:.1f}/5.0 ({result.score_label})")
    lines.append("")

    # Principle table
    lines.append("### Principle Scores")
    lines.append("")
    lines.append("| Principle | Score | Label | Top Gap |")
    lines.append("|-----------|-------|-------|---------|")

    for p in ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]:
        if p not in result.principle_results:
            continue
        pr = result.principle_results[p]
        e = _score_emoji(pr.score)
        top_gap = pr.improvement_suggestions[0][:60] if pr.improvement_suggestions else "—"
        from rubric import RUBRIC
        name = RUBRIC[p]["name"]
        lines.append(f"| {p}: {name} | {e} {pr.score}/5 | {pr.score_label} | {top_gap} |")

    lines.append("")

    # Risk flags section
    if result.risk_flags:
        lines.append("### ⚠️ Risk Flags")
        lines.append("")
        for flag in result.risk_flags:
            lines.append(f"- 🔴 **{flag['flag']}** [{flag['severity'].upper()}]")
            lines.append(f"  - Evidence: `{flag['evidence'][:100]}`")
            lines.append(f"  - Business Impact: {flag['business_impact']}")
        lines.append("")

    # Top 3 gaps with A/B/C type tags
    if result.top_gaps:
        lines.append("### Top Improvement Gaps")
        lines.append("")
        for i, gap in enumerate(result.top_gaps[:3], start=1):
            type_badge = f"[Type {gap.type}]"
            sev_badge = f"[{gap.severity.upper()}]"
            lines.append(f"**{i}. {gap.principle}** {type_badge} {sev_badge}")
            lines.append(f"- Issue: {gap.description}")
            if gap.fix_example:
                lines.append(f"- Fix: _{gap.fix_example[:120]}_")
            lines.append("")

    return "\n".join(lines)
