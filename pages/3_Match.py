"""Match — propose teams, show role coverage and gaps. Explainable, not magic."""

import streamlit as st

from teamup.store import (init_state, room_sidebar, set_locked, is_organizer,
                          gate_is_on, export_room, import_room)
from teamup.report import teams_csv
from teamup.match import form_teams, REQUIRED_ROLES, COMMITMENT

st.set_page_config(page_title="Match · TeamUp", page_icon="🧩", layout="wide")
init_state(st)
room_sidebar(st)

st.title("🧩 Match")
st.caption("Teams are formed to cover every role, share schedules, and align on stakes. "
           "The output isn't just a team — it's the team plus its gaps.")

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

size = st.slider("Target team size", 2, 6, 4)

if len(st.session_state.pool) < 2:
    st.warning("Add at least 2 people on the Join page first.")
    st.stop()

can_form = is_organizer(st)
if not can_form:
    st.info("🔒 Forming/locking teams is organizer-only. Unlock in the sidebar to proceed.")

if st.button("Form teams", type="primary", disabled=not can_form):
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

# Download the proposed teams so the organizer can share them anywhere.
st.download_button(
    "⬇️ Download teams (CSV)", data=teams_csv(teams),
    file_name=f"teamup-teams-{st.session_state.room}.csv", mime="text/csv",
)

if st.button("Lock these teams", disabled=not can_form):
    set_locked(st, [[m.name for m in t["members"]] for t in teams])
    st.success("Teams locked. Each team should run the Team Kickoff next.")
