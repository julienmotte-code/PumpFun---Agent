from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random

from .models import TokenFeatures, TokenSnapshot


@dataclass(slots=True)
class MarketObservation:
    features: TokenFeatures
    snapshot: TokenSnapshot


class MockMarketDataConnector:
    """Génère un flux déterministe de données pour mode papier/demo."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = Random(seed)

    def next_observation(self, mint: str = "demo-mint") -> MarketObservation:
        now = datetime.now(timezone.utc)

        buy_count = self._rng.randint(8, 80)
        sell_count = self._rng.randint(3, 60)
        wallets = self._rng.randint(20, 250)
        mean_tx_size = self._rng.uniform(0.3, 3.2)
        creator_has_sold = self._rng.random() < 0.12

        snapshot = TokenSnapshot(
            mint=mint,
            observed_at=now,
            age_seconds=self._rng.randint(10, 600),
            price=self._rng.uniform(0.00001, 0.0009),
            market_cap=self._rng.uniform(15000, 180000),
            buy_count=buy_count,
            sell_count=sell_count,
            unique_wallets=wallets,
            mean_tx_size=mean_tx_size,
            creator_has_sold=creator_has_sold,
        )

        features = TokenFeatures(
            mint=mint,
            score_creator_history=self._rng.uniform(0.2, 1.0),
            score_wallet_distribution=min(wallets / 240, 1.0),
            score_volume_quality=min((buy_count + sell_count) / 120, 1.0),
            score_momentum_5s=min(max((buy_count - sell_count + 30) / 80, 0.0), 1.0),
            score_volatility_regime=self._rng.uniform(0.0, 1.0),
        )

        return MarketObservation(features=features, snapshot=snapshot)
