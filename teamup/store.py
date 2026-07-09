"""Session state + persistence for TeamUp.

Key-less by design: data lives in ``st.session_state``, backed by a local JSON
file so it survives reruns within a session. No API key, no external service, no
secrets — nothing to leak and nothing to pay for.

(On a hosted free tier the JSON file resets when the app restarts, which is fine
for forming teams in a working session. For long-lived async intake, run it
locally or point _FILE at durable storage.)

All pages call save(st) and init_state(st) — storage is invisible to them.
"""

from __future__ import annotations

import json
from pathlib import Path

from teamup.match import Profile

_FILE = Path("teamup_state.json")


def _json_load() -> dict | None:
    if not _FILE.exists():
        return None
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ── public API ────────────────────────────────────────────────────────────────

def save(st) -> None:
    """Persist the current pool + locked teams to the local JSON file.

    Best-effort: if the filesystem is read-only, session_state still holds the
    data for the rest of the session, so the app never errors on save.
    """
    payload = {
        "pool": [p.__dict__.copy() for p in st.session_state.pool],
        "teams_locked": st.session_state.get("teams_locked", []),
    }
    try:
        _FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def init_state(st) -> None:
    """Load persisted state into st.session_state on first run of each session."""
    ss = st.session_state
    if ss.get("_inited"):
        return

    saved = _json_load()
    if saved:
        ss.pool = [Profile(**d) for d in saved.get("pool", [])]
        ss.teams_locked = saved.get("teams_locked", [])
    else:
        ss.pool = []
        ss.teams_locked = []

    ss._inited = True


# ── demo data (opt-in only) ───────────────────────────────────────────────────

def demo_pool() -> list[Profile]:
    """8 fictional people for trying the matching flow. Never loaded automatically."""
    return [
        Profile("p1", "Alex", ["Python / coding", "Data / ML"], ["Pitching / presenting"],
                ["Mon evening", "Wed evening", "Sat daytime"], 12, 3),
        Profile("p2", "Sam", ["UI/UX design", "Graphics / branding"], ["Python / coding"],
                ["Mon evening", "Sat daytime"], 8, 3),
        Profile("p3", "Jess", ["Pitching / presenting", "Writing / storytelling"], [],
                ["Wed evening", "Sat daytime"], 6, 2),
        Profile("p4", "Kim", ["Project management", "Market / user research"], [],
                ["Mon evening", "Sat daytime"], 10, 3),
        Profile("p5", "Lee", ["Web / frontend"], ["UI/UX design"],
                ["Tue evening", "Sun daytime"], 5, 1),
        Profile("p6", "Ravi", ["Finance / modeling", "Market / user research"], [],
                ["Tue evening", "Sun daytime"], 7, 2),
        Profile("p7", "Mia", ["Python / coding", "Web / frontend"], ["Data / ML"],
                ["Tue evening", "Sun daytime"], 9, 2),
        Profile("p8", "Tom", ["Graphics / branding"], ["Pitching / presenting"],
                ["Tue evening", "Sun daytime"], 4, 1),
    ]
