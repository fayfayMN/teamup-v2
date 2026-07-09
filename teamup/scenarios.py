"""Real-world team scenarios — what a team needs differs by what it's FOR.

A hackathon squad, an assigned class group, a two-person startup, and a volunteer
non-profit fail for different reasons and need different roles covered on day one.
Each scenario sets the roles that matter, a sensible size band, the failure mode to
watch, and the stakes framing used when commitment is mismatched.

Deterministic config only — no logic here beyond a lookup. ``kind`` feeds straight
into ``comm.recommend`` so the communication default also adapts.
"""

from __future__ import annotations

from typing import Dict, List

SCENARIOS: List[Dict] = [
    {"key": "competition",
     "label": "Competition / hackathon",
     "kind": "team",
     "required_roles": ["Build", "Design", "Pitch"],
     "ideal_size": (3, 4),
     "top_risk": "Great build, but no one can demo it — or scope creep sinks the deadline.",
     "stakes_note": "the clock is brutal and only a shipped, demoable slice counts,",
     "emphasis": "Name one decider now, cut scope to a slice you can finish, and assign "
                 "the pitch on day one — not the night before."},
    {"key": "coursework",
     "label": "Coursework project",
     "kind": "club",
     "required_roles": ["Build", "Organize", "Pitch"],
     "ideal_size": (3, 5),
     "top_risk": "Free-riders and unfair credit — everyone shares the grade.",
     "stakes_note": "everyone shares one grade, so a coasting member drags the whole team down,",
     "emphasis": "Agree an equal-contribution rule and keep a simple credit log, so the "
                 "grade (and any peer evaluation) reflects who actually did the work."},
    {"key": "small_business",
     "label": "Small business team",
     "kind": "small business",
     "required_roles": ["Build", "Research", "Customer"],
     "ideal_size": (3, 8),
     "top_risk": "The owner does everything and no one else has clear authority.",
     "stakes_note": "real money and real customers are on the line,",
     "emphasis": "Give each area a real owner with decision rights — and make sure money "
                 "(Research/finance) and customers are actually somebody's job, not an afterthought."},
    {"key": "nonprofit",
     "label": "Non-profit / volunteer group",
     "kind": "nonprofit",
     "required_roles": ["Organize", "Customer", "Ops"],
     "ideal_size": (4, 10),
     "top_risk": "Burnout, flaky availability, and knowledge that walks out the door.",
     "stakes_note": "people volunteer their spare time, so an unfair load quietly burns them out,",
     "emphasis": "Keep the load sustainable and async, and write down what each person "
                 "knows (suppliers, logins, contacts) so nothing leaves when they do."},
    {"key": "startup",
     "label": "Startup",
     "kind": "startup",
     "required_roles": ["Build", "Customer", "Ops"],
     "ideal_size": (2, 5),
     "top_risk": "Mismatched commitment and fuzzy founder roles blow up early.",
     "stakes_note": "the intensity is high and equity/ownership is at stake,",
     "emphasis": "Align on commitment and who decides what before you build — and make "
                 "sure someone owns customers/growth, not just the product."},
]

_BY_KEY: Dict[str, Dict] = {s["key"]: s for s in SCENARIOS}
LABELS: List[str] = [s["label"] for s in SCENARIOS]


def get(key: str) -> Dict:
    """Look up a scenario by key; falls back to the coursework/general profile."""
    return _BY_KEY.get(key, _BY_KEY["coursework"])


def by_label(label: str) -> Dict:
    """Look up a scenario by its display label (what the selectbox shows)."""
    for s in SCENARIOS:
        if s["label"] == label:
            return s
    return _BY_KEY["coursework"]
