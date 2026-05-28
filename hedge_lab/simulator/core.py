from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


@dataclass
class Position:
    ticket: int
    side: Side
    volume: float
    open_price: float
    comment: str = ""

    def floating_pnl(self, price: float, point_value: float = 1.0) -> float:
        if self.side == Side.BUY:
            return (price - self.open_price) * self.volume * point_value
        return (self.open_price - price) * self.volume * point_value


@dataclass
class PendingOrder:
    ticket: int
    order_type: OrderType
    side: Side
    volume: float
    price: float
    comment: str = ""


@dataclass
class AccountState:
    balance: float = 10_000.0
    equity: float = 10_000.0
    realized_profit: float = 0.0
    max_equity: float = 10_000.0
    min_equity: float = 10_000.0
    max_drawdown: float = 0.0


@dataclass
class PortfolioState:
    positions: List[Position] = field(default_factory=list)
    pendings: List[PendingOrder] = field(default_factory=list)

    def buy_lots(self) -> float:
        return sum(p.volume for p in self.positions if p.side == Side.BUY)

    def sell_lots(self) -> float:
        return sum(p.volume for p in self.positions if p.side == Side.SELL)

    def net_lots(self) -> float:
        return self.buy_lots() - self.sell_lots()

    def gross_lots(self) -> float:
        return self.buy_lots() + self.sell_lots()

    def floating_pnl(self, price: float, point_value: float = 1.0) -> float:
        return sum(p.floating_pnl(price, point_value) for p in self.positions)

    def oldest_position(self) -> Optional[Position]:
        if not self.positions:
            return None
        return sorted(self.positions, key=lambda p: p.ticket)[0]

    def biggest_loss_position(self, price: float, point_value: float = 1.0) -> Optional[Position]:
        if not self.positions:
            return None

        losses = [(p.floating_pnl(price, point_value), p) for p in self.positions]
        losses.sort(key=lambda item: item[0])

        if losses[0][0] < 0:
            return losses[0][1]

        return None


@dataclass
class SimulationConfig:
    initial_balance: float = 10_000.0
    spread_points: float = 0.0
    slippage_points: float = 0.0
    point_value: float = 1.0
    max_gross_lots: float = 1.0
    max_positions: int = 100
    max_drawdown_pct: float = 30.0


@dataclass
class SimulationResult:
    survived: bool
    failure_reason: Optional[str]
    final_balance: float
    final_equity: float
    realized_profit: float
    floating_profit: float
    max_drawdown: float
    max_gross_lots: float
    max_positions: int


class ExecutionEngine:
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

    def _new_ticket(self) -> int:
        ticket = self._next_ticket
        self._next_ticket += 1
        return ticket

    def open_market(self, side: Side, volume: float, price: float, comment: str = "") -> Position:
        position = Position(
            ticket=self._new_ticket(),
            side=side,
            volume=volume,
            open_price=price,
            comment=comment,
        )
        self.portfolio.positions.append(position)
        self._update_extremes()
        return position

    def close_position(self, ticket: int, price: float) -> float:
        for idx, position in enumerate(self.portfolio.positions):
            if position.ticket == ticket:
                pnl = position.floating_pnl(price, self.config.point_value)
                self.account.balance += pnl
                self.account.realized_profit += pnl
                del self.portfolio.positions[idx]
                self._update_account(price)
                return pnl

        raise ValueError(f"Position ticket not found: {ticket}")

    def _update_account(self, price: float) -> None:
        floating = self.portfolio.floating_pnl(price, self.config.point_value)
        self.account.equity = self.account.balance + floating
        self.account.max_equity = max(self.account.max_equity, self.account.equity)
        self.account.min_equity = min(self.account.min_equity, self.account.equity)

        if self.account.max_equity > 0:
            drawdown = (self.account.max_equity - self.account.equity) / self.account.max_equity * 100.0
            self.account.max_drawdown = max(self.account.max_drawdown, drawdown)

        self._update_extremes()

    def _update_extremes(self) -> None:
        self._max_gross_seen = max(self._max_gross_seen, self.portfolio.gross_lots())
        self._max_positions_seen = max(self._max_positions_seen, len(self.portfolio.positions))

    def check_risk_limits(self, price: float) -> Optional[str]:
        self._update_account(price)

        if self.portfolio.gross_lots() > self.config.max_gross_lots:
            return "MAX_GROSS_LOTS_EXCEEDED"

        if len(self.portfolio.positions) > self.config.max_positions:
            return "MAX_POSITIONS_EXCEEDED"

        if self.account.max_drawdown > self.config.max_drawdown_pct:
            return "MAX_DRAWDOWN_EXCEEDED"

        return None

    def result(self, price: float, failure_reason: Optional[str] = None) -> SimulationResult:
        self._update_account(price)

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
        )
