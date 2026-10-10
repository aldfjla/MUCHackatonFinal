"""`50`: opens at 0.80 x their price, halves the gap, accepts below 5% of their first price, lengthens the contract when they stall."""

from arena_kit.agents.fifty_agent import FiftyAgent


def _case():
    b = {"need_per_year": 1000, "horizon_years": 2, "fallback_unit_price": 40.0, "interest_rate": 0.1, "reference_payment_days": 30,
         "freight_eur_per_unit": {"DAP": 0.0}, "need_lead_time_days": 10, "current_unit_price": 30.0, "alternative": None}
    return {"buyer": b, "negotiable": ["unit_price", "contract_months"], "term_options": {"contract_months": [12, 24, 36]}, "max_messages": 20}


def _sup(price, i, months=12):
    return {"from": "supplier", "status": "open", "body": "", "term_sheets": [{"term_sheet_id": f"s{i}", "terms": {"unit_price": price, "contract_months": months}}]}


def _mine(price):
    return {"from": "buyer", "term_sheets": [{"terms": {"unit_price": price, "contract_months": 12}}]}


def _move(events):
    return FiftyAgent().decide(_case(), {"t": events})["message"]


def test_first_move_is_080():
    assert _move([_sup(30.0, 0)])["term_sheets"][0]["terms"]["unit_price"] == 24.0


def test_halves_the_gap():
    t = _move([_sup(30.0, 0), _mine(24.0), _sup(28.0, 1)])["term_sheets"][0]["terms"]
    assert t["unit_price"] == 26.0 and t["contract_months"] == 12  # they moved: no stall


def test_accepts_below_five_percent():
    m = _move([_sup(30.0, 0), _mine(28.6), _sup(29.0, 1)])  # gap 0.4 < 1.5
    assert m["action"] == {"type": "accept", "term_sheet_id": "s1"}


def test_stall_lengthens_contract():
    t = _move([_sup(30.0, 0), _mine(24.0), _sup(30.0, 1)])["term_sheets"][0]["terms"]
    assert t["unit_price"] == 27.0 and t["contract_months"] == 24
