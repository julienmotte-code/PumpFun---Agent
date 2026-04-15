from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from urllib.error import URLError
from urllib import request


class BrokerError(RuntimeError):
    pass


@dataclass(slots=True)
class Position:
    mint: str
    units: float
    avg_entry_price: float


class Broker:
    def buy(self, mint: str, notional: float, price: float) -> str:
        raise NotImplementedError

    def sell_all(self, mint: str, price: float) -> tuple[str, float]:
        raise NotImplementedError


@dataclass(slots=True)
class PaperBroker(Broker):
    """Exécuteur fictif (paper trading) qui garde l'état des positions."""

    initial_cash: float = 1000.0
    cash: float = field(init=False)
    positions: dict[str, Position] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.cash = self.initial_cash

    def has_position(self, mint: str) -> bool:
        return mint in self.positions and self.positions[mint].units > 0

    def buy(self, mint: str, notional: float, price: float) -> str:
        notional = min(notional, self.cash)
        if notional <= 0:
            return "BUY ignored (cash=0)"

        units = notional / max(price, 1e-12)
        self.cash -= notional

        existing = self.positions.get(mint)
        if existing is None:
            self.positions[mint] = Position(mint=mint, units=units, avg_entry_price=price)
        else:
            total_units = existing.units + units
            existing.avg_entry_price = ((existing.avg_entry_price * existing.units) + (price * units)) / max(total_units, 1e-12)
            existing.units = total_units

        return f"BUY paper: mint={mint} ${notional:.2f} at {price:.8f} -> +{units:.2f} units"

    def sell_all(self, mint: str, price: float) -> tuple[str, float]:
        pos = self.positions.get(mint)
        if pos is None or pos.units <= 0:
            return "SELL ignored (no position)", 0.0

        proceeds = pos.units * price
        cost_basis = pos.units * pos.avg_entry_price
        realized = proceeds - cost_basis

        self.cash += proceeds
        sold_units = pos.units
        del self.positions[mint]
        return (
            f"SELL paper: mint={mint} {sold_units:.2f} units at {price:.8f} -> +${proceeds:.2f} (pnl=${realized:.2f})",
            realized,
        )


@dataclass(slots=True)
class LiveBroker(Broker):
    """Exécuteur live vers un service HTTP d'exécution (webhook/adaptateur DEX)."""

    wallet_public_key: str
    executor_url: str
    private_key_env: str = "PUMPFUN_PRIVATE_KEY"
    enabled: bool = False

    def validate(self) -> None:
        if not self.enabled:
            raise BrokerError(
                "Live mode requires --enable-live-trading. "
                "Par sécurité, l'exécution réelle est désactivée par défaut."
            )
        if not self.wallet_public_key:
            raise BrokerError("Wallet public key missing")
        if not self.executor_url:
            raise BrokerError("Missing executor URL")
        if not os.getenv(self.private_key_env):
            raise BrokerError(f"Missing private key in env var: {self.private_key_env}")

    def _send_order(self, side: str, mint: str, notional: float, price: float) -> str:
        self.validate()
        payload = {
            "side": side,
            "mint": mint,
            "notional": notional,
            "reference_price": price,
            "wallet_public_key": self.wallet_public_key,
            "private_key_env": self.private_key_env,
        }
        req = request.Request(
            self.executor_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
        except URLError as exc:
            raise BrokerError(f"Executor request failed: {exc}") from exc
        return f"LIVE {side} sent to executor ({self.executor_url}): {body[:240]}"

    def buy(self, mint: str, notional: float, price: float) -> str:
        return self._send_order("BUY", mint, notional, price)

    def sell_all(self, mint: str, price: float) -> tuple[str, float]:
        return self._send_order("SELL", mint, 0.0, price), 0.0
