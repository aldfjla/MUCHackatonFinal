"""Bold Ram
School of thought: behavioural (anchoring and framing)
Backlog version: v4 - niko
Copied from: agent/arena_kit/agents/anchor.py
Date: 2026-10-10
ORIGINAL SNAPSHOT: do not edit; copy to Players/ for experiments.
Run: see Players/Originals/README.md
"""

"""Anchor-and-Frame: the behavioural school (anchoring, framed concessions, shrinking steps, neutral tone).
Opens with an ambitious, non-round, reasoned anchor; every later concession is presented as costly, is
smaller than the one before and is paired with an ask (longer payment days). Polite, no threats, no bluff.

Knobs: opening_depth (first cut below the quote), first_step (share of the gap conceded first), shrink
(each step as a share of the previous one), min_rounds (our own offers before accepting a non-final sheet).
"""

import math

from arena_kit.cost import complete_offer, must_haves_ok, total_cost
from arena_kit.docs import standard_terms
from arena_kit.play import closing_move, latest, live_threads, moves_left, standing
from patient_hawk import _first_terms, _message, _prices


def _walk():
    return {"action": {"type": "walk_away"}}


def _non_round(price, ceiling):
    """A price in cents that does not end in .00 or .50 (nudged down a cent or two), never above ceiling."""
    price = max(round(min(price, ceiling), 2), 0.01)
    while round(price * 100) % 50 == 0:
        price = round(price - 0.01, 2)
    return price


class AnchorAgent:
    def __init__(self, opening_depth=0.12, first_step=0.3, shrink=0.6, min_rounds=2):
        self.opening_depth, self.first_step, self.shrink, self.min_rounds = opening_depth, first_step, shrink, min_rounds
        self.case_id, self.state = None, {}  # state: supplier -> {"step": our last step, "price": our last price}

    def decide(self, case, threads):
        try:
            return self._decide(case, threads)
        except Exception:  # never crash a case: close safely (must-haves + alternative), else walk away
            try:
                return closing_move(case, threads)
            except Exception:
                live = live_threads(threads) or list(threads)
                return {"supplier_id": live[0] if live else None, "message": _walk()}

    def _decide(self, case, threads):
        if case["case_id"] != self.case_id:
            self.case_id, self.state = case["case_id"], {}
        live = live_threads(threads)
        if not live:
            return {"supplier_id": next(iter(threads), None), "message": _walk()}
        std = {s: standard_terms(threads[s]) for s in live}
        cost = lambda s, t: total_cost(case, t, std[s])  # noqa: E731
        quoting = [s for s in live if standing(threads[s])[1].get("unit_price") is not None]
        if not quoting:
            return {"supplier_id": live[0], "message": _walk()}
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        has_alt = bool(alt.get("unit_price"))
        opening = [cost(s, _first_terms(threads[s])) for s in quoting if _first_terms(threads[s]).get("unit_price")]
        reservation = total_cost(case, alt) if has_alt else min(opening, default=math.inf)
        sid = min(quoting, key=lambda s: cost(s, standing(threads[s])[1]))
        events = threads[sid]
        sheet_id, terms = standing(events)
        compliant = must_haves_ok(case, terms, std[sid])
        beats = compliant and cost(sid, terms) < reservation
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        status, left = latest(events).get("status"), moves_left(case, events)
        final_ok = beats or (compliant and not has_alt)  # no alternative: walking away scores 0
        sent = sum(m.get("from") == "buyer" for m in events)
        st = self.state.get(sid)
        if not sent or st is None:  # first move here, or a fresh instance: start clean, rebuild from our sent offers
            st = self.state[sid] = {"step": None, "price": None}
            mine = _prices(events, True)
            if mine:
                st["price"] = mine[-1]
                st["step"] = mine[-1] - mine[-2] if len(mine) > 1 else None
        theirs = terms["unit_price"]

        ask = {}
        if "payment_days" in case["negotiable"] and "payment_days" in terms:
            options = case.get("term_options", {}).get("payment_days")
            ask["payment_days"] = max(options) if options else terms["payment_days"] + 30
        if st["price"] is None:
            price, step = _non_round(theirs * (1 - self.opening_depth), theirs), None
            body = "Our cost review of this part points to this level. This is the level we can support on our side for this part."
        else:
            last = st["price"]
            step = max((self.first_step * (theirs - last)) if st["step"] is None else st["step"] * self.shrink, 0)
            price = _non_round(max(last + step, last + 0.01), theirs)
            if price <= last:  # nudge landed back on our last price: still move a cent
                price = _non_round(min(last + 0.02, theirs), theirs)
            price = min(max(price, last), theirs)
            body = ("This is a significant move for us, made because we want to reach an agreement on a "
                    "fair price; in return we ask for the longer payment terms below.")
        offer = complete_offer(case, {**terms, **ask, "unit_price": price})

        if status in {"agreed", "final_offer"} or left <= 0:
            if status == "final_offer" and left > 0 and final_ok:
                # their price, our terms: a price-only final sheet leaves other terms at their (costlier) standard
                at_their_price = complete_offer(case, {**terms, **ask, "unit_price": theirs})
                if cost(sid, at_their_price) < cost(sid, terms) and must_haves_ok(case, at_their_price, std[sid]):
                    return _message(case, sid, at_their_price, "We accept your price; please confirm the terms below.")
            return accept if final_ok else {"supplier_id": sid, "message": _walk()}
        # last move: a walk by the supplier would lose the deal, so take a good sheet
        if beats and (left <= 1 or (sent >= self.min_rounds and cost(sid, terms) <= cost(sid, offer))):
            return accept
        st.update(step=step if step is not None else st["step"], price=price)
        return _message(case, sid, offer, body)


if __name__ == "__main__":
    from _runner import main

    main(AnchorAgent)
