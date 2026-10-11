"""Evidence wrapper: lets any agent decide, then rewrites each 'send' into a short business e-mail that
cites verified data (see evidence.py): the delegate's body is kept, then up to 3 new claims (grouped by the
sheet change they justify, body capped at MAX_CHARS) and one question; refs = delegate refs + cited IDs.
Term sheets, accept and walk-away decisions are untouched; any failure keeps the delegate's decision."""

import logging
import re

from ..cost import OPS
from ..evidence import build_claims, load_package
from ..play import live_threads, standing

log = logging.getLogger("arena")

MAX_CLAIMS, MAX_WORDS, MAX_CHARS = 3, 160, 1200
# which requested change a fact justifies: price facts back unit_price, the forecast backs volume / length
LEVER = {"idx": "unit_price", "calc": "unit_price", "cost": "unit_price", "quote": "unit_price", "offer": "unit_price", "po": "unit_price",
         "doc": "unit_price", "fc": "volume_per_year"}
LEAD = {"unit_price": (("unit_price",), "To support the price in our term sheet"),
        "volume_per_year": (("volume_per_year", "contract_months"), "To support the volume and contract length we propose")}
ID = re.compile(r"\b(?:idx|quote|sc|qn|po|fc|cost|news|doc|ctr|offer):[\w@.#-]*\w")
FIELDS = {"volume_per_year": "lift your allocation to {v} units per year"}


def _cited(events):
    """Every data ID our messages in a thread already cite (refs and body)."""
    return {i for m in events if m.get("from") == "buyer" for i in [*(m.get("refs") or []), *ID.findall(m.get("body") or "")]}


class EvidenceAgent:
    def __init__(self, delegate, data=None, *, questions=True):
        self.delegate, self.data, self._pkg, self._loaded, self.questions = delegate, data, None, False, questions

    def __getattr__(self, name):  # e.g. `.chosen` of a wrapped router
        if name in ("delegate", "data", "_pkg", "_loaded", "questions"):
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
        own = {*(msg.get("refs") or []), *ID.findall(msg.get("body") or "")}  # the delegate already cites these
        focus = getattr(self.delegate, "focus", None) or {}  # the Listener's supplier model, if the delegate has one
        if focus.get("supplier_id", sid) != sid:
            focus = {}  # the guard redirected to another supplier: that model is not this supplier's
        claims = [c for c in build_claims(case, self._pkg, sid, price)
                  if not (used | own) & set(c["ids"]) and c["kind"] not in focus.get("dismissed", ())]
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
        elif not self.questions:
            pass
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

        keep = (msg.get("body") or "").strip()
        qs = list(asks)
        if keep:  # keep the delegate's conditional trade sentences verbatim; trim only our justification
            sheet = ((msg.get("term_sheets") or [{}])[-1]).get("terms") or {}

            def just(cs, qs):
                lines = []
                for lever in dict.fromkeys(LEVER.get(c["kind"], "") for c in cs):
                    group = [c for c in cs if LEVER.get(c["kind"], "") == lever]
                    if lever in LEAD and any(f in sheet for f in LEAD[lever][0]):
                        lines.append(LEAD[lever][1] + ":")
                    lines += [c["sentence"] for c in group]
                return "\n".join([keep, "", *lines, *qs] if lines or qs else [keep])

            while len(just(picked, qs)) > MAX_CHARS and (picked or qs):
                picked.pop() if picked else qs.pop()
            refs = list(dict.fromkeys([*(msg.get("refs") or []), *(i for c in picked for i in c["ids"])]))
            return {**msg, "subject": subject, "body": just(picked, qs), "refs": refs}
        while len(body(picked, qs).split()) > MAX_WORDS and (picked or len(qs) > 1):
            if picked:
                picked.pop()
            else:
                qs.pop()
        return {**msg, "subject": subject, "body": body(picked, qs), "refs": [*dict.fromkeys([*(msg.get("refs") or []), *(i for c in picked for i in c["ids"])])]}
