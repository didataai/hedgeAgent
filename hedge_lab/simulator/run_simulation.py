"""
File: hedge_lab/simulator/run_simulation.py

Purpose:
    Run the first executable Hedge Evolution Lab simulation using P1-Net v0.

Inputs:
    - Optional CLI arguments:
        --asset
        --timeframe
        --scenario
        --initial-side
        --start-lot
        --net-abs-lots
        --range-points
        --max-gross-lots
        --max-positions
        --max-drawdown-pct

Outputs:
    - Console summary with account, risk and exposure metrics.

Integrations:
    - Uses hedge_lab.simulator.core.ExecutionEngine.
    - Uses hedge_lab.scenarios.basic_paths.
    - Uses hedge_lab.strategies.p1_net.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - This is a deterministic smoke-test runner, not a full backtester yet.
    - Keep this file small until the simulator contract stabilizes.
    - Default initial side is SELL because the default range_up_down scenario moves upward first.
"""

from __future__ import annotations

import argparse
from typing import Iterable

from hedge_lab.scenarios.basic_paths import PricePathScenario, get_basic_scenarios
from hedge_lab.simulator.core import ExecutionEngine, Side, SimulationConfig
from hedge_lab.strategies.p1_net import P1NetConfig, P1NetStrategy


def parse_side(value: str) -> Side:
    """Parse BUY/SELL CLI values."""

    normalized = value.strip().upper()
    if normalized == "BUY":
        return Side.BUY
    if normalized == "SELL":
        return Side.SELL
    raise argparse.ArgumentTypeError("initial side must be BUY or SELL")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the smoke-test simulation runner."""

    parser = argparse.ArgumentParser(description="Run Hedge Evolution Lab P1-Net v0 simulation.")
    parser.add_argument("--asset", default="SYNTH", help="Asset/symbol label. Example: GOLD, EURUSD, SYNTH.")
    parser.add_argument("--timeframe", default="SIM", help="Timeframe label. Example: M5, H1, SIM.")
    parser.add_argument("--scenario", default="range_up_down", help="Scenario name.")
    parser.add_argument("--initial-side", type=parse_side, default=Side.SELL, help="Initial side: BUY or SELL.")
    parser.add_argument("--start-lot", type=float, default=0.02, help="Initial position volume.")
    parser.add_argument("--net-abs-lots", type=float, default=0.02, help="Target absolute net lots.")
    parser.add_argument("--range-points", type=float, default=300.0, help="Distance required to rebalance net.")
    parser.add_argument("--initial-balance", type=float, default=10_000.0, help="Initial simulated account balance.")
    parser.add_argument("--point-value", type=float, default=1.0, help="PNL multiplier per price unit and lot.")
    parser.add_argument("--max-gross-lots", type=float, default=1.0, help="Risk limit for gross lots.")
    parser.add_argument("--max-positions", type=int, default=100, help="Risk limit for open positions.")
    parser.add_argument("--max-drawdown-pct", type=float, default=30.0, help="Risk limit for max drawdown percent.")
    return parser


def run_scenario(scenario: PricePathScenario, strategy: P1NetStrategy, engine: ExecutionEngine) -> str | None:
    """
    Run a scenario and stop early if a risk limit is breached.

    Returns:
        Failure reason or None when survived.
    """

    failure_reason = None

    for index, price in enumerate(scenario.prices):
        strategy.on_price(engine=engine, price=price)
        failure_reason = engine.check_risk_limits(price)

        print_step(index=index, price=price, strategy=strategy, engine=engine)

        if failure_reason:
            break

    return failure_reason


def print_step(index: int, price: float, strategy: P1NetStrategy, engine: ExecutionEngine) -> None:
    """Print one compact simulation step."""

    print(
        f"step={index:02d} "
        f"price={price:.2f} "
        f"action={strategy.state.last_action} "
        f"buy={engine.portfolio.buy_lots():.2f} "
        f"sell={engine.portfolio.sell_lots():.2f} "
        f"net={engine.portfolio.net_lots():.2f} "
        f"gross={engine.portfolio.gross_lots():.2f} "
        f"floating={engine.portfolio.floating_pnl(price, engine.config.point_value):.2f} "
        f"equity={engine.account.equity:.2f}"
    )


def print_summary(scenario: PricePathScenario, strategy: P1NetStrategy, engine: ExecutionEngine, failure_reason: str | None) -> None:
    """Print final simulation summary."""

    final_price = scenario.prices[-1]
    result = engine.result(price=final_price, failure_reason=failure_reason)

    print("\n=== SIMULATION SUMMARY ===")
    print(f"asset: {scenario.asset}")
    print(f"timeframe: {scenario.timeframe}")
    print(f"scenario: {scenario.name}")
    print(f"description: {scenario.description}")
    print("strategy: P1-Net v0")
    print(f"survived: {result.survived}")
    print(f"failure_reason: {result.failure_reason}")
    print(f"final_balance: {result.final_balance:.2f}")
    print(f"final_equity: {result.final_equity:.2f}")
    print(f"realized_profit: {result.realized_profit:.2f}")
    print(f"floating_profit: {result.floating_profit:.2f}")
    print(f"max_drawdown_pct: {result.max_drawdown:.4f}")
    print(f"final_buy_lots: {engine.portfolio.buy_lots():.2f}")
    print(f"final_sell_lots: {engine.portfolio.sell_lots():.2f}")
    print(f"final_net_lots: {engine.portfolio.net_lots():.2f}")
    print(f"final_gross_lots: {engine.portfolio.gross_lots():.2f}")
    print(f"max_gross_lots: {result.max_gross_lots:.2f}")
    print(f"max_positions: {result.max_positions}")
    print(f"rebalance_count: {strategy.state.rebalance_count}")


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    scenarios = get_basic_scenarios(asset=args.asset, timeframe=args.timeframe)
    if args.scenario not in scenarios:
        available = ", ".join(sorted(scenarios))
        raise SystemExit(f"Unknown scenario '{args.scenario}'. Available: {available}")

    scenario = scenarios[args.scenario]

    engine = ExecutionEngine(
        SimulationConfig(
            initial_balance=args.initial_balance,
            point_value=args.point_value,
            max_gross_lots=args.max_gross_lots,
            max_positions=args.max_positions,
            max_drawdown_pct=args.max_drawdown_pct,
        )
    )

    strategy = P1NetStrategy(
        P1NetConfig(
            initial_side=args.initial_side,
            start_lot=args.start_lot,
            net_abs_lots=args.net_abs_lots,
            range_points=args.range_points,
        )
    )

    print("=== HEDGE EVOLUTION LAB — P1-NET V0 ===")
    failure_reason = run_scenario(scenario=scenario, strategy=strategy, engine=engine)
    print_summary(scenario=scenario, strategy=strategy, engine=engine, failure_reason=failure_reason)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
