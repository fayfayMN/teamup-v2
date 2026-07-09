"""Join — intake. Good matches depend entirely on what we collect here."""

import streamlit as st

from teamup.store import init_state, save, demo_pool
from teamup.match import Profile, SKILLS, COMMITMENT

st.set_page_config(page_title="Join · TeamUp", page_icon="✍️", layout="wide")
init_state(st)

st.title("✍️ Join the pool")
st.caption("Be honest about availability and commitment — mismatched stakes is the "
           "single biggest silent team killer.")

SLOTS = ["Mon evening", "Tue evening", "Wed evening", "Thu evening",
         "Fri evening", "Sat daytime", "Sun daytime"]

with st.form("join"):
    name = st.text_input("Name")
    skills = st.multiselect("What you're good at (pick your real strengths)", SKILLS)
    learn = st.multiselect("What you want to learn (optional)", SKILLS)

    st.markdown("**When you're available**")
    avail_preset = st.multiselect(
        "Common slots — tick all that apply",
        SLOTS,
        label_visibility="collapsed",
    )
    avail_custom = st.text_input(
        "Other times (optional)",
        placeholder="e.g. Weekday mornings, Fri afternoon, anytime after 9pm",
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
        st.session_state.pool.append(Profile(
            id=pid, name=name, skills=skills, wants_to_learn=learn,
            availability=avail, hours_per_week=hours, commitment=commit,
        ))
        save(st)
        st.success(f"Added {name}. Head to **Match** to form teams.")

st.divider()
st.markdown("#### Current pool")

# Demo / reset controls. A real deployment starts empty — these are opt-in.
bc1, bc2, _ = st.columns([1, 1, 2])
if bc1.button("Load demo data", help="Add 8 sample people to try matching"):
    have = {p.id for p in st.session_state.pool}
    st.session_state.pool.extend(p for p in demo_pool() if p.id not in have)
    save(st)
    st.rerun()
if bc2.button("Clear pool", help="Remove everyone (real and demo)"):
    st.session_state.pool = []
    st.session_state.teams_locked = []
    save(st)
    st.rerun()

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
