"""Confident Owl: the Portfolio Router with one change. Leverage items (the buyer has power) go to the
Confident Turtle: hold firm like Boulware, with the confidence index as the safety valve. Every other
goal keeps the parent mapping, and an unknown or missing goal still falls back to `rational`.
"""

from ..guard import GuardedAgent
from .router import FACTORIES, RouterAgent, _lazy

MAPPING = {
    "leverage": "confident_boulware",
    "routine": "rational",
    "stabilise": "explorer",
    "quality_first": "explorer",
    "secure_supply": "switcher",
}

# every routed archetype runs inside the guard layer (must-haves asked for, no premature walk-away)
GUARDED = {
    name: (lambda f=f: GuardedAgent(f()))
    for name, f in {
        **FACTORIES,
        "confident_boulware": _lazy("confident_boulware", "ConfidentBoulwareAgent"),
    }.items()
}


class ConfidentRouterAgent(RouterAgent):
    def __init__(self, mapping=None, agents=None):
        super().__init__(
            mapping={**MAPPING, **(mapping or {})},
            agents={**GUARDED, **(agents or {})},
        )
