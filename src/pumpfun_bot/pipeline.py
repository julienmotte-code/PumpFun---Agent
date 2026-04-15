from __future__ import annotations

from dataclasses import dataclass

from .models import TokenFeatures, TokenSnapshot, TradeDecision


@dataclass(slots=True)
class SelectionModel:
    """Filtre les tokens avec un score minimum exploitable."""

    threshold: float = 0.65

    def score(self, features: TokenFeatures) -> float:
        return (
            0.30 * features.score_creator_history
            + 0.25 * features.score_wallet_distribution
            + 0.20 * features.score_volume_quality
            + 0.15 * features.score_momentum_5s
            + 0.10 * (1 - features.score_volatility_regime)
        )

    def accept(self, features: TokenFeatures) -> bool:
        return self.score(features) >= self.threshold


@dataclass(slots=True)
class EntryModel:
    """Détermine le timing d'entrée sur un token déjà sélectionné."""

    entry_threshold: float = 0.70

    def confidence(self, snapshot: TokenSnapshot) -> float:
        buy_pressure = snapshot.buy_count / max(snapshot.buy_count + snapshot.sell_count, 1)
        wallet_signal = min(snapshot.unique_wallets / 200, 1.0)
        creator_penalty = 0.35 if snapshot.creator_has_sold else 0.0
        microstructure = min(snapshot.mean_tx_size / 2.0, 1.0)
        return max(0.0, min(1.0, 0.45 * buy_pressure + 0.25 * wallet_signal + 0.30 * microstructure - creator_penalty))

    def should_buy(self, snapshot: TokenSnapshot) -> bool:
        return self.confidence(snapshot) >= self.entry_threshold


@dataclass(slots=True)
class PositionPolicy:
    """Règles de sortie simplifiées (placeholder production)."""

    stop_loss_pct: float = -0.12
    take_profit_pct: float = 0.25
    max_hold_seconds: int = 240

    def decide(self, pnl_pct: float, hold_seconds: int) -> TradeDecision:
        if pnl_pct <= self.stop_loss_pct:
            return TradeDecision("SELL", 0.95, "stop_loss")
        if pnl_pct >= self.take_profit_pct:
            return TradeDecision("SELL", 0.90, "take_profit")
        if hold_seconds >= self.max_hold_seconds:
            return TradeDecision("SELL", 0.75, "time_exit")
        return TradeDecision("HOLD", 0.60, "trend_monitoring")


@dataclass(slots=True)
class TradingPipeline:
    selection_model: SelectionModel
    entry_model: EntryModel
    position_policy: PositionPolicy

    def evaluate_entry(self, features: TokenFeatures, snapshot: TokenSnapshot) -> TradeDecision:
        if not self.selection_model.accept(features):
            return TradeDecision("SKIP", 0.90, "selection_filter_rejected")
        if self.entry_model.should_buy(snapshot):
            return TradeDecision("BUY", self.entry_model.confidence(snapshot), "entry_signal_confirmed")
        return TradeDecision("HOLD", self.entry_model.confidence(snapshot), "waiting_confirmation")
