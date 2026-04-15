# PumpFun Agent

Ce dépôt contient une base de travail pour construire un robot de trading automatique orienté Pump.fun (Solana).

## Objectif

Créer un système **data-driven** qui :
1. Observe les nouveaux tokens Pump.fun.
2. Enregistre les 10 premières minutes de vie (événements + indicateurs toutes les 5 secondes).
3. Apprend des patterns de hausse pour filtrer les opportunités.
4. Détecte le meilleur timing d'entrée.
5. Gère la sortie (hold/sell) en temps réel.
6. Réentraîne en continu pour s'adapter aux changements de marché.

## Architecture proposée

Le système est découpé en 5 sous-systèmes :

- **Ingestion temps réel**
  - Flux des nouveaux tokens.
  - Flux transactions (swaps, buys/sells, wallet uniques, tailles de trade).
  - Snapshot market cap et prix.

- **Stockage et feature store**
  - Table `tokens`
  - Table `events`
  - Table `candles_5s`
  - Table `features_10m`
  - Table `trades`

- **Recherche de signaux (offline)**
  - Construction du dataset labellisé (hausse significative vs non).
  - Feature engineering (créateur, distribution des wallets, pression acheteuse, volatilité, momentum).
  - Entraînement modèle de sélection.
  - Entraînement modèle de timing d'entrée.

- **Exécution en réel**
  - Pipeline à 2 étages :
    1. `SelectionModel` (filtre token)
    2. `EntryModel` (déclenchement achat)
  - Risk management : taille de position, max exposition, stop-loss, take-profit, time-stop.

- **Boucle d'apprentissage continue**
  - Logging de tous les trades.
  - Backtest périodique.
  - Réentraînement planifié.
  - Monitoring de dérive (drift).

## Notes importantes

- Ce dépôt fournit une **ossature technique** et des objets de domaine pour implémenter la logique.
- Le trading comporte un risque élevé de perte totale du capital.
- Ne jamais utiliser une clé wallet de production sans environnement sécurisé (vault, permissions minimales, rotation).

## Démarrage rapide

```bash
python -m compileall src
```

Puis implémenter vos connecteurs Pump.fun / Solana dans `src/pumpfun_bot`.
