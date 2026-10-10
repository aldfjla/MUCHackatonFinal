"""Offline smoke test: every frozen Players/Originals script imports and exposes its agent class."""

import importlib
import sys
from pathlib import Path

ORIGINALS = Path(__file__).resolve().parents[2] / "Players" / "Originals"
EXPECTED = {
    "naive_baseline": "NaiveAgent",
    "smart_petra": "SmartAgent",
    "patient_hawk": "RationalAgent",
    "curious_fox": "ExplorerAgent",
    "bold_ram": "AnchorAgent",
    "chameleon": "SwitcherAgent",
    "iron_turtle": "BoulwareAgent",
    "wise_owl": "RouterAgent",
}


def test_originals_expose_agents():
    sys.path.insert(0, str(ORIGINALS))
    try:
        for module, cls in EXPECTED.items():
            agent = getattr(importlib.import_module(module), cls)
            assert callable(agent.decide), module
    finally:
        sys.path.remove(str(ORIGINALS))
