"""FiftyAgent ("50"): open at ANCHOR x their first price, then always move half the gap to their latest price.
Gap = their standing unit price - our last offered unit price. Gap < 5% of their first price: accept (closing_move
keeps must-haves and never accepts worse than the opening). Their price did not fall: also lengthen contract_months.
State is derived from the thread events each time."""

import math

from ..cost import complete_offer
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..play import closing_move, latest, moves_left
from .reciprocal import ANCHOR, _live, _mine, _sheets, _sup

STOP = 0.05  # gap below this x their first price: accept


def _prices(events):
    """Lowest unit price of each priced supplier message, oldest first."""
    return [min(s["terms"]["unit_price"] for s in m["term_sheets"] if s["terms"].get("unit_price") is not None)
            for m in _sup(events) if any(s["terms"].get("unit_price") is not None for s in m.get("term_sheets") or [])]


class FiftyAgent:
    def decide(self, case, threads):
        live = [s for s in _live(threads) if _prices(threads[s])]
        if not live:
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        open_ = [s for s in live if moves_left(case, threads[s]) >= 1 and latest(threads[s]).get("status") not in ("final_offer", "agreed")]
        if not open_:
            return closing_move(case, threads)
        sid = min(open_, key=lambda s: len(_mine(threads[s])))  # keep every thread moving
        events = threads[sid]
        ps, std = _prices(events), standard_terms(events)
        theirs = min((s["terms"] for s in _sheets(events) if s["terms"].get("unit_price") is not None), key=lambda t: t["unit_price"])
        mine = [m["term_sheets"][0]["terms"]["unit_price"] for m in _mine(events)
                if m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")]
        if mine:
            gap = theirs["unit_price"] - mine[-1]
            if gap < STOP * ps[0] or moves_left(case, events) <= 1:
                if (move := closing_move(case, threads))["message"]["action"]["type"] == "accept":
                    return move
            price = mine[-1] + gap / 2
        else:
            price = ANCHOR * ps[0]
        terms = {**{f: std[f] for f in case["negotiable"] if f in std}, **theirs, "unit_price": round(price, 2)}
        if len(ps) >= 2 and ps[-1] >= ps[-2]:  # stalled: offer a longer contract
            cap = 12 * case["buyer"].get("horizon_years", math.inf)
            longer = [o for o in (case.get("term_options") or {}).get("contract_months", []) if o and terms.get("contract_months", 0) < o <= cap]
            if "contract_months" in case["negotiable"] and longer:
                terms["contract_months"] = min(longer)
        return {
            "supplier_id": sid,
            "message": {
                "subject": case.get("title", "Our proposal"),
                "body": "Thank you for your offer. We have moved on our side; please see our updated terms.",
                "term_sheets": [{"terms": complete_offer(case, satisfy_must_haves(case, terms, std))}],
            },
        }
