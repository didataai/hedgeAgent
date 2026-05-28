"""
File: hedge_lab/analysis/compare_strategy_memories.py

Purpose:
    Compare dynamic Strategy Learning Summary files across two or more strategies.

Inputs:
    - Strategy memory files:
        datasets/strategies/<STRATEGY_ID>/_memory/strategy_learning_summary.json
    - CLI arguments:
        --strategy-ids
        --datasets-root
        --output-dir
        --comparison-id

Outputs:
    - JSON comparison:
        datasets/strategy_comparisons/<COMPARISON_ID>/comparison.json
    - Markdown comparison:
        datasets/strategy_comparisons/<COMPARISON_ID>/comparison.md

Integrations:
    - Consumes outputs from hedge_lab.analysis.build_strategy_learning_summary.
    - Feeds future orchestrator, RAG, LLM agents and strategy selection logic.
    - Works with multi-asset and multi-timeframe strategy memories.

Notes:
    - Must work on Windows and Linux.
    - Does not run simulations.
    - Does not mutate strategies.
    - Does not require all strategies to have the same schema fields.
    - Intended as the first official strategy-vs-strategy analytical layer.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class StrategyMemory:
    """Loaded strategy memory file."""

    strategy_id: str
    path: Path
    payload: dict[str, Any]


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Compare strategy learning memories.")
    parser.add_argument(
        "--strategy-ids",
        nargs="+",
        required=True,
        help="Strategy IDs to compare, e.g. P1_NET_V0 P1_MULTIPLIER_V0.",
    )
    parser.add_argument(
        "--datasets-root",
        default="datasets/strategies",
        help="Root directory containing strategy datasets.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/strategy_comparisons",
        help="Root directory for strategy comparison outputs.",
    )
    parser.add_argument(
        "--comparison-id",
        default=None,
        help="Optional comparison ID. Defaults to STRATEGY_A__vs__STRATEGY_B.",
    )
    return parser


def load_strategy_memory(datasets_root: Path, strategy_id: str) -> StrategyMemory:
    """Load one strategy memory file."""

    memory_path = datasets_root / safe_path_component(strategy_id) / "_memory" / "strategy_learning_summary.json"
    if not memory_path.exists():
        raise FileNotFoundError(
            f"Strategy memory not found for {strategy_id}: {memory_path}. "
            "Run build_strategy_learning_summary first."
        )

    payload = json.loads(memory_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid memory payload for {strategy_id}: {memory_path}")

    return StrategyMemory(strategy_id=strategy_id, path=memory_path, payload=payload)


def compare_memories(memories: list[StrategyMemory]) -> dict[str, Any]:
    """Build comparison payload."""

    now = datetime.now(timezone.utc).isoformat()
    rows = [strategy_scorecard(memory) for memory in memories]
    rankings = build_rankings(rows)
    winner = choose_winner(rows, rankings)

    return {
        "schema_version": "strategy_memory_comparison.v0",
        "generated_at_utc": now,
        "strategy_ids": [memory.strategy_id for memory in memories],
        "memory_files": {
            memory.strategy_id: normalize_path(memory.path)
            for memory in memories
        },
        "scorecards": rows,
        "rankings": rankings,
        "winner": winner,
        "interpretation": build_interpretation(rows=rows, rankings=rankings, winner=winner),
        "next_actions": build_next_actions(rows=rows, winner=winner),
    }


def strategy_scorecard(memory: StrategyMemory) -> dict[str, Any]:
    """Extract comparable fields from a strategy memory."""

    payload = memory.payload
    best = payload.get("best_known_genetic_result") or {}
    risk = payload.get("risk_observations") or {}
    regime = payload.get("regime_observations") or {}
    monte = payload.get("monte_carlo_observations") or {}

    score = as_float(best.get("score"))
    base_score = as_float(best.get("base_score"))
    regime_adjusted_score = as_float(best.get("regime_adjusted_score"))
    survival_rate_pct = as_float(best.get("survival_rate_pct"))
    worst_drawdown_pct = as_float(best.get("worst_max_drawdown_pct"))
    worst_gross_lots = as_float(best.get("worst_max_gross_lots"))
    worst_positions = as_float(best.get("worst_max_positions"))
    worst_risk_debt = as_float(best.get("worst_final_risk_debt"))
    avg_rebalance_count = as_float(best.get("avg_rebalance_count"))
    avg_protection_blocks = as_float(best.get("avg_protection_blocks"))
    regime_std = as_float(best.get("regime_score_stddev"))

    derived_score = calculate_decision_score(
        score=score,
        survival_rate_pct=survival_rate_pct,
        worst_drawdown_pct=worst_drawdown_pct,
        worst_gross_lots=worst_gross_lots,
        worst_positions=worst_positions,
        worst_risk_debt=worst_risk_debt,
        avg_rebalance_count=avg_rebalance_count,
        regime_std=regime_std,
    )

    return {
        "strategy_id": memory.strategy_id,
        "family": payload.get("strategy_family"),
        "version": payload.get("strategy_version"),
        "records_found": payload.get("records_found"),
        "available_assets": payload.get("available_assets", []),
        "available_timeframes": payload.get("available_timeframes", []),
        "experiments_found": payload.get("experiments_found", {}),
        "decision_score_v0": derived_score,
        "best_known_score": score,
        "base_score": base_score,
        "regime_adjusted_score": regime_adjusted_score,
        "survival_rate_pct": survival_rate_pct,
        "worst_max_drawdown_pct": worst_drawdown_pct,
        "worst_max_gross_lots": worst_gross_lots,
        "worst_max_positions": worst_positions,
        "worst_final_risk_debt": worst_risk_debt,
        "avg_rebalance_count": avg_rebalance_count,
        "avg_protection_blocks": avg_protection_blocks,
        "regime_score_stddev": regime_std,
        "best_regime": best.get("best_regime"),
        "best_regime_score": best.get("best_regime_score"),
        "worst_regime": best.get("worst_regime"),
        "worst_regime_score": best.get("worst_regime_score"),
        "best_genome": best.get("genome"),
        "risk_observations": risk,
        "regime_observations": regime,
        "monte_carlo_labels_found": monte.get("labels_found", []),
        "current_interpretation": payload.get("current_interpretation"),
    }


def calculate_decision_score(
    *,
    score: Optional[float],
    survival_rate_pct: Optional[float],
    worst_drawdown_pct: Optional[float],
    worst_gross_lots: Optional[float],
    worst_positions: Optional[float],
    worst_risk_debt: Optional[float],
    avg_rebalance_count: Optional[float],
    regime_std: Optional[float],
) -> float:
    """
    Calculate a simple comparable decision score.

    The raw strategy score is still preserved. This decision score adds explicit penalties
    for risk debt, gross expansion, inactivity and regime imbalance.
    """

    value = score if score is not None else 0.0

    if survival_rate_pct is not None:
        value += (survival_rate_pct - 95.0) * 0.50

    if worst_drawdown_pct is not None:
        value -= worst_drawdown_pct * 4.0

    if worst_gross_lots is not None:
        value -= worst_gross_lots * 20.0

    if worst_positions is not None:
        value -= worst_positions * 0.50

    if worst_risk_debt is not None:
        value -= worst_risk_debt * 0.03

    if avg_rebalance_count is not None:
        if avg_rebalance_count < 1.0:
            value -= (1.0 - avg_rebalance_count) * 12.0
        elif avg_rebalance_count > 6.0:
            value -= (avg_rebalance_count - 6.0) * 2.0

    if regime_std is not None:
        value -= regime_std * 0.35

    return round(value, 6)


def build_rankings(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build rankings for key metrics."""

    metrics = {
        "decision_score_v0": "desc",
        "best_known_score": "desc",
        "survival_rate_pct": "desc",
        "worst_max_drawdown_pct": "asc",
        "worst_max_gross_lots": "asc",
        "worst_max_positions": "asc",
        "worst_final_risk_debt": "asc",
        "avg_rebalance_count": "desc",
        "regime_score_stddev": "asc",
    }

    rankings: dict[str, list[dict[str, Any]]] = {}
    for metric, direction in metrics.items():
        rankings[metric] = rank_rows(rows=rows, metric=metric, direction=direction)

    return rankings


def choose_winner(rows: list[dict[str, Any]], rankings: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Choose a practical winner based on decision_score_v0."""

    ranked = rankings.get("decision_score_v0", [])
    if not ranked:
        return {
            "strategy_id": None,
            "reason": "No comparable strategy score available.",
        }

    top = ranked[0]
    return {
        "strategy_id": top["strategy_id"],
        "decision_score_v0": top["value"],
        "reason": (
            "Highest decision_score_v0 after considering raw score, survival, drawdown, "
            "gross exposure, position count, risk debt, activity and regime balance."
        ),
    }


def rank_rows(rows: list[dict[str, Any]], metric: str, direction: str) -> list[dict[str, Any]]:
    """Rank scorecards by one metric."""

    valid_rows = [
        row for row in rows
        if as_float(row.get(metric)) is not None and not math.isnan(float(row.get(metric)))
    ]

    reverse = direction == "desc"
    valid_rows.sort(key=lambda row: float(row.get(metric)), reverse=reverse)

    return [
        {
            "rank": index + 1,
            "strategy_id": row["strategy_id"],
            "value": row.get(metric),
        }
        for index, row in enumerate(valid_rows)
    ]


def build_interpretation(
    rows: list[dict[str, Any]],
    rankings: dict[str, list[dict[str, Any]]],
    winner: dict[str, Any],
) -> str:
    """Build high-level interpretation for humans/agents."""

    if not rows:
        return "No strategies were compared."

    winner_id = winner.get("strategy_id")
    if not winner_id:
        return "No winner could be selected because comparable metrics were missing."

    parts = [
        f"The current comparison winner is {winner_id} by decision_score_v0.",
    ]

    risk_rank = rankings.get("worst_final_risk_debt", [])
    gross_rank = rankings.get("worst_max_gross_lots", [])
    activity_rank = rankings.get("avg_rebalance_count", [])

    if risk_rank:
        parts.append(f"Lowest risk debt currently belongs to {risk_rank[0]['strategy_id']}.")
    if gross_rank:
        parts.append(f"Lowest gross exposure currently belongs to {gross_rank[0]['strategy_id']}.")
    if activity_rank:
        parts.append(f"Highest activity currently belongs to {activity_rank[0]['strategy_id']}.")

    parts.append(
        "This comparison is not a production promotion decision. It is an analytical layer "
        "to guide the next simulations, genetic runs and strategy mutations."
    )

    return " ".join(parts)


def build_next_actions(rows: list[dict[str, Any]], winner: dict[str, Any]) -> list[str]:
    """Build recommended next actions."""

    actions = [
        "Run larger Monte Carlo batches for all compared strategies using the same asset/timeframe.",
        "Run larger genetic searches for all compared strategies with identical runs, steps and seeds.",
        "Add historical data validation after synthetic behavior is understood.",
        "Compare strategies per regime instead of only aggregate score.",
    ]

    for row in rows:
        strategy_id = row["strategy_id"]
        avg_rebalance = as_float(row.get("avg_rebalance_count"))
        risk_debt = as_float(row.get("worst_final_risk_debt"))
        worst_gross = as_float(row.get("worst_max_gross_lots"))

        if avg_rebalance is not None and avg_rebalance < 1.0:
            actions.append(f"{strategy_id}: increase activity pressure or test smaller range_points.")

        if risk_debt is not None and risk_debt > 200:
            actions.append(f"{strategy_id}: add stronger risk_debt penalty or recovery logic.")

        if worst_gross is not None and worst_gross > 0.50:
            actions.append(f"{strategy_id}: test stricter gross exposure protection.")

    winner_id = winner.get("strategy_id")
    if winner_id:
        actions.append(f"Use {winner_id} as current reference baseline, not as final production strategy.")

    return dedupe_preserve_order(actions)


def write_outputs(
    comparison: dict[str, Any],
    output_root: Path,
    comparison_id: str,
) -> tuple[Path, Path]:
    """Write comparison JSON and Markdown."""

    output_dir = output_root / safe_path_component(comparison_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "comparison.json"
    md_path = output_dir / "comparison.md"

    json_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(comparison), encoding="utf-8")

    return json_path, md_path


def render_markdown(comparison: dict[str, Any]) -> str:
    """Render Markdown comparison."""

    lines = [
        f"# Strategy Comparison — {' vs '.join(comparison.get('strategy_ids', []))}",
        "",
        "## Identity",
        "",
        f"- Schema: `{comparison.get('schema_version')}`",
        f"- Generated UTC: `{comparison.get('generated_at_utc')}`",
        "",
        "## Winner",
        "",
        f"- Strategy: `{comparison.get('winner', {}).get('strategy_id')}`",
        f"- Decision score: `{comparison.get('winner', {}).get('decision_score_v0')}`",
        f"- Reason: {comparison.get('winner', {}).get('reason')}",
        "",
        "## Scorecards",
        "",
        "| Strategy | Decision Score | Raw Score | Survival % | Worst DD % | Worst Gross | Worst Pos | Worst Risk Debt | Avg Rebalance | Regime Std | Worst Regime | Best Regime |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for row in comparison.get("scorecards", []):
        lines.append(
            "| "
            f"{row.get('strategy_id')} | "
            f"{fmt(row.get('decision_score_v0'))} | "
            f"{fmt(row.get('best_known_score'))} | "
            f"{fmt(row.get('survival_rate_pct'))} | "
            f"{fmt(row.get('worst_max_drawdown_pct'))} | "
            f"{fmt(row.get('worst_max_gross_lots'))} | "
            f"{fmt(row.get('worst_max_positions'))} | "
            f"{fmt(row.get('worst_final_risk_debt'))} | "
            f"{fmt(row.get('avg_rebalance_count'))} | "
            f"{fmt(row.get('regime_score_stddev'))} | "
            f"{row.get('worst_regime')} | "
            f"{row.get('best_regime')} |"
        )

    lines.extend(
        [
            "",
            "## Rankings",
            "",
        ]
    )

    for metric, ranking in comparison.get("rankings", {}).items():
        lines.append(f"### {metric}")
        lines.append("")
        for item in ranking:
            lines.append(f"- #{item.get('rank')} `{item.get('strategy_id')}`: `{item.get('value')}`")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            str(comparison.get("interpretation", "")),
            "",
            "## Next Actions",
            "",
        ]
    )

    for action in comparison.get("next_actions", []):
        lines.append(f"- {action}")

    lines.extend(["", "## Memory Files", ""])
    for strategy_id, path in comparison.get("memory_files", {}).items():
        lines.append(f"- `{strategy_id}`: `{path}`")

    lines.append("")
    return "\n".join(lines)


def fmt(value: Any) -> str:
    """Format table value."""

    numeric = as_float(value)
    if numeric is None:
        return ""
    return f"{numeric:.4f}"


def as_float(value: Any) -> Optional[float]:
    """Convert value to float."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    """Dedupe list while preserving order."""

    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def default_comparison_id(strategy_ids: list[str]) -> str:
    """Build default comparison ID."""

    return "__vs__".join(strategy_ids)


def safe_path_component(value: str) -> str:
    """Return filesystem-safe path component."""

    cleaned = value.strip().replace("\\", "_").replace("/", "_").replace(" ", "_")
    return cleaned or "UNKNOWN"


def normalize_path(path: Path) -> str:
    """Return portable path string."""

    return str(path).replace("\\", "/")


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    strategy_ids = [item.strip() for item in args.strategy_ids if item.strip()]
    if len(strategy_ids) < 2:
        raise SystemExit("Provide at least two strategy IDs to compare.")

    datasets_root = Path(args.datasets_root)
    output_root = Path(args.output_dir)
    comparison_id = args.comparison_id or default_comparison_id(strategy_ids)

    memories = [
        load_strategy_memory(datasets_root=datasets_root, strategy_id=strategy_id)
        for strategy_id in strategy_ids
    ]

    comparison = compare_memories(memories)
    json_path, md_path = write_outputs(
        comparison=comparison,
        output_root=output_root,
        comparison_id=comparison_id,
    )

    print("=== HEDGE EVOLUTION LAB — STRATEGY MEMORY COMPARISON V0 ===")
    print(f"strategies: {', '.join(strategy_ids)}")
    print(f"winner: {comparison.get('winner', {}).get('strategy_id')}")
    print(f"json: {json_path}")
    print(f"markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
