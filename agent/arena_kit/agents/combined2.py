"""Combined2Agent (v8-petra): a router between two proven agent chains. Rules only, no language model.

- `better` (Niko, real v21 mean 0.70): EvidenceAgent(HealthScope(GuardedAgent(BetterAgent()))). Supplier-health
  estimate from the should-cost, accept guard over the band, late accept, overpay instead of walk, full-match steps.
- `combined` (Petra + Alex, real v7 mean 0.61): EvidenceAgent(GuardedAgent(CombinedCore()), questions=False).
  Alex's visible steps, the listener's supplier model, index clause only when it lowers C.

Route (from the real runs, same cases, both agents): a case with an index clause on the table and no supplier
health at stake (raw-material / leverage cases, real P08 .63 / P18 .52 against better's .45-.53 / .40-.51) goes
to `combined`; every other case goes to `better` (real P02 .67 vs .19, P11 .71 vs .15, P04 .86 vs .77, P05 .77
vs .72, P03 .92 vs .85, P10 .67 vs .64; P01 .84 vs .87 and P07 .68 vs .73 are the small losses).

CombinedCore adds two fixes for a supplier that prices our non-price asks (real P11: ppm 300 / chargeback 500 cost
us +3.50 a unit and were worth ~0.14): counter from the supplier's cheapest package so far, and drop a non-price ask
that saves less than MIN_ASK of C (the index clause keeps its own rule, cheapest_index).
"""

import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..guard import GuardedAgent, satisfy_must_haves
from .better_agent import BetterAgent, HealthScope
from .combined import CombinedAgent
from .evidence import EvidenceAgent
from .reciprocal import _c_alt, _mine, _sup
from .simplify_agent import _health_at_stake

MIN_ASK = 0.005  # a non-price ask must save at least this share of C


def route(case):
    """'combined' or 'better' for this case (see the module doc)."""
    try:
        index_on_table = "index_clause" in case.get("negotiable", ())
        return "combined" if index_on_table and not _health_at_stake(case) else "better"
    except Exception:  # missing fields (e.g. no buyer block): the default chain
        return "better"


class CombinedCore(CombinedAgent):
    def _sheets(self, case, events, std, theirs):
        cost = lambda t: total_cost(case, t, std)  # noqa: E731
        theirs = self._cheapest_theirs(case, events, std, theirs, cost)
        upper = min(_c_alt(case), self._c_open)  # the same bound `_clean` used
        sent = [x["terms"] for m in _mine(events) for x in m.get("term_sheets") or []]
        sheets = super()._sheets(case, events, std, theirs)
        return self._drop_small_asks(case, std, sheets, theirs, cost, upper, sent)

    @staticmethod
    def _cheapest_theirs(case, events, std, theirs, cost):
        """The supplier's cheapest must-have-compliant package so far (C), if it beats its latest one."""
        best, c_best = theirs, cost(theirs)
        for m in _sup(events):
            for s in m.get("term_sheets") or []:
                t = s.get("terms") or {}
                if t.get("unit_price") is None or not must_haves_ok(case, {**theirs, **t}, std):
                    continue
                if (c := cost(t := {**theirs, **t})) < c_best - 0.005:
                    best, c_best = t, c
        return best

    @staticmethod
    def _drop_small_asks(case, std, sheets, theirs, cost, upper=math.inf, sent=()):
        """A non-price field we ask away from the supplier's value goes back to theirs unless it saves >= MIN_ASK of C,
        and only if the result still fits under `upper` and was not sent before."""
        out = []
        for t in sheets:
            for f in case["negotiable"]:
                if f in ("unit_price", "index_clause") or f not in theirs or t.get(f) == theirs[f]:
                    continue
                back = complete_offer(case, satisfy_must_haves(case, {**t, f: theirs[f]}, std))
                if (
                    must_haves_ok(case, back, std)
                    and cost(back) - cost(t) < MIN_ASK * cost(t)
                    and cost(back) <= upper
                    and back not in sent
                ):
                    t = back
            if t not in out:
                out.append(t)
        return out or sheets


def _guard(agent):  # her v8 chains: resend check on, distress widening on (flags are off by default)
    g = GuardedAgent(agent)
    g.RESEND_CHECK = True
    return g


def _better():
    b = BetterAgent()
    b.RELEASE_DISTRESS = True
    return b


class Combined2Agent:
    def __init__(self, data=None):
        self.chains = {
            "better": lambda: EvidenceAgent(HealthScope(_guard(_better())), data),
            "combined": lambda: EvidenceAgent(_guard(CombinedCore()), data, questions=False),
        }
        self.case_id = self.chosen = self.delegate = None

    def __getattr__(self, name):
        if name in ("chains", "case_id", "chosen", "delegate"):
            raise AttributeError(name)
        return getattr(self.delegate, name)

    def decide(self, case, threads):
        if self.delegate is None or case.get("case_id") != self.case_id:
            self.case_id, self.chosen = case.get("case_id"), route(case)
            self.delegate = self.chains[self.chosen]()
        return self.delegate.decide(case, threads)
