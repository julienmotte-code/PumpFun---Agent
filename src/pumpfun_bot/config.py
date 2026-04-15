from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class RpcConfig:
    endpoint: str
    commitment: str = "confirmed"


@dataclass(slots=True)
class WalletConfig:
    public_key: str
    private_key_env: str = "PUMPFUN_PRIVATE_KEY"


@dataclass(slots=True)
class RiskConfig:
    max_daily_loss_usd: float = 150.0
    max_position_usd: float = 75.0
    max_open_positions: int = 3


@dataclass(slots=True)
class BotConfig:
    mode: str = "paper"
    iterations: int = 60
    loop_delay_seconds: float = 1.0
    trade_size_usd: float = 50.0
    token_mint: str = "demo-mint"
    enable_live_trading: bool = False
    db_path: str = "pumpfun_bot.sqlite"
    rpc: RpcConfig = field(default_factory=lambda: RpcConfig(endpoint="https://api.mainnet-beta.solana.com"))
    wallet: WalletConfig = field(default_factory=lambda: WalletConfig(public_key=""))
    risk: RiskConfig = field(default_factory=RiskConfig)


class ConfigError(ValueError):
    pass


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config_from_env() -> BotConfig:
    mode = os.getenv("PUMPFUN_MODE", "paper").strip().lower()
    if mode not in {"paper", "live"}:
        raise ConfigError("PUMPFUN_MODE must be 'paper' or 'live'")

    endpoint = os.getenv("PUMPFUN_RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")
    commitment = os.getenv("PUMPFUN_RPC_COMMITMENT", "confirmed")

    trade_size = float(os.getenv("PUMPFUN_TRADE_SIZE_USD", "50"))
    max_pos = float(os.getenv("PUMPFUN_MAX_POSITION_USD", str(trade_size)))

    cfg = BotConfig(
        mode=mode,
        iterations=max(1, int(os.getenv("PUMPFUN_ITERATIONS", "60"))),
        loop_delay_seconds=max(0.1, float(os.getenv("PUMPFUN_LOOP_DELAY_SECONDS", "1"))),
        trade_size_usd=max(1.0, trade_size),
        token_mint=os.getenv("PUMPFUN_TOKEN_MINT", "demo-mint"),
        enable_live_trading=_as_bool(os.getenv("PUMPFUN_ENABLE_LIVE_TRADING"), False),
        db_path=os.getenv("PUMPFUN_DB_PATH", "pumpfun_bot.sqlite"),
        rpc=RpcConfig(endpoint=endpoint, commitment=commitment),
        wallet=WalletConfig(
            public_key=os.getenv("PUMPFUN_WALLET_PUBLIC_KEY", ""),
            private_key_env=os.getenv("PUMPFUN_WALLET_PRIVATE_KEY_ENV", "PUMPFUN_PRIVATE_KEY"),
        ),
        risk=RiskConfig(
            max_daily_loss_usd=max(1.0, float(os.getenv("PUMPFUN_MAX_DAILY_LOSS_USD", "150"))),
            max_position_usd=max(1.0, max_pos),
            max_open_positions=max(1, int(os.getenv("PUMPFUN_MAX_OPEN_POSITIONS", "3"))),
        ),
    )

    return validate_config(cfg)


def validate_config(cfg: BotConfig) -> BotConfig:
    if cfg.mode not in {"paper", "live"}:
        raise ConfigError("mode must be paper/live")
    if cfg.mode == "live" and not cfg.wallet.public_key:
        raise ConfigError("PUMPFUN_WALLET_PUBLIC_KEY is required in live mode")
    return cfg
