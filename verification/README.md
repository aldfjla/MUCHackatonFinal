# Backlog verification

Independent re-check of `backlog.csv`. Run from the repo root: `bash verification/run_verification.sh`.

- Stage A (no network): recomputes every score, checks c_best <= c_deal <= c_open, version labels, replay links, per-case constants (c_open, c_best), duplicates, missing fields.
- Stage B (`--rerun`): re-runs each simulator row through the frozen `Players/Originals/*.py` twice (determinism) and compares c_open/c_deal/c_best/score. v2 rows are superseded (not reproducible); practice-arena rows are not reproducible locally.
- Stage C (`--rerun`): fetches the finished session from the simulator, recomputes c_deal with `arena_kit.cost.total_cost`, and recomputes c_open/c_best from the case JSON. Also checks Wise Owl's routing note and lists identical c_deal across agents.

Output: `verification/report.md`; exit code 0 only if no MISMATCH. Only the local simulator (127.0.0.1:8000) is contacted; the script refuses a non-local `ARENA_URL`. It never edits `backlog.csv`, `agent/` or `Players/`.

Offline checks: `python3 verification/verify_backlog.py --selftest` and no flag (Stage A only).
