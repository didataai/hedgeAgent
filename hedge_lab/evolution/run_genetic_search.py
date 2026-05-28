"""
File: hedge_lab/evolution/run_genetic_search.py

Purpose:
    Run Genetic Search v0.2 for Hedge Evolution Lab using P1-Net v0.

Inputs:
    - CLI arguments:
        --strategy-id
        --asset
        --timeframe
        --generations
        --population
        --elite-size
        --mutation-rate
        --runs
        --steps
        --seed
        --initial-balance
        --point-value
        --max-gross-lots
        --max-positions
        --max-drawdown-pct
        --min-avg-rebalance-count
        --max-avg-protection-blocks
        --regime-balance-weight
        --worst-regime-weight
        --save-json
        --output-dir

Outputs:
    - Console ranking of candidate genomes.
    - Optional JSON/JSONL datasets under datasets/strategies/<STRATEGY_ID>/...

Integrations:
    - Reuses hedge_lab.simulator.run_monte_carlo.ExperimentConfig.
    - Reuses hedge_lab.simulator.run_monte_carlo.run_monte_carlo.
    - Reuses hedge_lab.simulator.run_monte_carlo.calculate_robustness_score.
    - Later can feed strategy memory, agents, LLM ranking and promotion logic.

Notes:
    - Dataset contract v0:
        datasets/strategies/<STRATEGY_ID>/<ASSET>/<TIMEFRAME>/<EXPERIMENT_TYPE>/<RUN_ID>/
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - v0.2 adds regime-aware scoring.
    - P1-Net contract enforced here: start_lot == net_abs_lots.
    - Extra penalties are applied for excessive protection blocks, very low rebalance activity,
      weak worst-regime performance and regime imbalance.
    - This does not guarantee profitability. It searches for better robustness trade-offs.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from hedge_lab.simulator.core import Side
from hedge_lab.simulator.run_monte_carlo import (
    ExperimentConfig,
    RunMetrics,
    calculate_robustness_score,
    run_monte_carlo,
)


@dataclass(frozen=True)
class StrategyGenome:
    """Parameter genome for P1-Net v0.2.

    Contract:
        start_lot is intentionally not a free gene.
        For P1-Net, start_lot must equal net_abs_lots so the strategy starts
        with the intended absolute net exposure.
    """

    genome_id: str
    initial_side: Side
    net_abs_lots: float
    range_points: float
    enable_protection: bool
    max_gross_to_net_ratio: Optional[float]
    max_strategy_gross_lots: Optional[float]
    max_strategy_positions: Optional[int]

    @property
    def start_lot(self) -> float:
        """Return initial lot following P1-Net contract."""

        return self.net_abs_lots


@dataclass(frozen=True)
class RegimeScore:
    """Score and diagnostics for one synthetic regime."""

    regime: str
    runs: int
    survival_rate_pct: float
    avg_final_equity: float
    min_final_equity: float
    avg_max_drawdown_pct: float
    worst_max_drawdown_pct: float
    avg_max_gross_lots: float
    worst_max_gross_lots: float
    avg_max_positions: float
    worst_max_positions: int
    avg_final_risk_debt: float
    worst_final_risk_debt: float
    score: float


@dataclass(frozen=True)
class GenomeEvaluation:
    """Result of evaluating one genome."""

    generation: int
    rank: int
    genome: StrategyGenome
    base_score: float
    regime_adjusted_score: float
    adjusted_score: float
    activity_penalty: float
    protection_overblock_penalty: float
    regime_balance_penalty: float
    worst_regime_penalty: float
    survival_rate_pct: float
    avg_final_equity: float
    min_final_equity: float
    avg_max_drawdown_pct: float
    worst_max_drawdown_pct: float
    avg_max_gross_lots: float
    worst_max_gross_lots: float
    avg_max_positions: float
    worst_max_positions: int
    avg_final_risk_debt: float
    worst_final_risk_debt: float
    avg_rebalance_count: float
    avg_protection_blocks: float
    total_protection_blocks: int
    failure_count: int
    best_regime: str
    best_regime_score: float
    worst_regime: str
    worst_regime_score: float
    regime_score_stddev: float
    regime_scores: List[RegimeScore]


@dataclass(frozen=True)
class GeneticSearchConfig:
    """Config for the genetic search runner."""

    strategy_id: str
    asset: str
    timeframe: str
    generations: int
    population: int
    elite_size: int
    mutation_rate: float
    runs: int
    steps: int
    seed: int
    initial_balance: float
    point_value: float
    max_gross_lots: float
    max_positions: int
    max_drawdown_pct: float
    min_avg_rebalance_count: float
    max_avg_protection_blocks: float
    regime_balance_weight: float
    worst_regime_weight: float
    save_json: bool
    output_dir: str


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Run Hedge Evolution Lab Genetic Search v0.2.")
    parser.add_argument(
        "--strategy-id",
        default="P1_NET_V0",
        help="Stable strategy identifier used in dataset paths and summaries.",
    )
    parser.add_argument("--asset", default="SYNTH", help="Asset/symbol label. Example: GOLD, EURUSD, SYNTH.")
    parser.add_argument("--timeframe", default="SIM", help="Timeframe label. Example: M5, H1, SIM.")
    parser.add_argument("--generations", type=int, default=3, help="Number of generations.")
    parser.add_argument("--population", type=int, default=12, help="Candidates per generation.")
    parser.add_argument("--elite-size", type=int, default=4, help="Number of best genomes carried forward.")
    parser.add_argument("--mutation-rate", type=float, default=0.35, help="Mutation probability per parameter.")
    parser.add_argument("--runs", type=int, default=120, help="Monte Carlo paths per candidate.")
    parser.add_argument("--steps", type=int, default=120, help="Synthetic steps per path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--initial-balance", type=float, default=10_000.0, help="Initial simulated balance.")
    parser.add_argument("--point-value", type=float, default=1.0, help="PNL multiplier per price unit and lot.")
    parser.add_argument("--max-gross-lots", type=float, default=1.0, help="Engine gross lot limit.")
    parser.add_argument("--max-positions", type=int, default=100, help="Engine open positions limit.")
    parser.add_argument("--max-drawdown-pct", type=float, default=30.0, help="Engine max drawdown limit.")
    parser.add_argument(
        "--min-avg-rebalance-count",
        type=float,
        default=1.0,
        help="Minimum desired average rebalance count. Lower activity receives a penalty.",
    )
    parser.add_argument(
        "--max-avg-protection-blocks",
        type=float,
        default=25.0,
        help="Maximum desired average protection blocks. Higher blocking receives a penalty.",
    )
    parser.add_argument(
        "--regime-balance-weight",
        type=float,
        default=0.35,
        help="Penalty weight for high standard deviation between regime scores.",
    )
    parser.add_argument(
        "--worst-regime-weight",
        type=float,
        default=0.50,
        help="Penalty weight when worst regime score is much lower than base score.",
    )
    parser.add_argument("--save-json", action="store_true", help="Save JSON/JSONL datasets.")
    parser.add_argument(
        "--output-dir",
        default="datasets/strategies",
        help="Base output directory for strategy-aware genetic search datasets.",
    )
    return parser


def build_config(args: argparse.Namespace) -> GeneticSearchConfig:
    """Build config from CLI args."""

    return GeneticSearchConfig(
        strategy_id=args.strategy_id,
        asset=args.asset,
        timeframe=args.timeframe,
        generations=args.generations,
        population=args.population,
        elite_size=args.elite_size,
        mutation_rate=args.mutation_rate,
        runs=args.runs,
        steps=args.steps,
        seed=args.seed,
        initial_balance=args.initial_balance,
        point_value=args.point_value,
        max_gross_lots=args.max_gross_lots,
        max_positions=args.max_positions,
        max_drawdown_pct=args.max_drawdown_pct,
        min_avg_rebalance_count=args.min_avg_rebalance_count,
        max_avg_protection_blocks=args.max_avg_protection_blocks,
        regime_balance_weight=args.regime_balance_weight,
        worst_regime_weight=args.worst_regime_weight,
        save_json=args.save_json,
        output_dir=args.output_dir,
    )


def random_genome(rng: random.Random, genome_id: str) -> StrategyGenome:
    """Create a random but bounded P1-Net genome."""

    return StrategyGenome(
        genome_id=genome_id,
        initial_side=rng.choice([Side.BUY, Side.SELL]),
        net_abs_lots=rng.choice([0.01, 0.02, 0.03, 0.04]),
        range_points=rng.choice([150.0, 200.0, 250.0, 300.0, 400.0, 500.0, 700.0]),
        enable_protection=rng.choice([True, True, True, False]),
        max_gross_to_net_ratio=rng.choice([3.0, 5.0, 7.0, 9.0, 12.0, None]),
        max_strategy_gross_lots=rng.choice([None, 0.10, 0.20, 0.30, 0.50]),
        max_strategy_positions=rng.choice([None, 3, 5, 8, 13]),
    )


def mutate_genome(rng: random.Random, parent: StrategyGenome, genome_id: str, mutation_rate: float) -> StrategyGenome:
    """Create a mutated child genome from an elite parent."""

    genome = {
        "genome_id": genome_id,
        "initial_side": parent.initial_side,
        "net_abs_lots": parent.net_abs_lots,
        "range_points": parent.range_points,
        "enable_protection": parent.enable_protection,
        "max_gross_to_net_ratio": parent.max_gross_to_net_ratio,
        "max_strategy_gross_lots": parent.max_strategy_gross_lots,
        "max_strategy_positions": parent.max_strategy_positions,
    }

    mutation_choices = {
        "initial_side": [Side.BUY, Side.SELL],
        "net_abs_lots": [0.01, 0.02, 0.03, 0.04],
        "range_points": [150.0, 200.0, 250.0, 300.0, 400.0, 500.0, 700.0],
        "enable_protection": [True, True, True, False],
        "max_gross_to_net_ratio": [3.0, 5.0, 7.0, 9.0, 12.0, None],
        "max_strategy_gross_lots": [None, 0.10, 0.20, 0.30, 0.50],
        "max_strategy_positions": [None, 3, 5, 8, 13],
    }

    for key, choices in mutation_choices.items():
        if rng.random() <= mutation_rate:
            genome[key] = rng.choice(choices)

    return StrategyGenome(**genome)


def genome_to_experiment_config(
    genome: StrategyGenome,
    search_config: GeneticSearchConfig,
    seed: int,
) -> ExperimentConfig:
    """Convert a genome into a Monte Carlo experiment config."""

    return ExperimentConfig(
        strategy_id=search_config.strategy_id,
        asset=search_config.asset,
        timeframe=search_config.timeframe,
        runs=search_config.runs,
        steps=search_config.steps,
        seed=seed,
        initial_side=genome.initial_side,
        start_lot=genome.start_lot,
        net_abs_lots=genome.net_abs_lots,
        range_points=genome.range_points,
        initial_balance=search_config.initial_balance,
        point_value=search_config.point_value,
        max_gross_lots=search_config.max_gross_lots,
        max_positions=search_config.max_positions,
        max_drawdown_pct=search_config.max_drawdown_pct,
        enable_protection=genome.enable_protection,
        strategy_max_gross_to_net_ratio=genome.max_gross_to_net_ratio,
        strategy_max_gross_lots=genome.max_strategy_gross_lots,
        strategy_max_positions=genome.max_strategy_positions,
    )


def evaluate_genome(
    generation: int,
    rank: int,
    genome: StrategyGenome,
    search_config: GeneticSearchConfig,
    seed: int,
) -> GenomeEvaluation:
    """Evaluate one genome using Monte Carlo and Score Engine v0.2."""

    experiment_config = genome_to_experiment_config(
        genome=genome,
        search_config=search_config,
        seed=seed,
    )
    metrics = run_monte_carlo(experiment_config)
    return summarize_genome_metrics(
        generation=generation,
        rank=rank,
        genome=genome,
        metrics=metrics,
        config=search_config,
    )


def summarize_genome_metrics(
    generation: int,
    rank: int,
    genome: StrategyGenome,
    metrics: Sequence[RunMetrics],
    config: GeneticSearchConfig,
) -> GenomeEvaluation:
    """Aggregate metrics for one genome."""

    total = len(metrics)
    survived = sum(1 for item in metrics if item.survived)
    survival_rate_pct = (survived / total) * 100.0 if total else 0.0

    final_equities = [item.final_equity for item in metrics]
    drawdowns = [item.max_drawdown for item in metrics]
    max_gross = [item.max_gross_lots for item in metrics]
    max_positions = [item.max_positions for item in metrics]
    risk_debts = [item.risk_debt for item in metrics]
    protection_blocks = [item.protection_block_count for item in metrics]
    rebalance_counts = [item.rebalance_count for item in metrics]

    avg_final_equity = mean(final_equities)
    min_final_equity = min(final_equities) if final_equities else config.initial_balance
    avg_drawdown = mean(drawdowns)
    worst_drawdown = max(drawdowns) if drawdowns else 0.0
    avg_gross = mean(max_gross)
    worst_gross = max(max_gross) if max_gross else 0.0
    avg_positions = mean(max_positions)
    worst_positions = max(max_positions) if max_positions else 0
    avg_risk_debt = mean(risk_debts)
    worst_risk_debt = max(risk_debts) if risk_debts else 0.0
    avg_rebalance_count = mean(rebalance_counts)
    avg_protection_blocks = mean(protection_blocks)

    base_score = calculate_robustness_score(
        survival_rate_pct=survival_rate_pct,
        avg_final_equity=avg_final_equity,
        initial_balance=config.initial_balance,
        avg_max_drawdown_pct=avg_drawdown,
        worst_max_drawdown_pct=worst_drawdown,
        avg_max_gross_lots=avg_gross,
        worst_max_gross_lots=worst_gross,
        avg_max_positions=avg_positions,
        worst_max_positions=worst_positions,
        avg_final_risk_debt=avg_risk_debt,
        worst_final_risk_debt=worst_risk_debt,
    )

    regime_scores = calculate_regime_scores(
        metrics=metrics,
        initial_balance=config.initial_balance,
    )
    regime_diagnostics = calculate_regime_diagnostics(regime_scores=regime_scores)

    activity_penalty = calculate_activity_penalty(
        avg_rebalance_count=avg_rebalance_count,
        min_avg_rebalance_count=config.min_avg_rebalance_count,
    )
    protection_overblock_penalty = calculate_protection_overblock_penalty(
        avg_protection_blocks=avg_protection_blocks,
        max_avg_protection_blocks=config.max_avg_protection_blocks,
    )
    regime_balance_penalty = calculate_regime_balance_penalty(
        regime_score_stddev=regime_diagnostics["stddev"],
        weight=config.regime_balance_weight,
    )
    worst_regime_penalty = calculate_worst_regime_penalty(
        base_score=base_score,
        worst_regime_score=regime_diagnostics["worst_score"],
        weight=config.worst_regime_weight,
    )

    regime_adjusted_score = base_score - regime_balance_penalty - worst_regime_penalty
    adjusted_score = (
        regime_adjusted_score
        - activity_penalty
        - protection_overblock_penalty
    )

    return GenomeEvaluation(
        generation=generation,
        rank=rank,
        genome=genome,
        base_score=base_score,
        regime_adjusted_score=regime_adjusted_score,
        adjusted_score=adjusted_score,
        activity_penalty=activity_penalty,
        protection_overblock_penalty=protection_overblock_penalty,
        regime_balance_penalty=regime_balance_penalty,
        worst_regime_penalty=worst_regime_penalty,
        survival_rate_pct=survival_rate_pct,
        avg_final_equity=avg_final_equity,
        min_final_equity=min_final_equity,
        avg_max_drawdown_pct=avg_drawdown,
        worst_max_drawdown_pct=worst_drawdown,
        avg_max_gross_lots=avg_gross,
        worst_max_gross_lots=worst_gross,
        avg_max_positions=avg_positions,
        worst_max_positions=worst_positions,
        avg_final_risk_debt=avg_risk_debt,
        worst_final_risk_debt=worst_risk_debt,
        avg_rebalance_count=avg_rebalance_count,
        avg_protection_blocks=avg_protection_blocks,
        total_protection_blocks=sum(protection_blocks),
        failure_count=total - survived,
        best_regime=regime_diagnostics["best_regime"],
        best_regime_score=regime_diagnostics["best_score"],
        worst_regime=regime_diagnostics["worst_regime"],
        worst_regime_score=regime_diagnostics["worst_score"],
        regime_score_stddev=regime_diagnostics["stddev"],
        regime_scores=regime_scores,
    )


def calculate_regime_scores(metrics: Sequence[RunMetrics], initial_balance: float) -> List[RegimeScore]:
    """Calculate robustness score for each synthetic regime."""

    grouped: Dict[str, List[RunMetrics]] = defaultdict(list)
    for item in metrics:
        grouped[item.regime].append(item)

    regime_scores = []
    for regime, items in sorted(grouped.items()):
        total = len(items)
        survived = sum(1 for item in items if item.survived)
        survival_rate_pct = (survived / total) * 100.0 if total else 0.0

        final_equities = [item.final_equity for item in items]
        drawdowns = [item.max_drawdown for item in items]
        max_gross = [item.max_gross_lots for item in items]
        max_positions = [item.max_positions for item in items]
        risk_debts = [item.risk_debt for item in items]

        avg_final_equity = mean(final_equities)
        min_final_equity = min(final_equities) if final_equities else initial_balance
        avg_drawdown = mean(drawdowns)
        worst_drawdown = max(drawdowns) if drawdowns else 0.0
        avg_gross = mean(max_gross)
        worst_gross = max(max_gross) if max_gross else 0.0
        avg_positions = mean(max_positions)
        worst_positions = max(max_positions) if max_positions else 0
        avg_risk_debt = mean(risk_debts)
        worst_risk_debt = max(risk_debts) if risk_debts else 0.0

        score = calculate_robustness_score(
            survival_rate_pct=survival_rate_pct,
            avg_final_equity=avg_final_equity,
            initial_balance=initial_balance,
            avg_max_drawdown_pct=avg_drawdown,
            worst_max_drawdown_pct=worst_drawdown,
            avg_max_gross_lots=avg_gross,
            worst_max_gross_lots=worst_gross,
            avg_max_positions=avg_positions,
            worst_max_positions=worst_positions,
            avg_final_risk_debt=avg_risk_debt,
            worst_final_risk_debt=worst_risk_debt,
        )

        regime_scores.append(
            RegimeScore(
                regime=regime,
                runs=total,
                survival_rate_pct=survival_rate_pct,
                avg_final_equity=avg_final_equity,
                min_final_equity=min_final_equity,
                avg_max_drawdown_pct=avg_drawdown,
                worst_max_drawdown_pct=worst_drawdown,
                avg_max_gross_lots=avg_gross,
                worst_max_gross_lots=worst_gross,
                avg_max_positions=avg_positions,
                worst_max_positions=worst_positions,
                avg_final_risk_debt=avg_risk_debt,
                worst_final_risk_debt=worst_risk_debt,
                score=score,
            )
        )

    return regime_scores


def calculate_regime_diagnostics(regime_scores: Sequence[RegimeScore]) -> dict:
    """Return best/worst regime and score dispersion diagnostics."""

    if not regime_scores:
        return {
            "best_regime": "none",
            "best_score": 0.0,
            "worst_regime": "none",
            "worst_score": 0.0,
            "stddev": 0.0,
        }

    best = max(regime_scores, key=lambda item: item.score)
    worst = min(regime_scores, key=lambda item: item.score)
    scores = [item.score for item in regime_scores]
    stddev = statistics.pstdev(scores) if len(scores) > 1 else 0.0

    return {
        "best_regime": best.regime,
        "best_score": best.score,
        "worst_regime": worst.regime,
        "worst_score": worst.score,
        "stddev": stddev,
    }


def calculate_activity_penalty(avg_rebalance_count: float, min_avg_rebalance_count: float) -> float:
    """Penalize genomes that barely operate."""

    if avg_rebalance_count >= min_avg_rebalance_count:
        return 0.0

    gap = min_avg_rebalance_count - avg_rebalance_count
    return gap * 25.0


def calculate_protection_overblock_penalty(
    avg_protection_blocks: float,
    max_avg_protection_blocks: float,
) -> float:
    """Penalize excessive protection blocking."""

    if avg_protection_blocks <= max_avg_protection_blocks:
        return 0.0

    excess = avg_protection_blocks - max_avg_protection_blocks
    return excess * 0.75


def calculate_regime_balance_penalty(regime_score_stddev: float, weight: float) -> float:
    """Penalize unstable performance across regimes."""

    return regime_score_stddev * weight


def calculate_worst_regime_penalty(base_score: float, worst_regime_score: float, weight: float) -> float:
    """Penalize candidates whose worst regime is much weaker than their aggregate score."""

    gap = max(0.0, base_score - worst_regime_score)
    return gap * weight


def run_genetic_search(config: GeneticSearchConfig) -> List[GenomeEvaluation]:
    """Run the genetic/randomized search loop."""

    rng = random.Random(config.seed)
    population = [
        random_genome(rng=rng, genome_id=f"g00_i{index:03d}")
        for index in range(config.population)
    ]

    all_evaluations: List[GenomeEvaluation] = []

    for generation in range(config.generations):
        print(f"\n=== GENERATION {generation:02d} ===")

        generation_results = []
        for index, genome in enumerate(population):
            evaluation_seed = config.seed + generation * 10_000 + index
            evaluation = evaluate_genome(
                generation=generation,
                rank=0,
                genome=genome,
                search_config=config,
                seed=evaluation_seed,
            )
            generation_results.append(evaluation)

        generation_results.sort(key=lambda item: item.adjusted_score, reverse=True)
        ranked_results = [
            replace_rank(item=item, rank=rank + 1)
            for rank, item in enumerate(generation_results)
        ]

        all_evaluations.extend(ranked_results)
        print_generation_summary(ranked_results)

        elites = [item.genome for item in ranked_results[: max(1, config.elite_size)]]
        next_population = list(elites)

        while len(next_population) < config.population:
            parent = rng.choice(elites)
            child_id = f"g{generation + 1:02d}_i{len(next_population):03d}"
            next_population.append(
                mutate_genome(
                    rng=rng,
                    parent=parent,
                    genome_id=child_id,
                    mutation_rate=config.mutation_rate,
                )
            )

        population = next_population

    return sorted(all_evaluations, key=lambda item: item.adjusted_score, reverse=True)


def replace_rank(item: GenomeEvaluation, rank: int) -> GenomeEvaluation:
    """Return a copy of an evaluation with updated rank."""

    return GenomeEvaluation(
        generation=item.generation,
        rank=rank,
        genome=item.genome,
        base_score=item.base_score,
        regime_adjusted_score=item.regime_adjusted_score,
        adjusted_score=item.adjusted_score,
        activity_penalty=item.activity_penalty,
        protection_overblock_penalty=item.protection_overblock_penalty,
        regime_balance_penalty=item.regime_balance_penalty,
        worst_regime_penalty=item.worst_regime_penalty,
        survival_rate_pct=item.survival_rate_pct,
        avg_final_equity=item.avg_final_equity,
        min_final_equity=item.min_final_equity,
        avg_max_drawdown_pct=item.avg_max_drawdown_pct,
        worst_max_drawdown_pct=item.worst_max_drawdown_pct,
        avg_max_gross_lots=item.avg_max_gross_lots,
        worst_max_gross_lots=item.worst_max_gross_lots,
        avg_max_positions=item.avg_max_positions,
        worst_max_positions=item.worst_max_positions,
        avg_final_risk_debt=item.avg_final_risk_debt,
        worst_final_risk_debt=item.worst_final_risk_debt,
        avg_rebalance_count=item.avg_rebalance_count,
        avg_protection_blocks=item.avg_protection_blocks,
        total_protection_blocks=item.total_protection_blocks,
        failure_count=item.failure_count,
        best_regime=item.best_regime,
        best_regime_score=item.best_regime_score,
        worst_regime=item.worst_regime,
        worst_regime_score=item.worst_regime_score,
        regime_score_stddev=item.regime_score_stddev,
        regime_scores=item.regime_scores,
    )


def print_generation_summary(results: Sequence[GenomeEvaluation]) -> None:
    """Print best candidates for one generation."""

    for item in results[:5]:
        genome = item.genome
        print(
            f"rank={item.rank:02d} "
            f"id={genome.genome_id} "
            f"score={item.adjusted_score:.4f} "
            f"base={item.base_score:.4f} "
            f"regime_adj={item.regime_adjusted_score:.4f} "
            f"penalty_activity={item.activity_penalty:.4f} "
            f"penalty_blocks={item.protection_overblock_penalty:.4f} "
            f"penalty_regime_balance={item.regime_balance_penalty:.4f} "
            f"penalty_worst_regime={item.worst_regime_penalty:.4f} "
            f"survival={item.survival_rate_pct:.2f}% "
            f"equity={item.avg_final_equity:.2f} "
            f"dd={item.worst_max_drawdown_pct:.4f} "
            f"gross={item.worst_max_gross_lots:.2f} "
            f"pos={item.worst_max_positions} "
            f"risk_debt={item.worst_final_risk_debt:.2f} "
            f"rebalance_avg={item.avg_rebalance_count:.2f} "
            f"blocks_avg={item.avg_protection_blocks:.2f} "
            f"worst_regime={item.worst_regime}:{item.worst_regime_score:.2f} "
            f"best_regime={item.best_regime}:{item.best_regime_score:.2f} "
            f"regime_std={item.regime_score_stddev:.2f} "
            f"side={genome.initial_side.value} "
            f"lot={genome.start_lot:.2f} "
            f"net={genome.net_abs_lots:.2f} "
            f"range={genome.range_points:.0f} "
            f"prot={genome.enable_protection} "
            f"ratio={genome.max_gross_to_net_ratio} "
            f"max_gross={genome.max_strategy_gross_lots} "
            f"max_pos={genome.max_strategy_positions}"
        )


def print_final_ranking(results: Sequence[GenomeEvaluation]) -> None:
    """Print final ranking."""

    print("\n=== FINAL GENETIC SEARCH RANKING — TOP 10 ===")
    for index, item in enumerate(results[:10], start=1):
        genome = item.genome
        print(
            f"global_rank={index:02d} "
            f"gen={item.generation:02d} "
            f"id={genome.genome_id} "
            f"score={item.adjusted_score:.4f} "
            f"base={item.base_score:.4f} "
            f"regime_adj={item.regime_adjusted_score:.4f} "
            f"activity_penalty={item.activity_penalty:.4f} "
            f"blocks_penalty={item.protection_overblock_penalty:.4f} "
            f"regime_balance_penalty={item.regime_balance_penalty:.4f} "
            f"worst_regime_penalty={item.worst_regime_penalty:.4f} "
            f"survival={item.survival_rate_pct:.2f}% "
            f"avg_equity={item.avg_final_equity:.2f} "
            f"min_equity={item.min_final_equity:.2f} "
            f"worst_dd={item.worst_max_drawdown_pct:.4f} "
            f"worst_gross={item.worst_max_gross_lots:.2f} "
            f"worst_pos={item.worst_max_positions} "
            f"rebalance_avg={item.avg_rebalance_count:.2f} "
            f"blocks_avg={item.avg_protection_blocks:.2f} "
            f"worst_risk_debt={item.worst_final_risk_debt:.2f} "
            f"worst_regime={item.worst_regime}:{item.worst_regime_score:.2f} "
            f"best_regime={item.best_regime}:{item.best_regime_score:.2f} "
            f"regime_std={item.regime_score_stddev:.2f} "
            f"genome={genome_to_compact_string(genome)}"
        )


def genome_to_compact_string(genome: StrategyGenome) -> str:
    """Return compact genome representation."""

    return (
        f"side:{genome.initial_side.value}|"
        f"lot:{genome.start_lot}|"
        f"net:{genome.net_abs_lots}|"
        f"range:{genome.range_points}|"
        f"prot:{genome.enable_protection}|"
        f"ratio:{genome.max_gross_to_net_ratio}|"
        f"max_gross:{genome.max_strategy_gross_lots}|"
        f"max_pos:{genome.max_strategy_positions}"
    )


def safe_path_component(value: str) -> str:
    """Return a filesystem-safe path component for dataset paths."""

    cleaned = value.strip().replace("\\", "_").replace("/", "_").replace(" ", "_")
    return cleaned or "UNKNOWN"


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


def save_results(config: GeneticSearchConfig, results: Sequence[GenomeEvaluation]) -> Path:
    """Save genetic search datasets."""

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    strategy_id = safe_path_component(config.strategy_id)
    output_dir = Path(config.output_dir) / strategy_id / config.asset / config.timeframe / "genetic_search" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "summary.json"
    runs_path = output_dir / "genetic_evaluations.jsonl"

    payload = {
        "run_id": run_id,
        "dataset_contract_version": "strategy_dataset_contract.v0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "strategy_id": config.strategy_id,
        "strategy_family": parse_strategy_family(config.strategy_id),
        "strategy_version": parse_strategy_version(config.strategy_id),
        "asset": config.asset,
        "timeframe": config.timeframe,
        "experiment_type": "genetic_search",
        "config": asdict(config),
        "best": evaluation_to_dict(results[0]) if results else None,
        "top_10": [evaluation_to_dict(item) for item in results[:10]],
        "total_evaluations": len(results),
        "methodology_notes": [
            "P1-Net contract enforced: start_lot equals net_abs_lots.",
            "Adjusted score penalizes excessive protection blocking.",
            "Adjusted score penalizes very low rebalance activity.",
            "Adjusted score penalizes weak worst-regime performance.",
            "Adjusted score penalizes high score dispersion between regimes.",
            "Synthetic Monte Carlo only; historical data validation is not implemented yet.",
        ],
    }

    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with runs_path.open("w", encoding="utf-8") as handle:
        for item in results:
            handle.write(json.dumps(evaluation_to_dict(item), ensure_ascii=False) + "\n")

    print(f"\nSaved genetic search summary: {summary_path}")
    print(f"Saved genetic search evaluations: {runs_path}")
    return output_dir


def evaluation_to_dict(item: GenomeEvaluation) -> dict:
    """Convert evaluation to JSON-safe dict."""

    payload = asdict(item)
    payload["genome"]["initial_side"] = item.genome.initial_side.value
    payload["genome"]["start_lot"] = item.genome.start_lot
    return payload


def mean(values: Sequence[float]) -> float:
    """Return safe mean."""

    if not values:
        return 0.0

    return sum(values) / len(values)


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    config = build_config(args)

    print("=== HEDGE EVOLUTION LAB — GENETIC SEARCH V0.2 ===")
    print(f"strategy_id: {config.strategy_id}")
    print(f"asset: {config.asset}")
    print(f"timeframe: {config.timeframe}")
    print(f"generations: {config.generations}")
    print(f"population: {config.population}")
    print(f"elite_size: {config.elite_size}")
    print(f"mutation_rate: {config.mutation_rate}")
    print(f"runs_per_candidate: {config.runs}")
    print(f"steps: {config.steps}")
    print(f"seed: {config.seed}")
    print(f"min_avg_rebalance_count: {config.min_avg_rebalance_count}")
    print(f"max_avg_protection_blocks: {config.max_avg_protection_blocks}")
    print(f"regime_balance_weight: {config.regime_balance_weight}")
    print(f"worst_regime_weight: {config.worst_regime_weight}")

    results = run_genetic_search(config)
    print_final_ranking(results)

    if config.save_json:
        save_results(config=config, results=results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
