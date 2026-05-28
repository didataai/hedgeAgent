# -*- coding: utf-8 -*-
from __future__ import annotations

class StrategyModel:
    def __init__(self, params: dict):
        self.params = dict(params or {})
        self.family_id = 'P0'
        self.version_id = 'P0_V4'
        self.small_lot = float(self.params.get("HedgeSmallLot", 0.03))
        self.large_lot = float(self.params.get("HedgeLargeLot", 0.04))
        self.lot_increase = float(self.params.get("LotIncrease", 0.01))
        self.directional_lot = float(self.params.get("DirectionalLot", 0.020000000000000004))
        self.range_threshold_points = float(self.params.get("RangeThresholdPts", 400.0))
        self.stop_threshold_usd = float(self.params.get("StopThresholdUSD", -8.0))
        self.money_per_point_per_lot = float(self.params.get("money_per_point_per_lot", 1.0))
        self.started = False
        self.initial_price = None
        self.state = "S0_EMPTY_OR_RESET"
        self.positions = []
        self.events = []
        self.realized_pnl = 0.0

    def _event(self, event_type: str, price: float, bar_index: int, details: dict | None = None) -> None:
        self.events.append({"event_type": event_type, "price": float(price), "bar_index": int(bar_index), "state": self.state, "details": details or {}})

    def _open_position(self, side: str, lot: float, price: float, tag: str) -> None:
        self.positions.append({"side": side, "lot": float(lot), "open_price": float(price), "tag": tag})

    def _position_pnl(self, pos: dict, price: float) -> float:
        direction = 1.0 if pos["side"] == "BUY" else -1.0
        return (float(price) - pos["open_price"]) * direction * pos["lot"] * self.money_per_point_per_lot

    def _floating_pnl(self, price: float) -> float:
        return sum(self._position_pnl(pos, price) for pos in self.positions)

    def on_start(self, price: float) -> None:
        if self.started:
            return
        self.started = True
        self.initial_price = float(price)
        self.state = "S1_INITIAL_MARKET_HEDGE"
        self._open_position("BUY", self.small_lot, price, "initial_small_buy")
        self._open_position("SELL", self.small_lot, price, "initial_small_sell")
        self._open_position("BUY", self.large_lot, price, "initial_large_buy")
        self._open_position("SELL", self.large_lot, price, "initial_large_sell")
        self._event("initial_market_hedge_opened", price, 0, {"source": "block_scaffold"})

    def on_bar(self, price: float, bar_index: int) -> None:
        if not self.started:
            self.on_start(price)
        if self.state == "S1_INITIAL_MARKET_HEDGE":
            distance = float(price) - float(self.initial_price)
            if abs(distance) >= self.range_threshold_points:
                direction = "UP" if distance > 0 else "DOWN"
                self.state = "S2_RANGE_TRIGGER_REACHED"
                self._event("range_trigger_reached", price, bar_index, {"direction": direction, "distance_points": distance, "todo": "TODO_SOURCE_UNRESOLVED"})
                if direction == "UP":
                    close_tags = ["initial_large_buy", "initial_small_sell"]
                    side = "BUY"
                else:
                    close_tags = ["initial_large_sell", "initial_small_buy"]
                    side = "SELL"
                remaining = []
                closed = 0.0
                for pos in self.positions:
                    if pos["tag"] in close_tags:
                        closed += self._position_pnl(pos, price)
                    else:
                        remaining.append(pos)
                self.positions = remaining
                self.realized_pnl += closed
                self._open_position(side, self.directional_lot, price, "directional_after_elimination")
                self.state = "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL"
                self._event("partial_elimination_and_directional_opened", price, bar_index, {"closed_tags": close_tags, "closed_pnl": closed, "todo": "TODO_SOURCE_UNRESOLVED"})
        elif self.state == "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL":
            floating = self._floating_pnl(price)
            if floating <= self.stop_threshold_usd:
                self.state = "S4_RETURN_STOP_OR_RECOVERY"
                self._event("recovery_or_stop_threshold_reached", price, bar_index, {"floating_pnl": floating, "todo": "TODO_SOURCE_UNRESOLVED"})

    def get_positions(self) -> list[dict]:
        return [dict(pos) for pos in self.positions]

    def get_events(self) -> list[dict]:
        return [dict(event) for event in self.events]

    def get_metrics_snapshot(self) -> dict:
        return {"family_id": self.family_id, "version_id": self.version_id, "state": self.state, "positions_count": len(self.positions), "gross_lot": sum(abs(pos["lot"]) for pos in self.positions), "net_lot": sum((1 if pos["side"] == "BUY" else -1) * pos["lot"] for pos in self.positions), "realized_pnl": self.realized_pnl, "events_count": len(self.events), "model_status": "deterministic_block_scaffold_with_source_unresolved"}
