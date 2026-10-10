"""SmartAgent with a confidence index: holds firm while the supplier has room, concedes faster and
accepts earlier as the index falls. Same safety rules as SmartAgent."""

import logging
import math

from ..confidence import confidence_report
from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..play import closing_move as _closing_move
from ..play import latest, live_threads, moves_left, standing
from .smart import SmartAgent, _quote

log = logging.getLogger("arena")


TONE_HIGH = (
    "Thank you for your offer. We see room on both sides and would like to continue — "
    "could you consider these terms?"
)
TONE_MID = "Thank you, we appreciate the movement. We are getting close; could you consider one of these packages?"
TONE_LOW = (
    "Thank you for working with us on this. We are close to agreement — "
    "if one of these packages works for you we are ready to close."
)

ASK_BETTER = (
    "Thank you. Could you send us a better package, or a breakdown of your costs, "
    "so we can find terms that work for both sides?"
)
QUOTE_ASK = "Could you please send us your quote?"


class ConfidentAgent(SmartAgent):
    def __init__(self, first_cut=0.10, min_step=0.15, max_step=0.60, accept_below=0.25, late=2):
        super().__init__(first_cut=first_cut, late=late)
        self.min_step, self.max_step, self.accept_below = min_step, max_step, accept_below

    def step_for(self, conf):
        """High confidence: small step (push); low confidence: big step (secure the deal)."""
        return self.min_step + (1 - conf) * (self.max_step - self.min_step)

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
        open_ = [
            s for s in live if moves_left(case, threads[s]) > 0 and latest(threads[s]).get("status") != "final_offer"
        ]
        quoting = [s for s in live if standing(threads[s])[1].get("unit_price") is not None]
        if not quoting:
            if not open_:
                return closing_move(case, threads)
            return {"supplier_id": open_[0], "message": {"subject": case["title"], "body": QUOTE_ASK}}
        best = min(quoting, key=lambda s: cost(s, standing(threads[s])[1]))
        if not open_ or (best not in open_ and ok(best, standing(threads[best])[1])):
            return closing_move(case, threads)
        sid = min((s for s in open_ if s in quoting), key=lambda s: cost(s, standing(threads[s])[1]), default=None)
        if sid is None:
            return {"supplier_id": open_[0], "message": {"subject": case["title"], "body": QUOTE_ASK}}
        events = threads[sid]
        sheet_id, terms = standing(events)
        c_open = min([cost(s, q) for s in quoting if (q := _quote(threads[s])).get("unit_price")] or [math.inf])
        c_now, left = cost(sid, terms), moves_left(case, events)
        done = latest(events).get("status") == "agreed"
        report = confidence_report(case, events, std[sid])
        conf = report["score"]
        log.info("%s confidence %.2f %s", sid, conf, report["notes"])
        step = self.step_for(conf)
        early = conf <= self.accept_below and c_now <= c_open and ok(sid, terms)
        log.info("%s step %.2f early accept %s", sid, step, early)
        if (early or (c_now <= c_open and (done or left <= self.late)) or (done and left <= 1)) and ok(sid, terms):
            return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        mine = [
            m["term_sheets"][0]["terms"].get("unit_price")
            for m in events
            if m.get("from") == "buyer" and m.get("term_sheets")
        ]
        mine = [x for x in mine if x is not None]
        theirs = terms["unit_price"]
        price = theirs * (1 - self.first_cut) if not mine else mine[-1] + step * (theirs - mine[-1])
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
            fits = must_haves_ok(case, offer, std[sid]) and cost(sid, offer) <= min(c_open, c_now)
            if fits and {"terms": offer} not in sheets:
                sheets.append({"terms": offer})
        if not sheets:  # nothing valid to offer: take a safe sheet if there is one, else just move the price
            close = closing_move(case, threads)
            if close["message"].get("action", {}).get("type") == "accept":
                return close
            offer = complete_offer(case, {**terms, "unit_price": price})
            if must_haves_ok(case, offer, std[sid]) and cost(sid, offer) <= c_open:
                sheets = [{"terms": offer}]
            else:  # never send an unsafe sheet: ask in words
                return {"supplier_id": sid, "message": {"subject": case["title"], "body": ASK_BETTER}}
        body = TONE_HIGH if conf >= 0.6 else TONE_MID if conf >= 0.3 else TONE_LOW
        return {"supplier_id": sid, "message": {"subject": case["title"], "body": body, "term_sheets": sheets}}
