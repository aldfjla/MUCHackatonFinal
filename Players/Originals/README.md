# Players/Originals: frozen snapshots (2026-10-10)

ORIGINAL SNAPSHOTS: do not edit. Copy to `Players/` (e.g. `Players/Variants/`) for experiments.
Each script holds the full agent code copied from `agent/arena_kit/agents/`; only imports were rewritten
(`arena_kit.*` absolute, sibling snapshots for shared helpers). `_runner.py` plays a case like `arena play`.

| Script | Nickname | School | Backlog version | Class | Playstyle |
|---|---|---|---|---|---|
| naive_baseline.py | Naive Baseline | none (kit baseline, MIT) | v0 - niko | NaiveAgent | Anchors a little low, splits the difference, accepts early |
| smart_petra.py | Petra's Smart | rule-based (Petra) | v1-petra | SmartAgent | Slow concessions, up to 3 term sheets per e-mail, safety checks |
| patient_hawk.py | Patient Hawk | game theory | v2.1 - niko | RationalAgent | Opens firm, Boulware concessions, capped at estimated supplier floor |
| curious_fox.py | Curious Fox | principled / interest-based | v3 - niko | ExplorerAgent | Packages of equal-cost offers; learns what the supplier values |
| bold_ram.py | Bold Ram | behavioural (anchoring) | v4 - niko | AnchorAgent | Ambitious anchor, shrinking framed concessions, each paired with an ask |
| chameleon.py | Chameleon | adaptive switching | v5 - niko | SwitcherAgent | Switches collaborate / firm / closing on supplier cues |
| iron_turtle.py | Iron Turtle | computational (Boulware) | v6 - niko | BoulwareAgent | Holds firm in total-cost space, concedes late, tit-for-tat |
| wise_owl.py | Wise Owl | procurement (Kraljic) | v7 - niko | RouterAgent | Routes each case to an archetype by `category_goal` |

## Run

From the repo root:

```
cd agent && export PATH="$HOME/.local/bin:$PATH" UV_PROJECT_ENVIRONMENT="$HOME/.venvs/arena-agent" \
  && ARENA_URL=http://127.0.0.1:8000 ARENA_API_KEY=<key> uv run python ../Players/Originals/patient_hawk.py case:S01
```

`--list` shows the cases. `ARENA_URL` / `ARENA_API_KEY` (env or `.env`) must point to the local simulator
(arena-sim, simulator key) or, with a team key, the real arena. Real arena runs use practice sessions
(200 per day): run them deliberately.

The live, tested versions are in `agent/arena_kit/agents/` with unit tests in `agent/tests/`
(offline smoke test for these snapshots: `agent/tests/test_players_originals.py`).
