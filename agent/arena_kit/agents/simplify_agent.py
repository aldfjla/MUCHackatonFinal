"""SimplifyAgent: slim reciprocal agent. Anchor, steady matched concessions, RFQ round-robin, one sheet per message.

Closing, must-have and pin helpers are shared with reciprocal.py."""

import math

from ..cost import complete_offer, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..play import closing_move, latest, moves_left
from .reciprocal import (
    ANCHOR,
    ANCHOR_FLOOR,
    FRAC0,
    FRAC_MAX,
    FRAC_STEP,
    KEEP,
    MATCH,
    MIN_STEP,
    MOVING_MIN,
    _c_alt,
    _live,
    _mine,
    _pinned,
    _sup,
    _tick,
    _valid,
    closing_accept,
)


class SimplifyAgent:
    def decide(self, case, threads):
        if not _live(threads):  # nothing to answer
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        if accept := closing_accept(case, threads):
            return accept
        live = [s for s in _live(threads) if moves_left(case, threads[s]) >= 1]
        open_ = [s for s in live if latest(threads[s]).get("status") not in ("final_offer", "agreed")]
        if not open_:
            return closing_move(case, threads)

        def key(s):  # keep every thread moving: fewest messages first, then the cheapest
            ev = threads[s]
            c = min((c for c, _ in _valid(case, ev, standard_terms(ev), math.inf, musts=False)), default=math.inf)
            return len(_mine(ev)), c

        sid = min(open_, key=key)
        events = threads[sid]
        std = standard_terms(events)
        valid = _valid(case, events, std, math.inf) or _valid(case, events, std, math.inf, musts=False)  # a must-have breach is fixed in our sheet
        if not valid:  # no priced sheet to answer: ask for one, give up after 3 asks
            if len(_mine(events)) >= 3:
                return {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
            return {"supplier_id": sid, "message": {"subject": case.get("title", "Our enquiry"), "body": "Could you please send us your quote?"}}
        _, best = min(valid, key=lambda v: v[0])
        sheets = self._sheets(case, events, std, best["terms"])
        if not sheets:  # nothing new left to offer: close on the best sheet, or give up
            return closing_move(case, threads)
        return {
            "supplier_id": sid,
            "message": {
                "subject": case.get("title", "Our proposal"),
                "body": "Thank you for your offer. We have moved on our side; please see our updated terms.",
                "term_sheets": [{"terms": t} for t in sheets],
            },
        }

    @staticmethod
    def _their_move(events):
        """How far the supplier's best price fell in its last message (0 if it did not)."""
        ps = [min(s["terms"]["unit_price"] for s in m["term_sheets"] if s["terms"].get("unit_price") is not None)
              for m in _sup(events) if any(s["terms"].get("unit_price") is not None for s in m["term_sheets"])]
        return max(0.0, ps[-2] - ps[-1]) if len(ps) >= 2 else 0.0

    def _price(self, case, events, p):
        mine = [m["term_sheets"][0]["terms"]["unit_price"] for m in _mine(events) if m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")]
        if not mine:
            cur = case["buyer"].get("current_unit_price") or p
            return max(ANCHOR_FLOOR * p, min(ANCHOR * p, cur))  # anchor; never pay more than now unless forced
        frac = min(FRAC_MAX, FRAC0 + FRAC_STEP * len(mine))
        move = self._their_move(events)
        step = max(frac * (p - mine[-1]), MIN_STEP * p, _tick(p))
        if move > 0:  # they moved: answer in step, not beyond (a supplier that holds still gets the full step)
            step = max(MOVING_MIN * p, _tick(p), min(step, MATCH * move))
        top = p if moves_left(case, events) <= 2 else p * (1 - KEEP)
        return max(mine[-1], min(top, mine[-1] + step))

    def _sheets(self, case, events, std, theirs):
        p, pins = theirs["unit_price"], _pinned(events)
        base = {k: v for k, v in {**{f: std[f] for f in case["negotiable"] if f in std}, **theirs}.items() if v is not None}
        opts = case.get("term_options") or {}
        c_alt = _c_alt(case)
        sent = [m["term_sheets"] for m in _mine(events) if m.get("term_sheets")]
        seen = [s["terms"] for ss in sent for s in ss]

        def make(price, **over):
            over = {k: v for k, v in over.items() if k not in pins}
            return satisfy_must_haves(case, {**base, "unit_price": round(price, 2), **over}, std)

        def cost(t):
            return total_cost(case, t, std)

        def cap(t):  # hard floor: never offer a sheet that costs more than the alternative
            if (c := cost(t)) >= c_alt:
                slope = cost({**t, "unit_price": t["unit_price"] + 1}) - c
                if slope > 0:
                    t = {**t, "unit_price": round(t["unit_price"] - (c - c_alt) / slope - 0.01, 2)}
            return t

        def best_months(price, **over):
            months = [m for m in opts.get("contract_months", []) if m and "contract_months" in case["negotiable"]] or [None]
            return min(months, key=lambda m: (cost(make(price, **over, **({"contract_months": m} if m else {}))), m or 0))

        fields = [f for f in ("payment_days",) if f in case["negotiable"] and f not in pins and opts.get(f)]
        asks = [{}]
        for f in fields:
            asks = [{f: o} for o in opts[f]]

        def one(price):  # one sheet: cheapest allowed payment option and contract length
            months = best_months(price)
            return min((cap(make(price, **({"contract_months": months} if months else {}), **v)) for v in asks), key=cost)

        price = self._price(case, events, p)
        main = one(price)
        floor = max((x["terms"]["unit_price"] for ss in sent for x in ss[:1] if x["terms"].get("unit_price")), default=0.0)
        while (main in seen or main["unit_price"] <= floor) and price < p:  # always a visible step, never a repeat, never above theirs
            price = min(p, price + _tick(p))
            new = one(price)
            if new == main:  # capped: the price cannot move
                break
            main = new
        return [] if main in seen else [complete_offer(case, main)]
