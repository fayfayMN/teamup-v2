"""TeamUp — Streamlit app entry (Home).

Match strangers into healthy competition/project teams, then hand off to
Clearwork for contribution tracking and verified resume cards.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st

from teamup.store import init_state
from teamup.match import REQUIRED_ROLES, COMMITMENT

st.set_page_config(page_title="TeamUp", page_icon="🤝", layout="wide")
init_state(st)

st.title("🤝 TeamUp")
st.caption("Form healthy teams for high-stakes competitions and projects — matched on "
           "complementary skills, shared availability, and aligned commitment. Then a "
           "guided kickoff sets the team up to actually work well.")

c1, c2, c3 = st.columns(3)
c1.metric("People in pool", len(st.session_state.pool))
c2.metric("Roles a team needs", len(REQUIRED_ROLES))
c3.metric("Teams locked", len(st.session_state.get("teams_locked", [])))

st.info("Matching is deterministic and explainable — no API key, no cost. "
        "Data persists to `teamup_state.json`.", icon="🔒")

st.divider()
st.markdown(
    "#### How it works\n"
    "1. **Join** — add your skills, availability, and how serious you are\n"
    "2. **Match** — see proposed teams, the roles they cover, and any gaps\n"
    "3. **Team Kickoff** — generate a working agreement and 30-minute launch plan\n"
)

st.markdown("#### The product loop")
st.markdown(
    "- **TeamUp (this app)** — *form* healthy teams (prevention)\n"
    "- **Clearwork** — *track* who did what, fairly (detection + record)\n"
    "- **Verified resume cards** — proof of contribution flows back as a trust "
    "signal into the next match\n"
)

st.caption("Commitment levels: " + " · ".join(f"{k}={v}" for k, v in COMMITMENT.items()))
