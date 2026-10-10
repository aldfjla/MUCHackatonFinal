"""SimplifyAgent: slim reciprocal agent. Anchor, steady matched concessions, RFQ round-robin.

Every choice among candidate sheets is priced with cost.total_cost, over the five parts of C:
1. price: anchor 0.80 x theirs, steady concessions matched to theirs;
2. uncovered need: contract length and volume are the options with the lowest C (never leave need uncovered);
3. payment, freight, lead time: each negotiable lever takes its lowest-C option, unless the supplier pinned it;
4. quality and other: ppm commitment likewise, plus a second sheet with an index clause for a higher price;
5. the supplier's health (strategic / bottleneck goals with a relationship cost): C charges for leaving the supplier below a
   sustainable margin, but the buyer cannot estimate its full cost (should-cost exists for about half the parts and can exceed
   the price), so cost.total_cost sees 0 and the mock does not price it. Safer rule there, UNTESTED against the real penalty:
   anchor 0.90 and only levers that cost the supplier nothing (contract length, volume); payment, freight, lead time and
   quality stay at the supplier's own terms.

Closing, must-have and pin helpers are shared with reciprocal.py."""

import math

from ..cost import RELATIONSHIP_GOALS, complete_offer, total_cost
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
    case_c_open,
    closing_accept,
)

EASED_ANCHOR = 0.90
STALL = 0.01  # the supplier's best C fell by less than this (x C) across its last two replies: it has stalled
GAP = 0.05  # then our offer rises until it is at most this far (x their C) below theirs
FREE_LEVERS = ("contract_months", "volume_per_year")  # cost the supplier nothing in cash
LEVERS = ("contract_months", "volume_per_year", "payment_days", "incoterm", "lead_time_days", "ppm_commitment")


def _health_at_stake(case):
    """C charges for the supplier's margin (strategic / bottleneck goal with a price per margin point)."""
    b = case["buyer"]
    return b.get("category_goal") in RELATIONSHIP_GOALS and bool(b.get("relationship_eur_per_point"))


class SimplifyAgent:
    _c_open = math.inf  # set per decision; our offer never costs more than the closing rule would accept

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
        # cap: the opening and the best standing sheet of any other open thread
        others = [c for s in open_ if s != sid for c, _ in _valid(case, threads[s], standard_terms(threads[s]), math.inf)]
        self._c_open = min([case_c_open(case, threads), *others])
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

    @staticmethod
    def _stalled(case, events, std):
        """We have opened and the supplier's best C fell by < STALL across its last two replies (3+ priced messages)."""
        cs = [min(total_cost(case, t["terms"], std) for t in m["term_sheets"] if t["terms"].get("unit_price") is not None)
              for m in _sup(events) if any(t["terms"].get("unit_price") is not None for t in m["term_sheets"])]
        return bool(_mine(events)) and len(cs) >= 3 and cs[-3] - cs[-1] < STALL * cs[-3]

    def _price(self, case, events, p):
        mine = [m["term_sheets"][0]["terms"]["unit_price"] for m in _mine(events) if m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")]
        if not mine:
            cur = case["buyer"].get("current_unit_price") or p
            return max(ANCHOR_FLOOR * p, min((EASED_ANCHOR if _health_at_stake(case) else ANCHOR) * p, cur))  # anchor; never pay more than now unless forced
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

        def one(price):  # one sheet: for each negotiable lever the option with the lowest C (pinned ones stay theirs)
            over = {}
            for f in FREE_LEVERS if _health_at_stake(case) else LEVERS:
                options = [o for o in opts.get(f, []) if o] if f in case["negotiable"] and f not in pins else []
                if options:
                    over[f] = min(options, key=lambda o: cost(make(price, **over, **{f: o})))
            return cap(make(price, **over))

        price = self._price(case, events, p)
        main = one(price)
        floor = max((x["terms"]["unit_price"] for ss in sent for x in ss[:1] if x["terms"].get("unit_price")), default=0.0)
        while (main in seen or main["unit_price"] <= floor) and price < p:  # always a visible step, never a repeat, never above theirs
            price = min(p, price + _tick(p))
            new = one(price)
            if new == main:  # capped: the price cannot move
                break
            main = new
        if self._stalled(case, events, std):  # close the gap to <= GAP of their C, never past c_open
            f = lambda x: cost(one(x))
            target, lo, hi = (1 - GAP) * cost(theirs), main["unit_price"], p
            if f(hi) >= target:  # smallest price that reaches the target
                for _ in range(30):
                    mid = (lo + hi) / 2
                    lo, hi = (lo, mid) if f(mid) >= target else (mid, hi)
            if f(hi) > self._c_open:  # largest price that stays within c_open
                lo = main["unit_price"]
                for _ in range(30):
                    mid = (lo + hi) / 2
                    lo, hi = (mid, hi) if f(mid) <= self._c_open else (lo, mid)
                hi = lo
            hi = round(hi, 2)
            while hi > main["unit_price"] and f(hi) > self._c_open:  # rounding must not pass c_open
                hi = round(hi - 0.01, 2)
            if hi > main["unit_price"]:
                main = one(hi)
        if main in seen:
            return []
        out, variants = [main], []
        # the index clause is security for them, not cash: offer it at the price where our C stays just below main's
        clauses = (c for c in opts.get("index_clause", []) if c) if "index_clause" in case["negotiable"] and "index_clause" not in pins else []
        # the clause (deadband) with the lowest C at main's price is tried first: equal prices after the cap must not pick deadband 0
        for clause in sorted(clauses, key=lambda c: cost(make(main["unit_price"], index_clause=c, **{f: main[f] for f in LEVERS if f in main}))):
            t = make(main["unit_price"], index_clause=clause, **{f: main[f] for f in LEVERS if f in main})
            slope = cost({**t, "unit_price": t["unit_price"] + 1}) - cost(t)
            if t["index_clause"] == clause != main.get("index_clause") and slope > 0:
                price = round(max(0.75 * p, min(p, t["unit_price"] - (cost(t) - cost(main)) / slope - 0.01)), 2)  # no lowball
                v = cap({**t, "unit_price": price})
                if v not in seen and cost(v) < cost(main):
                    variants.append(v)
        if variants:
            out.append(max(variants, key=lambda v: v["unit_price"]))  # max keeps the first (lowest-C clause) on ties
        return [complete_offer(case, t) for t in out]
