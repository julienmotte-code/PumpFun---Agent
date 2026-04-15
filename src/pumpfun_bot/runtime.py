from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random
from typing import Protocol
from urllib.error import URLError
from urllib import parse, request

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


class HttpMarketDataConnector:
    """Récupère les observations depuis un service HTTP externe.

    Réponse JSON attendue:
    {
      "snapshot": {...TokenSnapshot fields except observed_at optional...},
      "features": {...TokenFeatures fields...}
    }
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _fetch_json(self, mint: str) -> dict:
        url = f"{self.base_url}?{parse.urlencode({'mint': mint})}"
        req = request.Request(url, method="GET")
        try:
            with request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except URLError as exc:
            raise RuntimeError(f"market data request failed: {exc}") from exc

    def next_observation(self, mint: str) -> MarketObservation:
        payload = self._fetch_json(mint)
        raw_snapshot = payload["snapshot"]
        raw_features = payload["features"]

        observed_at = raw_snapshot.get("observed_at")
        when = datetime.fromisoformat(observed_at) if observed_at else datetime.now(timezone.utc)

        snapshot = TokenSnapshot(
            mint=raw_snapshot.get("mint", mint),
            observed_at=when,
            age_seconds=int(raw_snapshot["age_seconds"]),
            price=float(raw_snapshot["price"]),
            market_cap=float(raw_snapshot["market_cap"]),
            buy_count=int(raw_snapshot["buy_count"]),
            sell_count=int(raw_snapshot["sell_count"]),
            unique_wallets=int(raw_snapshot["unique_wallets"]),
            mean_tx_size=float(raw_snapshot["mean_tx_size"]),
            creator_has_sold=bool(raw_snapshot["creator_has_sold"]),
        )

        features = TokenFeatures(
            mint=raw_features.get("mint", snapshot.mint),
            score_creator_history=float(raw_features["score_creator_history"]),
            score_wallet_distribution=float(raw_features["score_wallet_distribution"]),
            score_volume_quality=float(raw_features["score_volume_quality"]),
            score_momentum_5s=float(raw_features["score_momentum_5s"]),
            score_volatility_regime=float(raw_features["score_volatility_regime"]),
        )
        return MarketObservation(features=features, snapshot=snapshot)


class SolanaRpcMarketDataConnector:
    """Connector JSON-RPC minimal pour probe de connectivité."""

    def __init__(self, rpc: RpcConfig) -> None:
        self.rpc = rpc

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
        self._rpc_call("getSlot", [{"commitment": self.rpc.commitment}])
        raise RuntimeError("SolanaRpcMarketDataConnector requires an upstream parser; use PUMPFUN_MARKETDATA_URL")
