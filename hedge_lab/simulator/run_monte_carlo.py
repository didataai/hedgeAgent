"""
File: hedge_lab/simulator/run_monte_carlo.py

Purpose:
    Run Monte Carlo, synthetic walk-forward and synthetic back-forward validation
    for the Hedge Evolution Lab using strategy-aware prototypes.

Inputs:
    - CLI arguments:
        --strategy-id
        --asset
        --timeframe
        --runs
        --steps
        --seed
        --mode
        --initial-side
        --start-lot
        --net-abs-lots
        --range-points
        --multiplier
        --initial-balance
        --point-value
        --max-gross-lots
        --max-positions
        --max-drawdown-pct
        --disable-protection
        --compare-protection
        --strategy-max-gross-to-net-ratio
        --strategy-max-gross-lots
        --strategy-max-positions
        --save-json
        --output-dir

Outputs:
    - Console summaries for:
        - Monte Carlo aggregate results.
        - Optional protection ON vs OFF comparison.
        - Synthetic walk-forward windows.
        - Synthetic back-forward windows.
        - Score Engine v0 robustness ranking and protection delta.
        - Optional JSON/JSONL dataset files for later agent/evolution consumption.

Integrations:
    - Uses hedge_lab.simulator.core.ExecutionEngine.
    - Uses hedge_lab.strategies.p1_net.P1NetStrategy.
    - Uses hedge_lab.strategies.p1_multiplier.P1MultiplierStrategy.
    - Saves datasets in a strategy-aware layout for evolution, agents, LLM and orchestrator layers.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - Dataset contract v0:
        datasets/strategies/<STRATEGY_ID>/<ASSET>/<TIMEFRAME>/<EXPERIMENT_TYPE>/<RUN_ID>/
    - This v0 uses synthetic paths only. It is not historical backtest yet.
    - Walk-forward/back-forward here means synthetic window validation, not parameter optimization.
    - The purpose is to reveal robustness patterns before adding real historical data.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

from hedge_lab.simulator.core import ExecutionEngine, Side, SimulationConfig, SimulationResult
from hedge_lab.strategies.p1_net import P1NetConfig, P1NetStrategy
from hedge_lab.strategies.p1_multiplier import P1MultiplierConfig, P1MultiplierStrategy


@dataclass(frozen=True)
class SyntheticPath:
    """Synthetic market path for robustness tests."""

    name: str
    strategy_id: str
    asset: str
    timeframe: str
    regime: str
    prices: List[float]


@dataclass(frozen=True)
class RunMetrics:
    """Single simulation run metrics."""

    survived: bool
    failure_reason: Optional[str]
    final_equity: float
    final_balance: float
    realized_profit: float
    floating_profit: float
    max_drawdown: float
    max_gross_lots: float
    max_positions: int
    final_net_lots: float
    final_gross_lots: float
    recovery_power: float
    risk_debt: float
    gross_to_net_ratio: float
    rebalance_count: int
    protection_block_count: int
    path_name: str
    regime: str


@dataclass(frozen=True)
class AggregateMetrics:
    """Aggregate metrics and Score Engine v0 result."""

    label: str
    runs: int
    survived: int
    failed: int
    survival_rate_pct: float
    failure_rate_pct: float
    avg_final_equity: float
    min_final_equity: float
    max_final_equity: float
    avg_max_drawdown_pct: float
    worst_max_drawdown_pct: float
    avg_max_gross_lots: float
    worst_max_gross_lots: float
    avg_max_positions: float
    worst_max_positions: int
    avg_final_risk_debt: float
    worst_final_risk_debt: float
    total_protection_blocks: int
    avg_protection_blocks: float
    robustness_score: float


@dataclass(frozen=True)
class ExperimentConfig:
    """Combined configuration for synthetic experiments."""

    strategy_id: str
    asset: str
    timeframe: str
    runs: int
    steps: int
    seed: int
    initial_side: Side
    start_lot: float
    net_abs_lots: float
    range_points: float
    multiplier: float
    initial_balance: float
    point_value: float
    max_gross_lots: float
    max_positions: int
    max_drawdown_pct: float
    enable_protection: bool
    strategy_max_gross_to_net_ratio: Optional[float]
    strategy_max_gross_lots: Optional[float]
    strategy_max_positions: Optional[int]


def parse_side(value: str) -> Side:
    """Parse BUY/SELL CLI values."""

    normalized = value.strip().upper()
    if normalized == "BUY":
        return Side.BUY
    if normalized == "SELL":
        return Side.SELL

    raise argparse.ArgumentTypeError("initial side must be BUY or SELL")


def parse_optional_float(value: str) -> Optional[float]:
    """Parse optional float CLI values."""

    normalized = value.strip().lower()
    if normalized in {"none", "null", "off", "disabled"}:
        return None

    return float(value)


def parse_optional_int(value: str) -> Optional[int]:
    """Parse optional integer CLI values."""

    normalized = value.strip().lower()
    if normalized in {"none", "null", "off", "disabled"}:
        return None

    return int(value)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Run Hedge Evolution Lab Monte Carlo v0.")
    parser.add_argument(
        "--strategy-id",
        default="P1_NET_V0",
        help="Stable strategy identifier used in dataset paths and summaries.",
    )
    parser.add_argument("--asset", default="SYNTH", help="Asset/symbol label. Example: GOLD, EURUSD, SYNTH.")
    parser.add_argument("--timeframe", default="SIM", help="Timeframe label. Example: M5, H1, SIM.")
    parser.add_argument(
        "--mode",
        default="monte_carlo",
        choices=["monte_carlo", "walk_forward", "back_forward", "all"],
        help="Validation mode.",
    )
    parser.add_argument("--runs", type=int, default=1000, help="Number of Monte Carlo paths.")
    parser.add_argument("--steps", type=int, default=120, help="Number of prices per synthetic path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible synthetic paths.")

    parser.add_argument("--initial-side", type=parse_side, default=Side.SELL, help="Initial side: BUY or SELL.")
    parser.add_argument("--start-lot", type=float, default=0.02, help="Initial position volume.")
    parser.add_argument("--net-abs-lots", type=float, default=0.02, help="Target absolute net lots.")
    parser.add_argument("--range-points", type=float, default=300.0, help="Distance required to rebalance net.")
    parser.add_argument(
        "--multiplier",
        type=float,
        default=2.0,
        help="Multiplier used by P1_MULTIPLIER_V0. Ignored by P1_NET_V0.",
    )
    parser.add_argument("--initial-balance", type=float, default=10_000.0, help="Initial simulated account balance.")
    parser.add_argument("--point-value", type=float, default=1.0, help="PNL multiplier per price unit and lot.")

    parser.add_argument("--max-gross-lots", type=float, default=1.0, help="Engine risk limit for gross lots.")
    parser.add_argument("--max-positions", type=int, default=100, help="Engine risk limit for open positions.")
    parser.add_argument("--max-drawdown-pct", type=float, default=30.0, help="Engine risk limit for max drawdown percent.")

    parser.add_argument(
        "--disable-protection",
        action="store_true",
        help="Disable strategy-level Protection Mode v0.",
    )
    parser.add_argument(
        "--compare-protection",
        action="store_true",
        help="Run the same synthetic paths with protection ON and OFF and compare results.",
    )
    parser.add_argument(
        "--strategy-max-gross-to-net-ratio",
        type=parse_optional_float,
        default=7.0,
        help="Strategy protection limit for gross/net ratio. Use 'none' to disable.",
    )
    parser.add_argument(
        "--strategy-max-gross-lots",
        type=parse_optional_float,
        default=None,
        help="Strategy protection limit for gross lots. Use 'none' to disable.",
    )
    parser.add_argument(
        "--strategy-max-positions",
        type=parse_optional_int,
        default=None,
        help="Strategy protection limit for position count. Use 'none' to disable.",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save aggregate summaries and per-run metrics under --output-dir.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/strategies",
        help="Base output directory for strategy-aware JSON/JSONL datasets.",
    )

    return parser


def generate_monte_carlo_paths(config: ExperimentConfig) -> List[SyntheticPath]:
    """Generate reproducible synthetic paths across different regimes."""

    rng = random.Random(config.seed)
    regimes = [
        "random_walk",
        "range_noise",
        "trend_up",
        "trend_down",
        "spike_return",
        "spike_no_return",
        "whipsaw",
        "volatility_expansion",
    ]

    paths = []
    for run_id in range(config.runs):
        regime = regimes[run_id % len(regimes)]
        prices = generate_path(
            rng=rng,
            regime=regime,
            start_price=3000.0,
            steps=config.steps,
            range_points=config.range_points,
        )
        paths.append(
            SyntheticPath(
                name=f"mc_{run_id:06d}_{regime}",
                strategy_id=config.strategy_id,
                asset=config.asset,
                timeframe=config.timeframe,
                regime=regime,
                prices=prices,
            )
        )

    return paths


def generate_walk_windows(config: ExperimentConfig) -> List[SyntheticPath]:
    """Generate deterministic synthetic windows in chronological order."""

    rng = random.Random(config.seed)
    regimes = [
        "range_noise",
        "spike_return",
        "trend_up",
        "whipsaw",
        "trend_down",
        "volatility_expansion",
        "spike_no_return",
        "random_walk",
    ]

    return [
        SyntheticPath(
            name=f"wf_window_{index:02d}_{regime}",
            strategy_id=config.strategy_id,
            asset=config.asset,
            timeframe=config.timeframe,
            regime=regime,
            prices=generate_path(
                rng=rng,
                regime=regime,
                start_price=3000.0,
                steps=config.steps,
                range_points=config.range_points,
            ),
        )
        for index, regime in enumerate(regimes)
    ]


def generate_back_windows(config: ExperimentConfig) -> List[SyntheticPath]:
    """Generate deterministic synthetic windows in reverse validation order."""

    windows = generate_walk_windows(config)
    return list(reversed(windows))


def generate_path(
    rng: random.Random,
    regime: str,
    start_price: float,
    steps: int,
    range_points: float,
) -> List[float]:
    """Generate one synthetic price path."""

    if steps < 2:
        return [start_price]

    price = start_price
    prices = [price]

    for index in range(1, steps):
        if regime == "random_walk":
            delta = rng.choice([-1, 1]) * rng.uniform(0.2, 1.0) * range_points

        elif regime == "range_noise":
            center = start_price
            pull = (center - price) * 0.35
            noise = rng.uniform(-0.35, 0.35) * range_points
            delta = pull + noise

        elif regime == "trend_up":
            delta = rng.uniform(0.25, 0.85) * range_points

        elif regime == "trend_down":
            delta = -rng.uniform(0.25, 0.85) * range_points

        elif regime == "spike_return":
            if index == max(1, steps // 4):
                delta = rng.choice([-1, 1]) * rng.uniform(1.5, 3.0) * range_points
            else:
                delta = (start_price - price) * 0.25 + rng.uniform(-0.25, 0.25) * range_points

        elif regime == "spike_no_return":
            if index == max(1, steps // 4):
                delta = rng.choice([-1, 1]) * rng.uniform(1.5, 3.0) * range_points
            else:
                direction = 1 if price >= start_price else -1
                delta = direction * rng.uniform(0.05, 0.45) * range_points

        elif regime == "whipsaw":
            direction = 1 if index % 2 == 1 else -1
            delta = direction * rng.uniform(0.75, 1.25) * range_points

        elif regime == "volatility_expansion":
            scale = 0.15 + (index / max(1, steps - 1)) * 1.35
            delta = rng.choice([-1, 1]) * rng.uniform(0.2, scale) * range_points

        else:
            raise ValueError(f"Unknown regime: {regime}")

        price = max(0.01, price + delta)
        prices.append(round(price, 5))

    return prices



def build_strategy(config: ExperimentConfig) -> Any:
    """Build a strategy instance from strategy_id."""

    strategy_id = config.strategy_id.strip().upper()

    if strategy_id == "P1_NET_V0":
        return P1NetStrategy(
            P1NetConfig(
                initial_side=config.initial_side,
                start_lot=config.start_lot,
                net_abs_lots=config.net_abs_lots,
                range_points=config.range_points,
                enable_protection=config.enable_protection,
                max_gross_to_net_ratio=config.strategy_max_gross_to_net_ratio,
                max_strategy_gross_lots=config.strategy_max_gross_lots,
                max_strategy_positions=config.strategy_max_positions,
            )
        )

    if strategy_id == "P1_MULTIPLIER_V0":
        return P1MultiplierStrategy(
            P1MultiplierConfig(
                initial_side=config.initial_side,
                start_lot=config.start_lot,
                range_points=config.range_points,
                multiplier=config.multiplier,
                enable_protection=config.enable_protection,
                max_gross_to_net_ratio=config.strategy_max_gross_to_net_ratio,
                max_strategy_gross_lots=config.strategy_max_gross_lots,
                max_strategy_positions=config.strategy_max_positions,
            )
        )

    raise ValueError(
        f"Unsupported strategy_id: {config.strategy_id}. "
        "Supported: P1_NET_V0, P1_MULTIPLIER_V0"
    )


def run_path(path: SyntheticPath, config: ExperimentConfig) -> RunMetrics:
    """Run one strategy simulation over one synthetic path."""

    engine = ExecutionEngine(
        SimulationConfig(
            initial_balance=config.initial_balance,
            point_value=config.point_value,
            max_gross_lots=config.max_gross_lots,
            max_positions=config.max_positions,
            max_drawdown_pct=config.max_drawdown_pct,
        )
    )

    strategy = build_strategy(config=config)

    failure_reason = None
    for price in path.prices:
        strategy.on_price(engine=engine, price=price)
        failure_reason = engine.check_risk_limits(price)
        if failure_reason:
            break

    final_price = path.prices[-1]
    result = engine.result(
        price=final_price,
        failure_reason=failure_reason,
        target_net_abs=config.net_abs_lots,
    )

    return build_run_metrics(
        path=path,
        result=result,
        strategy=strategy,
    )


def build_run_metrics(path: SyntheticPath, result: SimulationResult, strategy: Any) -> RunMetrics:
    """Convert SimulationResult into Monte Carlo metrics."""

    return RunMetrics(
        survived=result.survived,
        failure_reason=result.failure_reason,
        final_equity=result.final_equity,
        final_balance=result.final_balance,
        realized_profit=result.realized_profit,
        floating_profit=result.floating_profit,
        max_drawdown=result.max_drawdown,
        max_gross_lots=result.max_gross_lots,
        max_positions=result.max_positions,
        final_net_lots=result.final_net_lots,
        final_gross_lots=result.final_gross_lots,
        recovery_power=result.recovery_power,
        risk_debt=result.risk_debt,
        gross_to_net_ratio=result.gross_to_net_ratio,
        rebalance_count=strategy.state.rebalance_count,
        protection_block_count=strategy.state.protection_block_count,
        path_name=path.name,
        regime=path.regime,
    )


def summarize_metrics(label: str, metrics: Sequence[RunMetrics], initial_balance: float) -> AggregateMetrics:
    """Print aggregate metrics and return Score Engine v0 aggregate values."""

    if not metrics:
        print(f"\n=== {label} ===")
        print("No metrics to summarize.")
        return AggregateMetrics(
            label=label,
            runs=0,
            survived=0,
            failed=0,
            survival_rate_pct=0.0,
            failure_rate_pct=100.0,
            avg_final_equity=0.0,
            min_final_equity=0.0,
            max_final_equity=0.0,
            avg_max_drawdown_pct=0.0,
            worst_max_drawdown_pct=0.0,
            avg_max_gross_lots=0.0,
            worst_max_gross_lots=0.0,
            avg_max_positions=0.0,
            worst_max_positions=0,
            avg_final_risk_debt=0.0,
            worst_final_risk_debt=0.0,
            total_protection_blocks=0,
            avg_protection_blocks=0.0,
            robustness_score=-999999.0,
        )

    total = len(metrics)
    survived = sum(1 for item in metrics if item.survived)
    failed = total - survived

    final_equities = [item.final_equity for item in metrics]
    drawdowns = [item.max_drawdown for item in metrics]
    max_gross = [item.max_gross_lots for item in metrics]
    max_positions = [item.max_positions for item in metrics]
    risk_debts = [item.risk_debt for item in metrics]
    protection_blocks = [item.protection_block_count for item in metrics]
    failure_reasons = Counter(item.failure_reason or "NONE" for item in metrics)
    regimes = Counter(item.regime for item in metrics)
    regime_failures = Counter(item.regime for item in metrics if not item.survived)

    avg_final_equity = safe_mean(final_equities)
    min_final_equity = min(final_equities)
    max_final_equity = max(final_equities)
    avg_max_drawdown_pct = safe_mean(drawdowns)
    worst_max_drawdown_pct = max(drawdowns)
    avg_max_gross_lots = safe_mean(max_gross)
    worst_max_gross_lots = max(max_gross)
    avg_max_positions = safe_mean(max_positions)
    worst_max_positions = max(max_positions)
    avg_final_risk_debt = safe_mean(risk_debts)
    worst_final_risk_debt = max(risk_debts)
    total_protection_blocks = sum(protection_blocks)
    avg_protection_blocks = safe_mean(protection_blocks)
    survival_rate_pct = (survived / total) * 100.0
    failure_rate_pct = (failed / total) * 100.0

    robustness_score = calculate_robustness_score(
        survival_rate_pct=survival_rate_pct,
        avg_final_equity=avg_final_equity,
        initial_balance=initial_balance,
        avg_max_drawdown_pct=avg_max_drawdown_pct,
        worst_max_drawdown_pct=worst_max_drawdown_pct,
        avg_max_gross_lots=avg_max_gross_lots,
        worst_max_gross_lots=worst_max_gross_lots,
        avg_max_positions=avg_max_positions,
        worst_max_positions=worst_max_positions,
        avg_final_risk_debt=avg_final_risk_debt,
        worst_final_risk_debt=worst_final_risk_debt,
    )

    aggregate = AggregateMetrics(
        label=label,
        runs=total,
        survived=survived,
        failed=failed,
        survival_rate_pct=survival_rate_pct,
        failure_rate_pct=failure_rate_pct,
        avg_final_equity=avg_final_equity,
        min_final_equity=min_final_equity,
        max_final_equity=max_final_equity,
        avg_max_drawdown_pct=avg_max_drawdown_pct,
        worst_max_drawdown_pct=worst_max_drawdown_pct,
        avg_max_gross_lots=avg_max_gross_lots,
        worst_max_gross_lots=worst_max_gross_lots,
        avg_max_positions=avg_max_positions,
        worst_max_positions=worst_max_positions,
        avg_final_risk_debt=avg_final_risk_debt,
        worst_final_risk_debt=worst_final_risk_debt,
        total_protection_blocks=total_protection_blocks,
        avg_protection_blocks=avg_protection_blocks,
        robustness_score=robustness_score,
    )

    print(f"\n=== {label} ===")
    print(f"runs: {aggregate.runs}")
    print(f"survived: {aggregate.survived}")
    print(f"failed: {aggregate.failed}")
    print(f"survival_rate_pct: {aggregate.survival_rate_pct:.2f}")
    print(f"failure_rate_pct: {aggregate.failure_rate_pct:.2f}")
    print(f"avg_final_equity: {aggregate.avg_final_equity:.2f}")
    print(f"min_final_equity: {aggregate.min_final_equity:.2f}")
    print(f"max_final_equity: {aggregate.max_final_equity:.2f}")
    print(f"avg_max_drawdown_pct: {aggregate.avg_max_drawdown_pct:.4f}")
    print(f"worst_max_drawdown_pct: {aggregate.worst_max_drawdown_pct:.4f}")
    print(f"avg_max_gross_lots: {aggregate.avg_max_gross_lots:.4f}")
    print(f"worst_max_gross_lots: {aggregate.worst_max_gross_lots:.4f}")
    print(f"avg_max_positions: {aggregate.avg_max_positions:.2f}")
    print(f"worst_max_positions: {aggregate.worst_max_positions}")
    print(f"avg_final_risk_debt: {aggregate.avg_final_risk_debt:.2f}")
    print(f"worst_final_risk_debt: {aggregate.worst_final_risk_debt:.2f}")
    print(f"total_protection_blocks: {aggregate.total_protection_blocks}")
    print(f"avg_protection_blocks: {aggregate.avg_protection_blocks:.2f}")
    print(f"robustness_score_v0: {aggregate.robustness_score:.4f}")
    print(f"failure_reasons: {dict(failure_reasons)}")
    print(f"regime_counts: {dict(regimes)}")
    print(f"regime_failures: {dict(regime_failures)}")

    return aggregate


def calculate_robustness_score(
    survival_rate_pct: float,
    avg_final_equity: float,
    initial_balance: float,
    avg_max_drawdown_pct: float,
    worst_max_drawdown_pct: float,
    avg_max_gross_lots: float,
    worst_max_gross_lots: float,
    avg_max_positions: float,
    worst_max_positions: int,
    avg_final_risk_debt: float,
    worst_final_risk_debt: float,
) -> float:
    """Calculate Score Engine v0 robustness score.

    The score intentionally rewards survival and modest profitability, but
    penalizes hidden hedge inventory risk. It is not a final optimization target.
    It is a first ranking signal for comparing variants.
    """

    equity_return_pct = ((avg_final_equity - initial_balance) / initial_balance) * 100.0
    avg_risk_debt_pct = (avg_final_risk_debt / initial_balance) * 100.0
    worst_risk_debt_pct = (worst_final_risk_debt / initial_balance) * 100.0

    return (
        survival_rate_pct * 2.00
        + equity_return_pct * 10.00
        - avg_max_drawdown_pct * 8.00
        - worst_max_drawdown_pct * 4.00
        - avg_max_gross_lots * 30.00
        - worst_max_gross_lots * 20.00
        - avg_max_positions * 1.50
        - worst_max_positions * 0.35
        - avg_risk_debt_pct * 3.00
        - worst_risk_debt_pct * 1.50
    )


def print_protection_delta(mode_label: str, on: AggregateMetrics, off: AggregateMetrics) -> None:
    """Print ON vs OFF delta for one validation mode."""

    print(f"\n=== PROTECTION COMPARISON DELTA — {mode_label} ===")
    print(f"avg_equity_delta_on_minus_off: {on.avg_final_equity - off.avg_final_equity:.2f}")
    print(f"min_equity_delta_on_minus_off: {on.min_final_equity - off.min_final_equity:.2f}")
    print(f"worst_gross_reduction: {off.worst_max_gross_lots - on.worst_max_gross_lots:.4f}")
    print(f"avg_gross_reduction: {off.avg_max_gross_lots - on.avg_max_gross_lots:.4f}")
    print(f"worst_positions_reduction: {off.worst_max_positions - on.worst_max_positions}")
    print(f"avg_positions_reduction: {off.avg_max_positions - on.avg_max_positions:.2f}")
    print(f"worst_drawdown_reduction_pct: {off.worst_max_drawdown_pct - on.worst_max_drawdown_pct:.4f}")
    print(f"avg_drawdown_reduction_pct: {off.avg_max_drawdown_pct - on.avg_max_drawdown_pct:.4f}")
    print(f"worst_risk_debt_reduction: {off.worst_final_risk_debt - on.worst_final_risk_debt:.2f}")
    print(f"avg_risk_debt_reduction: {off.avg_final_risk_debt - on.avg_final_risk_debt:.2f}")
    print(f"robustness_score_on: {on.robustness_score:.4f}")
    print(f"robustness_score_off: {off.robustness_score:.4f}")
    print(f"robustness_delta_on_minus_off: {on.robustness_score - off.robustness_score:.4f}")
    print(f"profit_winner: {winner('PROTECTION_ON', on.avg_final_equity, 'PROTECTION_OFF', off.avg_final_equity, higher_is_better=True)}")
    print(f"risk_winner: {risk_winner(on=on, off=off)}")
    print(f"robustness_winner: {winner('PROTECTION_ON', on.robustness_score, 'PROTECTION_OFF', off.robustness_score, higher_is_better=True)}")


def winner(label_a: str, value_a: float, label_b: str, value_b: float, higher_is_better: bool) -> str:
    """Return winning label for two values."""

    if value_a == value_b:
        return "TIE"

    if higher_is_better:
        return label_a if value_a > value_b else label_b

    return label_a if value_a < value_b else label_b


def risk_winner(on: AggregateMetrics, off: AggregateMetrics) -> str:
    """Return risk winner based on drawdown, gross, positions and risk debt."""

    on_score = (
        on.worst_max_drawdown_pct
        + on.worst_max_gross_lots * 100.0
        + on.worst_max_positions
        + (on.worst_final_risk_debt / 100.0)
    )
    off_score = (
        off.worst_max_drawdown_pct
        + off.worst_max_gross_lots * 100.0
        + off.worst_max_positions
        + (off.worst_final_risk_debt / 100.0)
    )
    return winner("PROTECTION_ON", on_score, "PROTECTION_OFF", off_score, higher_is_better=False)

def print_window_results(label: str, metrics: Sequence[RunMetrics]) -> None:
    """Print compact per-window validation results."""

    print(f"\n=== {label} WINDOWS ===")
    for item in metrics:
        print(
            f"{item.path_name} "
            f"regime={item.regime} "
            f"survived={item.survived} "
            f"failure={item.failure_reason} "
            f"equity={item.final_equity:.2f} "
            f"dd={item.max_drawdown:.4f} "
            f"gross={item.max_gross_lots:.2f} "
            f"positions={item.max_positions} "
            f"risk_debt={item.risk_debt:.2f} "
            f"blocks={item.protection_block_count}"
        )


def safe_mean(values: Sequence[float]) -> float:
    """Return mean without raising on empty sequences."""

    if not values:
        return 0.0

    return statistics.fmean(values)


def run_monte_carlo(config: ExperimentConfig) -> List[RunMetrics]:
    """Run Monte Carlo validation."""

    paths = generate_monte_carlo_paths(config)
    return [run_path(path=path, config=config) for path in paths]


def run_walk_forward(config: ExperimentConfig) -> List[RunMetrics]:
    """Run synthetic walk-forward validation."""

    paths = generate_walk_windows(config)
    return [run_path(path=path, config=config) for path in paths]


def run_back_forward(config: ExperimentConfig) -> List[RunMetrics]:
    """Run synthetic back-forward validation."""

    paths = generate_back_windows(config)
    return [run_path(path=path, config=config) for path in paths]


def with_protection(config: ExperimentConfig, enabled: bool) -> ExperimentConfig:
    """Return a copy of config with protection enabled or disabled."""

    return ExperimentConfig(
        strategy_id=config.strategy_id,
        asset=config.asset,
        timeframe=config.timeframe,
        runs=config.runs,
        steps=config.steps,
        seed=config.seed,
        initial_side=config.initial_side,
        start_lot=config.start_lot,
        net_abs_lots=config.net_abs_lots,
        range_points=config.range_points,
        multiplier=config.multiplier,
        initial_balance=config.initial_balance,
        point_value=config.point_value,
        max_gross_lots=config.max_gross_lots,
        max_positions=config.max_positions,
        max_drawdown_pct=config.max_drawdown_pct,
        enable_protection=enabled,
        strategy_max_gross_to_net_ratio=config.strategy_max_gross_to_net_ratio,
        strategy_max_gross_lots=config.strategy_max_gross_lots,
        strategy_max_positions=config.strategy_max_positions,
    )


def build_config(args: argparse.Namespace) -> ExperimentConfig:
    """Build experiment config from CLI args."""

    return ExperimentConfig(
        strategy_id=args.strategy_id,
        asset=args.asset,
        timeframe=args.timeframe,
        runs=args.runs,
        steps=args.steps,
        seed=args.seed,
        initial_side=args.initial_side,
        start_lot=args.start_lot,
        net_abs_lots=args.net_abs_lots,
        range_points=args.range_points,
        multiplier=args.multiplier,
        initial_balance=args.initial_balance,
        point_value=args.point_value,
        max_gross_lots=args.max_gross_lots,
        max_positions=args.max_positions,
        max_drawdown_pct=args.max_drawdown_pct,
        enable_protection=not args.disable_protection,
        strategy_max_gross_to_net_ratio=args.strategy_max_gross_to_net_ratio,
        strategy_max_gross_lots=args.strategy_max_gross_lots,
        strategy_max_positions=args.strategy_max_positions,
    )


def run_selected_mode(
    config: ExperimentConfig,
    mode: str,
    label_prefix: str,
) -> tuple[dict[str, AggregateMetrics], dict[str, list[RunMetrics]]]:
    """Run selected mode, print results and return aggregate and per-run metrics."""

    summaries: dict[str, AggregateMetrics] = {}
    runs_by_mode: dict[str, list[RunMetrics]] = {}

    if mode in {"monte_carlo", "all"}:
        mc_metrics = run_monte_carlo(config)
        runs_by_mode["monte_carlo"] = mc_metrics
        summaries["monte_carlo"] = summarize_metrics(
            f"{label_prefix} MONTE CARLO",
            mc_metrics,
            initial_balance=config.initial_balance,
        )

    if mode in {"walk_forward", "all"}:
        wf_metrics = run_walk_forward(config)
        runs_by_mode["walk_forward"] = wf_metrics
        print_window_results(f"{label_prefix} WALK-FORWARD", wf_metrics)
        summaries["walk_forward"] = summarize_metrics(
            f"{label_prefix} WALK-FORWARD SUMMARY",
            wf_metrics,
            initial_balance=config.initial_balance,
        )

    if mode in {"back_forward", "all"}:
        bf_metrics = run_back_forward(config)
        runs_by_mode["back_forward"] = bf_metrics
        print_window_results(f"{label_prefix} BACK-FORWARD", bf_metrics)
        summaries["back_forward"] = summarize_metrics(
            f"{label_prefix} BACK-FORWARD SUMMARY",
            bf_metrics,
            initial_balance=config.initial_balance,
        )

    return summaries, runs_by_mode


def build_delta_payload(mode_label: str, on: AggregateMetrics, off: AggregateMetrics) -> dict[str, object]:
    """Build serializable ON vs OFF delta payload."""

    return {
        "mode": mode_label,
        "avg_equity_delta_on_minus_off": on.avg_final_equity - off.avg_final_equity,
        "min_equity_delta_on_minus_off": on.min_final_equity - off.min_final_equity,
        "worst_gross_reduction": off.worst_max_gross_lots - on.worst_max_gross_lots,
        "avg_gross_reduction": off.avg_max_gross_lots - on.avg_max_gross_lots,
        "worst_positions_reduction": off.worst_max_positions - on.worst_max_positions,
        "avg_positions_reduction": off.avg_max_positions - on.avg_max_positions,
        "worst_drawdown_reduction_pct": off.worst_max_drawdown_pct - on.worst_max_drawdown_pct,
        "avg_drawdown_reduction_pct": off.avg_max_drawdown_pct - on.avg_max_drawdown_pct,
        "worst_risk_debt_reduction": off.worst_final_risk_debt - on.worst_final_risk_debt,
        "avg_risk_debt_reduction": off.avg_final_risk_debt - on.avg_final_risk_debt,
        "robustness_score_on": on.robustness_score,
        "robustness_score_off": off.robustness_score,
        "robustness_delta_on_minus_off": on.robustness_score - off.robustness_score,
        "profit_winner": winner(
            "PROTECTION_ON",
            on.avg_final_equity,
            "PROTECTION_OFF",
            off.avg_final_equity,
            higher_is_better=True,
        ),
        "risk_winner": risk_winner(on=on, off=off),
        "robustness_winner": winner(
            "PROTECTION_ON",
            on.robustness_score,
            "PROTECTION_OFF",
            off.robustness_score,
            higher_is_better=True,
        ),
    }


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

def config_to_dict(config: ExperimentConfig) -> dict[str, object]:
    """Return JSON-safe experiment configuration."""

    data = asdict(config)
    data["initial_side"] = config.initial_side.value
    return data


def save_report_bundle(
    output_dir: Path,
    config: ExperimentConfig,
    label: str,
    summaries: dict[str, AggregateMetrics],
    runs_by_mode: dict[str, list[RunMetrics]],
    deltas: Optional[dict[str, dict[str, object]]] = None,
) -> None:
    """Persist aggregate summaries and per-run metrics as JSON/JSONL."""

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_label = label.lower().replace(" ", "_")
    strategy_id = safe_path_component(config.strategy_id)
    base_dir = output_dir / strategy_id / config.asset / config.timeframe / "monte_carlo" / safe_label / run_id
    base_dir.mkdir(parents=True, exist_ok=True)

    summary_payload = {
        "schema_version": "hedge_lab.synthetic_validation.v0",
        "dataset_contract_version": "strategy_dataset_contract.v0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "strategy_id": config.strategy_id,
        "strategy_family": parse_strategy_family(config.strategy_id),
        "strategy_version": parse_strategy_version(config.strategy_id),
        "asset": config.asset,
        "timeframe": config.timeframe,
        "experiment_type": "monte_carlo",
        "label": label,
        "config": config_to_dict(config),
        "summaries": {key: asdict(value) for key, value in summaries.items()},
        "deltas": deltas or {},
    }

    summary_path = base_dir / "summary.json"
    summary_path.write_text(json.dumps(summary_payload, indent=2, sort_keys=True), encoding="utf-8")

    for mode_key, metrics in runs_by_mode.items():
        runs_path = base_dir / f"{mode_key}_runs.jsonl"
        with runs_path.open("w", encoding="utf-8") as handle:
            for item in metrics:
                handle.write(json.dumps(asdict(item), sort_keys=True) + "\n")

    print(f"\nSaved JSON report: {summary_path}")


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    config = build_config(args)

    print("=== HEDGE EVOLUTION LAB — MONTE CARLO / WALK-FORWARD V0 ===")
    print(f"strategy_id: {config.strategy_id}")
    print(f"asset: {config.asset}")
    print(f"timeframe: {config.timeframe}")
    print(f"mode: {args.mode}")
    print(f"runs: {config.runs}")
    print(f"steps: {config.steps}")
    print(f"seed: {config.seed}")
    print(f"protection_enabled: {config.enable_protection}")

    output_dir = Path(args.output_dir)

    if args.compare_protection:
        print("\n=== PROTECTION COMPARISON ENABLED ===")
        protection_on_summaries, protection_on_runs = run_selected_mode(
            config=with_protection(config, enabled=True),
            mode=args.mode,
            label_prefix="PROTECTION_ON",
        )
        protection_off_summaries, protection_off_runs = run_selected_mode(
            config=with_protection(config, enabled=False),
            mode=args.mode,
            label_prefix="PROTECTION_OFF",
        )

        deltas: dict[str, dict[str, object]] = {}
        for mode_key in ["monte_carlo", "walk_forward", "back_forward"]:
            if mode_key in protection_on_summaries and mode_key in protection_off_summaries:
                print_protection_delta(
                    mode_label=mode_key.upper(),
                    on=protection_on_summaries[mode_key],
                    off=protection_off_summaries[mode_key],
                )
                deltas[mode_key] = build_delta_payload(
                    mode_label=mode_key.upper(),
                    on=protection_on_summaries[mode_key],
                    off=protection_off_summaries[mode_key],
                )

        if args.save_json:
            save_report_bundle(
                output_dir=output_dir,
                config=with_protection(config, enabled=True),
                label="PROTECTION_ON",
                summaries=protection_on_summaries,
                runs_by_mode=protection_on_runs,
                deltas=deltas,
            )
            save_report_bundle(
                output_dir=output_dir,
                config=with_protection(config, enabled=False),
                label="PROTECTION_OFF",
                summaries=protection_off_summaries,
                runs_by_mode=protection_off_runs,
                deltas=deltas,
            )
    else:
        label = "PROTECTION_ON" if config.enable_protection else "PROTECTION_OFF"
        summaries, runs_by_mode = run_selected_mode(config=config, mode=args.mode, label_prefix=label)
        if args.save_json:
            save_report_bundle(
                output_dir=output_dir,
                config=config,
                label=label,
                summaries=summaries,
                runs_by_mode=runs_by_mode,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
