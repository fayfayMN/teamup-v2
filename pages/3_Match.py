"""Match — propose teams, show role coverage and gaps. Explainable, not magic."""

import streamlit as st

from teamup.store import init_state, save
from teamup.match import form_teams, REQUIRED_ROLES, COMMITMENT

st.set_page_config(page_title="Match · TeamUp", page_icon="🧩", layout="wide")
init_state(st)

st.title("🧩 Match")
st.caption("Teams are formed to cover every role, share schedules, and align on stakes. "
           "The output isn't just a team — it's the team plus its gaps.")

size = st.slider("Target team size", 2, 6, 4)

if len(st.session_state.pool) < 2:
    st.warning("Add at least 2 people on the Join page first.")
    st.stop()

if st.button("Form teams", type="primary"):
    st.session_state._teams = form_teams(st.session_state.pool, team_size=size)

teams = st.session_state.get("_teams")
if not teams:
    st.info("Click **Form teams** to generate matches.")
    st.stop()

for i, t in enumerate(teams, 1):
    with st.container(border=True):
        names = ", ".join(m.name for m in t["members"])
        st.markdown(f"#### Team {i} — {names}")

        cols = st.columns(3)
        cols[0].metric("Schedule cohesion", f"{t['schedule_cohesion']:.0%}")
        cols[1].metric("Avg commitment", f"{t['avg_commitment']}/3")
        cols[2].metric("Covered roles", f"{len(t['covered_roles'])}/{len(REQUIRED_ROLES)}")

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
                st.write(f"- **{m.name}** — {', '.join(sorted(m.roles())) or 'no role tags'} "
                         f"· {COMMITMENT[m.commitment]} · {', '.join(m.availability)}")

if st.button("Lock these teams"):
    st.session_state.teams_locked = [
        [m.name for m in t["members"]] for t in teams
    ]
    save(st)
    st.success("Teams locked. Each team should run the Team Kickoff next.")
