from __future__ import annotations

import pytest

from pumpfun_bot.execution import LiveBroker, PaperBroker
from pumpfun_bot.main import BotConfig, run_bot


def test_paper_broker_buy_and_sell() -> None:
    broker = PaperBroker(initial_cash=100)
    buy_msg = broker.buy(notional=40, price=2)
    assert "BUY paper" in buy_msg
    assert broker.cash == pytest.approx(60)
    assert broker.position_units == pytest.approx(20)

    sell_msg = broker.sell_all(price=2.5)
    assert "SELL paper" in sell_msg
    assert broker.position_units == pytest.approx(0)
    assert broker.cash == pytest.approx(110)


def test_live_mode_is_guarded_without_flag() -> None:
    config = BotConfig(mode="live", iterations=1, position_size_usd=50, live_enabled=False)
    with pytest.raises(RuntimeError, match="enable-live-trading"):
        run_bot(config)


def test_live_mode_with_flag_runs_placeholder() -> None:
    config = BotConfig(mode="live", iterations=1, position_size_usd=50, live_enabled=True)
    run_bot(config)
