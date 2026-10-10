"""Supplier model for the Listener: what is this supplier willing and able to move on?

Rebuilt from the thread on every turn (stateless, so it survives a crash or resume). Two sources:
- words: phrase rules over the supplier's e-mails (English and German), e.g. "capacity is fully
  utilized" -> volume is a hard constraint; "faster payment would help" -> payment is its currency;
- behaviour: which of our asks it took or refused, and what it priced when it sent two packages
  (90 days at 6.10 next to 30 days at 6.00 means payment days cost it EUR 0.10 per unit).

The result is a plain dict (see `supplier_model`), so the agent and the evidence layer can read it.
"""

import re

TOPIC = {  # negotiable field -> the "currency" it belongs to
    "payment_days": "payment",
    "volume_per_year": "capacity",
    "contract_months": "duration",
    "lead_time_days": "leadtime",
    "ppm_commitment": "quality",
    "chargeback_eur_per_complaint": "quality",
    "index_clause": "index",
    "effective_date": "timing",
    "tooling_eur": "cash",
}
CURRENCY = {  # topic -> phrases that show the supplier cares about it (a hit adds 1 to its priority)
    "payment": r"faster payment|pay (us )?(faster|sooner|earlier)|need the (cash|money)|pay (for )?(our|the) (own )?(bills|wages|staff|suppliers|material)"
    r"|cash flow|liquidit|financing|stick to \d+[- ]?days|payment must stay|\d+[- ]?days (payment|net) .{0,20}(limit|only)"
    r"|only with \d+[- ]?days|(would|must) (increase|necessitate)[^.]{0,30}price[^.]{0,40}\d+[- ]?days"
    r"|\d+[- ]?days[^.]{0,30}(higher|increase)[^.]{0,20}price|(longer|extended) payment[^.]{0,40}(increase|higher|raise)"
    r"|zahlung\w*[^.]{0,40}(halten|bleiben)|schneller(e)? zahlung|liquidität",
    "capacity": r"capacity|fully utili[sz]ed|allocat|maximum available volume|cannot increase|kapazität|ausgelastet",
    "duration": r"longer (contract|term|commitment)|contract (length|duration)|multi-year|planning security|planungssicherheit|laufzeit",
    "relationship": r"long-standing|core account|long-term partner|partnership|relationship|for generations",
    "quality": r"sorting|more checks|checks here|inspection effort",
    "index": r"preisgleitklausel[^.]{0,20}(offer|accept|possible)|index clause[^.]{0,20}(offer|accept|possible)|copper (costs|prices)|raw material",
    "leadtime": r"overtime|at a premium|faster deliver|express",
}
WEIGHT = {"relationship": 0.3}  # partnership words are mostly letterhead politeness, not a lever
HARD = {  # field -> phrases that make it a hard constraint (frozen at the supplier's value), matched per sentence
    "volume_per_year": r"cannot increase the allocation|capacity (is )?(fully|full)|fully utili[sz]ed|maximum available volume|strictly limit|voll ausgelastet",
    "payment_days": r"(payment|zahlung)\w*[^.]{0,40}(must|has to|have to|need to) (stay|remain)|(stick to|maintain|keep|stay at|remain at|only with|need the money in|really need the)[^.]{0,25}\d+[- ]?(days?|tage)"
    r"|\d+[- ]?(days?|tage)[^.]{0,30}(absolute limit|only option|non-negotiable|nicht verhandelbar)|standard \d+[- ]?day",
}
OWN_WORDS = {"payment_days": r"pay|zahlung|\bnet\b"}  # a hard payment phrase must sit next to a payment word
PRICE_FROZEN = (  # always about price: no more concessions
    r"no further concessions|cannot make any further|unable to offer further|no room for further|leaving no room|cannot give up margin"
    r"|keinen spielraum"
)
LIMIT = r"absolute limit|final word|have to stick to|hold our (offer|price|angebot)|maintain our (offer|price)|nicht möglich|endgültig"
PRICE_WORDS = r"price|preis|€|eur\b|per unit|concession"  # a generic limit phrase freezes price only next to these
SMALL_MOVES = (
    r"adjustment was (minimal|again very small|very small|small)|only make a (small|minor) concession|didn'?t move|did not move"
    r"|without movement on your side|flexibility from both|no movement"
)
DISMISSED = {  # evidence kind -> words the supplier uses for it when it says the data "does not change" its calculation
    "fc": r"volume (change|forecast)",
    "po": r"price history|past order|purchase order",
    "sc": r"delivery (record|data|numbers)",
    "cost": r"should.?cost",
    "idx": r"index",
    "news": r"news|report",
    "quote": r"other offer|alternative quote",
}
NOT_CHANGE = r"(does not|doesn'?t|do not) (change|impact)|not change our (position|calculation)"
FASTER_PAY = (  # the supplier itself asks to be paid sooner (not just "payment matters")
    r"faster payment|pay (us )?(faster|sooner|earlier)|earlier payment|shorter payment|need the (cash|money)"
    r"|schneller(e)? zahlung|frühere zahlung"
)
_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def _sheets(m):
    return [s.get("terms") or {} for s in m.get("term_sheets") or []]


def supplier_model(case, events):
    """{flex: {field: +n accepted / -n refused}, hard: set(fields), frozen: set(fields), preferred: {field: value},
    priced: {field: EUR per unit it charged for our value}, priority: {topic: score}, currency: topic or 'price',
    price_frozen, small_moves, dismissed: set(evidence kinds), prices: [their unit prices]}"""
    fields = [f for f in case.get("negotiable", []) if f != "unit_price"]
    sup = [m for m in events if m.get("from") != "buyer"]
    texts = [str(m.get("body") or "").lower() for m in sup]
    last = texts[-1] if texts else ""
    allt = " ".join(texts)
    model = {
        "flex": {f: 0 for f in fields},
        "hard": set(),
        "frozen": set(),
        "preferred": {},
        "priced": {},
        "priority": {t: 0.0 for t in CURRENCY},
        "currency": "price",
        "price_frozen": False,
        "small_moves": False,
        "dismissed": set(),
        "prices": [],
        "asks_faster_pay": bool(re.search(FASTER_PAY, allt)),
        "min_pay": None,  # the shortest payment days the supplier itself put on a sheet
        "tied": set(),  # fields the supplier ties to its price: they differ between its packages
    }

    for i, t in enumerate(texts):  # words: recent messages weigh more
        w = 1.0 + i / max(len(texts), 1)
        for topic, rx in CURRENCY.items():
            model["priority"][topic] += w * WEIGHT.get(topic, 1.0) * len(re.findall(rx, t))
    sents = [x for t in texts for x in _SENT.split(t)]
    for f, rx in HARD.items():
        if f in fields and any(re.search(rx, x) and re.search(OWN_WORDS.get(f, ""), x) for x in sents):
            model["hard"].add(f)
    limit = any(re.search(LIMIT, x) and re.search(PRICE_WORDS, x) for x in _SENT.split(last))
    model["price_frozen"] = bool(re.search(PRICE_FROZEN, last)) or limit or (
        sup[-1].get("status") == "final_offer" if sup else False
    )
    model["small_moves"] = bool(re.search(SMALL_MOVES, last))
    for sent in _SENT.split(allt):
        if re.search(NOT_CHANGE, sent):
            model["dismissed"] |= {k for k, rx in DISMISSED.items() if re.search(rx, sent)}

    # behaviour: our ask -> their next reply
    prev_theirs = None
    for i, m in enumerate(events):
        sheets = _sheets(m)
        if m.get("from") != "buyer":
            pays = [s["payment_days"] for s in sheets if isinstance(s.get("payment_days"), int | float)]
            if pays:
                model["min_pay"] = min(pays + ([model["min_pay"]] if model["min_pay"] is not None else []))
            if sheets and sheets[0].get("unit_price") is not None:
                model["prices"].append(sheets[0]["unit_price"])
                prev_theirs = sheets[0]
                _priced(model, sheets, fields)
            continue
        if not sheets or prev_theirs is None:
            continue
        reply = next((r for r in events[i + 1 :] if r.get("from") != "buyer"), None)
        rs = _sheets(reply) if reply else []
        if not rs:
            continue
        for f in fields:
            ours, before = sheets[0].get(f), prev_theirs.get(f)
            if f not in sheets[0] or ours == before:
                continue  # we did not ask for a change
            if rs[0].get(f) == ours:
                model["flex"][f] += 1
                if (
                    rs[0].get("unit_price")
                    and prev_theirs.get("unit_price")
                    and rs[0]["unit_price"] > prev_theirs["unit_price"]
                ):
                    model["priced"].setdefault(
                        f, rs[0]["unit_price"] - prev_theirs["unit_price"]
                    )  # took it, but charged
                    _bump(model, f, 1)
            elif any(s.get(f) == ours for s in rs[1:]) or rs[0].get(f) == before:
                model["flex"][f] -= 1
                _bump(model, f, 1)

    p = model["prices"]
    if len(p) >= 3 and p[-1] == p[-2] == p[-3]:  # their price stayed the same over 2 consecutive replies
        model["price_frozen"] = True
    standing = next((_sheets(m) for m in reversed(events) if m.get("from") != "buyer" and m.get("term_sheets")), [])
    if standing:
        model["tied"] = {f for f in fields for a in standing for b in standing if a.get(f) != b.get(f)}
        cheapest = min(standing, key=lambda s: s.get("unit_price") or float("inf"))
        for f in fields:  # what they want: the value on their cheapest package, else on their standing sheet
            if f in cheapest:
                model["preferred"][f] = cheapest[f]
    for f in fields:
        if f in model["hard"] or model["flex"][f] <= -2:
            model["frozen"].add(f)
    top = max(model["priority"].items(), key=lambda kv: kv[1])
    on_table = {TOPIC.get(f) for f in fields} | {"relationship"}
    model["currency"] = top[0] if top[1] >= 1 and top[0] in on_table else "price"
    return model


def _bump(model, field, n):
    topic = TOPIC.get(field, field)
    model["priority"][topic] = model["priority"].get(topic, 0.0) + n


def _priced(model, sheets, fields):
    """Two packages in one reply that differ in one field: the price gap is what that field costs it."""
    for a in sheets:
        for b in sheets:
            pa, pb = a.get("unit_price"), b.get("unit_price")
            if a is b or pa is None or pb is None or pa <= pb:
                continue
            diff = [f for f in fields if a.get(f) != b.get(f)]
            if len(diff) == 1:
                f = diff[0]
                model["priced"][f] = max(model["priced"].get(f, 0), pa - pb)  # a (dearer) holds the value we wanted
                _bump(model, f, 2)


def focus(model, case):
    """What the evidence layer should aim at: the supplier's currency, frozen fields and evidence it shrugged off."""
    q = {
        "payment": "What price can you offer us at {days}-day payment?",
        "capacity": "What would it take for you to free capacity for our volume: a longer contract or a longer lead time?",
        "duration": "What price could you offer us for a longer contract term?",
        "quality": "Which price works for you at the quality level in our term sheet?",
        "leadtime": "What price could you offer us at your standard lead time?",
        "index": "Would an index clause on your main cost driver let you lower the base price?",
        "relationship": "Which of the packages in our term sheet works best for you?",
        "price": "Which of the packages in our term sheet works best for you?",
    }[
        model["currency"]
        if model["currency"] in ("payment", "capacity", "duration", "quality", "leadtime", "index", "relationship")
        else "price"
    ]
    # their own payment days, never the shortest option: volunteering 14 days bought ~0.5 % in P01/P02
    days = model["preferred"].get("payment_days") or model.get("min_pay") or case["buyer"].get("reference_payment_days", 60)
    return {
        "currency": model["currency"],
        "frozen": set(model["frozen"]),
        "dismissed": set(model["dismissed"]),
        "question": q.format(days=days),
    }
