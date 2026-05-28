"""
File: hedge_lab/strategies/p1_multiplier.py

Purpose:
    Implement P1_MULTIPLIER_V0, the multiplier-based P1 hedge prototype.

Inputs:
    - Price events from a scenario.
    - ExecutionEngine from hedge_lab.simulator.core.
    - P1MultiplierConfig parameters such as initial side, start lot, range distance,
      multiplier and protection limits.

Outputs:
    - Market orders sent to the ExecutionEngine.
    - P1MultiplierState updates such as last_level, next_side, rebalance count
      and protection status.

Integrations:
    - Uses hedge_lab.simulator.core.Side and ExecutionEngine.
    - Used by hedge_lab.simulator.run_monte_carlo through --strategy-id P1_MULTIPLIER_V0.
    - Used by hedge_lab.evolution.run_genetic_search through --strategy-id P1_MULTIPLIER_V0.
    - Saves datasets under:
        datasets/strategies/P1_MULTIPLIER_V0/<ASSET>/<TIMEFRAME>/...

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - This strategy is intentionally separate from P1_NET_V0.
    - P1_NET_V0 controls a fixed absolute NET.
    - P1_MULTIPLIER_V0 grows the opposite side using a multiplier:
        desired_opposite_total = current_reference_side_total * multiplier.
    - This can recover strongly in range, but can grow gross exposure quickly.
    - Protection Mode v0 blocks planned additions when projected exposure breaches configured limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from hedge_lab.simulator.core import ExecutionEngine, Side


@dataclass(frozen=True)
class P1MultiplierConfig:
    """Configuration for P1_MULTIPLIER_V0."""

    initial_side: Side = Side.SELL
    start_lot: float = 0.02
    range_points: float = 300.0
    multiplier: float = 2.0
    min_add_lot: float = 0.01
    lot_step: float = 0.01
    net_tolerance: float = 1e-9
    comment: str = "P1_MULTIPLIER_V0"

    # Protection Mode v0.
    enable_protection: bool = True
    max_gross_to_net_ratio: Optional[float] = 7.0
    max_strategy_gross_lots: Optional[float] = None
    max_strategy_positions: Optional[int] = None


@dataclass
class P1MultiplierState:
    """Runtime state for P1_MULTIPLIER_V0."""

    started: bool = False
    last_level: Optional[float] = None
    next_side: Optional[Side] = None
    rebalance_count: int = 0
    protection_block_count: int = 0
    last_action: str = "NOT_STARTED"
    last_protection_reason: Optional[str] = None


@dataclass(frozen=True)
class PlannedMultiplierRebalance:
    """Order planned by the strategy before risk protection is applied."""

    side: Side
    volume: float
    desired_total_on_side: float


class P1MultiplierStrategy:
    """
    P1_MULTIPLIER_V0.

    Rule:
        - Start with one BUY or SELL.
        - On adverse range movement, open the opposite side so that:
            opposite_total = reference_total * multiplier
        - Then alternate between BUY and SELL levels.

    Example with initial SELL 0.02 and multiplier 2:
        1. Open SELL 0.02.
        2. If price rises by range, desired BUY total = SELL total * 2 = 0.04.
           Add BUY 0.04.
        3. If price falls by range, desired SELL total = BUY total * 2 = 0.08.
           Current SELL is 0.02, so add SELL 0.06.
        4. Continue alternating.

    Protection Mode v0:
        - Before opening a planned order, inspect projected exposure.
        - Block the order if projected gross/net ratio, projected gross lots,
          or projected position count breaches configured limits.
    """

    def __init__(self, config: P1MultiplierConfig):
        self.config = config
        self.state = P1MultiplierState()

    def on_price(self, engine: ExecutionEngine, price: float) -> None:
        """Process one price point and possibly send an order."""

        self.state.last_protection_reason = None

        if not self.state.started:
            self._start(engine=engine, price=price)
            return

        if self.state.last_level is None:
            self.state.last_level = price

        if self.state.next_side is None:
            self.state.next_side = self._opposite(self.config.initial_side)

        if not self._triggered(price=price):
            self.state.last_action = "HOLD"
            return

        plan = self._plan_rebalance(engine=engine)
        if plan is None:
            self.state.last_action = "HOLD_NO_VALID_REBALANCE"
            return

        if self._protection_blocks_plan(engine=engine, plan=plan, price=price):
            self.state.last_action = "PROTECTION_HOLD"
            return

        self._execute_plan(engine=engine, plan=plan, price=price)
        self.state.last_level = price
        self.state.next_side = self._opposite(plan.side)
        self.state.rebalance_count += 1
        self.state.last_action = f"MULTIPLIER_REBALANCE_{plan.side.value}"

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
        self.state.next_side = self._opposite(self.config.initial_side)
        self.state.last_action = f"START_{self.config.initial_side.value}"

    def _triggered(self, price: float) -> bool:
        """Return True when price has reached the next side trigger level."""

        if self.state.last_level is None or self.state.next_side is None:
            return False

        distance = self.config.range_points

        if self.state.next_side == Side.BUY:
            return price >= self.state.last_level + distance

        return price <= self.state.last_level - distance

    def _plan_rebalance(self, engine: ExecutionEngine) -> Optional[PlannedMultiplierRebalance]:
        """Build a multiplier rebalance plan without executing it."""

        if self.state.next_side is None:
            return None

        buy_lots = engine.portfolio.buy_lots()
        sell_lots = engine.portfolio.sell_lots()

        if self.state.next_side == Side.BUY:
            desired_buy_total = self._normalize_lot(sell_lots * self.config.multiplier)
            add_buy = self._normalize_lot(desired_buy_total - buy_lots)
            if add_buy >= self.config.min_add_lot:
                return PlannedMultiplierRebalance(
                    side=Side.BUY,
                    volume=add_buy,
                    desired_total_on_side=desired_buy_total,
                )
            return None

        desired_sell_total = self._normalize_lot(buy_lots * self.config.multiplier)
        add_sell = self._normalize_lot(desired_sell_total - sell_lots)
        if add_sell >= self.config.min_add_lot:
            return PlannedMultiplierRebalance(
                side=Side.SELL,
                volume=add_sell,
                desired_total_on_side=desired_sell_total,
            )

        return None

    def _execute_plan(self, engine: ExecutionEngine, plan: PlannedMultiplierRebalance, price: float) -> None:
        """Execute a previously approved rebalance plan."""

        engine.open_market(
            side=plan.side,
            volume=plan.volume,
            price=price,
            comment=f"{self.config.comment}:multiplier_{plan.side.value.lower()}",
        )

    def _protection_blocks_plan(
        self,
        engine: ExecutionEngine,
        plan: PlannedMultiplierRebalance,
        price: float,
    ) -> bool:
        """Return True when strategy-level protection blocks a planned rebalance."""

        if not self.config.enable_protection:
            return False

        current_exposure = engine.current_exposure_metrics(
            price=price,
            target_net_abs=self.config.start_lot,
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

    def _opposite(self, side: Side) -> Side:
        """Return opposite side."""

        return Side.BUY if side == Side.SELL else Side.SELL

    def _normalize_lot(self, volume: float) -> float:
        """Normalize volume to the configured lot step."""

        if volume <= 0:
            return 0.0

        step = self.config.lot_step
        normalized = round(round(volume / step) * step, 10)
        return normalized
