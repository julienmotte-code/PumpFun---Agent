# PumpFun Agent

Ce dépôt fournit une base **exécutable** pour un bot Pump.fun orienté production :
- mode **paper trading** avec suivi des positions,
- mode **live** protégé (garde-fous + validation config),
- pipeline décisionnel sélection/entrée/sortie,
- persistance SQLite des observations et décisions,
- architecture prête à brancher un exécuteur DEX réel.

## Architecture actuelle

- `runtime.py`
  - `MockMarketDataConnector` (démo/paper)
  - `SolanaRpcMarketDataConnector` (validation RPC + adaptateur à compléter pour flux Pump.fun)
- `pipeline.py`
  - `SelectionModel`, `EntryModel`, `PositionPolicy`
- `execution.py`
  - `PaperBroker` (état cash + positions + PnL réalisé)
  - `LiveBroker` (validation sécurité + hook `_send_order` à implémenter pour DEX)
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

Variables minimales :

```bash
export PUMPFUN_MODE=live
export PUMPFUN_ENABLE_LIVE_TRADING=true
export PUMPFUN_WALLET_PUBLIC_KEY=<YOUR_PUBLIC_KEY>
export PUMPFUN_PRIVATE_KEY=<YOUR_PRIVATE_KEY>
export PUMPFUN_RPC_ENDPOINT=https://api.mainnet-beta.solana.com
```

Puis :

```bash
PYTHONPATH=src python -m pumpfun_bot.main --mode live --enable-live-trading --iterations 100 --token-mint <TOKEN_MINT>
```

## Variables d'environnement

- `PUMPFUN_MODE` = `paper` | `live`
- `PUMPFUN_ENABLE_LIVE_TRADING` = `true/false`
- `PUMPFUN_RPC_ENDPOINT`
- `PUMPFUN_RPC_COMMITMENT`
- `PUMPFUN_WALLET_PUBLIC_KEY`
- `PUMPFUN_PRIVATE_KEY` (ou variable custom avec `PUMPFUN_WALLET_PRIVATE_KEY_ENV`)
- `PUMPFUN_DB_PATH`
- `PUMPFUN_TRADE_SIZE_USD`
- `PUMPFUN_MAX_POSITION_USD`
- `PUMPFUN_MAX_DAILY_LOSS_USD`
- `PUMPFUN_MAX_OPEN_POSITIONS`
- `PUMPFUN_TOKEN_MINT`
- `PUMPFUN_ITERATIONS`
- `PUMPFUN_LOOP_DELAY_SECONDS`

## Dernière étape avant vraie prod

Pour un live complet, implémenter l'adaptateur DEX dans `LiveBroker._send_order()` pour router/signature les ordres sur votre stack (Jupiter, Raydium, etc.).
