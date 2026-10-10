"""Play cases with an agent against the arena over HTTP - the hosted arena (practice, sandbox,
final) or `arena-sim`, the local contract simulator. Both speak the same API.

An agent is any object with `decide(case, threads) -> {"supplier_id": ..., "message": {...}}`:
  threads: {supplier_id: [message, ...]} - every e-mail so far, both directions, in order;
           supplier attachments carry their text under "text" (see `docs.read_document`).
  message: subject, body, up to 3 term sheets, refs - or an "action" that closes the case:
           {"type": "accept", "term_sheet_id": ...} or {"type": "walk_away"}.
"""

import copy
import functools
import logging
import re
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from .client import ArenaError
from .cost import must_haves_ok, total_cost
from .docs import read_document, standard_terms

log = logging.getLogger("arena")

ENDED = {"walked_away", "no_bid"}
# A message later than this after the supplier's last one counts as a timeout.
MOVE_LIMIT_S = 60
# In the Live Final, close this long before the wave's cap - or the slowest round of the case so far
# (your decision plus a supplier reply of up to about a minute) plus a margin, if that is longer.
CLOSE_BEFORE_CAP_S, ROUND_MARGIN_S = 90, 15
RUNNING = re.compile(r"one session per case in the final: (\S+)")
# Practice: the case list shows every practice case file; only those marked hosted can be played
# (a session on another is a 403). Without the marker every listed case counts as hosted.
HOSTED_FIELD = "hosted"


class RemoteTable:
    """The arena over HTTP: the practice arena, the final, or a hosted sandbox."""

    def __init__(self, client, case=None):
        self.client, self.session_id, self.case, self.done = client, None, case, None

    def open(self, case_id):
        try:
            r = self.client.open_session(case_id)
        except ArenaError as e:
            running = RUNNING.search(str(e.detail)) if e.status == 409 else None
            if not (running and self.case):
                raise
            return self.resume(running.group(1))
        self.session_id = r["session_id"]
        log.info("session %s", self.session_id)
        return r["case"], r["threads"]

    def resume(self, session_id):
        """Pick up a final session this team already started (e.g. after a crash): every thread
        so far, from the arena."""
        self.session_id = session_id
        log.info("resuming session %s", session_id)
        state = self.client.session(session_id)
        if state["status"] == "ended":
            self.done = self.result()
        return self.case, {s: self.client.thread(session_id, s)["messages"] for s in state["threads"]}

    def send(self, supplier_id, message):
        return self.client.send_message(self.session_id, supplier_id, message)

    def close(self, supplier_id, message):
        reply = self.client.send_message(self.session_id, supplier_id, message)
        return reply.get("result", reply)  # the supplier's last e-mail carries the result

    def attachment(self, attachment_id):
        return self.client.attachment(self.session_id, attachment_id)

    def missed(self, supplier_id, error):
        """After a 409: the result if the case has ended (e.g. at a wave's cap), else what the
        thread now says (a timeout answer, or the reason it ended)."""
        state = self.client.session(self.session_id)
        if state.get("status") == "ended":
            return {"result": state.get("result") or {"deal": False, "end_reason": state.get("end_reason")}}
        t = self.client.thread(self.session_id, supplier_id)
        last = (t.get("timeouts") or [{}])[-1]
        sheet = [{"term_sheet_id": t["offer_id"], "terms": last.get("terms", {})}]
        return {
            "from": "arena",
            "status": "walked_away" if t["closed"] else t["status"],
            "term_sheets": [] if t["closed"] else sheet,
            "body": f"({error.detail})",
            "missing_fields": last.get("missing_fields", []),
            "attachments": [],
        }

    def result(self):
        state = self.client.session(self.session_id)
        return state.get("result") or {"deal": False, "end_reason": state.get("end_reason"), **state}


def latest(events):
    """The supplier's latest message in a thread."""
    return next(m for m in reversed(events) if m.get("from") != "buyer")


def standing(events):
    """(term_sheet_id, terms) of the supplier's standing term sheet, or (None, {})."""
    sheets = latest(events).get("term_sheets") or []
    return (sheets[0]["term_sheet_id"], sheets[0]["terms"]) if sheets else (None, {})


def find_sheet(events, sheet_id):
    """Terms of `sheet_id` among the sheets of the supplier's newest message that has any (so its
    alternatives count, an older superseded sheet does not), or None."""
    for m in reversed(events):
        if m.get("from") != "buyer" and m.get("term_sheets"):
            return next((s["terms"] for s in m["term_sheets"] if s.get("term_sheet_id") == sheet_id), None)
    return None


def live_threads(threads):
    """Suppliers whose thread has not ended."""
    return [sid for sid, ev in threads.items() if latest(ev).get("status") not in ENDED]


def moves_left(case, events):
    """Messages you may still send in this thread (the round limit counts each of them)."""
    return case.get("round_limit", 10) - sum(m.get("from") == "buyer" for m in events)


def fetch_documents(table, message):
    """Download every attachment of a supplier message and add its text."""
    for att in message.get("attachments") or []:
        if att.get("attachment_id") and "text" not in att:
            att["text"] = read_document(att["name"], table.attachment(att["attachment_id"]))
    return message


def closing_move(case, threads, stds=None):
    """Accept the cheapest standing term sheet that keeps the must-haves and beats the alternative
    (C with each supplier's standard terms), else walk away - what to do when time runs out."""
    alt = case["buyer"].get("alternative") or {}
    c_alt = total_cost(case, alt["terms"]) if alt.get("terms", {}).get("unit_price") else float("inf")
    from .agents.reciprocal import case_c_open  # lazy: that module imports this one

    c_open, best = case_c_open(case, threads), None  # a deal worse than the opening quote scores 0 (equal: kept, it is full marks when nothing can be won)
    for sid in live_threads(threads):
        sheet_id, terms = standing(threads[sid])
        std = (stds or {}).get(sid) or standard_terms(threads[sid])
        if sheet_id and must_haves_ok(case, terms, std) and (c := total_cost(case, terms, std)) < c_alt and c <= c_open:
            best = min(best or (c, sid, sheet_id), (c, sid, sheet_id))
    if best is None:
        return {"supplier_id": live_threads(threads)[0], "message": {"action": {"type": "walk_away"}}}
    return {"supplier_id": best[1], "message": {"action": {"type": "accept", "term_sheet_id": best[2]}}}


def _safe_accept(case, threads, sid, terms):
    """The thread's standing sheet is live, keeps the must-haves and beats both the alternative and the opening."""
    from .agents.reciprocal import _c_alt, case_c_open  # lazy: that module imports this one

    ev, std = threads[sid], standard_terms(threads[sid])
    if latest(ev).get("status") in ENDED or terms.get("unit_price") is None or not must_haves_ok(case, terms, std):
        return False
    c = total_cost(case, terms, std)
    return c < _c_alt(case) and c < case_c_open(case, threads)


def cap_near(cap, slowest):
    return bool(cap) and time.time() > cap - max(CLOSE_BEFORE_CAP_S, slowest + ROUND_MARGIN_S)


def _snapshot(agent):
    """Mutable per-case state of the agent and its `delegate` chain, to undo a decision that is thrown
    away. Limits: only dict, list and set attributes are saved (tuples and scalars are not restored,
    so a stateful agent that keeps those drifts); an attribute that cannot be deep-copied is skipped."""
    out = []
    while agent is not None:
        saved = {}
        for k, v in vars(agent).items():
            if isinstance(v, (dict, list, set)):
                try:
                    saved[k] = copy.deepcopy(v)
                except Exception:
                    log.warning("%s.%s cannot be snapshotted", type(agent).__name__, k)
        out.append((agent, saved))
        agent = getattr(agent, "delegate", None)
    return out


def _restore(snap):
    for agent, state in snap:
        vars(agent).update(state)


def _open(case, threads):
    """Live threads we can still answer with a counter."""
    return [s for s in live_threads(threads) if moves_left(case, threads[s]) >= 1
            and latest(threads[s]).get("status") not in ("final_offer", "agreed")]


def play(table, case_id, agent, deadline=None):
    """Play one case to its end. `deadline` (time.time(), or a function returning it): a Live Final
    wave's cap - shortly before it, `closing_move` closes the case so it does not end without a deal.

    Every open thread gets its answer within the supplier's 60 s window: a message is chosen for each
    thread that has none in flight, all are sent at once, and each reply is merged and its thread
    answered again as soon as it arrives (not when the slowest supplier has answered). Decisions and
    merges all run in this thread, so `threads` and the agent need no lock; only `table.send` runs in workers.
    An accept or walk-away runs alone, after the replies in flight are in."""
    case, threads = table.open(case_id)
    if getattr(table, "done", None):  # resumed a case that had already ended
        return table.done
    for events in threads.values():
        for m in events:
            fetch_documents(table, m)
    slowest = 0.0  # the longest round so far: decision + the supplier's reply

    def run_action(sid, msg):
        """(True, result) when the case ended, else (False, None): the case goes on."""
        try:
            log.info("%s %s", sid, msg["action"])
            try:
                return True, table.close(sid, msg)
            except ArenaError as e:  # a refused accept id (422): retry once with the thread's standing sheet
                stand, terms = standing(threads[sid])
                if (e.status != 422 or msg["action"].get("type") != "accept" or stand in (None, msg["action"].get("term_sheet_id"))
                        or not _safe_accept(case, threads, sid, terms)):
                    raise
                log.warning("%s: accept refused (%s) - retrying with %s", sid, e.detail, stand)
                return True, table.close(sid, {"action": {"type": "accept", "term_sheet_id": stand}})
        except ArenaError as e:
            if e.status != 409:
                raise
            log.info("%s: %s", sid, e.detail)
            reply = table.missed(sid, e)  # e.g. late, or the thread or the case has ended
            if "result" in reply:
                return True, reply["result"]
            threads[sid].append(fetch_documents(table, reply))
            return False, None

    def send(sid, msg):
        t1 = time.monotonic()
        try:
            reply = table.send(sid, msg)
        except ArenaError as e:
            if e.status != 409:
                raise
            log.info("%s: %s", sid, e.detail)
            reply = table.missed(sid, e)
        log.info("%s send took %.1fs", sid, time.monotonic() - t1)
        return reply

    pending, started, futures = {}, {}, {}  # sid -> our message in flight / when sent; future -> sid
    errored = {}  # sid -> the exception of its last send: left out until another thread gets a reply
    with ThreadPoolExecutor(max_workers=max(1, len(threads))) as pool:
        while pending or live_threads(threads):
            while True:  # answer every open thread that has no message in flight
                cap = deadline() if callable(deadline) else deadline
                near = cap_near(cap, slowest)
                free = [s for s in _open(case, threads) if s not in pending and s not in errored]
                if errored and not pending and not free:
                    raise next(iter(errored.values()))  # every thread failed
                if pending and not near and not free:
                    break
                t0 = time.monotonic()
                snap = _snapshot(agent) if pending and not near else None  # this decision may be thrown away
                if near:
                    log.info("%s: the wave's cap is near - closing", case_id)
                    decision = closing_move(case, threads)
                else:
                    view = {s: ev + [{**pending[s], "from": "buyer"}] if s in pending else ev
                            for s, ev in threads.items() if s not in errored}
                    decision = agent.decide(case, view)
                    if pending and not decision["message"].get("action") and decision["supplier_id"] in pending and free:
                        # the agent prefers a thread that is already in flight: choose among the others
                        _restore(snap)
                        snap = _snapshot(agent)
                        decision = agent.decide(case, {s: ev for s, ev in threads.items() if s not in pending and s not in errored})
                if (took := time.monotonic() - t0) > MOVE_LIMIT_S * 0.75:
                    log.warning("decision took %.1fs - the limit is %ss per message", took, MOVE_LIMIT_S)
                sid, msg = decision["supplier_id"], decision["message"]
                if pending and not near and (msg.get("action") or sid in pending):
                    _restore(snap)  # decided again once the replies in flight are in
                    break
                if msg.get("action"):
                    done, result = run_action(sid, msg)
                    if done:
                        return result
                    continue
                pending[sid], started[sid] = msg, t0
                futures[pool.submit(send, sid, msg)] = sid
            if not pending:
                continue
            timeout = None
            if cap := (deadline() if callable(deadline) else deadline):
                timeout = max(0.0, cap - max(CLOSE_BEFORE_CAP_S, slowest + ROUND_MARGIN_S) - time.time())
            for f in wait(futures, timeout, return_when=FIRST_COMPLETED)[0]:
                sid = futures.pop(f)
                msg = pending.pop(sid)
                try:
                    reply = f.result()
                except Exception as e:  # one failing thread must not stop the others
                    log.exception("%s: send failed", sid)
                    errored[sid] = e
                    started.pop(sid)
                    continue
                errored.clear()
                if "result" in reply:  # the reply ended the case, e.g. the last supplier walked away
                    return reply["result"]
                threads[sid] += [{**msg, "from": "buyer"}, fetch_documents(table, reply)]
                slowest = max(slowest, time.monotonic() - started.pop(sid))
                log.info("%s %s %s", sid, reply.get("status"), standing(threads[sid])[1])
    return table.result()


def hosted(cases):
    """The cases you can play: those marked hosted, or all of them if the list has no marker."""
    if any(HOSTED_FIELD in c for c in cases):
        return [c for c in cases if c.get(HOSTED_FIELD)]
    return cases


def quota_used_up(error):
    """The practice quota's 429 ("practice limit: …"): retrying does not help before it resets."""
    return isinstance(error, ArenaError) and error.status == 429 and str(error.detail).startswith("practice limit")


def play_all(new_table, case_ids, new_agent, parallel=8):
    """Play many cases at once (e.g. every practice case). `new_table()` and `new_agent()` give
    each case its own table and agent. Once the practice quota is used up, no further case starts.
    Returns {case_id: result or the exception that stopped it}."""
    used_up = threading.Event()

    def one(case_id):
        if used_up.is_set():
            return case_id, ArenaError(429, "not started: the practice quota is used up")
        try:
            return case_id, play(new_table(), case_id, new_agent())
        except ArenaError as e:
            if quota_used_up(e):
                used_up.set()
                log.warning("practice quota used up: %s", e.detail)
            elif e.status == 403:
                log.warning("%s: %s", case_id, e.detail)  # e.g. not hosted for practice
            else:
                log.exception("%s failed", case_id)
            return case_id, e
        except Exception as e:  # one broken case must not stop the others
            log.exception("%s failed", case_id)
            return case_id, e

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        return dict(pool.map(one, case_ids))


def play_waves(client, new_agent, waves=5, parallel=10, poll=5.0):
    """The Live Final: wait for each wave, play its cases in parallel within the wave's cap, wait
    for the next. Keep it running from before the first wave until the last has closed; it returns
    after `waves` waves have closed and every case has finished: {case_id: result or exception}."""
    started, closed, caps = {}, set(), {}  # caps: wave -> its cap as time.time()

    def one(case, deadline):
        try:
            return play(RemoteTable(client, case), case["case_id"], new_agent(), deadline)
        except Exception as e:  # one broken case must not stop the others
            log.exception("%s failed", case["case_id"])
            return e

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        while len(closed) < waves or not all(f.done() for f in started.values()):
            try:
                cases = client.cases("final")
            except ArenaError as e:
                if e.status != 403:  # 403: no wave has started yet
                    raise
                cases = []
            for case in cases:
                if not case.get("open"):
                    closed.add(case["wave"])
                    continue
                if case.get("seconds_left") is not None:  # each wave has its own cap; follow an extension
                    caps[case["wave"]] = time.time() + case["seconds_left"]
                if case["case_id"] not in started and case.get("seconds_left"):
                    if case["wave"] not in {c["wave"] for c in cases if c["case_id"] in started}:
                        log.warning("wave %s started: %s", case["wave"], case.get("theme"))
                    started[case["case_id"]] = pool.submit(one, case, functools.partial(caps.get, case["wave"]))
            time.sleep(poll)
    return {case_id: f.result() for case_id, f in started.items()}
