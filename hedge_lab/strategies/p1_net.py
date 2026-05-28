"""
File: hedge_lab/strategies/p1_net.py

Purpose:
    Implement the first manual strategy prototype: P1-Net v0.

Inputs:
    - Price events from a scenario.
    - ExecutionEngine from hedge_lab.simulator.core.
    - P1NetConfig parameters such as initial side, target net, range distance and protection limits.

Outputs:
    - Market orders sent to the ExecutionEngine.
    - P1NetState updates such as last_level, rebalance count and protection status.

Integrations:
    - Uses hedge_lab.simulator.core.Side and ExecutionEngine.
    - Used by hedge_lab.simulator.run_simulation.
    - Later can be converted into a genome module for the evolution layer.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - No symbol-specific or timeframe-specific assumptions.
    - P1-Net controls NET exposure, but it does not guarantee low risk because gross lots can still grow.
    - Protection Mode v0 blocks new rebalances when current or projected inventory risk reaches configured limits.
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

    # Protection Mode v0.
    enable_protection: bool = True
    max_gross_to_net_ratio: Optional[float] = 7.0
    max_strategy_gross_lots: Optional[float] = None
    max_strategy_positions: Optional[int] = None


@dataclass
class P1NetState:
    """Runtime state for P1-Net v0."""

    started: bool = False
    last_level: Optional[float] = None
    rebalance_count: int = 0
    protection_block_count: int = 0
    last_action: str = "NOT_STARTED"
    last_protection_reason: Optional[str] = None


@dataclass(frozen=True)
class PlannedRebalance:
    """Order planned by the strategy before risk protection is applied."""

    side: Side
    volume: float
    target_net: float


class P1NetStrategy:
    """
    P1-Net v0.

    Rule:
        - Start with one BUY or SELL.
        - If net is positive and price falls by range_points from last_level,
          open SELL volume needed to make net = -net_abs_lots.
        - If net is negative and price rises by range_points from last_level,
          open BUY volume needed to make net = +net_abs_lots.

    Protection Mode v0:
        - Before opening a rebalance order, inspect both current and projected exposure.
        - If the next order would push gross/net ratio, gross lots, or position count to
          a configured limit, block the new order and keep current exposure.
        - This does not recover losses yet; it only prevents uncontrolled inventory growth.
    """

    def __init__(self, config: P1NetConfig):
        self.config = config
        self.state = P1NetState()

    def on_price(self, engine: ExecutionEngine, price: float) -> None:
        """Process one price point and possibly send an order."""

        self.state.last_protection_reason = None

        if not self.state.started:
            self._start(engine=engine, price=price)
            return

        if self.state.last_level is None:
            self.state.last_level = price

        net = engine.portfolio.net_lots()
        distance = self.config.range_points

        if net >= (self.config.net_abs_lots - self.config.net_tolerance):
            if price <= self.state.last_level - distance:
                plan = self._plan_rebalance_to(engine=engine, target_net=-self.config.net_abs_lots)
                if plan is None:
                    self.state.last_action = "HOLD_NO_VALID_REBALANCE"
                    return

                if self._protection_blocks_plan(engine=engine, plan=plan, price=price):
                    self.state.last_action = "PROTECTION_HOLD"
                    return

                self._execute_plan(engine=engine, plan=plan, price=price)
                self.state.last_level = price
                self.state.rebalance_count += 1
                self.state.last_action = "REBALANCE_TO_NEGATIVE_NET"
                return

        if net <= (-self.config.net_abs_lots + self.config.net_tolerance):
            if price >= self.state.last_level + distance:
                plan = self._plan_rebalance_to(engine=engine, target_net=self.config.net_abs_lots)
                if plan is None:
                    self.state.last_action = "HOLD_NO_VALID_REBALANCE"
                    return

                if self._protection_blocks_plan(engine=engine, plan=plan, price=price):
                    self.state.last_action = "PROTECTION_HOLD"
                    return

                self._execute_plan(engine=engine, plan=plan, price=price)
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

    def _plan_rebalance_to(self, engine: ExecutionEngine, target_net: float) -> Optional[PlannedRebalance]:
        """Build a rebalance plan without executing it."""

        buy_lots = engine.portfolio.buy_lots()
        sell_lots = engine.portfolio.sell_lots()

        if target_net > 0:
            required_buy_total = sell_lots + target_net
            add_buy = self._normalize_lot(required_buy_total - buy_lots)
            if add_buy >= self.config.min_add_lot:
                return PlannedRebalance(side=Side.BUY, volume=add_buy, target_net=target_net)
            return None

        required_sell_total = buy_lots + abs(target_net)
        add_sell = self._normalize_lot(required_sell_total - sell_lots)
        if add_sell >= self.config.min_add_lot:
            return PlannedRebalance(side=Side.SELL, volume=add_sell, target_net=target_net)

        return None

    def _execute_plan(self, engine: ExecutionEngine, plan: PlannedRebalance, price: float) -> None:
        """Execute a previously approved rebalance plan."""

        if plan.side == Side.BUY:
            comment = f"{self.config.comment}:rebalance_buy"
        else:
            comment = f"{self.config.comment}:rebalance_sell"

        engine.open_market(
            side=plan.side,
            volume=plan.volume,
            price=price,
            comment=comment,
        )

    def _protection_blocks_plan(self, engine: ExecutionEngine, plan: PlannedRebalance, price: float) -> bool:
        """Return True when strategy-level protection blocks a planned rebalance."""

        if not self.config.enable_protection:
            return False

        current_exposure = engine.current_exposure_metrics(
            price=price,
            target_net_abs=self.config.net_abs_lots,
        )

        current_buy = current_exposure.buy_lots
        current_sell = current_exposure.sell_lots

        projected_buy = current_buy + plan.volume if plan.side == Side.BUY else current_buy
        projected_sell = current_sell + plan.volume if plan.side == Side.SELL else current_sell
        projected_net = projected_buy - projected_sell
        projected_gross = projected_buy + projected_sell
        projected_positions = current_exposure.position_count + 1

        abs_projected_net = abs(projected_net)
        if abs_projected_net <= self.config.net_tolerance:
            projected_ratio = float("inf")
        else:
            projected_ratio = projected_gross / abs_projected_net

        tolerance = max(self.config.net_tolerance, 1e-9)

        if (
            self.config.max_gross_to_net_ratio is not None
            and projected_ratio + tolerance >= self.config.max_gross_to_net_ratio
        ):
            self._register_protection_block("MAX_GROSS_TO_NET_RATIO")
            return True

        if (
            self.config.max_strategy_gross_lots is not None
            and projected_gross + tolerance >= self.config.max_strategy_gross_lots
        ):
            self._register_protection_block("MAX_STRATEGY_GROSS_LOTS")
            return True

        if (
            self.config.max_strategy_positions is not None
            and projected_positions >= self.config.max_strategy_positions
        ):
            self._register_protection_block("MAX_STRATEGY_POSITIONS")
            return True

        return False

    def _register_protection_block(self, reason: str) -> None:
        """Register a protection block reason."""

        self.state.protection_block_count += 1
        self.state.last_protection_reason = reason

    def _normalize_lot(self, volume: float) -> float:
        """Normalize volume to the configured lot step."""

        if volume <= 0:
            return 0.0

        step = self.config.lot_step
        normalized = round(round(volume / step) * step, 10)
        return normalized
