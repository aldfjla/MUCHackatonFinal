"""A non-LLM buyer: concedes slowly, offers up to 3 trade-offs per e-mail, never pays more than the
best opening quote. Every candidate is priced with `total_cost`."""

import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..play import closing_move as _closing_move
from ..play import latest, live_threads, moves_left, standing


def _quote(events):
    """The supplier's first term sheet's terms, or {}."""
    return next((m["term_sheets"][0]["terms"] for m in events if m.get("from") != "buyer" and m.get("term_sheets")), {})


class SmartAgent:
    def __init__(self, first_cut=0.10, step=0.30, late=2):
        self.first_cut, self.step, self.late = first_cut, step, late
        self.std = {}  # per supplier, earliest value wins: the latest quote PDF alone may be gone later

    def decide(self, case, threads):
        live = live_threads(threads)
        for s in live:
            for k, v in standard_terms(threads[s]).items():
                self.std.setdefault((case["case_id"], s), {}).setdefault(k, v)
        std = {s: self.std.get((case["case_id"], s), {}) for s in live}
        closing_move = lambda c, t: _closing_move(c, t, std)  # noqa: E731
        cost = lambda s, t: total_cost(case, t, std[s])  # noqa: E731
        alt = case["buyer"].get("alternative") or {}
        c_alt = total_cost(case, alt["terms"]) if alt.get("terms", {}).get("unit_price") else math.inf
        ok = lambda s, t: must_haves_ok(case, t, std[s]) and cost(s, t) < c_alt  # noqa: E731
        # Threads we can still negotiate in: moves left and not a final offer. Closing a case the
        # way `closing_move` does takes the best safe sheet of ANY thread, or walks away.
        open_ = [s for s in live if moves_left(case, threads[s]) > 0 and latest(threads[s]).get("status") != "final_offer"]
        quoting = [s for s in live if standing(threads[s])[1].get("unit_price") is not None]
        if not quoting:
            if not open_:
                return closing_move(case, threads)
            return {"supplier_id": open_[0], "message": {"subject": case["title"], "body": "Could you please send us your quote?"}}
        best = min(quoting, key=lambda s: cost(s, standing(threads[s])[1]))
        if not open_ or (best not in open_ and ok(best, standing(threads[best])[1])):
            return closing_move(case, threads)
        sid = min((s for s in open_ if s in quoting), key=lambda s: cost(s, standing(threads[s])[1]), default=None)
        if sid is None:
            return {"supplier_id": open_[0], "message": {"subject": case["title"], "body": "Could you please send us your quote?"}}
        events = threads[sid]
        sheet_id, terms = standing(events)
        c_open = min([cost(s, q) for s in quoting if (q := _quote(threads[s])).get("unit_price")] or [math.inf])
        c_now, left = cost(sid, terms), moves_left(case, events)
        done = latest(events).get("status") == "agreed"
        if ((c_now <= c_open and (done or left <= self.late)) or (done and left <= 1)) and ok(sid, terms):
            return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        mine = [m["term_sheets"][0]["terms"].get("unit_price") for m in events if m.get("from") == "buyer" and m.get("term_sheets")]
        mine = [x for x in mine if x is not None]
        theirs = terms["unit_price"]
        price = theirs * (1 - self.first_cut) if not mine else mine[-1] + self.step * (theirs - mine[-1])
        price = min(price, theirs)
        half = theirs - (theirs - price) / 2
        options = case.get("term_options", {})
        longest = max(options.get("contract_months") or [0])
        base = {k: v for k, v in terms.items() if k != "incoterm"}  # complete_offer asks for the cheapest freight
        pay = max(case["buyer"]["reference_payment_days"], (terms.get("payment_days") or 0) + 30)
        asks = [{"unit_price": price}, {"unit_price": half, "payment_days": pay}]
        if "contract_months" in case["negotiable"] and longest:
            asks.append({"unit_price": (price + half) / 2, "contract_months": longest})
        sheets = []
        for ask in asks:
            offer = complete_offer(case, {**base, **ask})
            if must_haves_ok(case, offer, std[sid]) and cost(sid, offer) <= min(c_open, c_now) and {"terms": offer} not in sheets:
                sheets.append({"terms": offer})
        if not sheets:  # nothing valid to offer: take a safe sheet if there is one, else just move the price
            close = closing_move(case, threads)
            if close["message"].get("action", {}).get("type") == "accept":
                return close
            sheets = [{"terms": complete_offer(case, {**terms, "unit_price": price})}]
        return {
            "supplier_id": sid,
            "message": {"subject": case["title"], "body": "Thank you for your offer. Could you consider these terms?", "term_sheets": sheets},
        }
