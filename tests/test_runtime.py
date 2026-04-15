from __future__ import annotations

import os

import pytest

from pumpfun_bot.config import BotConfig, load_config_from_env
from pumpfun_bot.engine import EngineDependencies, TradingEngine, build_dependencies
from pumpfun_bot.execution import LiveBroker, PaperBroker


def test_paper_broker_buy_and_sell_tracks_pnl() -> None:
    broker = PaperBroker(initial_cash=100)
    buy_msg = broker.buy(mint="abc", notional=40, price=2)
    assert "BUY paper" in buy_msg
    assert broker.cash == pytest.approx(60)
    assert broker.has_position("abc")

    sell_msg, realized = broker.sell_all(mint="abc", price=2.5)
    assert "SELL paper" in sell_msg
    assert realized == pytest.approx(10)
    assert broker.cash == pytest.approx(110)


def test_live_mode_env_requires_core_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUMPFUN_MODE", "live")
    monkeypatch.setenv("PUMPFUN_ENABLE_LIVE_TRADING", "true")
    monkeypatch.delenv("PUMPFUN_WALLET_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("PUMPFUN_MARKETDATA_URL", raising=False)
    monkeypatch.delenv("PUMPFUN_EXECUTOR_URL", raising=False)
    with pytest.raises(ValueError, match="WALLET_PUBLIC_KEY"):
        load_config_from_env()


def test_engine_persists_decisions(tmp_path) -> None:
    db_path = tmp_path / "bot.sqlite"
    config = BotConfig(mode="paper", iterations=1, loop_delay_seconds=0.1, db_path=str(db_path))
    deps = build_dependencies(config)
    engine = TradingEngine(config=config, deps=deps)

    decision, message = engine.run_once("abc")
    assert decision.action in {"BUY", "HOLD", "SKIP", "SELL"}
    assert isinstance(message, str)
    assert os.path.exists(db_path)


def test_engine_handles_connector_failure(tmp_path) -> None:
    class FailingConnector:
        def next_observation(self, mint: str):
            raise RuntimeError("rpc down")

    db_path = tmp_path / "bot.sqlite"
    config = BotConfig(mode="paper", iterations=1, loop_delay_seconds=0.1, db_path=str(db_path))
    deps = build_dependencies(config)
    deps = EngineDependencies(connector=FailingConnector(), broker=deps.broker, storage=deps.storage)
    engine = TradingEngine(config=config, deps=deps)

    decision, message = engine.run_once("abc")
    assert decision.action == "SKIP"
    assert "connector" in message.lower()


def test_live_broker_requires_executor_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUMPFUN_PRIVATE_KEY", "abc")
    broker = LiveBroker(wallet_public_key="pub", executor_url="", enabled=True)
    with pytest.raises(RuntimeError, match="executor URL"):
        broker.validate()
