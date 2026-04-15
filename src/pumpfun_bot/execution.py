from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PaperBroker:
    """Exécuteur fictif (paper trading) qui logue les ordres en mémoire."""

    initial_cash: float = 1000.0
    cash: float = field(init=False)
    position_units: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.cash = self.initial_cash

    def buy(self, notional: float, price: float) -> str:
        notional = min(notional, self.cash)
        if notional <= 0:
            return "BUY ignored (cash=0)"
        units = notional / max(price, 1e-12)
        self.cash -= notional
        self.position_units += units
        return f"BUY paper: ${notional:.2f} at {price:.8f} -> +{units:.2f} units"

    def sell_all(self, price: float) -> str:
        if self.position_units <= 0:
            return "SELL ignored (no position)"
        proceeds = self.position_units * price
        units = self.position_units
        self.cash += proceeds
        self.position_units = 0.0
        return f"SELL paper: {units:.2f} units at {price:.8f} -> +${proceeds:.2f}"


@dataclass(slots=True)
class LiveBroker:
    """Placeholder live broker.

    Les appels API réels (wallet/signature/rpc) restent à implémenter.
    """

    enabled: bool = False

    def validate(self) -> None:
        if not self.enabled:
            raise RuntimeError(
                "Live mode requires --enable-live-trading. "
                "Par sécurité, l'exécution réelle est désactivée par défaut."
            )

    def buy(self, notional: float, price: float) -> str:
        self.validate()
        return (
            "LIVE BUY placeholder: implémenter ici la signature wallet + "
            f"appel DEX (notional=${notional:.2f}, price={price:.8f})"
        )

    def sell_all(self, price: float) -> str:
        self.validate()
        return f"LIVE SELL placeholder: implémenter liquidation au prix {price:.8f}"
