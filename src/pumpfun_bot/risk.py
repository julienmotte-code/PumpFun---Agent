from __future__ import annotations

from dataclasses import dataclass

from .config import RiskConfig


@dataclass(slots=True)
class RiskState:
    realized_pnl_usd: float = 0.0
    open_positions: int = 0


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config
        self.state = RiskState()

    def can_open_position(self, requested_notional: float) -> tuple[bool, str]:
        if requested_notional > self.config.max_position_usd:
            return False, "risk:max_position_usd_exceeded"
        if self.state.open_positions >= self.config.max_open_positions:
            return False, "risk:max_open_positions_reached"
        if self.state.realized_pnl_usd <= -abs(self.config.max_daily_loss_usd):
            return False, "risk:max_daily_loss_reached"
        return True, "risk:ok"

    def on_position_opened(self) -> None:
        self.state.open_positions += 1

    def on_position_closed(self, realized_pnl_usd: float) -> None:
        self.state.open_positions = max(0, self.state.open_positions - 1)
        self.state.realized_pnl_usd += realized_pnl_usd
