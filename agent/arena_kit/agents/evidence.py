"""Evidence wrapper: lets any agent decide, then rewrites each 'send' into a short business e-mail that
cites verified data (see evidence.py): up to 3 new claims, one question, refs set to the cited IDs.
Term sheets, accept and walk-away decisions are untouched; any failure keeps the delegate's decision."""

import logging
import re

from ..cost import OPS
from ..evidence import build_claims, load_package
from ..play import live_threads, standing

log = logging.getLogger("arena")

MAX_CLAIMS, MAX_WORDS = 3, 160
ID = re.compile(r"\b(?:idx|quote|sc|qn|po|fc|cost|news|doc|ctr|offer):[\w@.#-]*\w")
FIELDS = {"volume_per_year": "lift your allocation to {v} units per year"}


def _cited(events):
    """Every data ID our messages in a thread already cite (refs and body)."""
    return {i for m in events if m.get("from") == "buyer" for i in [*(m.get("refs") or []), *ID.findall(m.get("body") or "")]}


class EvidenceAgent:
    def __init__(self, delegate, data=None):
        self.delegate, self.data, self._pkg, self._loaded = delegate, data, None, False

    def __getattr__(self, name):  # e.g. `.chosen` of a wrapped router
        if name in ("delegate", "data", "_pkg", "_loaded"):
            raise AttributeError(name)
        return getattr(self.delegate, name)

    def decide(self, case, threads):
        decision = self.delegate.decide(case, threads)
        try:
            msg, sid = decision.get("message") or {}, decision.get("supplier_id")
            if msg.get("action") or sid not in threads or not threads[sid]:
                return decision
            if not self._loaded:
                self._loaded = True
                self._pkg = load_package(self.data)
            if self._pkg is None:
                return decision
            return {**decision, "message": self._rewrite(case, threads, sid, msg)}
        except Exception:
            log.exception("%s evidence: failed, keeping the delegate's message", case.get("case_id"))
            return decision

    def _rewrite(self, case, threads, sid, msg):
        events = threads[sid]
        _, terms = standing(events)
        price = terms.get("unit_price")
        used = set().union(*(_cited(e) for e in threads.values()))
        used = {i for i in used if not i.startswith("offer:")} | {i for i in _cited(events) if i.startswith("offer:")}
        focus = getattr(self.delegate, "focus", None) or {}  # the Listener's supplier model, if the delegate has one
        if focus.get("supplier_id", sid) != sid:
            focus = {}  # the guard redirected to another supplier: that model is not this supplier's
        claims = [c for c in build_claims(case, self._pkg, sid, price)
                  if not used & set(c["ids"]) and c["kind"] not in focus.get("dismissed", ())]
        asks = []
        for m in case["buyer"].get("must_haves", []):
            cur = terms.get(m["field"])
            if m["field"] in focus.get("frozen", ()):
                continue  # a declared hard constraint: asking again only repeats a refusal
            if cur is not None and not OPS[m["op"]](cur, m["value"]):
                what = FIELDS.get(m["field"]) or f"confirm {m['field'].replace('_', ' ')} {'of at least' if '>' in m['op'] else 'of at most'} {{v}}"
                asks.append(f"Could you {what.format(v=m['value'])}?")
                if m["field"] == "volume_per_year":
                    claims.sort(key=lambda c: c["kind"] != "fc")  # the forecast backs a volume ask (stable sort)
        rivals = [(standing(threads[o])[1].get("unit_price"), standing(threads[o])[0]) for o in live_threads(threads) if o != sid]
        rivals = [r for r in rivals if r[0] is not None and r[1] and price is not None and r[0] < price]
        if rivals and len(case.get("parts", [])) == 1 and not any(i.startswith("offer:") for i in _cited(events)):
            p, oid = min(rivals)
            claims.insert(0, {"kind": "offer", "ids": [oid], "strength": 90, "sentence": f"Another bidder's offer for this part stands at EUR {p:.2f} per unit ({oid})."})
        picked, ids = [], set()
        for c in claims:
            if c["kind"] != "calc" and len([x for x in picked if x["kind"] != "calc"]) < MAX_CLAIMS and not ids & set(c["ids"]):
                picked.append(c)
                ids |= set(c["ids"])
        calc = [c for c in claims if c["kind"] == "calc"]
        if calc and any(c["kind"] == "idx" for c in picked):
            picked.append(calc[0])
        picked.sort(key=lambda c: -c["strength"])
        theirs = [m for m in events if m.get("from") != "buyer"]
        last = theirs[-1]
        if not any(m.get("term_sheets") for m in theirs):
            asks.append("Could you please send us your quote?")
        elif focus.get("question"):
            asks.append(focus["question"])  # aim the one question at the supplier's currency
        elif sum(m.get("from") == "buyer" for m in events) == 0:
            asks.append("Could you send us a breakdown of the costs behind your price?")
        elif last.get("status") == "final_offer" or re.search(r"\b(limit|cap|allocation)", last.get("body") or "", re.I):
            asks.append("Could you explain the reason behind the limit you stated?")
        sheets = bool(msg.get("term_sheets"))
        company = re.search(r"for ([A-Z][\w&. -]+?) (?:with|from)", case.get("briefing", ""))
        sign = f"{company.group(1)}, Purchasing" if company else "Purchasing"
        subject = (msg.get("subject") or "Re: " + (last.get("subject") or case.get("title", "our enquiry")))[:300]

        def body(cs, qs):
            return "\n".join(["Dear Sir or Madam,", "", "thank you for your message." + (" Our proposed terms are in the term sheet of this message." if sheets else ""),
                              *[c["sentence"] for c in cs], *qs, "", "Best regards,", sign])

        qs = list(asks)
        while len(body(picked, qs).split()) > MAX_WORDS and (picked or len(qs) > 1):
            if picked:
                picked.pop()
            else:
                qs.pop()
        return {**msg, "subject": subject, "body": body(picked, qs), "refs": [i for c in picked for i in c["ids"]]}
