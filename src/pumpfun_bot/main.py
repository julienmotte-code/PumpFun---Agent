from __future__ import annotations

import argparse

from .config import BotConfig, ConfigError, load_config_from_env, validate_config
from .engine import TradingEngine, build_dependencies


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PumpFun trading bot")
    parser.add_argument("--mode", choices=["paper", "live"], default=None)
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--loop-delay-seconds", type=float, default=None)
    parser.add_argument("--trade-size-usd", type=float, default=None)
    parser.add_argument("--token-mint", type=str, default=None)
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--enable-live-trading", action="store_true")
    return parser.parse_args()


def merge_cli_overrides(base: BotConfig, args: argparse.Namespace) -> BotConfig:
    if args.mode is not None:
        base.mode = args.mode
    if args.iterations is not None:
        base.iterations = max(1, args.iterations)
    if args.loop_delay_seconds is not None:
        base.loop_delay_seconds = max(0.1, args.loop_delay_seconds)
    if args.trade_size_usd is not None:
        base.trade_size_usd = max(1.0, args.trade_size_usd)
    if args.token_mint is not None:
        base.token_mint = args.token_mint
    if args.db_path is not None:
        base.db_path = args.db_path
    if args.enable_live_trading:
        base.enable_live_trading = True
    return base


def main() -> None:
    args = parse_args()
    try:
        config = validate_config(merge_cli_overrides(load_config_from_env(), args))
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    deps = build_dependencies(config)
    engine = TradingEngine(config=config, deps=deps)
    engine.run_loop()


if __name__ == "__main__":
    main()
