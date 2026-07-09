# TeamUp — product plan

## One-line

Form healthy teams for high-stakes competitions and projects, keep them healthy
while they work, and turn the result into verified proof of contribution.

## The product loop

```
  TeamUp            Clearwork           Resume card
 (this app)   →    (separate app)   →   (in Clearwork)
  FORM the          TRACK who did        PROOF of work,
  team well         what, fairly         verified by team
       ↑                                       │
       └───────── reputation flows back ───────┘
```

- **TeamUp** = *prevention*. Match on complementary skills, shared availability,
  aligned commitment; then a guided kickoff produces a working agreement.
- **Clearwork** = *detection + record*. Hours-weighted contribution scores,
  free-rider signals, blocker-flag escalation that routes around a gatekeeper,
  immutable record of who decided what.
- **Verified resume card** = *payoff*. Locked facts from the record + the
  member's own narrative. People tolerate being measured if they get something
  back — and the card becomes a trust signal for the next match.

## Why no LLM / no paid API

Matching is a scoring problem, not a generation problem. A weighted score is:
- **free** — pure Python, no key, no quota
- **instant** — no network round-trip
- **explainable** — "you matched because you cover different roles and share Saturdays"
- **safe** — can't hallucinate a teammate or a skill

An LLM is reserved for a far-future nicety (e.g. "draft an intro message"), never
the matching itself.

## Free tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| App / UI | Streamlit (multipage) | Already in use for Clearwork; fits the 3 phases |
| Data | JSON file now → SQLite later | Zero deps; survives restarts |
| Matching | pure Python + stdlib | Deterministic, explainable, free |
| Optional NLP later | `sentence-transformers` (local) | Free, no key, only if free-text matching is wanted |
| Auth (v1) | email-code or `st.login` | Skip OAuth complexity until needed |
| Hosting | Streamlit Community Cloud | Free, deploys from GitHub |

## Matching model (current)

A healthy team needs **role coverage**, **schedule overlap**, and **aligned stakes**.

- Skills map to roles: Build / Design / Pitch / Research / Organize.
- `REQUIRED_ROLES = Build, Design, Pitch, Organize` — a team missing one is flagged.
- `pair_score` — transparent 0-1 compatibility with human-readable reasons.
- `form_teams` — greedy partition (optimal is NP-hard): seed with the least
  flexible people, then add whoever maximizes marginal fit (role gain + schedule
  overlap + commitment closeness).
- Output is the team **plus its gaps** ("missing a presenter — recruit or assign").

## Roadmap

**v1 (done — this scaffold)**
- Intake, weighted matching, team formation with gap detection, kickoff →
  working agreement.

**v2**
- SQLite store + simple auth.
- "Looking for one more" board for 3/4-formed teams needing a specific role.
- Anonymous mid-point pulse check (surfaces a quiet free-rider before the deadline).

**v3 — integration with Clearwork**
- Lock a team → spin up a Clearwork workspace for it.
- Post-competition peer ratings → reputation score.
- Verified resume card's "verified" badge feeds back as a match input.

**v4 — polish**
- Optional local NLP matching on free-text interests.
- Optional LLM-drafted intro messages (the only place an LLM earns its keep).

## Risks / decisions to make

- **Trust of self-reported skills.** Mitigated over time by reputation flowing
  back from Clearwork records.
- **Greedy ≠ optimal.** Fine for a prototype and explainable; revisit only if
  users report bad partitions at scale.
- **Privacy of pulse checks.** Must be genuinely anonymous or people won't be honest.
