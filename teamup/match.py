"""Team matching — pure-Python, deterministic, explainable. No API, no ML.

Matching is a scoring problem, not a generation problem. A weighted score is
free, instant, and explainable to users ("you matched because…"), and it can't
hallucinate. We deliberately avoid an LLM here.

A healthy team needs role *coverage*, *availability overlap*, and *aligned
stakes*. Optimal partitioning is NP-hard, so we form teams greedily — seed with
the least-flexible candidates, then add whoever maximizes marginal fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from teamup.comm import recommend as comm_recommend

# Each pickable skill maps to the team role it covers.
SKILL_TO_ROLE: Dict[str, str] = {
    "Python / coding": "Build",
    "Web / frontend": "Build",
    "Data / ML": "Build",
    "UI/UX design": "Design",
    "Graphics / branding": "Design",
    "Pitching / presenting": "Pitch",
    "Writing / storytelling": "Pitch",
    "Market / user research": "Research",
    "Finance / modeling": "Research",
    "Project management": "Organize",
    "Operations / logistics": "Ops",
    "Sales / customer support": "Customer",
    "Community / outreach": "Customer",
}

SKILLS = list(SKILL_TO_ROLE)

# Plain-English gloss for each role — used in explanations and "how to grow into it" tips.
ROLE_LABEL: Dict[str, str] = {
    "Build": "building the thing (code / product)",
    "Design": "design & user experience",
    "Pitch": "presenting, writing & storytelling",
    "Research": "research, finance & analysis",
    "Organize": "project management & keeping things on track",
    "Ops": "operations, logistics & admin",
    "Customer": "customers, sales & outreach",
}

# One concrete first step for a member stretching into a role they don't yet hold.
ROLE_GROWTH: Dict[str, str] = {
    "Build": "pair with any builder for the first week; own one small component end-to-end.",
    "Design": "start from a free template (Figma/Canva); copy a layout you like before inventing one.",
    "Pitch": "write the one-paragraph 'what we do' first; rehearse the 60-second version out loud twice.",
    "Research": "list your 5 riskiest assumptions and go find one data point for each this week.",
    "Organize": "put every task in one shared list with an owner and a date; run a 15-min weekly check-in.",
    "Ops": "make one checklist for the recurring work; who does what, and by when.",
    "Customer": "talk to 3 real users/customers this week and write down their exact words.",
}

# A generic team without one of these is structurally weak. Scenarios override this
# with their own required set (see teamup/scenarios.py).
REQUIRED_ROLES = ["Build", "Design", "Pitch", "Organize"]

# Commitment is the #1 silent team killer when mismatched.
COMMITMENT = {1: "Here to learn", 2: "Will contribute", 3: "Here to win"}


@dataclass
class Profile:
    id: str
    name: str
    skills: List[str] = field(default_factory=list)         # subset of SKILLS
    wants_to_learn: List[str] = field(default_factory=list)
    availability: List[str] = field(default_factory=list)   # e.g. ["mon-eve", "sat-day"]
    hours_per_week: int = 5
    commitment: int = 2                                     # 1-3, see COMMITMENT

    def roles(self) -> set:
        return {SKILL_TO_ROLE[s] for s in self.skills if s in SKILL_TO_ROLE}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def pair_score(a: Profile, b: Profile) -> Dict:
    """Transparent 0-1 compatibility between two people, with reasons."""
    reasons = []

    # Complementary skills: reward different roles, not duplicates.
    overlap = a.roles() & b.roles()
    union = a.roles() | b.roles()
    complement = 1 - (len(overlap) / len(union)) if union else 0.0
    if complement > 0.5:
        reasons.append("cover different roles")
    elif overlap:
        reasons.append("overlapping skills (some redundancy)")

    # Availability overlap is a near-hard requirement.
    avail = _jaccard(set(a.availability), set(b.availability))
    if avail == 0:
        reasons.append("no shared availability")
    elif avail > 0.4:
        reasons.append("strong schedule overlap")

    # Commitment closeness — mismatched stakes wreck teams.
    commit = 1 - abs(a.commitment - b.commitment) / 2
    if a.commitment == b.commitment:
        reasons.append(f"both '{COMMITMENT[a.commitment].lower()}'")
    elif abs(a.commitment - b.commitment) == 2:
        reasons.append("mismatched stakes")

    # Teach/learn synergy: someone can teach what the other wants to learn.
    synergy = 0.0
    if set(a.wants_to_learn) & set(b.skills) or set(b.wants_to_learn) & set(a.skills):
        synergy = 1.0
        reasons.append("mentor/learn fit")

    score = 0.40 * complement + 0.30 * avail + 0.20 * commit + 0.10 * synergy
    return {"score": round(score, 3), "reasons": reasons}


def _marginal_fit(team: List[Profile], cand: Profile) -> float:
    """How much does this candidate improve the team if added?"""
    if not team:
        return 0.0

    team_roles = set().union(*(m.roles() for m in team))
    new_roles = cand.roles() - team_roles
    role_gain = len(new_roles & set(REQUIRED_ROLES)) / len(REQUIRED_ROLES)

    avail = max(_jaccard(set(cand.availability), set(m.availability)) for m in team)
    avg_commit = sum(m.commitment for m in team) / len(team)
    commit = 1 - abs(cand.commitment - avg_commit) / 2

    return 0.45 * role_gain + 0.30 * avail + 0.25 * commit


def form_teams(pool: List[Profile], team_size: int = 4) -> List[Dict]:
    """Greedily partition the pool into teams, maximizing role coverage,
    schedule overlap, and aligned commitment."""
    remaining = list(pool)
    # Seed with the least flexible (fewest roles, narrowest schedule) so they
    # aren't left as awkward leftovers at the end.
    remaining.sort(key=lambda p: (len(p.roles()), len(p.availability)))

    teams: List[List[Profile]] = []
    while remaining:
        seed = remaining.pop(0)
        team = [seed]
        while len(team) < team_size and remaining:
            best = max(remaining, key=lambda c: _marginal_fit(team, c))
            team.append(best)
            remaining.remove(best)
        teams.append(team)

    return [summarize_team(t) for t in teams]


def summarize_team(team: List[Profile], required: List[str] = None) -> Dict:
    required = required or REQUIRED_ROLES
    covered = set().union(*(m.roles() for m in team)) if team else set()
    missing = [r for r in required if r not in covered]

    # Pairwise availability overlap as a rough cohesion signal.
    overlaps = [
        _jaccard(set(a.availability), set(b.availability))
        for i, a in enumerate(team) for b in team[i + 1:]
    ]
    cohesion = round(sum(overlaps) / len(overlaps), 2) if overlaps else 1.0

    commits = [m.commitment for m in team]
    return {
        "members": team,
        "covered_roles": sorted(covered),
        "missing_roles": missing,
        "schedule_cohesion": cohesion,
        "commitment_spread": max(commits) - min(commits) if commits else 0,
        "avg_commitment": round(sum(commits) / len(commits), 1) if commits else 0,
    }


# ── Fixed-team coaching ────────────────────────────────────────────────────────
# You can't always pick your teammates — an assigned class group, the hackathon
# squad you landed in, the volunteers who showed up. These functions take the team
# you HAVE and make it the best it can be: explain the scores in plain English,
# assign owners (flagging stretch picks), and coach the gaps. All deterministic.

def _holders(team: List[Profile], role: str) -> List[Profile]:
    return [m for m in team if role in m.roles()]


def _wants_role(m: Profile, role: str) -> bool:
    return any(SKILL_TO_ROLE.get(s) == role for s in m.wants_to_learn)


def assign_roles(team: List[Profile], required: List[str]) -> List[Dict]:
    """Give every required role an Accountable owner from the roster we have.

    A real owner where someone holds the skill; otherwise the best person to
    *stretch* into it (prefers whoever wants to learn it, else the least-loaded);
    otherwise nobody — a genuine recruit gap. Load is balanced so one person
    doesn't silently end up owning everything.
    """
    load: Dict[str, int] = {m.id: 0 for m in team}
    out: List[Dict] = []
    for role in required:
        holders = _holders(team, role)
        if holders:
            owner = min(holders, key=lambda m: load[m.id])
            load[owner.id] += 1
            out.append({"role": role, "owner": owner.name, "stretch": False,
                        "why": f"{owner.name} covers {ROLE_LABEL[role]}."})
            continue
        # No one holds it — find the best stretch owner.
        eager = [m for m in team if _wants_role(m, role)]
        pool = eager or team
        if pool:
            owner = min(pool, key=lambda m: load[m.id])
            load[owner.id] += 1
            reason = ("wanted to learn it" if eager else "has the most room to take it on")
            out.append({"role": role, "owner": owner.name, "stretch": True,
                        "why": f"Nobody holds {role} yet — {owner.name} takes it as a "
                               f"stretch ({reason}). First step: {ROLE_GROWTH[role]}"})
        else:
            out.append({"role": role, "owner": None, "stretch": False,
                        "why": f"No one can cover {role}. Recruit one person, or "
                               f"drop scope that needs it."})
    return out


def explain_scores(summary: Dict, required: List[str]) -> List[str]:
    """Turn the raw numbers into plain-English sentences a first-timer understands."""
    lines: List[str] = []
    n = len(required)
    covered_req = [r for r in required if r in summary["covered_roles"]]
    miss = summary["missing_roles"]
    cov = f"Role coverage: {len(covered_req)} of {n} needed roles covered."
    if miss:
        cov += (" Missing " + ", ".join(miss)
                + f" — nobody listed a skill for {', '.join(ROLE_LABEL[r] for r in miss)}.")
    else:
        cov += " Every role this kind of team needs has someone on it. ✅"
    lines.append(cov)

    pct = round(summary["schedule_cohesion"] * 100)
    coh = (f"Schedule fit: {pct}% — on average, any two teammates share about {pct}% "
           "of their free time slots.")
    if pct < 25:
        coh += " That's low: plan to work mostly async, with one fixed time you all protect."
    elif pct >= 60:
        coh += " That's strong — real-time work will be easy."
    lines.append(coh)

    avg, spread = summary["avg_commitment"], summary["commitment_spread"]
    com = f"Commitment: average {avg}/3 across the team, spread of {spread}."
    if spread >= 2:
        com += (" You have both a 'here to learn' and a 'here to win' member — that "
                "gap sinks teams silently, so agree on expectations out loud on day one.")
    else:
        com += " Everyone's roughly aligned on how hard they'll push. ✅"
    lines.append(com)
    return lines


def coach_team(team: List[Profile], scenario: Dict) -> Dict:
    """The full 'make the best of this team' read: assignments + gap advice."""
    required = scenario["required_roles"]
    summary = summarize_team(team, required)
    assignments = assign_roles(team, required)
    advice: List[Dict] = []

    # 1. Missing roles → who grows into them (the assignment already picked a
    #    stretch owner; surface it as advice with the concrete step).
    for a in assignments:
        if a["owner"] is None:
            advice.append({"sev": "high", "title": f"No one covers {a['role']}",
                           "body": a["why"]})
        elif a["stretch"]:
            advice.append({"sev": "med",
                           "title": f"{a['role']} is a stretch for {a['owner']}",
                           "body": a["why"]})

    # 2. Single point of failure: exactly one person holds a required role.
    for role in required:
        h = _holders(team, role)
        if len(h) == 1 and role in summary["covered_roles"]:
            advice.append({"sev": "med", "title": f"Only {h[0].name} covers {role}",
                           "body": f"If {h[0].name} disappears, {role} is uncovered. Have "
                                   f"one teammate shadow them so it isn't a single point "
                                   "of failure."})

    # 3. Commitment mismatch → expectation-setting, tuned to the scenario stakes.
    if summary["commitment_spread"] >= 2:
        advice.append({"sev": "high", "title": "Mismatched stakes",
                       "body": "Someone is 'here to learn' and someone is 'here to win.' "
                               f"For a {scenario['label'].lower()}, {scenario['stakes_note']} "
                               "Say out loud who wants what — before the first deadline."})

    # 4. Weak schedule → async norms.
    if summary["schedule_cohesion"] < 0.25:
        advice.append({"sev": "med", "title": "Little shared time",
                       "body": "Your calendars barely overlap. Pick ONE weekly time you all "
                               "protect, and do everything else in writing so no one's blocked."})

    # 5. Size vs the scenario's ideal band.
    lo, hi = scenario["ideal_size"]
    size = len(team)
    size_note = None
    if size < lo:
        size_note = (f"You're {size}; a {scenario['label'].lower()} usually needs {lo}–{hi}. "
                     "Expect everyone to wear two hats — the assignments above already double up.")
    elif size > hi:
        size_note = (f"You're {size}; more than the {lo}–{hi} a {scenario['label'].lower()} "
                     "usually needs. Split into sub-owners so people aren't idle.")

    comm_key, comm_why = comm_recommend(scenario["kind"], size)
    return {
        "summary": summary,
        "explanations": explain_scores(summary, required),
        "assignments": assignments,
        "advice": advice,
        "size_note": size_note,
        "comm": {"style": comm_key, "why": comm_why},
    }
