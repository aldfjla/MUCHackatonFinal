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
- Closing: FinalAgent's closing_accept (cheapest valid sheet over all live threads); after a final offer, one
  try at their price with cheaper non-price terms (tied terms and their effective date kept) if it saves
  >= 0.5 % and was not tried. Never walks away while a supplier is alive (FinalAgent).
"""

import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..listener import focus, supplier_model
from ..play import latest, live_threads, moves_left
from .final import FinalAgent
from .listener import BODY_THEIR_PRICE, ListenerAgent, _tried_after_final
from .reciprocal import _c_alt, _mine, _sup, _valid, case_c_open

TRY_SAVING = 0.005  # the one try after a final offer must save at least this share of their sheet's cost


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
        """One non-price try per thread at the supplier's final price, if it is clearly cheaper for us."""
        c_alt, c_open = _c_alt(case), case_c_open(case, threads)
        for sid in live_threads(threads):
            ev = threads[sid]
            if latest(ev).get("status") != "final_offer" or moves_left(case, ev) < 2 or _tried_after_final(ev):
                continue  # keep the last message for the accept
            std, model = standard_terms(ev), self._models.get(sid)
            valid = _valid(case, ev, std, c_alt)
            if not valid or model is None:
                continue
            c_best, best = min(valid, key=lambda v: v[0])
            terms = best["terms"]

            def cost(t, std=std):
                return total_cost(case, t, std)

            hold = self.ears._held(model, terms)
            at = self.ears._best_terms(case, model, dict(terms), cost, strict=True, hold=hold)
            at = complete_offer(case, satisfy_must_haves(case, at, std))
            sent = [x["terms"] for m in _mine(ev) for x in m.get("term_sheets") or []]
            if (
                at not in sent
                and must_haves_ok(case, at, std)
                and self.ears._pay_filter(model, [at], cost, ref=terms)
                and cost(at) < min(c_alt, c_open)
                and cost(at) < c_best * (1 - TRY_SAVING)
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
