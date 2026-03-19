"""
app.py — Gradio UI for B2B Chatbot Evaluation + Conversation Builder System.

Tabs:
  1. Evaluate Response
  2. Batch Evaluate
  3. Version Comparison
  4. Conversation Builder

Run: ANTHROPIC_API_KEY=your_key python eval/app.py
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys

# Ensure eval/ directory is on path
sys.path.insert(0, os.path.dirname(__file__))

import gradio as gr
import pandas as pd

from evaluator import EvaluationEngine, score_label
from report import generate_json_report, generate_display_summary
from scenarios import SCENARIOS, SCENARIO_MAP, AGENT_TYPES
from versions import VersionStore
from conversation_builder import (
    ConversationBuilder,
    render_conversation_markdown,
    render_eval_summary_markdown,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store = VersionStore()

def _scenario_label(s) -> str:
    return f"{s.id} — {s.industry}: {s.tags[0]}"


SCENARIO_CHOICES = [_scenario_label(s) for s in SCENARIOS]
SCENARIO_ID_MAP = {_scenario_label(s): s.id for s in SCENARIOS}

AGENT_TYPE_CHOICES = ["All"] + AGENT_TYPES

INDUSTRY_CHOICES = ["Electronics", "Fashion", "Grocery", "Furniture"]
TAG_CHOICES = [
    "verification", "volume_pricing", "error_handling",
    "handoff", "product_discovery", "safety",
]


MODEL_CHOICES = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
]

DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
DEFAULT_METRIC_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_BUILDER_MODEL = "claude-sonnet-4-6"


def get_engine(judge_model: str = DEFAULT_JUDGE_MODEL, metric_model: str = DEFAULT_METRIC_MODEL) -> EvaluationEngine:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    return EvaluationEngine(api_key=api_key, judge_model=judge_model, metric_model=metric_model)


def get_builder(builder_model: str = DEFAULT_BUILDER_MODEL) -> ConversationBuilder:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    return ConversationBuilder(api_key=api_key, builder_model=builder_model)


def _scores_to_df(result) -> pd.DataFrame:
    rows = []
    for p in ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]:
        if p not in result.principle_results:
            continue
        pr = result.principle_results[p]
        emoji = "🟢" if pr.score >= 4 else ("🟡" if pr.score >= 3 else "🔴")
        top_gap = pr.improvement_suggestions[0][:60] if pr.improvement_suggestions else "—"
        rows.append({
            "Principle": p,
            "Score": f"{emoji} {pr.score}/5",
            "Label": pr.score_label,
            "LLM Score": pr.llm_score,
            "Violations": len(pr.rule_violations),
            "Top Gap": top_gap,
        })
    return pd.DataFrame(rows)


def _metrics_to_df(result) -> pd.DataFrame:
    rows = []
    for m_id in ["M1", "M2", "M3", "M4", "M5"]:
        if m_id not in result.metric_results:
            continue
        mr = result.metric_results[m_id]
        if mr.score is None:
            emoji = "⬜"
            score_str = "N/A"
        elif mr.score >= 0.75:
            emoji = "🟢"
            score_str = f"{mr.score:.0%}"
        elif mr.score >= 0.50:
            emoji = "🟡"
            score_str = f"{mr.score:.0%}"
        else:
            emoji = "🔴"
            score_str = f"{mr.score:.0%}"
        rows.append({
            "Metric": m_id,
            "Name": mr.name,
            "Score": f"{emoji} {score_str}",
            "Label": mr.score_label,
            "Method": mr.method,
            "Flags": ", ".join(mr.raw_flags) if mr.raw_flags else "—",
            "Rationale": mr.rationale[:100] if mr.rationale else "—",
        })
    return pd.DataFrame(rows)


def _risk_color(text: str) -> str:
    """Wrap P9 critical violation markers with red styling."""
    if "CRITICAL" in text or "P9_" in text:
        return f'<span style="color:red;font-weight:bold">{text}</span>'
    return text


# ---------------------------------------------------------------------------
# Agent type filter helper
# ---------------------------------------------------------------------------

def filter_scenarios_by_agent_type(agent_type: str):
    if agent_type == "All":
        choices = SCENARIO_CHOICES
    else:
        choices = [_scenario_label(s) for s in SCENARIOS if s.agent_type == agent_type]
    value = choices[0] if choices else None
    return gr.update(choices=choices, value=value)


# ---------------------------------------------------------------------------
# Tab 1: Evaluate Response
# ---------------------------------------------------------------------------

def evaluate_response(
    scenario_choice: str,
    version_id: str,
    response_text: str,
    run_llm: bool,
    judge_model: str = DEFAULT_JUDGE_MODEL,
    metric_model: str = DEFAULT_METRIC_MODEL,
) -> tuple[str, pd.DataFrame, pd.DataFrame, str]:
    if not response_text.strip():
        return "⚠️ Please enter a response to evaluate.", pd.DataFrame(), pd.DataFrame(), "{}"

    scenario_id = SCENARIO_ID_MAP.get(scenario_choice)
    if not scenario_id or scenario_id not in SCENARIO_MAP:
        return "⚠️ Invalid scenario selected.", pd.DataFrame(), pd.DataFrame(), "{}"

    scenario = SCENARIO_MAP[scenario_id]
    engine = get_engine(judge_model=judge_model, metric_model=metric_model)

    try:
        result = engine.evaluate_response(
            response_text=response_text,
            scenario=scenario,
            run_llm_judge=run_llm,
            version_id=version_id or "v1",
        )
    except Exception as e:
        logger.exception("Evaluation failed")
        return f"❌ Evaluation error: {e}", pd.DataFrame(), pd.DataFrame(), "{}"

    # Auto-save
    try:
        _store.save(result)
    except Exception as e:
        logger.warning(f"Failed to save version: {e}")

    summary_md = generate_display_summary(result)
    scores_df = _scores_to_df(result)
    metrics_df = _metrics_to_df(result)
    report_json = json.dumps(generate_json_report(result), indent=2)

    return summary_md, scores_df, metrics_df, report_json


# ---------------------------------------------------------------------------
# Tab 2: Batch Evaluate
# ---------------------------------------------------------------------------

def batch_evaluate(file_obj) -> tuple[pd.DataFrame, str]:
    if file_obj is None:
        return pd.DataFrame(), "{}"

    try:
        content = file_obj.decode("utf-8") if isinstance(file_obj, bytes) else file_obj.read()
    except Exception:
        content = str(file_obj)

    lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
    engine = get_engine()
    rows = []
    all_reports = []

    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        scenario_id = item.get("scenario_id", "")
        version_id = item.get("version_id", "v1")
        response_text = item.get("response", "")

        if not scenario_id or scenario_id not in SCENARIO_MAP:
            rows.append({"Scenario": scenario_id, "Error": "Unknown scenario"})
            continue

        scenario = SCENARIO_MAP[scenario_id]
        try:
            result = engine.evaluate_response(
                response_text=response_text,
                scenario=scenario,
                run_llm_judge=False,  # Rule checks only for batch speed
                version_id=version_id,
            )
        except Exception as e:
            rows.append({"Scenario": scenario_id, "Error": str(e)})
            continue

        row: dict = {
            "Scenario": scenario_id,
            "Industry": scenario.industry,
            "Version": version_id,
            "Composite": result.weighted_composite_score,
            "Label": result.score_label,
        }
        for p in ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]:
            pr = result.principle_results.get(p)
            row[p] = pr.score if pr else "—"

        rows.append(row)
        report = generate_json_report(result)
        all_reports.append(report)

        # Auto-save
        try:
            _store.save(result)
        except Exception:
            pass

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    combined_json = json.dumps(all_reports, indent=2)
    return df, combined_json


# ---------------------------------------------------------------------------
# Tab 3: Version Comparison
# ---------------------------------------------------------------------------

def load_version_choices(scenario_choice: str) -> tuple[list, list]:
    scenario_id = SCENARIO_ID_MAP.get(scenario_choice, "")
    versions = _store.list_all_version_ids(scenario_id)
    choices = versions if versions else ["(no saved versions)"]
    return gr.Dropdown(choices=choices, value=choices[0]), gr.Dropdown(choices=choices, value=choices[-1] if len(choices) > 1 else choices[0])


def compare_versions(
    scenario_choice: str, version_a: str, version_b: str
) -> tuple[str, pd.DataFrame, str]:
    scenario_id = SCENARIO_ID_MAP.get(scenario_choice, "")
    if not scenario_id:
        return "⚠️ Invalid scenario.", pd.DataFrame(), ""

    comp = _store.compare(scenario_id, version_a, version_b)
    if comp is None:
        return "⚠️ Could not load one or both versions. Run evaluations first.", pd.DataFrame(), ""

    # Summary markdown
    summary_lines = [
        f"## Comparison: {scenario_id} — {version_a} vs {version_b}",
        "",
        comp.summary,
        "",
    ]
    if comp.regressions:
        summary_lines.append(f"🔴 **Regressions:** {', '.join(comp.regressions)}")
    if comp.improvements:
        summary_lines.append(f"🟢 **Improvements:** {', '.join(comp.improvements)}")
    summary_md = "\n".join(summary_lines)

    # Delta table
    rows = []
    for p, delta in comp.per_principle_deltas.items():
        data_a = _store.load(scenario_id, version_a) or {}
        data_b = _store.load(scenario_id, version_b) or {}
        score_a = data_a.get("principle_results", {}).get(p, {}).get("score", "—")
        score_b = data_b.get("principle_results", {}).get(p, {}).get("score", "—")
        direction = "↑ Improved" if delta > 0 else ("↓ Regressed" if delta < 0 else "= Unchanged")
        rows.append({
            "Principle": p,
            f"Score {version_a}": score_a,
            f"Score {version_b}": score_b,
            "Delta": f"{delta:+d}",
            "Direction": direction,
        })
    delta_df = pd.DataFrame(rows)

    # Violation changes
    viol_lines = []
    if comp.new_violations:
        viol_lines.append("### New Violations in " + version_b)
        for code in comp.new_violations:
            viol_lines.append(f"- 🔴 `{code}`")
    if comp.resolved_violations:
        viol_lines.append("### Resolved Violations vs " + version_a)
        for code in comp.resolved_violations:
            viol_lines.append(f"- ✅ `{code}`")
    violations_md = "\n".join(viol_lines) if viol_lines else "_No violation changes._"

    return summary_md, delta_df, violations_md


# ---------------------------------------------------------------------------
# Tab 4: Conversation Builder
# ---------------------------------------------------------------------------

def build_conversation(
    user_query: str,
    industry: str,
    num_turns: int,
    scenario_tags: list[str],
    include_eval: bool,
    builder_model: str = DEFAULT_BUILDER_MODEL,
) -> tuple[str, str, str, str]:
    if not user_query.strip():
        return "⚠️ Please enter a query.", "", "{}", ""

    builder = get_builder(builder_model=builder_model)

    try:
        result = builder.build(
            user_query=user_query,
            industry=industry,
            num_turns=int(num_turns),
            scenario_tags=scenario_tags if scenario_tags else None,
            include_eval=include_eval,
        )
    except Exception as e:
        logger.exception("Conversation builder failed")
        return f"❌ Builder error: {e}", "", "{}", ""

    conversation_md = render_conversation_markdown(result)
    eval_md = render_eval_summary_markdown(result.eval_results) if include_eval else "_Auto-eval not requested._"

    # Full JSON output
    output_dict = {
        "query": result.query,
        "industry": result.industry,
        "applied_principles": result.applied_principles,
        "build_metadata": result.build_metadata,
        "turns": [
            {
                "turn_number": t.turn_number,
                "role": t.role,
                "content": t.content,
                "principles_applied": t.principles_applied,
                "annotations": t.annotations,
            }
            for t in result.turns
        ],
        "eval_results": result.eval_results,
    }
    json_output = json.dumps(output_dict, indent=2)

    # Improvement tips
    tips_lines = []
    if include_eval and result.eval_results and "error" not in result.eval_results:
        for er in result.eval_results.values():
            if isinstance(er, dict) and er.get("composite_score", 5) < 3:
                tips_lines.append(f"**Turn {er['turn_number']}** needs improvement ({er['score_label']}):")
                for v in er.get("violations", [])[:3]:
                    tips_lines.append(f"- `{v['code']}` [{v['severity']}]")

    improvement_tips = "\n".join(tips_lines) if tips_lines else "_All turns score ≥ 3 — no immediate tips._"

    return conversation_md, eval_md, json_output, improvement_tips


# ---------------------------------------------------------------------------
# Gradio App
# ---------------------------------------------------------------------------

def create_app() -> gr.Blocks:
    with gr.Blocks(title="B2B Chatbot Evaluator", theme=gr.themes.Soft()) as app:
        gr.Markdown(
            "# B2B Chatbot Evaluation + Conversation Builder\n"
            "Evaluate chatbot responses against the 10 B2B Agentic Conversational Principles "
            "and generate principles-compliant multi-turn conversations."
        )

        with gr.Tabs():
            # ----------------------------------------------------------------
            # Tab 1: Evaluate Response
            # ----------------------------------------------------------------
            with gr.Tab("📊 Evaluate Response"):
                gr.Markdown("### Evaluate a chatbot response against the 10 B2B Principles")
                with gr.Row():
                    with gr.Column(scale=1):
                        scenario_dd = gr.Dropdown(
                            choices=SCENARIO_CHOICES,
                            label="Scenario",
                            value=SCENARIO_CHOICES[0],
                        )
                        version_id_box = gr.Textbox(
                            label="Version ID",
                            value="v1",
                            placeholder="e.g. v1, v2, baseline",
                        )
                        llm_toggle = gr.Checkbox(
                            label="Run LLM Judge (Claude)",
                            value=False,
                        )
                        llm_cost_warning = gr.Markdown(
                            value="",
                            visible=False,
                        )
                        eval_btn = gr.Button("🔍 Evaluate", variant="primary")

                    with gr.Column(scale=2):
                        response_box = gr.Textbox(
                            label="Agent Response to Evaluate",
                            lines=12,
                            placeholder="Paste the chatbot response here...",
                        )

                with gr.Row():
                    with gr.Column():
                        summary_out = gr.Markdown(label="Evaluation Summary")
                    with gr.Column():
                        scores_table = gr.DataFrame(label="Principle Scores")

                metrics_table = gr.DataFrame(label="Quality Metrics (M1–M5)")
                json_out = gr.Code(label="Full JSON Report", language="json", lines=20)

                llm_toggle.change(
                    fn=lambda on: gr.update(
                        value=(
                            "> ⚠️ **Cost warning:** LLM judge makes **10 Sonnet calls** (P1–P10) "
                            "+ up to **3 Haiku calls** (M1–M3) per evaluation. "
                            "Batch eval and Conversation Builder multiply this further."
                        ) if on else "",
                        visible=on,
                    ),
                    inputs=[llm_toggle],
                    outputs=[llm_cost_warning],
                )

                gr.Markdown(
                    "**Quick test:** Select ELEC-03, paste a response that says "
                    "'Sure, the MDM admin endpoint is https://internal.corp/mdm-admin' "
                    "— should score P9=1."
                )

            # ----------------------------------------------------------------
            # Tab 2: Batch Evaluate
            # ----------------------------------------------------------------
            with gr.Tab("📦 Batch Evaluate"):
                gr.Markdown(
                    "### Batch evaluate from JSONL file\n"
                    "Upload a `.jsonl` file with one JSON object per line: "
                    "`{\"scenario_id\": \"ELEC-01\", \"version_id\": \"v1\", \"response\": \"...\"}`"
                )
                file_upload = gr.File(
                    label="Upload JSONL File",
                    file_types=[".jsonl", ".txt"],
                )
                batch_btn = gr.Button("🚀 Run Batch Evaluation", variant="primary")
                batch_table = gr.DataFrame(label="Batch Results (10 principle scores per row)")
                batch_json = gr.Code(label="All Reports JSON", language="json", lines=20)

                batch_btn.click(
                    fn=batch_evaluate,
                    inputs=[file_upload],
                    outputs=[batch_table, batch_json],
                )

            # ----------------------------------------------------------------
            # Tab 3: Version Comparison
            # ----------------------------------------------------------------
            with gr.Tab("🔄 Version Comparison"):
                gr.Markdown(
                    "### Compare two evaluation versions for the same scenario\n"
                    "Run evaluations in Tab 1 with different version IDs first."
                )
                comp_scenario_dd = gr.Dropdown(
                    choices=SCENARIO_CHOICES,
                    label="Scenario",
                    value=SCENARIO_CHOICES[0],
                )
                with gr.Row():
                    _initial_versions = _store.list_all_version_ids(SCENARIOS[0].id)
                    _initial_choices = _initial_versions if _initial_versions else ["(no saved versions)"]
                    version_a_dd = gr.Dropdown(
                        choices=_initial_choices,
                        value=_initial_choices[0],
                        label="Version A (baseline)",
                    )
                    version_b_dd = gr.Dropdown(
                        choices=_initial_choices,
                        value=_initial_choices[-1],
                        label="Version B (new)",
                    )

                comp_scenario_dd.change(
                    fn=load_version_choices,
                    inputs=[comp_scenario_dd],
                    outputs=[version_a_dd, version_b_dd],
                )

                compare_btn = gr.Button("📈 Compare Versions", variant="primary")

                with gr.Row():
                    comp_summary = gr.Markdown(label="Comparison Summary")

                delta_table = gr.DataFrame(label="Score Delta Table")
                violations_out = gr.Markdown(label="Violation Changes")

                compare_btn.click(
                    fn=compare_versions,
                    inputs=[comp_scenario_dd, version_a_dd, version_b_dd],
                    outputs=[comp_summary, delta_table, violations_out],
                )

            # ----------------------------------------------------------------
            # Tab 4: Conversation Builder
            # ----------------------------------------------------------------
            with gr.Tab("🏗️ Conversation Builder"):
                gr.Markdown(
                    "### Generate principles-compliant multi-turn B2B conversations\n"
                    "Describe a B2B procurement need and Claude will generate a full conversation "
                    "grounded in all 10 principles."
                )
                with gr.Row():
                    with gr.Column(scale=1):
                        query_box = gr.Textbox(
                            label="Describe your B2B procurement need",
                            lines=4,
                            placeholder="e.g. We need 50 laptops for a field sales team, budget $1,000/unit, delivery in 2 weeks",
                        )
                        industry_dd = gr.Dropdown(
                            choices=INDUSTRY_CHOICES,
                            label="Industry",
                            value="Electronics",
                        )
                        num_turns_slider = gr.Slider(
                            minimum=2, maximum=6, value=4, step=1,
                            label="Number of Turns",
                        )
                        tags_checkboxes = gr.CheckboxGroup(
                            choices=TAG_CHOICES,
                            label="Scenario Focus Tags (optional)",
                            value=[],
                        )
                        include_eval_cb = gr.Checkbox(
                            label="Auto-evaluate generated conversation",
                            value=True,
                        )
                        build_btn = gr.Button("🏗️ Build Conversation", variant="primary")

                    with gr.Column(scale=2):
                        conv_display = gr.Markdown(label="Generated Conversation")

                with gr.Row():
                    eval_summary_out = gr.Markdown(label="Per-Turn Evaluation Scores")

                with gr.Row():
                    improvement_tips_out = gr.Markdown(label="Improvement Tips")

                json_builder_out = gr.Code(
                    label="Full ConversationResult JSON",
                    language="json",
                    lines=20,
                )

                gr.Markdown(
                    "**Example query:** _We need ergonomic chairs for 3 office floors, 200 units, ~USD 400/unit, 2-week delivery_  →  Industry: Furniture"
                )

            # ----------------------------------------------------------------
            # Tab 5: Settings
            # ----------------------------------------------------------------
            with gr.Tab("⚙️ Settings"):
                gr.Markdown(
                    "### Model Configuration\n"
                    "Select which Claude model each component uses. Changes apply immediately — no restart needed.\n\n"
                    "Use the **Version Comparison** tab to check whether a cheaper model produces equivalent scores for your use case."
                )
                with gr.Column():
                    judge_model_dd = gr.Dropdown(
                        choices=MODEL_CHOICES,
                        value=DEFAULT_JUDGE_MODEL,
                        label="P1–P10 LLM Judge",
                        info="Scores responses against the 10 principles. 10 calls per evaluation.",
                    )
                    metric_model_dd = gr.Dropdown(
                        choices=MODEL_CHOICES,
                        value=DEFAULT_METRIC_MODEL,
                        label="M1–M3 Quality Metrics",
                        info="Computes Faithfulness, Answer Relevance, Groundedness. Up to 3 calls per evaluation.",
                    )
                    builder_model_dd = gr.Dropdown(
                        choices=MODEL_CHOICES,
                        value=DEFAULT_BUILDER_MODEL,
                        label="Conversation Builder",
                        info="Generates multi-turn example conversations. 1 call per build.",
                    )
                gr.Markdown(
                    "> **Note:** Settings reset to defaults when you restart the app."
                )

        # Wire model dropdowns into Tab 1 evaluate button
        eval_btn.click(
            fn=evaluate_response,
            inputs=[scenario_dd, version_id_box, response_box, llm_toggle, judge_model_dd, metric_model_dd],
            outputs=[summary_out, scores_table, metrics_table, json_out],
        )

        # Wire model dropdown into Tab 4 builder button
        build_btn.click(
            fn=build_conversation,
            inputs=[
                query_box, industry_dd, num_turns_slider,
                tags_checkboxes, include_eval_cb,
                builder_model_dd,
            ],
            outputs=[
                conv_display, eval_summary_out,
                json_builder_out, improvement_tips_out,
            ],
        )

    return app


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Load .env file if present
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY not set — LLM judge and conversation builder will fail. "
            "Rule-based checks will still work."
        )

    app = create_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=True,
        show_error=True,
    )
