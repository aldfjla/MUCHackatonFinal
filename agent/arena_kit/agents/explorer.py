"""The Interest Explorer: the principled / interest-based school (interests over positions, packages of
equivalent offers, objective data). Each e-mail carries 2-3 term sheets that cost us about the same
but trade price against payment days / contract length; the supplier's next sheet shows which it values.

Learning (light): per (case, supplier) we remember the sheet we last sent; if the supplier's next sheet
moved payment days / contract length up we count a "terms" interest, if its price fell a "price" one.
The favoured kind leads the package list (terms-heavy first, or the price-led package first).

Knobs: anchor (first price cut vs their quote), step (share of the gap to their price we close per
concession), close_gap (accept when this near our package cost), patience (concede unasked when this
few moves are left).
"""

import math

from ..cost import complete_offer, must_haves_ok, snap, total_cost
from ..docs import standard_terms
from ..play import closing_move, latest, live_threads, moves_left
from .rational import _first_terms, _message

FIELDS = ("payment_days", "contract_months")


class ExplorerAgent:
    def __init__(self, anchor=0.10, step=0.25, close_gap=0.01, patience=2):
        self.anchor, self.step, self.close_gap, self.patience = anchor, step, close_gap, patience
        self.state = {}  # (case_id, supplier) -> {"base", "terms", "cost", "pref": {"price", "terms"}}

    def decide(self, case, threads):
        try:
            return self._decide(case, threads)
        except Exception:  # never crash a case: close safely (must-haves + alternative), else walk away
            try:
                return closing_move(case, threads)
            except Exception:
                live = live_threads(threads) or list(threads)
                return {"supplier_id": live[0] if live else None, "message": {"action": {"type": "walk_away"}}}

    def _packages(self, case, terms, price, cost, pref, ok):
        """2-3 term sheets at about equal cost: the price-led one at `price`, others trade price for longer terms."""
        opts, fields = case.get("term_options", {}), [f for f in FIELDS if f in case["negotiable"] and f in terms]
        longer = {f: max(opts[f]) if opts.get(f) else terms[f] + (30 if f == "payment_days" else 12) for f in fields}
        mixes = [{}, longer]  # {} = the supplier's current terms
        if len(fields) > 1 and "payment_days" in longer:
            mixes.append({"payment_days": snap(case, "payment_days", (terms["payment_days"] + longer["payment_days"]) / 2)})
        sheets = []
        target = cost(complete_offer(case, {**terms, "unit_price": round(price, 2)}))  # package A as actually sent
        for mix in mixes:
            at = lambda p: complete_offer(case, {**terms, **mix, "unit_price": round(p, 2)})  # noqa: E731
            slope = cost(at(price + 1)) - cost(at(price))
            p = price + (target - cost(at(price))) / slope if slope > 0 and mix else price  # equal total cost
            sheets.append(at(min(max(p, 0.5 * price), terms["unit_price"])))
        sheets = [s for i, s in enumerate(sheets) if s not in sheets[:i]]
        sheets = [s for s in sheets if cost(s) <= cost(terms) and ok(s)]  # never worse than their sheet, must-haves kept
        return sheets[::-1] if pref["terms"] > pref["price"] else sheets

    def _decide(self, case, threads):
        live = live_threads(threads)
        if not live:
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        std = {s: standard_terms(threads[s]) for s in live}
        cost = lambda s, t: total_cost(case, t, std[s])  # noqa: E731
        def best(s):  # the supplier's cheapest standing sheet
            sheets = latest(threads[s]).get("term_sheets") or []
            return min(((x["term_sheet_id"], x["terms"]) for x in sheets), key=lambda x: cost(s, x[1]), default=(None, {}))

        quoting = [s for s in live if best(s)[1].get("unit_price") is not None]
        walk = {"supplier_id": live[0], "message": {"action": {"type": "walk_away"}}}
        if not quoting:
            return walk
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        has_alt = bool(alt.get("unit_price"))
        opening = [cost(s, _first_terms(threads[s])) for s in quoting if _first_terms(threads[s]).get("unit_price")]
        reservation = total_cost(case, alt) if has_alt else min(opening, default=math.inf)
        sid = min(quoting, key=lambda s: cost(s, best(s)[1]))
        events = threads[sid]
        sheet_id, terms = best(sid)
        compliant = must_haves_ok(case, terms, std[sid])
        beats = compliant and cost(sid, terms) < reservation
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        status, left = latest(events).get("status"), moves_left(case, events)
        final_ok = beats or (compliant and not has_alt)
        c = lambda t: cost(sid, t)  # noqa: E731
        theirs = terms["unit_price"]
        st = self.state.setdefault((case["case_id"], sid), {"pref": {"price": 0, "terms": 0}})
        fresh = "base" in st and st["seen"] != len(events)  # act once per new supplier message
        moved = fresh and c(terms) < st["cost"]  # reciprocity: they improved since our last message
        if fresh:  # learn what they moved on
            st["pref"]["terms"] += any(terms.get(f, 0) > st["terms"].get(f, 0) for f in FIELDS)
            st["pref"]["price"] += theirs < st["terms"]["unit_price"]
        base = theirs * (1 - self.anchor) if "base" not in st else st["base"]
        reason = "Which of these terms matter most to you: price, payment timing or contract length?"
        if "base" in st:
            if fresh and (moved or left <= self.patience + 1):
                base += (theirs - base) * self.step
                reason = ("Thank you for the improvement; we have moved our price closer to yours." if moved
                          else "We are adjusting our offer to help close this.")
            else:
                reason = "We keep these packages, which are equivalent for us; please pick the one that suits you best."
        base = round(min(base, theirs), 2)
        packages = self._packages(case, terms, base, c, st["pref"], lambda t: must_haves_ok(case, t, std[sid]))
        if status in {"agreed", "final_offer"} or left <= 0:
            if status == "final_offer" and left > 0 and final_ok:
                # their price, our terms (same rule as RationalAgent): a price-only sheet leaves our other terms at standard
                best = min(packages, key=c)
                at_theirs = {**best, "unit_price": theirs}
                if c(at_theirs) < c(terms) and must_haves_ok(case, at_theirs, std[sid]):
                    return _message(case, sid, at_theirs, "We accept your price; please confirm the terms below.")
            return accept if final_ok else walk | {"supplier_id": sid}
        if beats and c(terms) <= min(map(c, packages)) * (1 + self.close_gap):
            return accept
        st.update(base=base, terms=terms, cost=c(terms), seen=len(events))
        msg = _message(case, sid, packages[0], reason)
        msg["message"]["term_sheets"] = [{"terms": p} for p in packages[:3]]
        return msg
