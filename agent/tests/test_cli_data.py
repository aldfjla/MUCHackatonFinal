"""A relative ARENA_DATA (as in .env) must not switch better's health estimate off when --data is absolute."""

import json
from pathlib import Path

import pytest

from arena_kit.agents import better_agent
from arena_kit.cli import agent_factory

PKG = Path("~/negotiation-arena-kit/starter-kit/data/package").expanduser()
P02 = Path("~/MUCHakatonFinal/learning_information/03_practice_cases/P02.json").expanduser()


@pytest.mark.skipif(not (PKG / "world.sqlite").is_file() or not P02.is_file(), reason="no data package or P02 case file")
@pytest.mark.parametrize("env", ["data/package", None])
def test_data_flag_reaches_the_health_estimate(monkeypatch, tmp_path, env):
    monkeypatch.chdir(tmp_path)  # a folder without data/package, like agent/ in the real runs
    if env:
        monkeypatch.setenv("ARENA_DATA", env)
    else:
        monkeypatch.delenv("ARENA_DATA", raising=False)
    case = json.loads(P02.read_text())
    agent_factory("better", str(PKG))
    assert better_agent._health(case) is not None
