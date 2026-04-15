from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TokenSnapshot:
    """Observation unitaire d'un token à un instant donné."""

    mint: str
    observed_at: datetime
    age_seconds: int
    price: float
    market_cap: float
    buy_count: int
    sell_count: int
    unique_wallets: int
    mean_tx_size: float
    creator_has_sold: bool


@dataclass(slots=True)
class TokenFeatures:
    """Features agrégées utilisées par les modèles de décision."""

    mint: str
    score_creator_history: float
    score_wallet_distribution: float
    score_volume_quality: float
    score_momentum_5s: float
    score_volatility_regime: float


@dataclass(slots=True)
class TradeDecision:
    """Décision d'exécution issue du pipeline en temps réel."""

    action: str  # BUY | HOLD | SELL | SKIP
    confidence: float
    reason: str
