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
}

SKILLS = list(SKILL_TO_ROLE)

# A team without one of these is structurally weak (see the kickoff cheatsheet).
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


def summarize_team(team: List[Profile]) -> Dict:
    covered = set().union(*(m.roles() for m in team)) if team else set()
    missing = [r for r in REQUIRED_ROLES if r not in covered]

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
