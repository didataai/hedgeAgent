"""
File: hedge_lab/strategies/p1_net.py

Purpose:
    Implement the first manual strategy prototype: P1-Net v0.

Inputs:
    - Price events from a scenario.
    - ExecutionEngine from hedge_lab.simulator.core.
    - P1NetConfig parameters such as initial side, target net and range distance.

Outputs:
    - Market orders sent to the ExecutionEngine.
    - P1NetState updates such as last_level and number of fired rebalances.

Integrations:
    - Uses hedge_lab.simulator.core.Side and ExecutionEngine.
    - Used by hedge_lab.simulator.run_simulation.
    - Later can be converted into a genome module for the evolution layer.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - No symbol-specific or timeframe-specific assumptions.
    - P1-Net controls NET exposure, but it does not guarantee low risk because gross lots can still grow.
    - Default initial_side is SELL because the first default scenario moves upward first, which validates adverse-move rebalance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from hedge_lab.simulator.core import ExecutionEngine, Side


@dataclass(frozen=True)
class P1NetConfig:
    """Configuration for P1-Net v0."""

    initial_side: Side = Side.SELL
    start_lot: float = 0.02
    net_abs_lots: float = 0.02
    range_points: float = 300.0
    min_add_lot: float = 0.01
    lot_step: float = 0.01
    net_tolerance: float = 1e-9
    comment: str = "P1_NET_V0"


@dataclass
class P1NetState:
    """Runtime state for P1-Net v0."""

    started: bool = False
    last_level: Optional[float] = None
    rebalance_count: int = 0
    last_action: str = "NOT_STARTED"


class P1NetStrategy:
    """
    P1-Net v0.

    Rule:
        - Start with one BUY or SELL.
        - If net is positive and price falls by range_points from last_level,
          open SELL volume needed to make net = -net_abs_lots.
        - If net is negative and price rises by range_points from last_level,
          open BUY volume needed to make net = +net_abs_lots.
    """

    def __init__(self, config: P1NetConfig):
        self.config = config
        self.state = P1NetState()

    def on_price(self, engine: ExecutionEngine, price: float) -> None:
        """Process one price point and possibly send an order."""

        if not self.state.started:
            self._start(engine=engine, price=price)
            return

        if self.state.last_level is None:
            self.state.last_level = price

        net = engine.portfolio.net_lots()
        distance = self.config.range_points

        if net >= (self.config.net_abs_lots - self.config.net_tolerance):
            if price <= self.state.last_level - distance:
                self._rebalance_to(engine=engine, target_net=-self.config.net_abs_lots, price=price)
                self.state.last_level = price
                self.state.rebalance_count += 1
                self.state.last_action = "REBALANCE_TO_NEGATIVE_NET"
                return

        if net <= (-self.config.net_abs_lots + self.config.net_tolerance):
            if price >= self.state.last_level + distance:
                self._rebalance_to(engine=engine, target_net=self.config.net_abs_lots, price=price)
                self.state.last_level = price
                self.state.rebalance_count += 1
                self.state.last_action = "REBALANCE_TO_POSITIVE_NET"
                return

        self.state.last_action = "HOLD"

    def _start(self, engine: ExecutionEngine, price: float) -> None:
        """Open the initial position and define the first reference level."""

        engine.open_market(
            side=self.config.initial_side,
            volume=self._normalize_lot(self.config.start_lot),
            price=price,
            comment=f"{self.config.comment}:initial",
        )
        self.state.started = True
        self.state.last_level = price
        self.state.last_action = f"START_{self.config.initial_side.value}"

    def _rebalance_to(self, engine: ExecutionEngine, target_net: float, price: float) -> None:
        """Open the minimum required order to reach the target net."""

        buy_lots = engine.portfolio.buy_lots()
        sell_lots = engine.portfolio.sell_lots()

        if target_net > 0:
            required_buy_total = sell_lots + target_net
            add_buy = self._normalize_lot(required_buy_total - buy_lots)
            if add_buy >= self.config.min_add_lot:
                engine.open_market(
                    side=Side.BUY,
                    volume=add_buy,
                    price=price,
                    comment=f"{self.config.comment}:rebalance_buy",
                )
            return

        required_sell_total = buy_lots + abs(target_net)
        add_sell = self._normalize_lot(required_sell_total - sell_lots)
        if add_sell >= self.config.min_add_lot:
            engine.open_market(
                side=Side.SELL,
                volume=add_sell,
                price=price,
                comment=f"{self.config.comment}:rebalance_sell",
            )

    def _normalize_lot(self, volume: float) -> float:
        """Normalize volume to the configured lot step."""

        if volume <= 0:
            return 0.0

        step = self.config.lot_step
        normalized = round(round(volume / step) * step, 10)
        return normalized
