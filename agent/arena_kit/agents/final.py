"""FinalAgent: the Reciprocal Bargainer tuned for the live final. Differences from ReciprocalAgent:

- No throttle by default (`match=None`): the supplier mirrors our concessions, so a step of 0.25 x its
  last move got equally tiny moves back and froze (P08 v16: ours 4.79 -> 4.92 -> 4.93, theirs 5.51 -> 5.47).
- Cases of type "price_increase": anchor at our current price, not 20% below their quote (that made the
  supplier move backwards on P02). Every other case anchors as the parent does (`anchor` x their price).
- A silent thread is skipped after `max_asks` (2) of our messages instead of walking away: a walk_away on
  ANY thread ends the whole case. Only `closing_move`, when nothing else can be done, may walk away.
- Questions instead of moves count as no move, so the wrapper (questions=False) only asks for a missing quote.
Everything else (closing rule, sheets, never repeating a sheet, never countering a final_offer) is inherited.
"""

import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..play import ENDED, closing_move, latest, live_threads, moves_left
from .reciprocal import (
    ANCHOR,
    ANCHOR_FLOOR,
    FRAC0,
    FRAC_MAX,
    FRAC_STEP,
    KEEP,
    MIN_STEP,
    MOVING_MIN,
    ReciprocalAgent,
    _c_alt,
    _live,
    _mine,
    _sup,
    _tick,
    _valid,
    case_c_open,
    closing_accept,
)

QUOTE_ASK = "Could you please send us your quote?"


def _priced(case, events, std):
    """[(C, sheet)] of the thread's standing sheets, must-haves ignored."""
    return _valid(case, events, std, math.inf, musts=False)


class FinalAgent(ReciprocalAgent):
    def __init__(self, match=None, anchor=ANCHOR, max_asks=2):
        self.match, self.anchor, self.max_asks = match, anchor, max_asks

    def _ask(self, case, sid):
        return {"supplier_id": sid, "message": {"subject": case.get("title", "Our enquiry"), "body": QUOTE_ASK}}

    def _unheard(self, threads):
        """A thread that never answered and has had fewer than max_asks of our messages, or None."""
        return next((s for s, ev in threads.items() if not _sup(ev) and len(_mine(ev)) < self.max_asks), None)

    def _close(self, case, quoted):
        """Accept the best acceptable sheet; else rescue a priced sheet that only breaks a must-have by
        sending it with the must-haves fixed; else walk away (only when nothing else can be done)."""
        if not live_threads(quoted):
            return {"supplier_id": next(iter(quoted), None), "message": {"action": {"type": "walk_away"}}}
        move = closing_move(case, quoted)
        if move["message"].get("action", {}).get("type") != "walk_away":
            return move
        c_alt, c_open, best = _c_alt(case), case_c_open(case, quoted), None
        for sid, ev in quoted.items():
            if latest(ev).get("status") in ENDED or moves_left(case, ev) < 1:
                continue
            std = standard_terms(ev)
            base = {k: std[k] for k in case["negotiable"] if k in std}
            sent = [x["terms"] for m in _mine(ev) for x in m.get("term_sheets") or []]
            for _, sh in _priced(case, ev, std):
                fixed = complete_offer(case, satisfy_must_haves(case, {**base, **sh["terms"]}, std))
                if not must_haves_ok(case, fixed, std) or fixed in sent:
                    continue
                if (c := total_cost(case, fixed, std)) < c_alt and c <= c_open:
                    best = min(best or (c, sid, fixed), (c, sid, fixed), key=lambda x: x[0])
        if best is None:
            return move
        _, sid, fixed = best
        body = "We can accept your price with the terms below; please confirm."
        message = {"subject": case.get("title", "Our proposal"), "body": body, "term_sheets": [{"terms": fixed}]}
        return {"supplier_id": sid, "message": message}

    def decide(self, case, threads):
        quoted = {s: ev for s, ev in threads.items() if _sup(ev)}
        if not _live(threads):  # nothing to answer: ask a thread that never wrote, else give up
            if (sid := self._unheard(threads)) is not None:
                return self._ask(case, sid)
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        if accept := closing_accept(case, quoted):
            return accept
        live = [s for s in _live(threads) if moves_left(case, threads[s]) >= 1]
        open_ = [s for s in live if latest(threads[s]).get("status") not in ("final_offer", "agreed")]

        def silent(s):  # no priced sheet and already asked enough: skip it, never walk away from it
            ev = threads[s]
            return not _priced(case, ev, standard_terms(ev)) and len(_mine(ev)) >= self.max_asks

        open_ = [s for s in open_ if not silent(s)]
        if not open_:
            if (sid := self._unheard(threads)) is not None:
                return self._ask(case, sid)
            return self._close(case, quoted)

        def key(s):  # keep every thread moving: fewest messages first, then the cheapest
            ev = threads[s]
            c = min((c for c, _ in _priced(case, ev, standard_terms(ev))), default=math.inf)
            return len(_mine(ev)), c

        sid = min(open_, key=key)
        events = threads[sid]
        if moves_left(case, events) <= 1:  # our last message must never be a counter that can time out
            return self._close(case, quoted)
        std = standard_terms(events)
        # a must-have breach is fixed in our sheet
        valid = _valid(case, events, std, math.inf) or _priced(case, events, std)
        if not valid:  # no priced sheet to answer: ask for one
            return self._ask(case, sid)
        _, best = min(valid, key=lambda v: v[0])
        sheets = self._sheets(case, events, std, best["terms"])
        if not sheets:  # nothing new left to offer: close on the best sheet, or give up
            return self._close(case, quoted)
        return {
            "supplier_id": sid,
            "message": {
                "subject": case.get("title", "Our proposal"),
                "body": "Thank you for your offer. We have moved on our side; please see our updated terms.",
                "term_sheets": [{"terms": t} for t in sheets],
            },
        }

    def _price(self, case, events, p):  # called by the inherited _sheets
        sheets = [m["term_sheets"][0]["terms"].get("unit_price") for m in _mine(events) if m.get("term_sheets")]
        mine = [x for x in sheets if x]
        if not mine:
            cur = case["buyer"].get("current_unit_price")
            if cur and case.get("type") == "price_increase":
                return max(ANCHOR_FLOOR * p, min(p, cur))  # labelled price increase: anchor at today's price
            return max(ANCHOR_FLOOR * p, min(self.anchor * p, cur or p))
        frac = min(FRAC_MAX, FRAC0 + FRAC_STEP * len(mine))
        step = max(frac * (p - mine[-1]), MIN_STEP * p, _tick(p))
        move = self._their_move(events)
        if self.match is not None and move > 0:
            step = max(MOVING_MIN * p, _tick(p), min(step, self.match * move))
        top = p if moves_left(case, events) <= 2 else p * (1 - KEEP)
        return max(mine[-1], min(top, mine[-1] + step))
