"""CombinedAgent (v6-petra): Alex's FinalAgent moves, the Listener's ears. Rules only, no language model.
Compose as EvidenceAgent(GuardedAgent(CombinedAgent()), data, questions=False), like `final`.

- While the supplier still moves and the supplier model (arena_kit/listener.py) sees no hard price limit:
  FinalAgent's visible reciprocal step (anchor 0.80 x their price, 0.75 floor, 3 % gap kept until the last
  two messages) and its main + variant sheets; the variant becomes the Listener's currency package when the
  supplier's currency is known.
- On a real limit (price frozen: "no further concessions", same price twice, a final offer; capacity full;
  payment fixed): our price holds and the Listener's packages change the non-price terms instead.
- Listener rules on every sheet: frozen fields stay at the supplier's value, no payment faster than the
  supplier offered (unless it asked and it saves >= 0.3 %), never a sheet sent before, never worse than the
  opening or the alternative.
- Closing: FinalAgent's closing_accept (cheapest valid sheet over all live threads). An acceptable final offer
  is accepted at once (suppliers walk after a push). Only an unacceptable one (misses a must-have or loses to
  the alternative, P07: 5.64 at 24 months) gets a try at their price with cheaper non-price terms (tied terms
  and their effective date kept). Refused: accept the best acceptable sheet, else the next untried package. Never walks away while a supplier is alive (FinalAgent).
"""

import json
import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..listener import focus, supplier_model
from ..play import latest, live_threads, moves_left
from .final import FinalAgent
from .listener import BODY_THEIR_PRICE, ListenerAgent
from .reciprocal import _c_alt, _mine, _sup, _valid, case_c_open, closing_accept

def _limit(model):
    """The supplier says its price will not move ("no further concessions", same price twice, a final offer):
    hold our price, change the package. A fixed payment term or full capacity is a limit on that field only:
    the price keeps its visible step and the field stays at the supplier's value (`_clean`)."""
    return bool(model["price_frozen"])


class CombinedAgent(FinalAgent):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.ears = ListenerAgent()  # its packages and filters; its own decide() is never called
        self.focus = None  # read by the evidence layer (the supplier we message)
        self._models, self._c_open = {}, math.inf

    def decide(self, case, threads):
        quoted = {s: ev for s, ev in threads.items() if _sup(ev)}
        self._models = {s: supplier_model(case, ev) for s, ev in quoted.items()}
        self._c_open = case_c_open(case, quoted) if quoted else math.inf
        try:
            if (move := self._after_final(case, threads)) is not None:
                return self._aim(case, move)
        except Exception:  # the extra try is optional: fall back to FinalAgent's rules
            pass
        return self._aim(case, super().decide(case, threads))

    def _aim(self, case, decision):
        sid = decision.get("supplier_id")
        model = self._models.get(sid)
        try:
            self.focus = {**focus(model, case), "supplier_id": sid} if model else {"supplier_id": sid}
        except Exception:  # the focus only steers the evidence layer's wording
            self.focus = {"supplier_id": sid}
        return decision

    def _after_final(self, case, threads):
        """A try per thread at the supplier's final price with cheaper non-price terms (P07: 5.64 at 24 months
        instead of 12). Built even when their own final sheet misses a must-have or loses to the alternative.
        After our first try, only when no acceptable sheet exists (else FinalAgent accepts): the next untried one."""
        c_alt, c_open = _c_alt(case), case_c_open(case, threads)
        quoted = {s: ev for s, ev in threads.items() if _sup(ev)}
        if closing_accept(case, quoted):
            return None  # an acceptable sheet is on the table: FinalAgent accepts it, no extra push (suppliers walk)
        for sid in live_threads(threads):
            ev = threads[sid]
            if latest(ev).get("status") != "final_offer" or moves_left(case, ev) < 2:
                continue  # keep the last message for the accept
            std, model = standard_terms(ev), self._models.get(sid)
            priced = _valid(case, ev, std, math.inf, musts=False)
            if not priced or model is None:
                continue
            c_best, best = min(priced, key=lambda v: v[0])
            terms = best["terms"]
            if must_haves_ok(case, terms, std) and c_best < c_alt and c_best < c_open:
                continue  # their final is acceptable as it stands: accept it, never push again

            def cost(t, std=std):
                return total_cost(case, t, std)

            # a field the supplier itself changed between its sheets is part of its price (P10: 54 -> 56 days)
            theirs = [s["terms"] for m in _sup(ev) for s in m.get("term_sheets") or []]
            moved = {f for f in terms if f != "unit_price" and len({json.dumps(t.get(f)) for t in theirs}) > 1}
            hold = self.ears._held(model, terms) | moved
            first = self.ears._best_terms(case, model, dict(terms), cost, strict=True, hold=hold)
            upper = min(c_alt, c_open)
            cands = [first] + self.ears._packages(case, model, dict(terms), terms["unit_price"], cost, upper)
            sent = [x["terms"] for m in _mine(ev) for x in m.get("term_sheets") or []]
            for at in cands:
                at = {**at, **{f: terms[f] for f in hold}, "unit_price": terms["unit_price"]}
                at = complete_offer(case, satisfy_must_haves(case, at, std))
                if (
                    at not in sent
                    and must_haves_ok(case, at, std)
                    and self.ears._pay_filter(model, [at], cost, ref=terms)
                    and cost(at) < upper
                ):
                    return {"supplier_id": sid, "message": {"subject": case.get("title", "Our proposal"),
                                                            "body": BODY_THEIR_PRICE, "term_sheets": [{"terms": at}]}}
        return None

    def _sheets(self, case, events, std, theirs):
        model = supplier_model(case, events)
        cost = lambda t: total_cost(case, t, std)  # noqa: E731
        upper = min(_c_alt(case), self._c_open)
        sent = [x["terms"] for m in _mine(events) for x in m.get("term_sheets") or []]
        mine = [x["terms"]["unit_price"] for m in _mine(events) for x in (m.get("term_sheets") or [])[:1]
                if x["terms"].get("unit_price") is not None]
        base = {**{f: std[f] for f in case["negotiable"] if f in std}, **theirs}
        best = {k: v for k, v in base.items() if v is not None}

        if _limit(model) and mine:  # hold our price, move the package
            out = [t for t in self.ears._packages(case, model, best, mine[-1], cost, upper)
                   if t["unit_price"] <= mine[-1]]  # its mid price point would be a concession: dropped
            if held := self._clean(case, model, out, sent, std, cost, upper):
                return held
            # nothing new at our price: fall through to the visible step rather than close early
        out = list(super()._sheets(case, events, std, theirs))  # Alex's visible step: main + variant
        if out and model["currency"] != "price":  # swap the variant for the currency package at our price
            pk = self.ears._packages(case, model, best, out[0]["unit_price"], cost, upper)
            if pk and pk[0] != out[0]:
                out = [out[0], pk[0]] + out[1:2]
        return self._clean(case, model, out, sent, std, cost, upper)

    def _clean(self, case, model, sheets, sent, std, cost, upper):
        """Listener rules on every sheet: frozen fields at their value, must-haves met, new, affordable, no fast pay."""
        keep = []
        for t in sheets:
            t = dict(t)
            for f in model["frozen"]:
                if f in model["preferred"] and f in t:
                    t[f] = model["preferred"][f]
            t = complete_offer(case, satisfy_must_haves(case, t, std))
            if t in keep or t in sent or not must_haves_ok(case, t, std) or cost(t) > upper:
                continue
            keep.append(t)
        return self.ears._pay_filter(model, keep, cost)[:3]
