"""
File: hedge_lab/simulator/core.py

Purpose:
    Core simulation primitives for the Hedge Evolution Lab.

Inputs:
    - Strategy decisions.
    - Market prices/events.
    - SimulationConfig parameters.

Outputs:
    - AccountState.
    - PortfolioState.
    - ExposureMetrics.
    - SimulationResult.

Integrations:
    - Used by strategy modules.
    - Used by scenario runners.
    - Later used by metrics, evolution and agent layers.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - Avoid hardcoded symbol/timeframe assumptions.
    - This simulator is intentionally simple in v0.
    - PNL model is synthetic: price distance * volume * point_value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Side(str, Enum):
    """Trade side."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type placeholder for future pending-order simulation."""

    MARKET = "MARKET"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


@dataclass
class Position:
    """Open simulated position."""

    ticket: int
    side: Side
    volume: float
    open_price: float
    comment: str = ""

    def floating_pnl(self, price: float, point_value: float = 1.0) -> float:
        """Return synthetic floating PNL for the given price."""

        if self.side == Side.BUY:
            return (price - self.open_price) * self.volume * point_value

        return (self.open_price - price) * self.volume * point_value


@dataclass
class PendingOrder:
    """Pending simulated order.

    Pending execution is not implemented yet in v0, but the structure is kept
    in the core because HedgeCycle/Worm/P4/P5 will require it later.
    """

    ticket: int
    order_type: OrderType
    side: Side
    volume: float
    price: float
    comment: str = ""


@dataclass
class AccountState:
    """Synthetic account state."""

    balance: float = 10_000.0
    equity: float = 10_000.0
    realized_profit: float = 0.0
    max_equity: float = 10_000.0
    min_equity: float = 10_000.0
    max_drawdown: float = 0.0


@dataclass(frozen=True)
class ExposureMetrics:
    """Risk and exposure metrics at a given price."""

    buy_lots: float
    sell_lots: float
    net_lots: float
    gross_lots: float
    floating_profit: float
    winning_floating_profit: float
    losing_floating_loss: float
    recovery_power: float
    risk_debt: float
    position_count: int
    gross_to_net_ratio: float
    net_is_controlled: bool
    gross_is_expanding: bool


@dataclass
class PortfolioState:
    """Current simulated portfolio."""

    positions: List[Position] = field(default_factory=list)
    pendings: List[PendingOrder] = field(default_factory=list)

    def buy_lots(self) -> float:
        """Return total BUY volume."""

        return sum(p.volume for p in self.positions if p.side == Side.BUY)

    def sell_lots(self) -> float:
        """Return total SELL volume."""

        return sum(p.volume for p in self.positions if p.side == Side.SELL)

    def net_lots(self) -> float:
        """Return net lots: buy lots - sell lots."""

        return self.buy_lots() - self.sell_lots()

    def gross_lots(self) -> float:
        """Return gross lots: buy lots + sell lots."""

        return self.buy_lots() + self.sell_lots()

    def floating_pnl(self, price: float, point_value: float = 1.0) -> float:
        """Return total floating PNL."""

        return sum(p.floating_pnl(price, point_value) for p in self.positions)

    def winning_floating_profit(self, price: float, point_value: float = 1.0) -> float:
        """Return sum of positive floating PNL."""

        return sum(
            max(0.0, p.floating_pnl(price, point_value))
            for p in self.positions
        )

    def losing_floating_loss(self, price: float, point_value: float = 1.0) -> float:
        """Return absolute sum of negative floating PNL."""

        return sum(
            abs(min(0.0, p.floating_pnl(price, point_value)))
            for p in self.positions
        )

    def exposure_metrics(
        self,
        price: float,
        point_value: float = 1.0,
        target_net_abs: Optional[float] = None,
        initial_gross_lots: Optional[float] = None,
        net_tolerance: float = 1e-9,
    ) -> ExposureMetrics:
        """Return a compact risk snapshot for the current portfolio.

        Definitions:
            recovery_power:
                Sum of positive floating PNL. This is the available unrealized
                profit that could help close losing positions.

            risk_debt:
                Absolute sum of negative floating PNL. This is the current
                floating loss burden.

            gross_to_net_ratio:
                Gross lots divided by absolute net lots. This exposes the
                classic hedge trap where NET is small but GROSS is large.

            net_is_controlled:
                True when abs(net) is close to target_net_abs. If no target is
                passed, this remains False.

            gross_is_expanding:
                True when current gross is higher than the initial gross.
        """

        buy = self.buy_lots()
        sell = self.sell_lots()
        net = buy - sell
        gross = buy + sell
        floating = self.floating_pnl(price, point_value)
        winners = self.winning_floating_profit(price, point_value)
        losers = self.losing_floating_loss(price, point_value)

        abs_net = abs(net)
        gross_to_net_ratio = gross / abs_net if abs_net > net_tolerance else float("inf")

        net_is_controlled = False
        if target_net_abs is not None:
            net_is_controlled = abs(abs_net - target_net_abs) <= max(net_tolerance, 1e-9)

        gross_is_expanding = False
        if initial_gross_lots is not None:
            gross_is_expanding = gross > (initial_gross_lots + net_tolerance)

        return ExposureMetrics(
            buy_lots=buy,
            sell_lots=sell,
            net_lots=net,
            gross_lots=gross,
            floating_profit=floating,
            winning_floating_profit=winners,
            losing_floating_loss=losers,
            recovery_power=winners,
            risk_debt=losers,
            position_count=len(self.positions),
            gross_to_net_ratio=gross_to_net_ratio,
            net_is_controlled=net_is_controlled,
            gross_is_expanding=gross_is_expanding,
        )

    def oldest_position(self) -> Optional[Position]:
        """Return oldest position by ticket."""

        if not self.positions:
            return None

        return sorted(self.positions, key=lambda p: p.ticket)[0]

    def biggest_loss_position(self, price: float, point_value: float = 1.0) -> Optional[Position]:
        """Return the position with the worst floating loss."""

        if not self.positions:
            return None

        losses = [(p.floating_pnl(price, point_value), p) for p in self.positions]
        losses.sort(key=lambda item: item[0])

        if losses[0][0] < 0:
            return losses[0][1]

        return None


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""

    initial_balance: float = 10_000.0
    spread_points: float = 0.0
    slippage_points: float = 0.0
    point_value: float = 1.0
    max_gross_lots: float = 1.0
    max_positions: int = 100
    max_drawdown_pct: float = 30.0


@dataclass
class SimulationResult:
    """Final simulation result."""

    survived: bool
    failure_reason: Optional[str]
    final_balance: float
    final_equity: float
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


class ExecutionEngine:
    """Simple execution engine for v0 simulations."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.account = AccountState(
            balance=config.initial_balance,
            equity=config.initial_balance,
            max_equity=config.initial_balance,
            min_equity=config.initial_balance,
        )
        self.portfolio = PortfolioState()
        self._next_ticket = 1
        self._max_gross_seen = 0.0
        self._max_positions_seen = 0
        self._initial_gross_lots: Optional[float] = None

    @property
    def initial_gross_lots(self) -> Optional[float]:
        """Return gross lots after the first position was opened."""

        return self._initial_gross_lots

    def _new_ticket(self) -> int:
        """Create a new synthetic ticket."""

        ticket = self._next_ticket
        self._next_ticket += 1
        return ticket

    def open_market(self, side: Side, volume: float, price: float, comment: str = "") -> Position:
        """Open a synthetic market position."""

        position = Position(
            ticket=self._new_ticket(),
            side=side,
            volume=volume,
            open_price=price,
            comment=comment,
        )
        self.portfolio.positions.append(position)

        if self._initial_gross_lots is None:
            self._initial_gross_lots = self.portfolio.gross_lots()

        self._update_extremes()
        return position

    def close_position(self, ticket: int, price: float) -> float:
        """Close a position and realize its PNL."""

        for idx, position in enumerate(self.portfolio.positions):
            if position.ticket == ticket:
                pnl = position.floating_pnl(price, self.config.point_value)
                self.account.balance += pnl
                self.account.realized_profit += pnl
                del self.portfolio.positions[idx]
                self._update_account(price)
                return pnl

        raise ValueError(f"Position ticket not found: {ticket}")

    def current_exposure_metrics(
        self,
        price: float,
        target_net_abs: Optional[float] = None,
    ) -> ExposureMetrics:
        """Return current exposure metrics from the portfolio."""

        return self.portfolio.exposure_metrics(
            price=price,
            point_value=self.config.point_value,
            target_net_abs=target_net_abs,
            initial_gross_lots=self._initial_gross_lots,
        )

    def _update_account(self, price: float) -> None:
        """Update equity and drawdown metrics."""

        floating = self.portfolio.floating_pnl(price, self.config.point_value)
        self.account.equity = self.account.balance + floating
        self.account.max_equity = max(self.account.max_equity, self.account.equity)
        self.account.min_equity = min(self.account.min_equity, self.account.equity)

        if self.account.max_equity > 0:
            drawdown = (self.account.max_equity - self.account.equity) / self.account.max_equity * 100.0
            self.account.max_drawdown = max(self.account.max_drawdown, drawdown)

        self._update_extremes()

    def _update_extremes(self) -> None:
        """Update max gross and max positions observed."""

        self._max_gross_seen = max(self._max_gross_seen, self.portfolio.gross_lots())
        self._max_positions_seen = max(self._max_positions_seen, len(self.portfolio.positions))

    def check_risk_limits(self, price: float) -> Optional[str]:
        """Return failure reason if any risk limit is breached."""

        self._update_account(price)

        if self.portfolio.gross_lots() > self.config.max_gross_lots:
            return "MAX_GROSS_LOTS_EXCEEDED"

        if len(self.portfolio.positions) > self.config.max_positions:
            return "MAX_POSITIONS_EXCEEDED"

        if self.account.max_drawdown > self.config.max_drawdown_pct:
            return "MAX_DRAWDOWN_EXCEEDED"

        return None

    def result(
        self,
        price: float,
        failure_reason: Optional[str] = None,
        target_net_abs: Optional[float] = None,
    ) -> SimulationResult:
        """Return final simulation result."""

        self._update_account(price)
        exposure = self.current_exposure_metrics(price=price, target_net_abs=target_net_abs)

        return SimulationResult(
            survived=failure_reason is None,
            failure_reason=failure_reason,
            final_balance=self.account.balance,
            final_equity=self.account.equity,
            realized_profit=self.account.realized_profit,
            floating_profit=self.portfolio.floating_pnl(price, self.config.point_value),
            max_drawdown=self.account.max_drawdown,
            max_gross_lots=self._max_gross_seen,
            max_positions=self._max_positions_seen,
            final_net_lots=exposure.net_lots,
            final_gross_lots=exposure.gross_lots,
            recovery_power=exposure.recovery_power,
            risk_debt=exposure.risk_debt,
            gross_to_net_ratio=exposure.gross_to_net_ratio,
        )
