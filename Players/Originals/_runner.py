"""Shared runner for the frozen player snapshots: plays one case like `arena play` does."""

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE.parents[1] / "agent", HERE):  # arena_kit and the sibling snapshots
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from arena_kit.cli import load_env, summary  # noqa: E402
from arena_kit.client import ArenaClient, ArenaError  # noqa: E402
from arena_kit.play import RemoteTable, hosted, play  # noqa: E402


def main(agent_class):
    load_env()
    ap = argparse.ArgumentParser(description=f"Play a case with {agent_class.__name__} (ARENA_URL, ARENA_API_KEY from env or .env)")
    ap.add_argument("case_id", nargs="?", default="case:S01")
    ap.add_argument("--list", action="store_true", help="list the practice cases and exit")
    args = ap.parse_args()
    client = ArenaClient()
    if args.list:
        for case in hosted(client.cases("practice")):
            print(case["case_id"], case.get("type", ""), case.get("title", ""), sep="  ")
        return
    table = RemoteTable(client)
    try:
        result = play(table, args.case_id, agent_class())
    except ArenaError as e:
        raise SystemExit(str(e)) from None
    print(json.dumps(summary(result), indent=2))
    replay = client.session(table.session_id).get("replay_url")
    if replay:
        print(f"replay: {os.environ['ARENA_URL'].rstrip('/')}{replay}")
