"""The Sunday release (news, letters) reaches the evidence layer and better's health band."""

import os
from pathlib import Path

import pytest

from arena_kit.agents import better_agent
from arena_kit.data import DataPackage
from arena_kit.evidence import DISTRESS, build_claims, check_claim

PKG = Path(os.environ.get("ARENA_DATA") or "~/negotiation-arena-kit/starter-kit/data/package").expanduser()
needs_release = pytest.mark.skipif(not (PKG / "world.sqlite").is_file() or not (PKG.parent / "release-sunday" / "facts.json").is_file(),
                                   reason="no data package with a Sunday release next to it")


@pytest.fixture
def with_release():
    return DataPackage(PKG)


@pytest.fixture
def without_release(tmp_path):
    return DataPackage(PKG, release=tmp_path)  # a folder without facts.json: no release


def _case(supplier, part="part:310060"):  # part:310060 has a generic should-cost row only
    return {"case_id": "case:T", "type": "renewal", "title": "t", "parts": [part], "suppliers": [supplier], "refs": [],
            "negotiable": ["unit_price"], "buyer": {"category_goal": "stabilise", "relationship_eur_per_point": 1000.0,
                                                   "sustainable_margin_pct": 8.0, "interest_rate": 0.08, "current_unit_price": 50.0}}


@needs_release
def test_release_rows_are_read_and_typed(with_release, without_release):
    news = with_release.release_rows("news")
    assert {r["id"] for r in news} >= {"news:20261006-S1", "news:20261002-S3"}
    docs = with_release.release_rows("documents")
    assert any(d["id"] == "doc:20261005-70250-S2" and d["asked_pct"] is None for d in docs)
    assert without_release.release_rows("news") == [] and without_release.release is None


@needs_release
@pytest.mark.parametrize("supplier", ["sup:70140", "sup:70350"])  # insolvency / credit cover withdrawn
def test_distressed_supplier_widens_the_health_band(monkeypatch, with_release, without_release, supplier):
    case = _case(supplier)
    monkeypatch.setattr(better_agent, "load_package", lambda: without_release)
    lo0, hi0 = better_agent._health(case)["band"]
    monkeypatch.setattr(better_agent, "load_package", lambda: with_release)
    lo1, hi1 = better_agent._health(case)["band"]
    assert hi1 - lo1 == pytest.approx(hi0 - lo0 + 2 * better_agent.BAND_WEAK)


@needs_release
def test_healthy_supplier_band_unchanged(monkeypatch, with_release, without_release):
    case = _case("sup:70110")
    monkeypatch.setattr(better_agent, "load_package", lambda: without_release)
    b0 = better_agent._health(case)["band"]
    monkeypatch.setattr(better_agent, "load_package", lambda: with_release)
    assert better_agent._health(case)["band"] == b0


@needs_release
def test_release_news_cited_only_from_facts_and_never_distress(with_release, without_release):
    claims = build_claims(_case("sup:70540"), with_release)  # supply back to normal: a neutral, citable fact
    news = [c for c in claims if c["kind"] == "news" and c["ids"][0].startswith("news:2026100")]
    assert news and all(c["ids"][0] in with_release.facts and check_claim(c, with_release) for c in news)
    assert not [c for c in build_claims(_case("sup:70540"), without_release) if c["ids"][0].startswith("news:2026100")]
    for sup in ("sup:70140", "sup:70350"):  # distress news is never put to the supplier
        rel = {r["id"] for r in with_release.release_rows("news") if r["topic"] in DISTRESS}
        assert not [c for c in build_claims(_case(sup), with_release) if set(c["ids"]) & rel]
