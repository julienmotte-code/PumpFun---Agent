from datetime import datetime, timezone

from pumpfun_bot.models import TokenFeatures, TokenSnapshot
from pumpfun_bot.pipeline import EntryModel, PositionPolicy, SelectionModel, TradingPipeline


def test_pipeline_buy_signal() -> None:
    pipeline = TradingPipeline(SelectionModel(), EntryModel(entry_threshold=0.5), PositionPolicy())
    features = TokenFeatures(
        mint="abc",
        score_creator_history=0.8,
        score_wallet_distribution=0.7,
        score_volume_quality=0.75,
        score_momentum_5s=0.8,
        score_volatility_regime=0.2,
    )
    snapshot = TokenSnapshot(
        mint="abc",
        observed_at=datetime.now(timezone.utc),
        age_seconds=45,
        price=0.0001,
        market_cap=20000,
        buy_count=30,
        sell_count=5,
        unique_wallets=120,
        mean_tx_size=2.5,
        creator_has_sold=False,
    )

    decision = pipeline.evaluate_entry(features, snapshot)
    assert decision.action == "BUY"


def test_position_policy_stop_loss() -> None:
    policy = PositionPolicy(stop_loss_pct=-0.1)
    decision = policy.decide(pnl_pct=-0.15, hold_seconds=20)
    assert decision.action == "SELL"
    assert decision.reason == "stop_loss"
