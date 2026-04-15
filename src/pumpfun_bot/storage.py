from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import TokenFeatures, TokenSnapshot, TradeDecision


class SqliteStorage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mint TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    price REAL NOT NULL,
                    market_cap REAL NOT NULL,
                    buy_count INTEGER NOT NULL,
                    sell_count INTEGER NOT NULL,
                    unique_wallets INTEGER NOT NULL,
                    mean_tx_size REAL NOT NULL,
                    creator_has_sold INTEGER NOT NULL,
                    score_creator_history REAL NOT NULL,
                    score_wallet_distribution REAL NOT NULL,
                    score_volume_quality REAL NOT NULL,
                    score_momentum_5s REAL NOT NULL,
                    score_volatility_regime REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    mint TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    execution_message TEXT NOT NULL
                );
                """
            )

    def save_observation(self, features: TokenFeatures, snapshot: TokenSnapshot) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO observations (
                    mint, observed_at, price, market_cap, buy_count, sell_count,
                    unique_wallets, mean_tx_size, creator_has_sold,
                    score_creator_history, score_wallet_distribution, score_volume_quality,
                    score_momentum_5s, score_volatility_regime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.mint,
                    snapshot.observed_at.isoformat(),
                    snapshot.price,
                    snapshot.market_cap,
                    snapshot.buy_count,
                    snapshot.sell_count,
                    snapshot.unique_wallets,
                    snapshot.mean_tx_size,
                    1 if snapshot.creator_has_sold else 0,
                    features.score_creator_history,
                    features.score_wallet_distribution,
                    features.score_volume_quality,
                    features.score_momentum_5s,
                    features.score_volatility_regime,
                ),
            )

    def save_decision(self, mint: str, decision: TradeDecision, execution_message: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO decisions (mint, action, confidence, reason, execution_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mint, decision.action, decision.confidence, decision.reason, execution_message),
            )
