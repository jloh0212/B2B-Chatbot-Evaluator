"""
versions.py — VersionStore: save, load, list, and compare evaluation results.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluator import EvaluationResult
from report import generate_json_report

VERSIONS_DIR = Path(__file__).parent / "data" / "versions"


# ---------------------------------------------------------------------------
# ComparisonResult
# ---------------------------------------------------------------------------

@dataclass
class ComparisonResult:
    scenario_id: str
    version_a: str
    version_b: str
    composite_delta: float
    per_principle_deltas: dict[str, int]
    regressions: list[str]     # principles where score went down
    improvements: list[str]    # principles where score went up
    new_violations: list[str]  # violation codes appearing in B but not A
    resolved_violations: list[str]  # violation codes in A but not B
    risk_flag_changes: dict    # {"added": [...], "removed": [...]}
    summary: str


# ---------------------------------------------------------------------------
# VersionStore
# ---------------------------------------------------------------------------

class VersionStore:
    def __init__(self, versions_dir: Path | str | None = None):
        self.dir = Path(versions_dir) if versions_dir else VERSIONS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def _filename(self, scenario_id: str, version_id: str, timestamp: str) -> Path:
        # Sanitize for filesystem
        ts = timestamp.replace(":", "-").replace("+", "_")[:19]
        return self.dir / f"{scenario_id}__{version_id}__{ts}.json"

    def save(self, result: EvaluationResult) -> Path:
        report = generate_json_report(result)
        path = self._filename(result.scenario.id, result.version_id, result.timestamp)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return path

    def load(self, scenario_id: str, version_id: str) -> dict | None:
        """Load the most recent saved result for a given scenario + version."""
        candidates = sorted(
            self.dir.glob(f"{scenario_id}__{version_id}__*.json"),
            reverse=True,
        )
        if not candidates:
            return None
        with open(candidates[0], encoding="utf-8") as f:
            return json.load(f)

    def list_versions(self, scenario_id: str) -> list[dict]:
        """Return list of saved version metadata for a scenario, sorted newest-first."""
        files = sorted(self.dir.glob(f"{scenario_id}__*.json"), reverse=True)
        results = []
        for f in files:
            parts = f.stem.split("__")
            if len(parts) >= 2:
                results.append({
                    "scenario_id": scenario_id,
                    "version_id": parts[1],
                    "timestamp": parts[2] if len(parts) > 2 else "",
                    "filename": f.name,
                })
        return results

    def list_all_version_ids(self, scenario_id: str) -> list[str]:
        """Return list of unique version IDs for a scenario."""
        seen = []
        for item in self.list_versions(scenario_id):
            vid = item["version_id"]
            if vid not in seen:
                seen.append(vid)
        return seen

    def compare(
        self, scenario_id: str, version_a: str, version_b: str
    ) -> ComparisonResult | None:
        data_a = self.load(scenario_id, version_a)
        data_b = self.load(scenario_id, version_b)

        if not data_a or not data_b:
            return None

        pr_a = data_a.get("principle_results", {})
        pr_b = data_b.get("principle_results", {})

        per_principle_deltas: dict[str, int] = {}
        regressions: list[str] = []
        improvements: list[str] = []

        principles = [f"P{i}" for i in range(1, 11)]
        for p in principles:
            score_a = pr_a.get(p, {}).get("score", 0)
            score_b = pr_b.get(p, {}).get("score", 0)
            delta = score_b - score_a
            per_principle_deltas[p] = delta
            if delta < 0:
                regressions.append(p)
            elif delta > 0:
                improvements.append(p)

        # Violation code diffs
        def get_violation_codes(pr: dict) -> set[str]:
            codes: set[str] = set()
            for p_data in pr.values():
                for v in p_data.get("rule_violations", []):
                    codes.add(v.get("code", ""))
            return codes

        codes_a = get_violation_codes(pr_a)
        codes_b = get_violation_codes(pr_b)
        new_violations = sorted(codes_b - codes_a)
        resolved_violations = sorted(codes_a - codes_b)

        # Risk flag changes
        flags_a = {f["flag"] for f in data_a.get("risk_flags", [])}
        flags_b = {f["flag"] for f in data_b.get("risk_flags", [])}
        risk_flag_changes = {
            "added": sorted(flags_b - flags_a),
            "removed": sorted(flags_a - flags_b),
        }

        # Composite delta
        composite_a = data_a.get("weighted_composite_score", 0.0)
        composite_b = data_b.get("weighted_composite_score", 0.0)
        composite_delta = round(composite_b - composite_a, 2)

        # Human-readable summary
        direction = "improved" if composite_delta > 0 else ("regressed" if composite_delta < 0 else "unchanged")
        summary_parts = [
            f"Version {version_b} {direction} vs {version_a} "
            f"(composite delta: {composite_delta:+.2f})."
        ]
        if improvements:
            summary_parts.append(f"Improvements in: {', '.join(improvements)}.")
        if regressions:
            summary_parts.append(f"Regressions in: {', '.join(regressions)}.")
        if new_violations:
            summary_parts.append(f"New violations: {', '.join(new_violations[:5])}.")
        if resolved_violations:
            summary_parts.append(f"Resolved violations: {', '.join(resolved_violations[:5])}.")
        if risk_flag_changes["added"]:
            summary_parts.append(f"⚠️ New risk flags: {', '.join(risk_flag_changes['added'])}.")
        if risk_flag_changes["removed"]:
            summary_parts.append(f"✅ Cleared risk flags: {', '.join(risk_flag_changes['removed'])}.")

        return ComparisonResult(
            scenario_id=scenario_id,
            version_a=version_a,
            version_b=version_b,
            composite_delta=composite_delta,
            per_principle_deltas=per_principle_deltas,
            regressions=regressions,
            improvements=improvements,
            new_violations=new_violations,
            resolved_violations=resolved_violations,
            risk_flag_changes=risk_flag_changes,
            summary=" ".join(summary_parts),
        )
