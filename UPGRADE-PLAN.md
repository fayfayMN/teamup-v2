# Plan: TeamUp v2 — "make the best of the team you have" (new folder)

## Context
TeamUp today only does **pool → auto-split into teams**, shows bare scores with no
explanation, and can't export anything. Feifei's real-world need is the opposite and more
common: on day one you're often **stuck with a fixed group** (an assigned hackathon squad,
a coursework team, the volunteers who showed up) and you want to make it the *best team
possible* — cover the gaps, grow people into missing skills, and set expectations — not
re-pick members. She also wants Team-Doctor-parity **download**, a clear **"why this team /
why these scores,"** and it to work **day one** across competition / coursework / small
business / non-profit / startup.

All work goes in a **new folder so the live demo app is never touched**. This turn delivers
the **plan + folder scaffold only** (copy + design doc); no feature code yet.

## New capability (headline): Fixed-Team Coaching
A new flow: *"We already have a team — make it work."* Enter the N people you're stuck with
(same `Profile` intake), pick a **scenario**, and the app — deterministically, no LLM —:
1. **Analyzes** the fixed roster (role coverage, schedule cohesion, commitment spread) via
   the existing `match.summarize_team` (`teamup/match.py:134`).
2. **Explains every score in plain English** (the missing piece today): *"Covered 3 of 4
   roles — missing Design, nobody listed a design skill." / "Cohesion 55% = any two
   teammates share ~55% of free slots." / "Commitment spread 2 = one 'here to learn' + one
   'here to win'; align early."*
3. **Coaches the limited hand** — the "not much choice" advice:
   - Missing required role → name the **best internal person to grow into it** (prefer
     someone whose `wants_to_learn` matches, else adjacent skill, else least-loaded), with a
     concrete first step + a "skill-up" tip. Recruit only as last resort.
   - Single-point-of-failure role (only one covers it) → assign a backup/pair.
   - Commitment spread → a scenario-tuned **expectations script**.
   - Weak schedule overlap → async norms + one fixed sync.
4. **Assigns roles day-one**: proposes an Accountable owner per required role from the fixed
   roster (best fit even if imperfect; flags **stretch** assignments), so the team leaves
   with clarity, not just a score.
5. **Feeds Kickoff + downloads** a full "Team plan" HTML report (parity with Team Doctor).

The existing **pool → auto-form** flow (`pages/1_Join.py`, `pages/2_Match.py`,
`match.form_teams`) stays intact and gains the same explanations + download.

## Real-world scenarios (day-one) — the brainstorm to verify
Each scenario sets required roles, ideal size, the top risk, and the advice tone. Reuses
`comm.recommend(kind, size)` (`teamup/comm.py`) for the communication default.

| Scenario | Ideal size | Must-cover roles | Top risk | Advice emphasis |
|----------|-----------|------------------|----------|-----------------|
| Competition / hackathon | 3–4 | Build, Design, Pitch | no one can demo/pitch; scope creep | one decider, ship a slice, assign the pitch on day one |
| Coursework project | 3–5 | Build, Organize, Pitch(writing) | free-riders, unfair credit, grade risk | equal-contribution rule, credit log, milestones |
| Small business team | 3–8 | Build/Ops, Finance, Customer | owner does everything; no role clarity | real owners + decision rights; cover money & customer |
| Non-profit / volunteer | 4–10 | Organize, Customer(outreach), Ops | burnout, flaky availability, knowledge loss | sustainable load, async, document knowledge |
| Startup | 2–5 | Build, Customer(growth), Ops | commitment mismatch; founder ambiguity | commitment alignment; who decides; expectations talk |

Role vocabulary extends `SKILL_TO_ROLE` (`teamup/match.py:18`) with two roles the scenarios
need — **Ops** (operations/admin/logistics) and **Customer** (sales/support/outreach) — plus
matching skills on the Join form. `REQUIRED_ROLES` becomes per-scenario, not a global const.

## Files (all inside the new folder `Documents\ClaudeProjects\teamup-v2\`)
- `teamup/scenarios.py` **(new)** — `SCENARIOS` config (label, required_roles, ideal_size,
  top_risks, expectation/credit notes) + `get(kind)`.
- `teamup/match.py` **(extend)** — `assess_fixed_team(team, scenario)`, `coach_team(team,
  scenario)` (gap-fill + skill-growth + role assignment), and `explain_scores()` /
  `why_assigned()` plain-English helpers. Make required-roles/size scenario-driven. Keep
  `form_teams` / `summarize_team` / `pair_score` (already returns `reasons` — surface them).
- `teamup/report.py` **(new)** — `report_html(team(s), scenario, agreement=None)`, mirroring
  Team Doctor's `doctor.report_html` + the `st.download_button` pattern (`team-doctor/app.py:421`).
- `pages/1_Fixed_Team.py` **(new)** — the headline "make our team work" page.
- `pages/2_Match.py` **(extend)** — scenario picker, show explanations + coaching, download.
- `pages/3_Team_Kickoff.py` **(extend)** — scenario defaults, pull assignments, add download.
- `tests/test_match.py` **(extend)** — `coach_team`, scenario required-roles, fixed-team assess.

## Reuse / patterns
- `match.pair_score` already computes **reasons** ("cover different roles", "mentor/learn
  fit") — the explainability groundwork exists; v2 surfaces it instead of hiding it.
- `summarize_team` already returns coverage / cohesion / commitment spread — wrap it in
  `explain_scores()` rather than recomputing.
- `comm.py` `recommend()` already maps team kind → communication style — the scenario `kind`
  feeds straight into it (no duplicate logic).
- Download mirrors Team Doctor exactly: a `report_html()` string → `st.download_button(...,
  mime="text/html")` (`team-doctor/app.py:421`). Same "opens in browser, print to PDF" UX.
- Keep it **LLM-free / key-less** — the whole point is a free, explainable, can't-hallucinate
  team tool.

## This turn's deliverable (scaffold only)
1. Copy `Documents\ClaudeProjects\teamup-v2\` from the live `teamup\` (excluding
   `.git`, `__pycache__`, `teamup_state.json`).
2. Write this plan as `teamup-v2\UPGRADE-PLAN.md` inside it.
3. No feature code, no git, no deploy. Live TeamUp untouched.

## Verification (when built, next turn)
- `python -m py_compile` on new/changed files; `python -m pytest tests/` for match logic.
- `streamlit run app.py` → Fixed-Team page → enter a deliberately gappy 4-person team (no
  designer, one "here to win" + one "here to learn") under each scenario → confirm: the
  missing-role coaching names a real grower, scores have plain-English explanations, role
  assignments appear (stretch flagged), and the **Download** produces a self-contained HTML
  that prints to PDF. Regression: pool → Match → Lock → Kickoff still works.
