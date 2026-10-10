"""The Rational Bargainer: the game-theory school (reservation value, outside option, time-dependent
concessions, supplier-floor estimate). Opens firm, concedes along a Boulware curve, caps itself at the
supplier's estimated floor and trades payment days for price.

Knobs: anchor (first cut below the quote), target (final discount vs the opening quote), exponent
(>1 holds firm early), margin (above the estimated floor), close_gap (accept when this near our own offer).
"""

import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..play import closing_move, latest, live_threads, moves_left, standing


def _prices(events, sender):
    """Unit prices of the first term sheet in each message from the buyer (sender=True) or the supplier."""
    return [
        m["term_sheets"][0]["terms"]["unit_price"]
        for m in events
        if (m.get("from") == "buyer") == sender and m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")
    ]


def estimate_floor(prices):
    """Extrapolate the supplier's geometric concession decay to its limit; None with too little data."""
    steps = [a - b for a, b in zip(prices, prices[1:])]
    if len(steps) < 2 or steps[-1] <= 0 or steps[-2] <= 0:
        return None
    ratio = min(steps[-1] / steps[-2], 0.95)
    return prices[-1] - steps[-1] * ratio / (1 - ratio)


class RationalAgent:
    def __init__(self, anchor=0.12, target=0.03, exponent=2.0, margin=0.02, close_gap=0.01):
        self.anchor, self.target, self.exponent, self.margin, self.close_gap = anchor, target, exponent, margin, close_gap

    def decide(self, case, threads):
        try:
            return self._decide(case, threads)
        except Exception:  # never crash a case: close safely (must-haves + alternative), else walk away
            try:
                return closing_move(case, threads)
            except Exception:
                live = live_threads(threads) or list(threads)
                return {"supplier_id": live[0] if live else None, "message": {"action": {"type": "walk_away"}}}

    def _decide(self, case, threads):
        live = live_threads(threads)
        if not live:
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        std = {s: standard_terms(threads[s]) for s in live}
        cost = lambda s, t: total_cost(case, t, std[s])  # noqa: E731
        quoting = [s for s in live if standing(threads[s])[1].get("unit_price") is not None]
        walk = {"supplier_id": live[0], "message": {"action": {"type": "walk_away"}}}
        if not quoting:
            return walk
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        has_alt = bool(alt.get("unit_price"))
        # like with like: the alternative, else the cheapest opening sheet, both with their whole terms
        opening = [cost(s, _first_terms(threads[s])) for s in quoting if _first_terms(threads[s]).get("unit_price")]
        reservation = total_cost(case, alt) if has_alt else min(opening, default=math.inf)
        sid = min(quoting, key=lambda s: cost(s, standing(threads[s])[1]))
        events = threads[sid]
        sheet_id, terms = standing(events)
        compliant = must_haves_ok(case, terms, std[sid])
        beats = compliant and cost(sid, terms) < reservation
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        status, left = latest(events).get("status"), moves_left(case, events)
        # no alternative: walking away scores 0, so any compliant sheet is worth taking at the end
        final_ok = beats or (compliant and not has_alt)
        ending = status in {"agreed", "final_offer"} or left <= 0

        theirs_all, mine = _prices(events, False), _prices(events, True)
        theirs = terms["unit_price"]
        first = theirs_all[0] if theirs_all else theirs
        start = first * (1 - self.anchor)
        progress = len(mine) / max(case.get("round_limit", 10) - 1, 1)  # 0 at the first move, 1 at the last
        price = start + (first * (1 - self.target) - start) * min(progress, 1) ** self.exponent
        if (floor := estimate_floor(theirs_all)) is not None:
            price = min(price, floor * (1 + self.margin))
        price = round(min(max(price, mine[-1] if mine else 0), theirs), 2)  # never retreat, never above their price
        ask = {}
        options = case.get("term_options", {}).get("payment_days")
        if "payment_days" in case["negotiable"] and "payment_days" in terms:
            ask["payment_days"] = max(options) if options else terms["payment_days"] + 30
        offer = complete_offer(case, {**terms, **ask, "unit_price": price})
        if ending:
            if status == "final_offer" and left > 0 and final_ok:
                # their price, our terms: a price-only final sheet leaves the other terms at their standard
                # values, which can cost far more than the price step we would still win
                at_their_price = complete_offer(case, {**terms, **ask, "unit_price": theirs})
                if cost(sid, at_their_price) < cost(sid, terms) and must_haves_ok(case, at_their_price, std[sid]):
                    return _message(case, sid, at_their_price, "We accept your price; please confirm the terms below.")
            return accept if final_ok else walk | {"supplier_id": sid}
        if beats and cost(sid, terms) <= cost(sid, offer) * (1 + self.close_gap):
            return accept
        return _message(case, sid, offer, "Thank you for your offer. Based on our analysis we can offer the terms below.")


def _first_terms(events):
    sheets = next((m["term_sheets"] for m in events if m.get("from") != "buyer" and m.get("term_sheets")), None)
    return sheets[0]["terms"] if sheets else {}


def _message(case, sid, offer, body):
    return {"supplier_id": sid, "message": {"subject": case["title"], "body": body, "term_sheets": [{"terms": offer}]}}
