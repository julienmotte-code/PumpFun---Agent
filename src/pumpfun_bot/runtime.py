from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random
from typing import Protocol
from urllib import request

from .config import RpcConfig
from .models import TokenFeatures, TokenSnapshot


@dataclass(slots=True)
class MarketObservation:
    features: TokenFeatures
    snapshot: TokenSnapshot


class MarketDataConnector(Protocol):
    def next_observation(self, mint: str) -> MarketObservation:
        ...


class MockMarketDataConnector:
    """Génère un flux déterministe de données pour mode papier/demo."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = Random(seed)

    def next_observation(self, mint: str) -> MarketObservation:
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


class SolanaRpcMarketDataConnector:
    """Connector minimal via JSON-RPC Solana (market proxy à implémenter).

    Cette implémentation interroge le slot pour vérifier la connectivité RPC,
    puis produit une observation synthétique en attendant un parseur Pump.fun complet.
    """

    def __init__(self, rpc: RpcConfig, seed: int = 42) -> None:
        self.rpc = rpc
        self._rng = Random(seed)

    def _rpc_call(self, method: str, params: list[object] | None = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        req = request.Request(
            self.rpc.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def next_observation(self, mint: str) -> MarketObservation:
        # smoke check RPC availability (raises if down)
        self._rpc_call("getSlot", [{"commitment": self.rpc.commitment}])

        # Tant que le parseur Pump.fun n'est pas branché, on garde une génération
        # déterministe pour préserver le comportement du pipeline.
        base = MockMarketDataConnector(seed=self._rng.randint(1, 999999))
        return base.next_observation(mint)
