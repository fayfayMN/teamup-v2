"""Shared, room-scoped state for TeamUp.

Key-less by design — no API key, no external service, nothing to pay for — but,
unlike a per-session JSON file, this store is **shared across everyone using the
same running app** so a whole cohort joins one pool and the organizer sees it.

How it works
------------
* ``@st.cache_resource`` gives every user session the *same* in-memory object on
  Streamlit's single free-tier replica, so joins from different people land in one
  place. A lock guards concurrent writes.
* Pools are namespaced by a **room code** (e.g. ``MUDAC26``) so separate events —
  or a test run vs the real one — never collide.
* Each room is mirrored to a best-effort JSON backup on disk, so an app *restart*
  restores it. The filesystem is still ephemeral across full redeploys/sleeps, so
  the organizer can also **download the room** and re-upload it to restore.
* Destructive/forming actions can be gated behind an **organizer passphrase**
  (set ``organizer_pass`` in Streamlit secrets); with no passphrase set, the app
  stays open (with a visible note) so it works out of the box.

Pages call ``init_state(st)`` (syncs the room into session_state) and the small
mutators below; storage stays invisible to them.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import streamlit as st

from teamup.match import Profile

DEFAULT_ROOM = "MAIN"
_BACKUP_DIR = Path("teamup_rooms")


# ── shared singleton (same object for every session on this replica) ───────────
@st.cache_resource
def _shared() -> dict:
    return {"rooms": {}, "lock": threading.RLock()}


def _rooms() -> dict:
    return _shared()["rooms"]


def _lock() -> threading.RLock:
    return _shared()["lock"]


def _clean_code(code: str) -> str:
    code = (code or "").strip().upper()
    keep = "".join(c for c in code if c.isalnum() or c in "-_")
    return keep[:24] or DEFAULT_ROOM


def _backup_path(code: str) -> Path:
    return _BACKUP_DIR / f"{code}.json"


def _load_backup(code: str) -> dict | None:
    p = _backup_path(code)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _save_backup(code: str, room: dict) -> None:
    try:
        _BACKUP_DIR.mkdir(exist_ok=True)
        _backup_path(code).write_text(
            json.dumps({
                "pool": [p.__dict__.copy() for p in room["pool"]],
                "teams_locked": room["teams_locked"],
                "created": room["created"],
            }, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass  # read-only FS — in-memory store still holds everything


def _ensure_room(code: str) -> dict:
    """Return the room dict, creating (and restoring from backup) if needed."""
    rooms = _rooms()
    if code not in rooms:
        saved = _load_backup(code)
        if saved:
            rooms[code] = {
                "pool": [Profile(**d) for d in saved.get("pool", [])],
                "teams_locked": saved.get("teams_locked", []),
                "created": saved.get("created", time.time()),
            }
        else:
            rooms[code] = {"pool": [], "teams_locked": [], "created": time.time()}
    return rooms[code]


# ── session wiring ─────────────────────────────────────────────────────────────
def init_state(st) -> None:
    """Set session defaults and pull the current room into session_state.

    Safe to call at the top of every page — it re-syncs each run so a session sees
    joins made by other people.
    """
    ss = st.session_state
    # First load can be seeded from a shareable link, e.g. ?room=MUDAC26 — this
    # is what lets a QR code drop people straight into the right room.
    if "room" not in ss:
        qp_room = None
        try:
            qp_room = st.query_params.get("room")
        except Exception:
            qp_room = None
        ss.room = _clean_code(qp_room) if qp_room else DEFAULT_ROOM
    ss.setdefault("is_organizer", False)
    with _lock():
        room = _ensure_room(ss.room)
        ss.pool = room["pool"]
        ss.teams_locked = room["teams_locked"]


def set_room(st, code: str) -> None:
    st.session_state.room = _clean_code(code)


def room_count(code: str) -> int:
    with _lock():
        return len(_ensure_room(code)["pool"])


# ── mutators (concurrency-safe) ────────────────────────────────────────────────
def add_profile(st, profile: Profile) -> bool:
    """Append a person to the current room. Returns False if the name is taken."""
    code = st.session_state.room
    with _lock():
        room = _ensure_room(code)
        if any(p.name.strip().lower() == profile.name.strip().lower() for p in room["pool"]):
            return False
        room["pool"].append(profile)
        _save_backup(code, room)
    init_state(st)
    return True


def remove_profile(st, pid: str) -> None:
    code = st.session_state.room
    with _lock():
        room = _ensure_room(code)
        room["pool"] = [p for p in room["pool"] if p.id != pid]
        _save_backup(code, room)
    init_state(st)


def add_many(st, profiles: list[Profile]) -> int:
    """Add several profiles (used by demo data); skips name collisions."""
    added = 0
    code = st.session_state.room
    with _lock():
        room = _ensure_room(code)
        have = {p.name.strip().lower() for p in room["pool"]}
        for pr in profiles:
            if pr.name.strip().lower() not in have:
                room["pool"].append(pr)
                have.add(pr.name.strip().lower())
                added += 1
        _save_backup(code, room)
    init_state(st)
    return added


def clear_room(st) -> None:
    code = st.session_state.room
    with _lock():
        room = _ensure_room(code)
        room["pool"] = []
        room["teams_locked"] = []
        _save_backup(code, room)
    init_state(st)


def set_locked(st, teams: list) -> None:
    code = st.session_state.room
    with _lock():
        room = _ensure_room(code)
        room["teams_locked"] = teams
        _save_backup(code, room)
    init_state(st)


# ── organizer gate ─────────────────────────────────────────────────────────────
def _organizer_pass() -> str:
    try:
        return str(st.secrets.get("organizer_pass", "") or "")
    except Exception:
        return ""


def gate_is_on() -> bool:
    """True when a passphrase is configured (i.e. organizer actions are gated)."""
    return bool(_organizer_pass())


def is_organizer(st) -> bool:
    """Anyone may act when no passphrase is set; otherwise must have unlocked."""
    return (not gate_is_on()) or bool(st.session_state.get("is_organizer"))


def try_unlock(st, entered: str) -> bool:
    if entered and entered == _organizer_pass():
        st.session_state.is_organizer = True
        return True
    return False


# ── backup / restore (download & upload the whole room) ────────────────────────
def export_room(st) -> str:
    code = st.session_state.room
    with _lock():
        room = _ensure_room(code)
        return json.dumps({
            "room": code,
            "pool": [p.__dict__.copy() for p in room["pool"]],
            "teams_locked": room["teams_locked"],
            "exported": time.time(),
        }, indent=2)


def import_room(st, raw: bytes | str) -> int:
    """Replace the current room's pool/teams from an exported JSON. Returns count."""
    data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    code = st.session_state.room
    with _lock():
        room = _ensure_room(code)
        room["pool"] = [Profile(**d) for d in data.get("pool", [])]
        room["teams_locked"] = data.get("teams_locked", [])
        _save_backup(code, room)
    init_state(st)
    return len(_ensure_room(code)["pool"])


# ── shared sidebar UI (room code + organizer unlock) ───────────────────────────
def room_sidebar(st) -> None:
    """Render the room selector + organizer unlock in the sidebar on every page."""
    with st.sidebar:
        st.markdown("### 🏷️ Room")
        code = st.text_input(
            "Room code", value=st.session_state.room,
            help="Everyone on the same code shares one pool. Use one code per event, "
                 "e.g. MUDAC26.",
        )
        cleaned = _clean_code(code)
        if cleaned != st.session_state.room:
            st.session_state.room = cleaned
            # Keep the URL in sync so this page stays shareable/bookmarkable.
            try:
                st.query_params["room"] = cleaned
            except Exception:
                pass
            st.rerun()
        st.caption(f"**{room_count(st.session_state.room)}** in room "
                   f"`{st.session_state.room}`")

        st.divider()
        if not gate_is_on():
            st.caption("🔓 Open mode — set `organizer_pass` in Streamlit secrets to "
                       "lock forming/clearing to the organizer.")
        elif st.session_state.get("is_organizer"):
            st.success("🔑 Organizer unlocked")
        else:
            with st.form("org_unlock", clear_on_submit=True):
                pw = st.text_input("Organizer passphrase", type="password")
                if st.form_submit_button("Unlock organizer") and not try_unlock(st, pw):
                    st.error("Wrong passphrase.")
            st.caption("Participants can join without this; only forming/clearing needs it.")


# ── demo data (opt-in only) ─────────────────────────────────────────────────────
def demo_pool() -> list[Profile]:
    """8 fictional people for trying the matching flow. Never loaded automatically."""
    return [
        Profile("p1", "Alex", ["Python / coding", "Data / ML"], ["Pitching / presenting"],
                ["Weekday evenings", "Weekend daytime"], 12, 3),
        Profile("p2", "Sam", ["UI/UX design", "Graphics / branding"], ["Python / coding"],
                ["Weekday evenings", "Weekend daytime"], 8, 3),
        Profile("p3", "Jess", ["Pitching / presenting", "Writing / storytelling"], [],
                ["Weekday evenings", "Weekend daytime"], 6, 2),
        Profile("p4", "Kim", ["Project management", "Market / user research"], [],
                ["Weekday evenings", "Weekend daytime"], 10, 3),
        Profile("p5", "Lee", ["Web / frontend"], ["UI/UX design"],
                ["Weekday mornings", "Weekend daytime"], 5, 1),
        Profile("p6", "Ravi", ["Finance / modeling", "Market / user research"], [],
                ["Weekday mornings", "Weekend daytime"], 7, 2),
        Profile("p7", "Mia", ["Python / coding", "Web / frontend"], ["Data / ML"],
                ["Weekday mornings", "Weekend daytime"], 9, 2),
        Profile("p8", "Tom", ["Graphics / branding"], ["Pitching / presenting"],
                ["Weekend daytime", "Flexible / anytime"], 4, 1),
    ]
