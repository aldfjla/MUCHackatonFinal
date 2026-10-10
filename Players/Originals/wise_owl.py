"""Wise Owl
School of thought: procurement (Kraljic portfolio routing)
Backlog version: v7 - niko
Copied from: agent/arena_kit/agents/router.py
Date: 2026-10-10
ORIGINAL SNAPSHOT: do not edit; copy to Players/ for experiments.
Run: see Players/Originals/README.md
"""

"""The Portfolio Router: the procurement school (Kraljic-style portfolio routing). Reads the buyer's
`category_goal` and hands the case to one archetype: competitive for leverage items, collaborative for
strategic ones, accommodating for bottleneck ones. The evidence for such a mapping is weak and contested
(SCHOOLS.md, section 6); it is a hypothesis to test, not a proven rule.

Default mapping (constructor knob `mapping`, goal -> archetype name):
  leverage -> anchor (competitive, the buyer has power)      routine -> rational (efficient, game theory)
  stabilise, quality_first -> explorer (collaborative)       secure_supply -> switcher (adaptive)
  unknown or missing goal -> rational

Knobs: mapping (goal -> archetype), agents ({archetype: zero-argument factory}; the defaults import the
real classes lazily, so tests can inject stubs and a broken sibling cannot break this module).
Exposes `chosen` (archetype name) and `goal` after the first decide; logs the choice once per case.
Safety: any delegate error falls back to closing_move, then to a walk-away; an accept that is not
strictly cheaper than the alternative (or not compliant without one) is replaced by closing_move.
"""

import logging

from arena_kit.cost import must_haves_ok, total_cost
from arena_kit.docs import standard_terms
from arena_kit.play import closing_move, live_threads, standing

log = logging.getLogger(__name__)

MAPPING = {
    "leverage": "anchor",
    "routine": "rational",
    "stabilise": "explorer",
    "quality_first": "explorer",
    "secure_supply": "switcher",
}
DEFAULT = "rational"


def _lazy(module, name):
    def make():
        import importlib

        return getattr(importlib.import_module(module), name)()

    return make


FACTORIES = {
    "anchor": _lazy("bold_ram", "AnchorAgent"),
    "rational": _lazy("patient_hawk", "RationalAgent"),
    "explorer": _lazy("curious_fox", "ExplorerAgent"),
    "switcher": _lazy("chameleon", "SwitcherAgent"),
    "boulware": _lazy("iron_turtle", "BoulwareAgent"),
}


class RouterAgent:
    def __init__(self, mapping=None, agents=None):
        self.mapping = {**MAPPING, **(mapping or {})}
        self.agents = {**FACTORIES, **(agents or {})}
        self.case_id = self.delegate = self.chosen = self.goal = None

    def _pick(self, case):
        self.goal = case.get("category_goal") or (case.get("buyer") or {}).get("category_goal")
        name = self.mapping.get(self.goal, DEFAULT)
        self.chosen = name if name in self.agents else DEFAULT
        self.case_id, self.delegate = case.get("case_id"), self.agents[self.chosen]()
        log.info("%s: goal %r -> %s", self.case_id, self.goal, self.chosen)

    def decide(self, case, threads):
        try:
            if self.delegate is None or case.get("case_id") != self.case_id:
                self.delegate = None
                self._pick(case)
            decision = self.delegate.decide(case, threads)
            return decision if self._accept_ok(case, threads, decision) else closing_move(case, threads)
        except Exception:  # never crash a case: close safely, else walk away
            log.exception("router delegate failed")
            try:
                return closing_move(case, threads)
            except Exception:
                live = live_threads(threads) or list(threads)
                return {"supplier_id": live[0] if live else None, "message": {"action": {"type": "walk_away"}}}

    @staticmethod
    def _accept_ok(case, threads, decision):
        """False only when an accept is provably not strictly better than the alternative."""
        action = (decision.get("message") or {}).get("action") or {}
        if action.get("type") != "accept":
            return True
        try:
            sid = decision["supplier_id"]
            sheet_id, terms = standing(threads[sid])
            if sheet_id != action.get("term_sheet_id"):
                return True  # cannot check an older sheet safely: leave it to the delegate
            std = standard_terms(threads[sid])
            alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
            if not must_haves_ok(case, terms, std):
                return False
            return not alt.get("unit_price") or total_cost(case, terms, std) < total_cost(case, alt)
        except Exception:
            return True


if __name__ == "__main__":
    from _runner import main

    main(RouterAgent)
