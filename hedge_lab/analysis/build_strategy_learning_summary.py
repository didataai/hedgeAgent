"""
File: hedge_lab/analysis/build_strategy_learning_summary.py

Purpose:
    Build a dynamic Strategy Learning Summary from strategy-aware datasets.

Inputs:
    - Strategy datasets under:
        datasets/strategies/<STRATEGY_ID>/<ASSET>/<TIMEFRAME>/<EXPERIMENT_TYPE>/<RUN_ID>/summary.json
    - CLI arguments:
        --strategy-id
        --datasets-root
        --output-dir

Outputs:
    - JSON memory:
        datasets/strategies/<STRATEGY_ID>/_memory/strategy_learning_summary.json
    - Markdown memory:
        datasets/strategies/<STRATEGY_ID>/_memory/strategy_learning_summary.md

Integrations:
    - Consumes outputs from run_monte_carlo.py.
    - Consumes outputs from run_genetic_search.py.
    - Feeds future orchestrator, agents, RAG and strategy comparison tools.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - This file does not run simulations. It only reads existing summaries.
    - It is intentionally robust to missing/older fields because dataset schemas will evolve.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class SummaryRecord:
    """One discovered strategy summary file."""

    path: Path
    payload: dict[str, Any]
    strategy_id: str
    asset: str
    timeframe: str
    experiment_type: str
    run_id: str
    created_at: str


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Build dynamic strategy learning summary.")
    parser.add_argument(
        "--strategy-id",
        default="P1_NET_V0",
        help="Strategy identifier to summarize.",
    )
    parser.add_argument(
        "--datasets-root",
        default="datasets/strategies",
        help="Root directory for strategy-aware datasets.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Defaults to datasets/strategies/<STRATEGY_ID>/_memory.",
    )
    return parser


def discover_summary_records(datasets_root: Path, strategy_id: str) -> list[SummaryRecord]:
    """Discover summary.json files for a strategy."""

    strategy_root = datasets_root / safe_path_component(strategy_id)
    if not strategy_root.exists():
        return []

    records: list[SummaryRecord] = []
    for path in sorted(strategy_root.rglob("summary.json")):
        if "_memory" in path.parts:
            continue

        payload = read_json(path)
        if not isinstance(payload, dict):
            continue

        record_strategy_id = str(payload.get("strategy_id") or strategy_id)
        asset = str(payload.get("asset") or infer_from_path(path, strategy_root, index=0, default="UNKNOWN"))
        timeframe = str(payload.get("timeframe") or infer_from_path(path, strategy_root, index=1, default="UNKNOWN"))
        experiment_type = str(payload.get("experiment_type") or infer_experiment_type(path))
        run_id = str(payload.get("run_id") or path.parent.name)
        created_at = str(payload.get("created_at_utc") or payload.get("generated_at_utc") or "")

        records.append(
            SummaryRecord(
                path=path,
                payload=payload,
                strategy_id=record_strategy_id,
                asset=asset,
                timeframe=timeframe,
                experiment_type=experiment_type,
                run_id=run_id,
                created_at=created_at,
            )
        )

    return records


def build_learning_summary(strategy_id: str, records: list[SummaryRecord]) -> dict[str, Any]:
    """Build aggregate strategy memory from records."""

    now = datetime.now(timezone.utc).isoformat()
    strategy_family = parse_strategy_family(strategy_id)
    strategy_version = parse_strategy_version(strategy_id)

    experiment_counts = Counter(record.experiment_type for record in records)
    asset_counts = Counter(record.asset for record in records)
    timeframe_counts = Counter(record.timeframe for record in records)

    genetic_records = [record for record in records if record.experiment_type == "genetic_search"]
    monte_records = [record for record in records if record.experiment_type == "monte_carlo"]

    best_genetic = find_best_genetic_result(genetic_records)
    regime_observations = build_regime_observations(genetic_records)
    monte_observations = build_monte_carlo_observations(monte_records)
    recommended_next_experiments = recommend_next_experiments(
        best_genetic=best_genetic,
        regime_observations=regime_observations,
        monte_observations=monte_observations,
    )

    return {
        "schema_version": "strategy_learning_summary.v0",
        "dataset_contract_version": "strategy_dataset_contract.v0",
        "strategy_id": strategy_id,
        "strategy_family": strategy_family,
        "strategy_version": strategy_version,
        "last_updated_utc": now,
        "records_found": len(records),
        "available_assets": sorted(asset_counts),
        "available_timeframes": sorted(timeframe_counts),
        "experiments_found": dict(sorted(experiment_counts.items())),
        "latest_records": [record_to_dict(record) for record in records[-10:]],
        "best_known_genetic_result": best_genetic,
        "regime_observations": regime_observations,
        "monte_carlo_observations": monte_observations,
        "risk_observations": build_risk_observations(best_genetic, regime_observations, monte_observations),
        "current_interpretation": build_current_interpretation(
            strategy_id=strategy_id,
            best_genetic=best_genetic,
            regime_observations=regime_observations,
            monte_observations=monte_observations,
        ),
        "recommended_next_experiments": recommended_next_experiments,
        "source_summary_files": [normalize_path(record.path) for record in records],
    }


def find_best_genetic_result(records: list[SummaryRecord]) -> Optional[dict[str, Any]]:
    """Find best known genetic result across summary files."""

    best_result: Optional[dict[str, Any]] = None

    for record in records:
        candidate = record.payload.get("best")
        if not isinstance(candidate, dict):
            top_10 = record.payload.get("top_10")
            if isinstance(top_10, list) and top_10 and isinstance(top_10[0], dict):
                candidate = top_10[0]

        if not isinstance(candidate, dict):
            continue

        score = extract_score(candidate)
        if score is None:
            continue

        enriched = {
            "source_run_id": record.run_id,
            "source_summary": normalize_path(record.path),
            "asset": record.asset,
            "timeframe": record.timeframe,
            "score": score,
            "base_score": candidate.get("base_score"),
            "regime_adjusted_score": candidate.get("regime_adjusted_score"),
            "survival_rate_pct": candidate.get("survival_rate_pct"),
            "avg_final_equity": candidate.get("avg_final_equity"),
            "min_final_equity": candidate.get("min_final_equity"),
            "worst_max_drawdown_pct": candidate.get("worst_max_drawdown_pct"),
            "worst_max_gross_lots": candidate.get("worst_max_gross_lots"),
            "worst_max_positions": candidate.get("worst_max_positions"),
            "avg_rebalance_count": candidate.get("avg_rebalance_count"),
            "avg_protection_blocks": candidate.get("avg_protection_blocks"),
            "worst_final_risk_debt": candidate.get("worst_final_risk_debt"),
            "best_regime": candidate.get("best_regime"),
            "best_regime_score": candidate.get("best_regime_score"),
            "worst_regime": candidate.get("worst_regime"),
            "worst_regime_score": candidate.get("worst_regime_score"),
            "regime_score_stddev": candidate.get("regime_score_stddev"),
            "genome": candidate.get("genome"),
        }

        if best_result is None or score > float(best_result.get("score", float("-inf"))):
            best_result = enriched

    return best_result


def build_regime_observations(records: list[SummaryRecord]) -> dict[str, Any]:
    """Build regime observations from genetic summaries."""

    worst_counter: Counter[str] = Counter()
    best_counter: Counter[str] = Counter()
    worst_scores: dict[str, list[float]] = defaultdict(list)
    best_scores: dict[str, list[float]] = defaultdict(list)

    for record in records:
        candidates = []
        best = record.payload.get("best")
        if isinstance(best, dict):
            candidates.append(best)

        top_10 = record.payload.get("top_10")
        if isinstance(top_10, list):
            candidates.extend(item for item in top_10 if isinstance(item, dict))

        for candidate in candidates:
            worst_regime = candidate.get("worst_regime")
            best_regime = candidate.get("best_regime")
            if isinstance(worst_regime, str) and worst_regime:
                worst_counter[worst_regime] += 1
                score = as_float(candidate.get("worst_regime_score"))
                if score is not None:
                    worst_scores[worst_regime].append(score)

            if isinstance(best_regime, str) and best_regime:
                best_counter[best_regime] += 1
                score = as_float(candidate.get("best_regime_score"))
                if score is not None:
                    best_scores[best_regime].append(score)

    return {
        "most_common_weak_regimes": counter_to_ranked_list(worst_counter),
        "most_common_strong_regimes": counter_to_ranked_list(best_counter),
        "average_worst_regime_scores": average_score_map(worst_scores),
        "average_best_regime_scores": average_score_map(best_scores),
    }


def build_monte_carlo_observations(records: list[SummaryRecord]) -> dict[str, Any]:
    """Build Monte Carlo observations from summary files."""

    labels: dict[str, list[dict[str, Any]]] = defaultdict(list)
    deltas: list[dict[str, Any]] = []

    for record in records:
        summaries = record.payload.get("summaries")
        if isinstance(summaries, dict):
            for label, summary in summaries.items():
                if isinstance(summary, dict):
                    labels[str(label)].append(
                        {
                            "source_run_id": record.run_id,
                            "asset": record.asset,
                            "timeframe": record.timeframe,
                            "summary": summary,
                        }
                    )

        comparison_deltas = record.payload.get("comparison_deltas")
        if isinstance(comparison_deltas, dict):
            deltas.append(
                {
                    "source_run_id": record.run_id,
                    "asset": record.asset,
                    "timeframe": record.timeframe,
                    "comparison_deltas": comparison_deltas,
                }
            )

    return {
        "labels_found": sorted(labels),
        "latest_by_label": {
            label: items[-1] for label, items in sorted(labels.items()) if items
        },
        "comparison_delta_records": deltas[-10:],
    }


def build_risk_observations(
    best_genetic: Optional[dict[str, Any]],
    regime_observations: dict[str, Any],
    monte_observations: dict[str, Any],
) -> dict[str, Any]:
    """Build high-level risk observations."""

    risks: dict[str, Any] = {
        "gross_expansion_risk": "unknown",
        "risk_debt_risk": "unknown",
        "regime_imbalance_risk": "unknown",
        "overblocking_risk": "unknown",
    }

    if best_genetic:
        worst_gross = as_float(best_genetic.get("worst_max_gross_lots"))
        worst_risk_debt = as_float(best_genetic.get("worst_final_risk_debt"))
        blocks = as_float(best_genetic.get("avg_protection_blocks"))
        regime_std = as_float(best_genetic.get("regime_score_stddev"))

        if worst_gross is not None:
            risks["gross_expansion_risk"] = "controlled" if worst_gross <= 0.10 else "monitor"
        if worst_risk_debt is not None:
            risks["risk_debt_risk"] = "low" if worst_risk_debt <= 100 else "monitor"
        if blocks is not None:
            risks["overblocking_risk"] = "low" if blocks <= 10 else "monitor"
        if regime_std is not None:
            risks["regime_imbalance_risk"] = "low" if regime_std <= 7 else "monitor"

    weak_regimes = regime_observations.get("most_common_weak_regimes") or []
    if weak_regimes:
        risks["weak_regime_watchlist"] = weak_regimes[:5]

    return risks


def recommend_next_experiments(
    best_genetic: Optional[dict[str, Any]],
    regime_observations: dict[str, Any],
    monte_observations: dict[str, Any],
) -> list[str]:
    """Recommend next experiments based on current memory."""

    recommendations = [
        "Run a larger genetic search with the same strategy_id to confirm stability.",
        "Run Monte Carlo with more paths and longer synthetic sequences.",
        "Compare against P1_MULTIPLIER_V0 once implemented.",
    ]

    if best_genetic:
        weak = best_genetic.get("worst_regime")
        if weak:
            recommendations.append(f"Stress-test weak regime: {weak}.")

        avg_rebalance = as_float(best_genetic.get("avg_rebalance_count"))
        if avg_rebalance is not None and avg_rebalance < 1.0:
            recommendations.append("Increase activity pressure or reduce range_points to avoid near-inactive behavior.")

        risk_debt = as_float(best_genetic.get("worst_final_risk_debt"))
        if risk_debt is not None and risk_debt > 150:
            recommendations.append("Add stronger risk_debt penalty or recovery logic in future strategy variants.")

    weak_regimes = regime_observations.get("most_common_weak_regimes") or []
    if weak_regimes:
        recommendations.append("Use regime-aware fitness to reduce repeated weak regimes.")

    return recommendations


def build_current_interpretation(
    strategy_id: str,
    best_genetic: Optional[dict[str, Any]],
    regime_observations: dict[str, Any],
    monte_observations: dict[str, Any],
) -> str:
    """Build a concise natural-language interpretation."""

    if not best_genetic:
        return (
            f"{strategy_id} has a conceptual Strategy Card, but no genetic search summary "
            "was found yet. Run genetic search with --save-json to enrich learning memory."
        )

    worst_regime = best_genetic.get("worst_regime", "unknown")
    best_regime = best_genetic.get("best_regime", "unknown")
    score = best_genetic.get("score", "unknown")

    return (
        f"{strategy_id} currently has best known genetic score {score}. "
        f"The strongest observed regime is {best_regime}; the weakest observed regime is {worst_regime}. "
        "The strategy should continue to be evaluated with regime-aware scoring, gross exposure controls, "
        "risk debt monitoring and comparison against alternative hedge structures."
    )


def write_outputs(summary: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Write JSON and Markdown memory files."""

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "strategy_learning_summary.json"
    md_path = output_dir / "strategy_learning_summary.md"

    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")

    return json_path, md_path


def render_markdown(summary: dict[str, Any]) -> str:
    """Render human/RAG friendly Markdown from strategy memory."""

    strategy_id = summary.get("strategy_id", "UNKNOWN")
    best = summary.get("best_known_genetic_result") or {}
    regimes = summary.get("regime_observations") or {}
    risks = summary.get("risk_observations") or {}
    recommendations = summary.get("recommended_next_experiments") or []

    lines = [
        f"# Strategy Learning Summary — {strategy_id}",
        "",
        "## Identity",
        "",
        f"- Strategy ID: `{strategy_id}`",
        f"- Family: `{summary.get('strategy_family', 'UNKNOWN')}`",
        f"- Version: `{summary.get('strategy_version', 'UNKNOWN')}`",
        f"- Last updated UTC: `{summary.get('last_updated_utc', '')}`",
        f"- Records found: `{summary.get('records_found', 0)}`",
        "",
        "## Available Data",
        "",
        f"- Assets: `{', '.join(summary.get('available_assets', []))}`",
        f"- Timeframes: `{', '.join(summary.get('available_timeframes', []))}`",
        f"- Experiments: `{json.dumps(summary.get('experiments_found', {}), ensure_ascii=False)}`",
        "",
        "## Best Known Genetic Result",
        "",
    ]

    if best:
        lines.extend(
            [
                f"- Source run: `{best.get('source_run_id')}`",
                f"- Score: `{best.get('score')}`",
                f"- Base score: `{best.get('base_score')}`",
                f"- Regime adjusted score: `{best.get('regime_adjusted_score')}`",
                f"- Worst regime: `{best.get('worst_regime')}` / `{best.get('worst_regime_score')}`",
                f"- Best regime: `{best.get('best_regime')}` / `{best.get('best_regime_score')}`",
                f"- Worst gross lots: `{best.get('worst_max_gross_lots')}`",
                f"- Worst positions: `{best.get('worst_max_positions')}`",
                f"- Worst risk debt: `{best.get('worst_final_risk_debt')}`",
                f"- Avg rebalance count: `{best.get('avg_rebalance_count')}`",
                f"- Avg protection blocks: `{best.get('avg_protection_blocks')}`",
                "",
                "### Best Genome",
                "",
                "```json",
                json.dumps(best.get("genome"), indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    else:
        lines.append("No genetic result found yet.\n")

    lines.extend(
        [
            "## Regime Observations",
            "",
            "### Most Common Weak Regimes",
            "",
        ]
    )

    for item in regimes.get("most_common_weak_regimes", []):
        lines.append(f"- `{item.get('name')}`: `{item.get('count')}`")

    lines.extend(["", "### Most Common Strong Regimes", ""])

    for item in regimes.get("most_common_strong_regimes", []):
        lines.append(f"- `{item.get('name')}`: `{item.get('count')}`")

    lines.extend(["", "## Risk Observations", ""])

    for key, value in risks.items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Current Interpretation", "", str(summary.get("current_interpretation", "")), ""])

    lines.extend(["## Recommended Next Experiments", ""])
    for item in recommendations:
        lines.append(f"- {item}")

    lines.extend(["", "## Source Summary Files", ""])
    for path in summary.get("source_summary_files", []):
        lines.append(f"- `{path}`")

    lines.append("")
    return "\n".join(lines)


def read_json(path: Path) -> Any:
    """Read JSON safely."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def extract_score(candidate: dict[str, Any]) -> Optional[float]:
    """Extract best available score from a genetic candidate."""

    for key in ("adjusted_score", "score", "regime_adjusted_score", "base_score", "robustness_score"):
        value = as_float(candidate.get(key))
        if value is not None:
            return value
    return None


def as_float(value: Any) -> Optional[float]:
    """Convert value to float when possible."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def average_score_map(values: dict[str, list[float]]) -> dict[str, float]:
    """Average values per key."""

    return {
        key: round(sum(items) / len(items), 6)
        for key, items in sorted(values.items())
        if items
    }


def counter_to_ranked_list(counter: Counter[str]) -> list[dict[str, Any]]:
    """Convert counter to ranked list."""

    return [
        {"name": name, "count": count}
        for name, count in counter.most_common()
    ]


def record_to_dict(record: SummaryRecord) -> dict[str, Any]:
    """Convert record metadata to dict."""

    return {
        "path": normalize_path(record.path),
        "strategy_id": record.strategy_id,
        "asset": record.asset,
        "timeframe": record.timeframe,
        "experiment_type": record.experiment_type,
        "run_id": record.run_id,
        "created_at": record.created_at,
    }


def infer_from_path(path: Path, strategy_root: Path, index: int, default: str) -> str:
    """Infer path part under strategy root."""

    try:
        relative = path.relative_to(strategy_root)
        return relative.parts[index]
    except Exception:
        return default


def infer_experiment_type(path: Path) -> str:
    """Infer experiment type from path."""

    parts = set(path.parts)
    if "genetic_search" in parts:
        return "genetic_search"
    if "monte_carlo" in parts:
        return "monte_carlo"
    return "unknown"


def parse_strategy_family(strategy_id: str) -> str:
    """Return strategy family from a strategy_id such as P1_NET_V0."""

    normalized = strategy_id.strip()
    if "_V" in normalized:
        return normalized.rsplit("_V", 1)[0]
    return normalized


def parse_strategy_version(strategy_id: str) -> str:
    """Return strategy version from a strategy_id such as P1_NET_V0."""

    normalized = strategy_id.strip()
    if "_V" in normalized:
        return "V" + normalized.rsplit("_V", 1)[1]
    return "UNKNOWN"


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

    strategy_id = args.strategy_id
    datasets_root = Path(args.datasets_root)
    output_dir = Path(args.output_dir) if args.output_dir else datasets_root / safe_path_component(strategy_id) / "_memory"

    records = discover_summary_records(datasets_root=datasets_root, strategy_id=strategy_id)
    summary = build_learning_summary(strategy_id=strategy_id, records=records)
    json_path, md_path = write_outputs(summary=summary, output_dir=output_dir)

    print("=== HEDGE EVOLUTION LAB — STRATEGY LEARNING SUMMARY V0 ===")
    print(f"strategy_id: {strategy_id}")
    print(f"records_found: {len(records)}")
    print(f"json: {json_path}")
    print(f"markdown: {md_path}")

    if not records:
        print("warning: no summary.json files found for this strategy_id")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
