from __future__ import annotations

import argparse
from dataclasses import dataclass

from .execution import LiveBroker, PaperBroker
from .pipeline import EntryModel, PositionPolicy, SelectionModel, TradingPipeline
from .runtime import MockMarketDataConnector


@dataclass(slots=True)
class BotConfig:
    mode: str
    iterations: int
    position_size_usd: float
    live_enabled: bool


def run_bot(config: BotConfig) -> None:
    connector = MockMarketDataConnector(seed=42)
    pipeline = TradingPipeline(SelectionModel(), EntryModel(), PositionPolicy())

    if config.mode == "paper":
        broker: PaperBroker | LiveBroker = PaperBroker(initial_cash=1000.0)
    else:
        broker = LiveBroker(enabled=config.live_enabled)
        broker.validate()

    print(f"Starting PumpFun bot in {config.mode!r} mode for {config.iterations} iterations")

    for step in range(1, config.iterations + 1):
        obs = connector.next_observation(mint=f"token-{step}")
        decision = pipeline.evaluate_entry(obs.features, obs.snapshot)

        if decision.action == "BUY":
            msg = broker.buy(config.position_size_usd, obs.snapshot.price)
        elif decision.action == "SELL":
            msg = broker.sell_all(obs.snapshot.price)
        else:
            msg = f"No execution ({decision.action})"

        print(
            f"[{step:02d}] mint={obs.snapshot.mint} "
            f"price={obs.snapshot.price:.8f} decision={decision.action} "
            f"confidence={decision.confidence:.2f} reason={decision.reason} | {msg}"
        )

    if isinstance(broker, PaperBroker):
        print(
            "Paper summary: "
            f"cash=${broker.cash:.2f}, position_units={broker.position_units:.2f}, "
            f"equity≈${broker.cash + broker.position_units * obs.snapshot.price:.2f}"
        )


def parse_args() -> BotConfig:
    parser = argparse.ArgumentParser(description="PumpFun trading bot scaffold")
    parser.add_argument("--mode", choices=["paper", "live"], default="paper")
    parser.add_argument("--iterations", type=int, default=12)
    parser.add_argument("--position-size-usd", type=float, default=50.0)
    parser.add_argument(
        "--enable-live-trading",
        action="store_true",
        help="Required in live mode to avoid accidental real trading",
    )

    args = parser.parse_args()
    return BotConfig(
        mode=args.mode,
        iterations=max(1, args.iterations),
        position_size_usd=max(1.0, args.position_size_usd),
        live_enabled=args.enable_live_trading,
    )


def main() -> None:
    config = parse_args()
    run_bot(config)


if __name__ == "__main__":
    main()
