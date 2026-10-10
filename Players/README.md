# Players

- `Originals/`: frozen, runnable snapshots of all eight buyer agents. Do not edit them; see
  [Originals/README.md](Originals/README.md) for the table and how to run.
- Experiments: copy an Original into a new folder here (e.g. `Players/Variants/`) and change the copy.

Run example (repo root):
`cd agent && export PATH="$HOME/.local/bin:$PATH" UV_PROJECT_ENVIRONMENT="$HOME/.venvs/arena-agent" && ARENA_URL=... ARENA_API_KEY=... uv run python ../Players/Originals/patient_hawk.py case:S01`

ARENA_URL/KEY must point to the local simulator (arena-sim) or, with a team key, the real arena. Real arena
runs use practice sessions (200 per day), so run them deliberately.

The live, tested versions are in `agent/arena_kit/agents/`, with unit tests in `agent/tests/`.
