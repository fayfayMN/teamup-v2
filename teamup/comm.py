"""Communication style — the deterministic trade-off engine (TeamUp side).

Mirrors ``teamdoctor/comm.py`` so both apps agree on the four styles and the
recommendation rules. TeamUp asks the team type directly (a selectbox), so it
only needs the styles and ``recommend()`` — no current-style detection.

No LLM, no key: every style and recommendation is a transparent rule.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

STYLES: List[Dict] = [
    {"key": "async_channel",
     "name": "Async-first (one shared channel)",
     "speed": "Medium",
     "record": "Strong — written by default",
     "inclusion": "High — everyone sees the same thread",
     "scales": "Excellent",
     "watch_out": "Genuinely urgent calls can wait too long — pair it with a clear "
                  "escalation rule (tag the owner, then call)."},
    {"key": "hybrid",
     "name": "Hybrid (async default + a scheduled sync)",
     "speed": "Balanced",
     "record": "Strong, if you write decisions down",
     "inclusion": "High",
     "scales": "Good",
     "watch_out": "Takes discipline to log what was decided in the sync, not just "
                  "say it out loud and lose it."},
    {"key": "sync_meetings",
     "name": "Sync-heavy (meetings / calls)",
     "speed": "Fast in the room",
     "record": "Weak unless someone takes notes",
     "inclusion": "Only the people present",
     "scales": "Poor",
     "watch_out": "Anyone absent gets bypassed, and decisions evaporate the moment "
                  "the call ends."},
    {"key": "ad_hoc",
     "name": "Ad-hoc / DMs (no single channel)",
     "speed": "Feels fast",
     "record": "None",
     "inclusion": "Fragmented — different people know different things",
     "scales": "Breaks down quickly",
     "watch_out": "This is the #1 way teams quietly fall apart — decisions get made, "
                  "lost, and reversed in private with no trail."},
]

_BY_KEY: Dict[str, Dict] = {s["key"]: s for s in STYLES}

# ── Communication directness ─────────────────────────────────────────────────
# How directly team members express themselves — a cultural/interpersonal layer
# that complements the async/sync channel choice. No recommendation engine here;
# it's a pure preference. The Asana "how people prefer to receive information"
# model (bottom-line-first / big-picture-first / process-first / relationship-first)
# maps loosely onto this spectrum — but for team formation, a simple 3-point
# scale is more actionable than a 4-style matrix.
DIRECTNESS: List[Dict] = [
    {"key": "direct",
     "name": "Direct — say what you mean",
     "detail": "Explicit asks, direct feedback, no reading between the lines. "
               "\"This needs to change.\" \"I disagree because…\" Faster, but can "
               "feel blunt to indirect communicators."},
    {"key": "balanced",
     "name": "Balanced — direct on facts, softer on people",
     "detail": "Clear on deadlines and deliverables; gentler on interpersonal "
               "feedback. \"The deadline moved to Friday. On the approach — have "
               "you considered…?\" Default for most teams."},
    {"key": "indirect",
     "name": "Indirect — suggestions over demands",
     "detail": "Context before conclusion; preserve harmony. \"Have you thought "
               "about…?\" instead of \"Do this.\" Direct communicators may miss "
               "the signal; indirect communicators feel respected."},
]

# Above this head-count, even a small-team default tips toward async-first: more
# people means a meeting can't include everyone and a written channel wins.
SMALL_TEAM_MAX = 6


def style(key: str) -> Dict:
    """Look up a style by key; falls back to hybrid for an unknown key."""
    return _BY_KEY.get(key, _BY_KEY["hybrid"])


def recommend(kind: str, size: int, in_crisis: bool = False) -> Tuple[str, str]:
    """Best-fit style for a team, with a plain-English 'why'. Deterministic;
    adapts to team type, head-count, and whether the team is in flux."""
    if in_crisis:
        return ("hybrid",
                "You're in flux — a short daily sync keeps everyone aligned, but log "
                "every decision in one shared channel so nothing gets reversed in "
                "private while things are moving fast.")
    if kind == "small business":
        return ("hybrid",
                "Shift-based, in-person teams do best with a quick pre-shift huddle "
                "plus one group chat for anything that comes up between shifts.")
    if kind == "startup" or size > SMALL_TEAM_MAX:
        return ("async_channel",
                "A busy or growing team needs an async-first channel that keeps a "
                "written record and doesn't depend on everyone being in the same "
                "meeting at the same time.")
    if kind == "nonprofit":
        return ("async_channel",
                "Part-time volunteers and board members can't all make one meeting — "
                "an async channel with a shared decisions doc keeps everyone included, "
                "with periodic syncs for the big calls.")
    # project team / club / generic / small steady team
    return ("hybrid",
            "A small team runs best async-first with one regular sync — fast enough "
            "to decide, with a written trail so nothing gets lost between meetings.")
