# PumpFun Agent

Ce dépôt fournit une base **exécutable** pour un bot Pump.fun orienté production :
- mode **paper trading** avec suivi des positions,
- mode **live** protégé (garde-fous + validation config),
- pipeline décisionnel sélection/entrée/sortie,
- persistance SQLite des observations et décisions,
- intégration **HTTP** explicite vers un fournisseur de market data et un exécuteur d'ordres.

## Architecture actuelle

- `runtime.py`
  - `MockMarketDataConnector` (démo/paper)
  - `HttpMarketDataConnector` (source live via API JSON)
  - `SolanaRpcMarketDataConnector` (fallback probe RPC)
- `pipeline.py`
  - `SelectionModel`, `EntryModel`, `PositionPolicy`
- `execution.py`
  - `PaperBroker` (état cash + positions + PnL réalisé)
  - `LiveBroker` (validation sécurité + envoi HTTP à l'exécuteur)
- `risk.py`
  - règles globales: taille max, perte max journalière, positions max
- `storage.py`
  - stockage SQLite (`observations`, `decisions`)
- `engine.py`
  - orchestration complète (data → décision → exécution → stockage)

## Installation

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip pytest
```

### Windows (cmd)

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip pytest
```

## Vérification

```bash
PYTHONPATH=src pytest
```

## Lancement rapide (paper)

```bash
PYTHONPATH=src python -m pumpfun_bot.main --mode paper --iterations 20 --trade-size-usd 50 --db-path ./data/pumpfun.sqlite
```

## Lancement live (sécurisé)

Le mode live **exige** les variables suivantes :

```bash
export PUMPFUN_MODE=live
export PUMPFUN_ENABLE_LIVE_TRADING=true
export PUMPFUN_WALLET_PUBLIC_KEY=<YOUR_PUBLIC_KEY>
export PUMPFUN_PRIVATE_KEY=<YOUR_PRIVATE_KEY>
export PUMPFUN_MARKETDATA_URL=https://your-marketdata-service/observation
export PUMPFUN_EXECUTOR_URL=https://your-executor-service/order
```

Puis :

```bash
PYTHONPATH=src python -m pumpfun_bot.main --mode live --enable-live-trading --iterations 100 --token-mint <TOKEN_MINT>
```

## Contrat API requis

### Market data API (`PUMPFUN_MARKETDATA_URL`)

GET `...?mint=<TOKEN_MINT>` doit retourner:

```json
{
  "snapshot": {
    "mint": "...",
    "observed_at": "2026-04-15T12:34:56+00:00",
    "age_seconds": 45,
    "price": 0.00012,
    "market_cap": 34000,
    "buy_count": 45,
    "sell_count": 20,
    "unique_wallets": 130,
    "mean_tx_size": 1.1,
    "creator_has_sold": false
  },
  "features": {
    "mint": "...",
    "score_creator_history": 0.8,
    "score_wallet_distribution": 0.7,
    "score_volume_quality": 0.75,
    "score_momentum_5s": 0.77,
    "score_volatility_regime": 0.2
  }
}
```

### Executor API (`PUMPFUN_EXECUTOR_URL`)

POST JSON:

```json
{
  "side": "BUY",
  "mint": "...",
  "notional": 50,
  "reference_price": 0.00012,
  "wallet_public_key": "...",
  "private_key_env": "PUMPFUN_PRIVATE_KEY"
}
```

## Variables d'environnement

- `PUMPFUN_MODE` = `paper` | `live`
- `PUMPFUN_ENABLE_LIVE_TRADING` = `true/false`
- `PUMPFUN_RPC_ENDPOINT`
- `PUMPFUN_RPC_COMMITMENT`
- `PUMPFUN_WALLET_PUBLIC_KEY`
- `PUMPFUN_PRIVATE_KEY` (ou variable custom avec `PUMPFUN_WALLET_PRIVATE_KEY_ENV`)
- `PUMPFUN_MARKETDATA_URL`
- `PUMPFUN_EXECUTOR_URL`
- `PUMPFUN_DB_PATH`
- `PUMPFUN_TRADE_SIZE_USD`
- `PUMPFUN_MAX_POSITION_USD`
- `PUMPFUN_MAX_DAILY_LOSS_USD`
- `PUMPFUN_MAX_OPEN_POSITIONS`
- `PUMPFUN_TOKEN_MINT`
- `PUMPFUN_ITERATIONS`
- `PUMPFUN_LOOP_DELAY_SECONDS`
