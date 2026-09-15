"""Match — propose teams, show role coverage and gaps. Explainable, not magic."""

import streamlit as st

from teamup.store import (init_state, room_sidebar, set_locked, is_organizer,
                          gate_is_on, export_room, import_room, get_track)
from teamup.report import teams_csv
from teamup.match import (form_teams, form_balanced_teams, _team_quality,
                          required_for, TRACKS, COMMITMENT)

st.set_page_config(page_title="Match · TeamUp", page_icon="🧩", layout="wide")
init_state(st)
room_sidebar(st)

st.title("🧩 Match")
st.caption("Teams are formed to cover every role, share schedules, and align on stakes. "
           "The output isn't just a team — it's the team plus its gaps.")

# The room's goal decides which roles a team should cover (set on the Join page).
track = get_track(st)
required = required_for(track)
st.caption(f"🎯 Goal: **{TRACKS[track]['label']}** — teams aim to cover: "
           + ", ".join(required) + ". Change it on the **Join** page.")

# Organizer backup / restore — the durable safety net on an ephemeral host.
with st.expander("🗄️ Organizer: back up / restore this room"):
    st.caption("The live pool survives app restarts via a local backup, but a full "
               "redeploy/sleep can wipe it. Download a copy now; re-upload to restore.")
    st.download_button("⬇️ Download room backup (JSON)", data=export_room(st),
                       file_name=f"teamup-room-{st.session_state.room}.json",
                       mime="application/json")
    up = st.file_uploader("Restore from a backup file", type="json")
    if up is not None and st.button("Restore this room from file"):
        if is_organizer(st):
            n = import_room(st, up.getvalue())
            st.success(f"Restored {n} people into room {st.session_state.room}.")
            st.rerun()
        else:
            st.error("Restore is organizer-only. Unlock in the sidebar.")

n_people = len(st.session_state.pool)
if n_people < 2:
    st.warning("Add at least 2 people on the Join page first.")
    st.stop()

mode = st.radio(
    "How should we split the pool?",
    ["⚖️ Even & balanced — every team about equally strong (best for a class)",
     "🎯 Best-fit — build the strongest teams first"],
    index=0,
)
balanced = mode.startswith("⚖️")

if balanced:
    how = st.radio(
        "How should I decide the number of teams?",
        ["Aim for a team size — adapts to however many actually show up",
         "I know exactly how many teams I want"],
        index=0,
        help="If sign-ups are open-ended, pick a team size and the app makes as many "
             "teams as the final headcount needs — no math on your end.",
    )
    if how.startswith("Aim"):
        per = st.slider("Aim for about this many people per team", 2, 8, 5)
        n_teams = max(1, -(-n_people // per))   # ceil: keeps every team at or below `per`
    else:
        default_teams = min(max(2, round(n_people / 4)), n_people)
        n_teams = int(st.number_input("How many teams?", min_value=1,
                                      max_value=n_people, value=default_teams, step=1))

    base, extra = divmod(n_people, n_teams)
    smallest, largest = base, base + (1 if extra else 0)
    size_desc = f"{smallest}" if smallest == largest else f"{smallest}–{largest}"
    st.caption(f"**{n_people} people in the pool → {n_teams} balanced teams** of "
               f"{size_desc} each. The split re-adapts to whoever's joined — just click "
               "**Form teams** again after the last person is in.")

    separate_div = st.checkbox(
        "Keep divisions separate (Graduate / Undergraduate / Novice each in their own teams)",
        value=False,
        help="On: students only team up with others of their own level, so novices "
             "can compete in the Novice division. Off: mixed teams allowed, and each "
             "team's division is set by its most advanced member.")
else:
    size = st.slider("Target team size", 2, 6, 4)
    st.caption(f"{n_people} people → about {-(-n_people // size)} teams of {size}.")
    separate_div = False

can_form = is_organizer(st)
if not can_form:
    st.info("🔒 Forming/locking teams is organizer-only. Unlock in the sidebar to proceed.")

if st.button("Form teams", type="primary", disabled=not can_form):
    pool = st.session_state.pool
    if balanced and separate_div:
        # Form balanced teams within each level group, then combine.
        groups: dict = {}
        for p in pool:
            groups.setdefault(p.level or "Unspecified", []).append(p)
        result = []
        for lvl, members in groups.items():
            g_teams = max(1, round(int(n_teams) * len(members) / len(pool)))
            result += form_balanced_teams(members, g_teams, required=required)
        st.session_state._teams = result
    elif balanced:
        st.session_state._teams = form_balanced_teams(
            pool, int(n_teams), required=required)
    else:
        st.session_state._teams = form_teams(pool, team_size=size, required=required)

teams = st.session_state.get("_teams")
if not teams:
    st.info("Click **Form teams** to generate matches.")
    st.stop()

# Fairness readout — how close in quality the teams are to each other.
if len(teams) > 1:
    qs = [_team_quality(t["members"], required) for t in teams]
    gap = max(qs) - min(qs)
    fc1, fc2 = st.columns(2)
    fc1.metric("Teams formed", len(teams))
    fc2.metric("Quality gap between teams", f"{gap:.0%}",
               help="0% = every team scored identically. Lower is fairer. "
                    "The Even & balanced mode keeps this small.")
    if gap <= 0.12:
        st.success("✅ Well balanced — the strongest and weakest teams are very close in quality.")
    elif gap <= 0.25:
        st.info("Reasonably balanced. For an even fairer split, use **Even & balanced** mode above.")
    else:
        st.warning("⚠️ Uneven — some teams are much stronger than others. "
                   "Switch to **Even & balanced** mode and re-form for fairer teams.")

# Deterministic rules check — no AI needed; these are all checkable facts.
with st.expander("📋 Competition rules check", expanded=True):
    from collections import Counter
    oversize = [i + 1 for i, t in enumerate(teams) if t["size"] > 5]
    if oversize:
        st.error(f"⚠️ Over the 5-student limit: Team(s) {oversize}. "
                 "Set 'aim for a team size' = 5 (or add teams) and re-form.")
    else:
        st.success("✅ Every team has 5 or fewer students (competition limit).")
    st.markdown("- **One team per student** — guaranteed; each person is on exactly one team.")
    st.markdown("- **Faculty/staff advisor** — required per team. The app matches *students*; "
                "attach one advisor to each team below (they register separately).")
    divs = Counter(t["division"] for t in teams)
    st.markdown("- **Divisions** (auto-set by each team's most advanced student): "
                + ", ".join(f"**{n}** {d}" for d, n in divs.items()))
    if any(t["majors"] for t in teams):
        single = [i + 1 for i, t in enumerate(teams) if len(t["majors"]) == 1]
        st.markdown("- **Blended majors** are encouraged — "
                    + (f"single-major team(s): {single}." if single
                       else "every team already mixes majors. ✅"))
    else:
        st.caption("Tip: collect **major** on the Join page and the balancer will also "
                   "mix majors (blended teams are encouraged).")

for i, t in enumerate(teams, 1):
    with st.container(border=True):
        names = ", ".join(m.name for m in t["members"])
        st.markdown(f"#### Team {i} — {names}")

        meta = f"👥 {t['size']} students · 🏅 {t['division']} division"
        if t["majors"]:
            meta += " · 🎓 " + ", ".join(t["majors"])
        st.caption(meta)
        if t["size"] > 5:
            st.error("⚠️ Over the 5-student competition limit — drop or move one member.")

        cols = st.columns(3)
        cols[0].metric("Schedule cohesion", f"{t['schedule_cohesion']:.0%}")
        cols[1].metric("Avg commitment", f"{t['avg_commitment']}/3")
        cols[2].metric("Covered roles",
                       f"{len(required) - len(t['missing_roles'])}/{len(required)}")

        st.markdown("**Covered:** " + (", ".join(t["covered_roles"]) or "—"))

        if t["missing_roles"]:
            st.error("⚠️ **Gap — missing role(s): " + ", ".join(t["missing_roles"])
                     + ".** Designate someone to cover it, or recruit one more person.")
        else:
            st.success("✅ All core roles covered.")

        if t["commitment_spread"] >= 2:
            st.warning("⚠️ Mixed stakes: this team has both '"
                       + COMMITMENT[1].lower() + "' and '" + COMMITMENT[3].lower()
                       + "' members. Talk about expectations at kickoff.")

        if t["schedule_cohesion"] < 0.25:
            st.warning("⚠️ Weak schedule overlap — agree on async working norms early.")

        with st.expander("Members"):
            for m in t["members"]:
                extra = " · ".join(x for x in [
                    getattr(m, "level", ""), getattr(m, "major", ""),
                    getattr(m, "school", "")] if x)
                line = (f"- **{m.name}** — {', '.join(sorted(m.roles())) or 'no role tags'} "
                        f"· {COMMITMENT[m.commitment]} · {', '.join(m.availability)}")
                if extra:
                    line += f"  \n  <small>{extra}</small>"
                st.markdown(line, unsafe_allow_html=True)

# Download the proposed teams so the organizer can share them anywhere.
st.download_button(
    "⬇️ Download teams (CSV)", data=teams_csv(teams),
    file_name=f"teamup-teams-{st.session_state.room}.csv", mime="text/csv",
)

if st.button("Lock these teams", disabled=not can_form):
    set_locked(st, [[m.name for m in t["members"]] for t in teams])
    st.success("Teams locked. Each team should run the Team Kickoff next.")
