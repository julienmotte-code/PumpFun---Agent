from __future__ import annotations

import time
from dataclasses import dataclass

from .config import BotConfig
from .execution import Broker, LiveBroker, PaperBroker
from .models import TradeDecision
from .pipeline import EntryModel, PositionPolicy, SelectionModel, TradingPipeline
from .risk import RiskManager
from .runtime import MarketDataConnector, MockMarketDataConnector, SolanaRpcMarketDataConnector
from .storage import SqliteStorage


@dataclass(slots=True)
class EngineDependencies:
    connector: MarketDataConnector
    broker: Broker
    storage: SqliteStorage


class TradingEngine:
    def __init__(self, config: BotConfig, deps: EngineDependencies) -> None:
        self.config = config
        self.pipeline = TradingPipeline(SelectionModel(), EntryModel(), PositionPolicy())
        self.deps = deps
        self.risk = RiskManager(config.risk)

    def _choose_execution(self, mint: str, decision: TradeDecision, price: float) -> tuple[str, float]:
        if decision.action == "BUY":
            ok, reason = self.risk.can_open_position(self.config.trade_size_usd)
            if not ok:
                return f"BUY blocked ({reason})", 0.0

            message = self.deps.broker.buy(mint, self.config.trade_size_usd, price)
            if "BUY" in message:
                self.risk.on_position_opened()
            return message, 0.0

        if decision.action == "SELL":
            message, realized = self.deps.broker.sell_all(mint, price)
            if "SELL" in message:
                self.risk.on_position_closed(realized_pnl_usd=realized)
            return message, realized

        return f"No execution ({decision.action})", 0.0

    def run_once(self, mint: str) -> tuple[TradeDecision, str]:
        try:
            obs = self.deps.connector.next_observation(mint=mint)
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            decision = TradeDecision("SKIP", 0.99, "data_connector_error")
            message = f"Data connector failure: {exc}"
            self.deps.storage.save_decision(mint, decision, message)
            return decision, message

        self.deps.storage.save_observation(obs.features, obs.snapshot)

        entry_decision = self.pipeline.evaluate_entry(obs.features, obs.snapshot)

        # Si position ouverte (paper), on applique aussi la policy de sortie.
        decision = entry_decision
        if isinstance(self.deps.broker, PaperBroker) and self.deps.broker.has_position(mint):
            pos = self.deps.broker.positions[mint]
            pnl_pct = (obs.snapshot.price - pos.avg_entry_price) / max(pos.avg_entry_price, 1e-12)
            exit_decision = self.pipeline.position_policy.decide(pnl_pct=pnl_pct, hold_seconds=obs.snapshot.age_seconds)
            if exit_decision.action == "SELL":
                decision = exit_decision

        message, _ = self._choose_execution(mint=mint, decision=decision, price=obs.snapshot.price)
        self.deps.storage.save_decision(mint, decision, message)
        return decision, message

    def run_loop(self) -> None:
        for i in range(1, self.config.iterations + 1):
            mint = self.config.token_mint if self.config.token_mint != "demo-mint" else f"token-{i}"
            decision, message = self.run_once(mint)
            print(
                f"[{i:03d}] mint={mint} action={decision.action} "
                f"confidence={decision.confidence:.2f} reason={decision.reason} | {message}"
            )
            time.sleep(self.config.loop_delay_seconds)


def build_dependencies(config: BotConfig) -> EngineDependencies:
    if config.mode == "paper":
        connector: MarketDataConnector = MockMarketDataConnector(seed=42)
        broker: Broker = PaperBroker(initial_cash=1000.0)
    else:
        connector = SolanaRpcMarketDataConnector(config.rpc)
        live = LiveBroker(
            wallet_public_key=config.wallet.public_key,
            private_key_env=config.wallet.private_key_env,
            enabled=config.enable_live_trading,
        )
        live.validate()
        broker = live

    storage = SqliteStorage(config.db_path)
    storage.init_schema()
    return EngineDependencies(connector=connector, broker=broker, storage=storage)
