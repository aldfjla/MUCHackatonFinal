import json
import re
from pathlib import Path

import pytest

from arena_kit.agents.evidence import ID, EvidenceAgent
from arena_kit.evidence import DEFAULT_DATA, build_claims, check_claim, load_package

REAL = sorted((Path(__file__).parent.parent / "arena_kit/sim_cases/real").glob("P*.json"))
pkg = load_package() if Path(DEFAULT_DATA).expanduser().exists() else None
needs_data = pytest.mark.skipif(pkg is None, reason=f"data package not found at {DEFAULT_DATA} (set ARENA_DATA): evidence tests skipped")


class Stub:
    """A delegate that sends one fixed message (or any decision) to the first supplier."""

    def __init__(self, message=None, decision=None):
        self.decision = decision or {"supplier_id": None, "message": message or {"subject": "S", "body": "generic text", "term_sheets": [{"terms": {"unit_price": 1.0}}]}}

    def decide(self, case, threads):
        return {**self.decision, "supplier_id": self.decision["supplier_id"] or next(iter(threads))}


def threads(case, price=None, **terms):
    out = {}
    for s in case["suppliers"]:
        doc = next(iter(pkg.query("select asked_price from documents where supplier_id=? and asked_price is not null order by date desc", (s,))), {})
        out[s] = [{"from": s, "subject": "Quote", "status": "open", "term_sheets": [{"term_sheet_id": f"offer:{s[4:]}-0", "terms": {"unit_price": price or doc.get("asked_price") or 50.0, **terms}}]}]
    return out


@needs_data
@pytest.mark.parametrize("path", REAL, ids=lambda p: p.stem)
def test_every_claim_verifies(path):
    case = json.loads(path.read_text())
    for s in case["suppliers"]:
        claims = build_claims(case, pkg, s)
        assert claims
        for c in claims:
            assert check_claim(c, pkg), c
            assert c["ids"] == [] or c["sentence"].endswith(")."), c
            assert set(ID.findall(c["sentence"])) == set(c["ids"]), c


@needs_data
def test_check_claim_rejects_wrong_figures():
    case = json.loads((REAL[0]).read_text())
    c = next(c for c in build_claims(case, pkg) if c["kind"] == "idx")
    assert not check_claim({**c, "figure": c["figure"] + 1.0}, pkg)
    assert not check_claim({**c, "ids": [c["ids"][0], "idx:NOPE@2026-08"]}, pkg)


@needs_data
def test_wrapper_message_and_no_repeats():
    case = json.loads((REAL[0]).read_text())
    th = threads(case)
    agent = EvidenceAgent(Stub())
    sent = []
    for _ in range(4):
        d = agent.decide(case, th)
        m = d["message"]
        assert len(m["body"].split()) <= 160 and "{" not in m["body"] and m["term_sheets"] == [{"terms": {"unit_price": 1.0}}]
        body_ids = ID.findall(m["body"])
        assert len(body_ids) == len(set(body_ids)) and set(body_ids) == set(m["refs"]) and len(m["refs"]) == len(set(m["refs"]))
        assert len(re.findall(r"\(\w+:[^)]*\)\.", m["body"])) <= 3
        ids = set(m["refs"])
        assert not ids & set(sent)
        sent += m["refs"]
        th[d["supplier_id"]] += [{**m, "from": "buyer"}, {**th[d["supplier_id"]][0], "status": "open"}]
    assert sent


@needs_data
def test_p10_asks_to_lift_allocation_and_cites_forecast():
    case = json.loads((REAL[0].parent / "P10.json").read_text())
    d = EvidenceAgent(Stub()).decide(case, threads(case, 30.0, volume_per_year=19890))
    assert "allocation to 22230" in d["message"]["body"] and "fc:340010@2026-09" in d["message"]["refs"]


@needs_data
def test_rfq_cites_a_cheaper_rival_offer_once():
    case = json.loads((REAL[0].parent / "P05.json").read_text())
    th = threads(case)
    a, b = case["suppliers"][:2]
    th[a][0]["term_sheets"][0]["terms"]["unit_price"], th[b][0]["term_sheets"][0]["terms"]["unit_price"] = 40.0, 30.0
    agent = EvidenceAgent(Stub({"subject": "S", "body": "x"}))
    m = agent.decide(case, th)["message"]
    assert f"offer:{b[4:]}-0" in m["refs"] and "EUR 30.00" in m["body"]
    th[a] += [{**m, "from": "buyer"}, th[a][0]]
    assert not any(r.startswith("offer:") for r in agent.decide(case, th)["message"]["refs"])


@needs_data
def test_actions_are_untouched_and_failures_fall_back():
    case = json.loads((REAL[0]).read_text())
    th = threads(case)
    act = {"supplier_id": case["suppliers"][0], "message": {"action": {"type": "walk_away"}}}
    assert EvidenceAgent(Stub(decision=act)).decide(case, th) == act
    plain = Stub().decide(case, th)
    agent = EvidenceAgent(Stub())
    agent._pkg, agent._loaded = object(), True  # breaks inside the rewrite
    assert agent.decide(case, th) == plain


def test_without_data_the_delegate_decides(tmp_path):
    case = json.loads((REAL[0]).read_text())
    th = {s: [{"from": s, "status": "open", "term_sheets": []}] for s in case["suppliers"]}
    agent = EvidenceAgent(Stub(), data=tmp_path / "nothing")
    assert agent.decide(case, th) == Stub().decide(case, th)


def _case(name):
    return json.loads((REAL[0].parent / f"{name}.json").read_text())


@needs_data
@pytest.mark.parametrize("path", REAL, ids=lambda p: p.stem)
def test_figures_match_facts_json(path):
    case = json.loads(path.read_text())
    for c in build_claims(case, pkg, case["suppliers"][0]):
        f = [pkg.facts[i] for i in c["ids"] if i in pkg.facts]
        if c["kind"] == "idx":
            a, b = f[0]["value"], f[1]["value"]
            assert abs((b / a - 1) * 100 - c["figure"]) <= 0.5
        elif c["kind"] in ("quote", "po", "cost", "fc"):
            key = {"quote": "unit_price", "po": "unit_price", "cost": "unit_cost", "fc": "change_pct"}[c["kind"]]
            assert all(abs(x[key] - c["figure"]) <= (0.5 if c["kind"] == "fc" else 0.005 * c["figure"] + 0.01) for x in f)
        elif c["kind"] == "sc":
            vals = [x[c["metric"]] for x in f]
            assert abs(sum(vals) / len(vals) - c["figure"]) <= (0.5 if c["metric"] == "otd_pct" else 0.005 * c["figure"] + 0.01)
        elif c["kind"] == "doc":
            assert f[0]["days"] == c["figure"] < f[1]["days"]


@needs_data
def test_check_claim_rejects_po_sc_doc():
    p01 = _case("P01")
    by = {c["kind"]: c for c in build_claims(p01, pkg)}
    assert not check_claim({**by["sc"], "figure": by["sc"]["figure"] + 2}, pkg)
    assert not check_claim({**by["doc"], "figure": by["doc"]["figure"] + 5}, pkg)
    po = next((c for n in ("P10", "P18") for c in build_claims(_case(n), pkg, price=1000.0) if c["kind"] == "po"), None)
    assert po and not check_claim({**po, "figure": po["figure"] * 1.2}, pkg)
    assert not check_claim({**po, "part": "part:999999"}, pkg)


@needs_data
def test_po_only_when_cheaper_than_the_suppliers_price_and_fc_only_when_positive():
    case = _case("P10")
    assert any(c["kind"] == "po" for c in build_claims(case, pkg, price=1000.0))
    assert not any(c["kind"] == "po" for c in build_claims(case, pkg, price=0.01))
    for n in (p.stem for p in REAL):
        assert all(c["figure"] > 0 for c in build_claims(_case(n), pkg) if c["kind"] == "fc")


@needs_data
def test_must_have_ask_and_forecast_order_and_questions():
    case = _case("P10")
    m = EvidenceAgent(Stub()).decide(case, threads(case, 30.0, volume_per_year=19890))["message"]
    assert m["body"].index("fc:340010@2026-09") < m["body"].index("allocation to 22230")
    ok = EvidenceAgent(Stub()).decide(case, threads(case, 30.0, volume_per_year=23400))["message"]
    assert "allocation" not in ok["body"]
    # later rounds: no "reason behind the limit" unless the supplier states one
    th = threads(case, 30.0, volume_per_year=23400)
    s = case["suppliers"][0]
    th[s] += [{"from": "buyer", "body": "x"}, {**th[s][0], "status": "open", "body": "We keep our price."}]
    assert "reason" not in EvidenceAgent(Stub()).decide(case, th)["message"]["body"]
    th[s][-1]["status"] = "final_offer"
    assert "reason" in EvidenceAgent(Stub()).decide(case, th)["message"]["body"]


@needs_data
def test_quote_ask_only_when_no_earlier_term_sheet():
    case = _case("P10")
    s = case["suppliers"][0]
    th = threads(case, 30.0, volume_per_year=23400)
    th[s] += [{"from": "buyer", "body": "x"}, {"from": s, "status": "open", "term_sheets": []}]
    assert "send us your quote" not in EvidenceAgent(Stub()).decide(case, th)["message"]["body"]
    assert "send us your quote" in EvidenceAgent(Stub()).decide(case, {s: [{"from": s, "status": "open", "term_sheets": []}]})["message"]["body"]


@needs_data
def test_multi_part_claims_name_their_part():
    for n in ("P07", "P15"):
        case = _case(n)
        for c in build_claims(case, pkg):
            if c["kind"] in ("quote", "po", "cost", "fc"):
                assert c["part"] in c["sentence"] and c["part"] in case["parts"]


@needs_data
def test_each_thread_has_its_own_connection_and_stays_read_only():
    # IndexError root cause: one shared sqlite connection gave empty/odd results when threads queried at once
    from concurrent.futures import ThreadPoolExecutor

    def conn(_):
        return pkg.db, len(pkg.query("select max(last_month) m from index_series"))

    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(conn, range(40)))
    assert all(n == 1 for _, n in res) and len({id(d) for d, _ in res}) > 1 and pkg.db is pkg.db
    with pytest.raises(ValueError):
        pkg.query("delete from news")


@needs_data
def test_concurrent_decisions_match_sequential(caplog):
    from concurrent.futures import ThreadPoolExecutor

    def run(path):
        case = json.loads(path.read_text())
        m = EvidenceAgent(Stub()).decide(case, threads(case))["message"]
        return m["body"], m["refs"]

    seq = [run(p) for p in REAL]
    with caplog.at_level("ERROR", logger="arena"), ThreadPoolExecutor(8) as ex:
        par = list(ex.map(run, REAL * 4))
    assert not [r for r in caplog.records if "evidence: failed" in r.getMessage()]
    assert par == seq * 4


COND = "We can commit to 24 months and 30,000 units/year if the price comes to 5.50."


@needs_data
def test_delegate_conditional_sentence_kept_and_facts_attach_to_price_lever():
    case = _case("P10")
    msg = {"subject": "S", "body": f"Dear Sir,\n{COND}", "refs": ["offer:keep-0"], "term_sheets": [{"terms": {"unit_price": 5.5, "contract_months": 24}}]}
    m = EvidenceAgent(Stub(msg)).decide(case, threads(case, 30.0, volume_per_year=19890))["message"]
    assert m["body"].startswith(f"Dear Sir,\n{COND}") and len(m["body"]) <= 1200
    assert "To support the price in our term sheet:" in m["body"] and "To support the volume and contract length we propose:" in m["body"]
    assert m["body"].index("To support the price") < m["body"].index("fc:340010@2026-09")
    assert m["refs"][0] == "offer:keep-0" and "fc:340010@2026-09" in m["refs"] and len(m["refs"]) == len(set(m["refs"]))
    assert set(ID.findall(m["body"])) - {"offer:keep-0"} <= set(m["refs"])


@needs_data
def test_cap_trims_justification_never_the_delegate_text():
    case = _case("P10")
    long = COND + " " + "x" * 1150
    m = EvidenceAgent(Stub({"subject": "S", "body": long, "term_sheets": [{"terms": {"unit_price": 5.5}}]})).decide(case, threads(case, 30.0))["message"]
    assert m["body"] == long and m["refs"] == []


@needs_data
def test_only_verified_claims_are_cited(monkeypatch):
    import arena_kit.agents.evidence as ev

    case = _case("P10")
    real = ev.build_claims
    monkeypatch.setattr(ev, "build_claims", lambda *a: [c for c in real(*a) if c["kind"] != "fc"])
    m = EvidenceAgent(Stub({"subject": "S", "body": COND, "term_sheets": [{"terms": {"unit_price": 5.5}}]})).decide(case, threads(case, 30.0))["message"]
    assert "fc:" not in m["body"] and not any(r.startswith("fc:") for r in m["refs"])
    for r in m["refs"]:  # every cited id comes from a claim that passes check_claim
        assert any(r in c["ids"] and check_claim(c, pkg) for c in real(case, pkg, case["suppliers"][0], 30.0))
