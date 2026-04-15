# System design - Pump.fun auto trader

## 1) Données à capturer (T0 -> T+10m)

### Métadonnées token
- mint
- créateur
- timestamp création
- market cap initial
- liquidité initiale

### Données créateur
- nombre de tokens déjà lancés
- taux de réussite historique (si disponible)
- comportements de dump précoces
- proportion de tokens où le créateur vend dans les 10 premières minutes

### Microstructure marché
- nombre de wallets uniques acheteurs/vendeurs
- concentration des volumes (top wallets)
- tailles de transactions (moyenne, médiane, skew)
- ratio buy/sell
- vitesse d'arrivée des ordres

### Séries temporelles (5 secondes)
- prix
- volume
- market cap
- variation %
- volatilité rolling
- RSI court
- EMA courtes (ex: 10/20 ticks)
- MACD ultra-court
- momentum

## 2) Schéma de décision

### Étape A - sélection token
Scorer chaque token avec un modèle de classification/ranking (`SelectionModel`) :
- entrées = features structurelles + comportement initial
- sortie = probabilité de scénario haussier exploitable

### Étape B - timing d'entrée
Sur les tokens retenus, un second modèle (`EntryModel`) valide le timing :
- entrées = séquence technique en 5s
- sortie = signal BUY avec niveau de confiance

### Étape C - gestion de position
Un module de politique (`PositionPolicy`) arbitre hold/sell :
- stop-loss dynamique
- take-profit partiel
- trailing stop
- time-based exit (invalidité du setup)

## 3) Labeling recommandé

Exemple de labels :
- `target_up_60s`: +X% dans les 60s après l'instant t
- `target_up_180s`: +Y% dans les 180s
- `max_drawdown_180s`: drawdown max post-entrée

Ces labels permettent de transformer le problème en:
- classification (go/no-go)
- optimisation de seuil (profit net après frais/slippage)

## 4) Contrôles de risque minimum
- risque fixe par trade (ex: 0.5% à 1% du capital)
- limite de perte journalière
- kill-switch si latence ou anomalies API
- blacklist automatique des patterns frauduleux

## 5) Boucle d'apprentissage continue
- journalisation complète des décisions et du contexte
- recalcul hebdomadaire des features les plus prédictives
- recalibration des seuils selon le régime de marché
- test hors-échantillon permanent avant promotion en production
