"""Join — intake. Good matches depend entirely on what we collect here."""

import streamlit as st

from teamup.store import (init_state, room_sidebar, add_profile, add_many,
                          clear_room, remove_profile, is_organizer, demo_pool,
                          get_track, set_track)
from teamup.report import roster_csv
from teamup.match import (Profile, COMMITMENT, AVAILABILITY, TRACKS, TRACK_LABELS,
                          track_key_by_label, skills_for)

st.set_page_config(page_title="Join · TeamUp", page_icon="✍️", layout="wide")
init_state(st)
room_sidebar(st)

st.title("✍️ Join the pool")
st.caption("Be honest about availability and commitment — mismatched stakes is the "
           "single biggest silent team killer.")
st.caption(f"You're joining room **{st.session_state.room}** — everyone on this code "
           "shares one pool.")

# Goal picker — sets which skill list everyone in this room picks from. Stored on
# the room so every participant answers the same tailored question.
cur_track = get_track(st)
cur_label = TRACKS[cur_track]["label"]
goal_label = st.selectbox(
    "What's this team for?  (sets the skills everyone picks from)",
    TRACK_LABELS, index=TRACK_LABELS.index(cur_label),
    help="Pick your event type once — the skill list below adapts to it. "
         "For a data-science competition you'll see EDA, ML, SQL, etc.",
)
goal_key = track_key_by_label(goal_label)
if goal_key != cur_track:
    set_track(st, goal_key)
    st.rerun()
track_skills = skills_for(goal_key)
st.caption(f"Skills below are tailored for **{goal_label}**.")

with st.form("join", clear_on_submit=True):
    name = st.text_input("Name")
    skills = st.multiselect("What you're good at (pick your real strengths)", track_skills)
    learn = st.multiselect("What you want to learn (optional)", track_skills)

    st.markdown("**When you're available** — tick the broad times that fit; no need to be exact")
    avail_preset = st.multiselect(
        "When you're available",
        AVAILABILITY,
        label_visibility="collapsed",
    )
    avail_custom = st.text_input(
        "Anything more specific? (optional)",
        placeholder="e.g. Fri afternoons, anytime after 9pm",
    )

    hours = st.slider("Hours per week you can commit", 1, 40, 8)
    commit = st.select_slider(
        "How serious are you?",
        options=list(COMMITMENT.keys()),
        format_func=lambda k: COMMITMENT[k],
        value=2,
    )
    submitted = st.form_submit_button("Add me to the pool")

if submitted:
    if not name or not skills:
        st.error("Name and at least one skill are required.")
    else:
        # Merge preset ticks + free-text custom slots into one list.
        avail = list(avail_preset)
        if avail_custom.strip():
            avail += [s.strip() for s in avail_custom.split(",") if s.strip()]
        if not avail:
            avail = ["flexible"]

        pid = f"p{len(st.session_state.pool) + 1}_{name.lower().replace(' ', '')}"
        ok = add_profile(st, Profile(
            id=pid, name=name, skills=skills, wants_to_learn=learn,
            availability=avail, hours_per_week=hours, commitment=commit,
        ))
        if ok:
            st.success(f"Added {name} to room {st.session_state.room}. "
                       "Head to **Match** to form teams.")
        else:
            st.warning(f"Someone named **{name}** is already in this room. "
                       "Use a distinct name (add an initial) if that's not you.")

st.divider()
st.markdown("#### Current pool")

# Demo / reset controls. A real deployment starts empty — these are opt-in.
bc1, bc2, _ = st.columns([1, 1, 2])
if bc1.button("Load demo data", help="Add 8 sample people to try matching"):
    add_many(st, demo_pool())
    st.rerun()
if bc2.button("Clear pool", help="Remove everyone (real and demo)"):
    if is_organizer(st):
        clear_room(st)
        st.rerun()
    else:
        st.error("Clearing is organizer-only. Unlock in the sidebar.")

if not st.session_state.pool:
    st.caption("Empty — add real people above, or load demo data to try it out.")
else:
    st.dataframe(
        [{
            "Name": p.name,
            "Roles": ", ".join(sorted(p.roles())) or "—",
            "Available": ", ".join(p.availability),
            "Hrs/wk": p.hours_per_week,
            "Commitment": COMMITMENT[p.commitment],
        } for p in st.session_state.pool],
        use_container_width=True, hide_index=True,
    )

    # Download the roster, and let anyone remove their own (mistaken) entry.
    dl, rm = st.columns([1, 2])
    dl.download_button(
        "⬇️ Download roster (CSV)",
        data=roster_csv(st.session_state.pool),
        file_name=f"teamup-roster-{st.session_state.room}.csv",
        mime="text/csv", use_container_width=True,
    )
    with rm:
        names = {p.name: p.id for p in st.session_state.pool}
        who = st.selectbox("Remove an entry (e.g. a mistake or a no-show)",
                           ["—"] + list(names))
        if who != "—" and st.button(f"Remove {who}"):
            remove_profile(st, names[who])
            st.rerun()
