"""PlaybookAgent: replays what the real practice runs taught us (playbook.json, see playbook_build.py).

For a supplier with a playbook entry for this case type and goal: move 1 is the best known term sheet at ~2% below
the supplier's known floor price, move 2 the floor price on that package; we accept the standing sheet once it is
within 1% of the floor, or on a final_offer whose C is no worse than the best known deal. A supplier that replies
more than 1% above the floor after move 2 (a reply >5% above it is the deviation case), and every supplier without an entry,
goes to the delegate for the rest of the case. State is plain dict/list/set so play()'s snapshot works."""

import json
from pathlib import Path

from ..cost import RELATIONSHIP_GOALS, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..play import _safe_accept, latest, live_threads, moves_left, standing
from .reciprocal import _mine

PLAYBOOK = Path(__file__).parents[1] / "playbook.json"
FIRST, NEAR = 0.98, 1.01  # after move 2 any reply not within NEAR of the floor (so also one >5% above it) hands over


def load_playbook(path=PLAYBOOK):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).is_file() else {}


class PlaybookAgent:
    def __init__(self, delegate, playbook=None):
        self.delegate, self.playbook = delegate, load_playbook() if playbook is None else playbook
        self.handed = set()  # suppliers of this case the delegate has taken over

    def __getattr__(self, name):
        if name in ("delegate", "playbook", "handed"):
            raise AttributeError(name)
        return getattr(self.delegate, name)

    def entry(self, case, sid):
        e = self.playbook.get(sid, {}).get(f"{case.get('type')}/{case['buyer'].get('category_goal')}")
        return e if e and e.get("best_deal") else None

    def _floor(self, case, e):
        """The price we hold the supplier to: its lowest ever offer; a relationship goal never goes below the C-minimising price."""
        floor = e["lowest_offered_price"]
        if case["buyer"].get("category_goal") in RELATIONSHIP_GOALS:
            floor = max(floor, e.get("c_min_price") or e["best_deal"]["price"])
        return floor

    def _sheet(self, case, events, e, price):
        t = {k: v for k, v in e["best_deal"]["terms"].items() if k in case["negotiable"]}
        t["unit_price"] = round(max(price, (e.get("target") or {}).get("price_with_best_levers") or 0.0), 2)
        sheet = satisfy_must_haves(case, t, standard_terms(events))
        return {"supplier_id": None, "message": {"subject": case.get("title", "Our proposal"),
                "body": "Thank you for your offer. Please see our proposed terms.", "term_sheets": [{"terms": sheet}]}}

    def decide(self, case, threads):
        for sid in live_threads(threads):
            if sid in self.handed or not (e := self.entry(case, sid)):
                continue
            ev, floor = threads[sid], self._floor(case, e)
            sheet_id, terms = standing(ev)
            price, n = terms.get("unit_price"), len(_mine(ev))
            final = latest(ev).get("status") == "final_offer"
            ok = bool(sheet_id) and price is not None and _safe_accept(case, threads, sid, terms)
            if ok and (price <= floor * NEAR or final and total_cost(case, terms, standard_terms(ev)) <= e["best_deal"]["c_deal"]):
                return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
            # no price or a final offer we do not take, no move left, or both scripted moves spent (a reply more than 5% above the floor is the deviation case)
            if price is None or final or n >= 2 or moves_left(case, ev) < 1:
                self.handed.add(sid)
                continue
            move = self._sheet(case, ev, e, floor * FIRST if n == 0 else floor)
            return {**move, "supplier_id": sid}
        return self.delegate.decide(case, threads)
