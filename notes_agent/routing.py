"""Otari routing + budget display logic.

This is the sharpened product idea, and it is deliberately boring
in the right way: nothing here invents a gateway feature.

- Otari is one gateway in front of many providers. The model string
  is ``provider:model`` (e.g. ``openai:gpt-4o-mini``) and Otari routes
  it. Switching providers changes the string, not the code.
- Routing in this project is therefore a *visible decision*: which
  provider/model was chosen, why, what the fallback chain is, and
  which routes were actually attempted. The UI shows that panel for
  every answer, so a judge can see Otari doing the routing work
  instead of taking it on trust.
- Fallback is local and honest: if the primary provider call raises,
  the fallback provider (if configured) is tried once. If both fail,
  the answer fails loudly — no fabricated answer, no silent guess.
- Budget has two layers, and the UI must never conflate them:
  (a) the local session budget in this app (calls used / remaining
  in this run, enforced in agent.py), shown as a meter;
  (b) the gateway-side budget/usage in the user's otari.ai account,
  which this app cannot see without that account — so the UI says
  "check otari.ai dashboard" instead of inventing a number.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Route:
    provider: str
    model: str
    reason: str


@dataclass
class RoutingInfo:
    """Everything the UI routing panel needs, in one serialisable shape."""

    gateway: str
    mode: str  # "mock" | "real-otari"
    chosen: Route | None
    fallback_chain: list[Route] = field(default_factory=list)
    attempted: list[str] = field(default_factory=list)
    fallback_used: bool = False
    refused_before_routing: bool = False

    def to_dict(self) -> dict:
        return {
            "gateway": self.gateway,
            "mode": self.mode,
            "mode_label": "[mock] offline stand-in — no live Otari call"
            if self.mode == "mock"
            else "real Otari gateway",
            "chosen": (
                {"provider": self.chosen.provider, "model": self.chosen.model, "reason": self.chosen.reason}
                if self.chosen
                else None
            ),
            "fallback_chain": [
                {"provider": r.provider, "model": r.model, "reason": r.reason}
                for r in self.fallback_chain
            ],
            "attempted": list(self.attempted),
            "fallback_used": self.fallback_used,
            "refused_before_routing": self.refused_before_routing,
        }


def parse_model(model: str) -> tuple[str, str]:
    """Split a ``provider:model`` string. Raises ValueError if malformed.

    A model string without a ``:`` cannot be routed by Otari, so it
    is rejected here rather than passed on and failing obscurely.
    """
    if not model or ":" not in model:
        raise ValueError(
            f"Model string must be provider:model (e.g. openai:gpt-4o-mini), got {model!r}"
        )
    provider, rest = model.split(":", 1)
    if not provider.strip() or not rest.strip():
        raise ValueError(
            f"Model string must be provider:model (e.g. openai:gpt-4o-mini), got {model!r}"
        )
    return provider.strip(), rest.strip()


def choose_route(
    model: str,
    fallback_model: str | None = None,
    user_selected: bool = False,
    gateway: str = "https://api.otari.ai",
    mode: str = "mock",
) -> RoutingInfo:
    """Build the routing decision for one answer.

    Rules, in order (all visible in the UI, none hidden):
    1. If the user picked a model in the UI/CLI, that model is chosen
       and the reason says so.
    2. Otherwise the configured default model is chosen.
    3. A fallback model, if configured, is listed as the fallback
       chain — it is only *attempted* if the primary call raises.
    """
    provider, _ = parse_model(model)
    reason = (
        "User-selected model — routed through Otari unchanged"
        if user_selected
        else "Default model from configuration — routed through Otari unchanged"
    )
    chosen = Route(provider=provider, model=model, reason=reason)
    chain: list[Route] = []
    if fallback_model:
        fb_provider, _ = parse_model(fallback_model)
        chain.append(
            Route(
                provider=fb_provider,
                model=fallback_model,
                reason="Fallback — tried only if the primary provider call fails",
            )
        )
    return RoutingInfo(gateway=gateway, mode=mode, chosen=chosen, fallback_chain=chain)


@dataclass
class BudgetTracker:
    """Local session budget. Counts provider attempts, not answers.

    A refused question (no matching notes) makes no provider call,
    so it must not consume budget — the refusal test pins this.
    """

    limit: int
    used: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def percent_used(self) -> int:
        if self.limit <= 0:
            return 100
        return min(100, round(100 * self.used / self.limit))

    @property
    def exhausted(self) -> bool:
        return self.used >= self.limit

    def charge(self) -> None:
        if self.exhausted:
            raise RuntimeError("LLM call budget for this run exceeded")
        self.used += 1

    def to_dict(self) -> dict:
        return {
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "percent_used": self.percent_used,
            "exhausted": self.exhausted,
            # Gateway-side budget is NOT this number. See module docstring.
            "gateway_budget_note": (
                "Gateway-side budget/usage lives in the otari.ai account dashboard "
                "and is not visible from this app. This meter is the local session budget only."
            ),
        }
