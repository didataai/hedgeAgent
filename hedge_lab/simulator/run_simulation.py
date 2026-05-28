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
        --disable-protection
        --strategy-max-gross-to-net-ratio
        --strategy-max-gross-lots
        --strategy-max-positions

Outputs:
    - Console summary with account, risk, protection and exposure metrics.

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
from typing import Iterable, Optional

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

    parser.add_argument("--max-gross-lots", type=float, default=1.0, help="Engine risk limit for gross lots.")
    parser.add_argument("--max-positions", type=int, default=100, help="Engine risk limit for open positions.")
    parser.add_argument("--max-drawdown-pct", type=float, default=30.0, help="Engine risk limit for max drawdown percent.")

    parser.add_argument(
        "--disable-protection",
        action="store_true",
        help="Disable strategy-level Protection Mode v0.",
    )
    parser.add_argument(
        "--strategy-max-gross-to-net-ratio",
        type=parse_optional_float,
        default=7.0,
        help="Strategy protection limit for gross/net ratio. Use 'none' to disable this limit.",
    )
    parser.add_argument(
        "--strategy-max-gross-lots",
        type=parse_optional_float,
        default=None,
        help="Strategy protection limit for gross lots. Use 'none' to disable this limit.",
    )
    parser.add_argument(
        "--strategy-max-positions",
        type=parse_optional_int,
        default=None,
        help="Strategy protection limit for position count. Use 'none' to disable this limit.",
    )

    return parser


def run_scenario(scenario: PricePathScenario, strategy: P1NetStrategy, engine: ExecutionEngine) -> str | None:
    """
    Run a scenario and stop early if an engine risk limit is breached.

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

    exposure = engine.current_exposure_metrics(
        price=price,
        target_net_abs=strategy.config.net_abs_lots,
    )

    gross_flag = "GROSS_EXPANDING" if exposure.gross_is_expanding else "gross_ok"
    net_flag = "NET_CONTROLLED" if exposure.net_is_controlled else "net_drift"
    protection_reason = strategy.state.last_protection_reason or "none"

    print(
        f"step={index:02d} "
        f"price={price:.2f} "
        f"action={strategy.state.last_action} "
        f"protection={protection_reason} "
        f"buy={exposure.buy_lots:.2f} "
        f"sell={exposure.sell_lots:.2f} "
        f"net={exposure.net_lots:.2f} "
        f"gross={exposure.gross_lots:.2f} "
        f"ratio={exposure.gross_to_net_ratio:.2f} "
        f"recovery_power={exposure.recovery_power:.2f} "
        f"risk_debt={exposure.risk_debt:.2f} "
        f"floating={exposure.floating_profit:.2f} "
        f"equity={engine.account.equity:.2f} "
        f"{net_flag} "
        f"{gross_flag}"
    )


def print_summary(
    scenario: PricePathScenario,
    strategy: P1NetStrategy,
    engine: ExecutionEngine,
    failure_reason: str | None,
) -> None:
    """Print final simulation summary."""

    final_price = scenario.prices[-1]
    result = engine.result(
        price=final_price,
        failure_reason=failure_reason,
        target_net_abs=strategy.config.net_abs_lots,
    )

    exposure = engine.current_exposure_metrics(
        price=final_price,
        target_net_abs=strategy.config.net_abs_lots,
    )

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
    print(f"final_buy_lots: {exposure.buy_lots:.2f}")
    print(f"final_sell_lots: {exposure.sell_lots:.2f}")
    print(f"final_net_lots: {result.final_net_lots:.2f}")
    print(f"final_gross_lots: {result.final_gross_lots:.2f}")
    print(f"max_gross_lots: {result.max_gross_lots:.2f}")
    print(f"max_positions: {result.max_positions}")
    print(f"recovery_power: {result.recovery_power:.2f}")
    print(f"risk_debt: {result.risk_debt:.2f}")
    print(f"gross_to_net_ratio: {result.gross_to_net_ratio:.2f}")
    print(f"net_is_controlled: {exposure.net_is_controlled}")
    print(f"gross_is_expanding: {exposure.gross_is_expanding}")
    print(f"rebalance_count: {strategy.state.rebalance_count}")
    print(f"protection_enabled: {strategy.config.enable_protection}")
    print(f"protection_block_count: {strategy.state.protection_block_count}")
    print(f"last_protection_reason: {strategy.state.last_protection_reason}")

    print("\n=== INTERPRETATION ===")
    if strategy.state.protection_block_count > 0:
        print(
            "Protection Mode blocked at least one new rebalance. "
            "The strategy stopped adding inventory after reaching a configured risk limit."
        )

    if exposure.net_is_controlled and exposure.gross_is_expanding:
        print(
            "NET is controlled, but GROSS is expanding. "
            "This confirms hidden hedge inventory risk."
        )
    elif exposure.net_is_controlled:
        print("NET is controlled and GROSS is not expanding beyond the initial exposure.")
    else:
        print("NET is not controlled at the final price. Strategy state requires review.")

    if result.risk_debt > result.recovery_power:
        print("Risk debt is greater than recovery power at the final price.")
    elif result.recovery_power > result.risk_debt:
        print("Recovery power is greater than risk debt at the final price.")
    else:
        print("Recovery power and risk debt are balanced at the final price.")


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
            enable_protection=not args.disable_protection,
            max_gross_to_net_ratio=args.strategy_max_gross_to_net_ratio,
            max_strategy_gross_lots=args.strategy_max_gross_lots,
            max_strategy_positions=args.strategy_max_positions,
        )
    )

    print("=== HEDGE EVOLUTION LAB — P1-NET V0 ===")
    failure_reason = run_scenario(scenario=scenario, strategy=strategy, engine=engine)
    print_summary(scenario=scenario, strategy=strategy, engine=engine, failure_reason=failure_reason)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
