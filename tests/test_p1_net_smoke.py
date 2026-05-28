"""
File: tests/test_p1_net_smoke.py

Purpose:
    Provide a minimal smoke test for the first P1-Net v0 simulation.

Inputs:
    - Internal synthetic range_up_down scenario.
    - P1NetStrategy default-compatible configuration.

Outputs:
    - Pytest pass/fail result.

Integrations:
    - Uses hedge_lab.simulator.core.
    - Uses hedge_lab.scenarios.basic_paths.
    - Uses hedge_lab.strategies.p1_net.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - This test validates mechanics only; it does not claim profitability.
"""

from hedge_lab.scenarios.basic_paths import get_basic_scenarios
from hedge_lab.simulator.core import ExecutionEngine, SimulationConfig, Side
from hedge_lab.strategies.p1_net import P1NetConfig, P1NetStrategy


def test_p1_net_range_up_down_survives_with_expected_exposure():
    scenarios = get_basic_scenarios(asset="TEST", timeframe="SIM")
    scenario = scenarios["range_up_down"]

    engine = ExecutionEngine(SimulationConfig(max_gross_lots=1.0))
    strategy = P1NetStrategy(
        P1NetConfig(
            initial_side=Side.SELL,
            start_lot=0.02,
            net_abs_lots=0.02,
            range_points=300.0,
        )
    )

    failure_reason = None
    for price in scenario.prices:
        strategy.on_price(engine=engine, price=price)
        failure_reason = engine.check_risk_limits(price)
        if failure_reason:
            break

    assert failure_reason is None
    assert round(abs(engine.portfolio.net_lots()), 2) == 0.02
    assert engine.portfolio.gross_lots() > 0.02
    assert strategy.state.rebalance_count >= 1
