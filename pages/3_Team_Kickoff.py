"""Team Kickoff — the differentiator. A guided 30-minute launch that outputs a
working agreement. This is where most matching tools stop and most teams fail."""

from datetime import date, timedelta

import streamlit as st

from teamup.comm import STYLES as COMM_STYLES, DIRECTNESS, recommend, style as comm_style
from teamup.store import init_state

st.set_page_config(page_title="Team Kickoff · TeamUp", page_icon="🚀", layout="wide")
init_state(st)

st.title("🚀 Team Kickoff")
st.caption("Spend the first 30 minutes on people, not ideas. This produces a working "
           "agreement the whole team signs off on — your defense against free riders "
           "and credit-takers later.")

# One-click demo fill: populates the team name + domain owners so you can show a
# complete working agreement instantly. (The rules below come pre-filled already.)
_EXAMPLE = {
    "kick_team": "HackMAC 2026",
    "own_Build": "Mia", "own_Design": "Sam", "own_Pitch": "Jess",
    "own_Organize": "Kim", "own_Integrator (watches the whole picture)": "Alex",
}
if st.button("✨ Fill with an example team"):
    for _k, _v in _EXAMPLE.items():
        st.session_state[_k] = _v
    st.rerun()

team_name = st.text_input("Team / project name", key="kick_team",
                          placeholder="e.g. HackMAC 2026")

st.markdown("#### 1. Domain owners (one per area — not a leader for everything)")
ROLES = ["Build", "Design", "Pitch", "Organize", "Integrator (watches the whole picture)"]
owners = {}
for r in ROLES:
    owners[r] = st.text_input(r, key=f"own_{r}", placeholder="who owns this?")

st.markdown("#### 2. Decision rule")
decision = st.text_input(
    "When stuck, how do we decide?",
    value="The domain owner decides after 10 minutes of disagreement, and we move on.",
)

st.markdown("#### 2a. Scope & approval boundaries")
st.caption("Who decides alone vs. what needs the group — so no one person becomes the "
           "sole gatekeeper.")
boundaries = st.text_input(
    "Our boundary rule:",
    value="Owners decide within their area. Anything public-facing, team-branded, or "
          "cross-area needs a quick group sign-off — no single gatekeeper.",
)

st.markdown("#### 2b. Change & review window")
st.caption("Stops work being reversed or wiped on a whim.")
change_rule = st.text_input(
    "How do we change a decision already made?",
    value="A logged proposal gets a 48-hour written review window before it locks. "
          "Changing it needs a written counter-proposal, not a verbal override.",
)

st.markdown("#### 3. Check-ins")
checkins = st.text_input("When do we sync?",
                         value="At the midpoint and 2 hours before the deadline.")

st.markdown("#### 4. Communication style")
st.caption("How a team communicates is the #1 thing it never agrees on until it's "
           "already a problem. Pick your team type and size, and we'll recommend the "
           "style that fits — and show what each one costs.")

# Team type drives the recommendation (so it adapts, instead of assuming a project team).
_KIND_LABELS = {
    "Project / hackathon team": "team",
    "Club / student org": "club",
    "Startup": "startup",
    "Nonprofit / volunteer group": "nonprofit",
    "Small business": "small business",
}
kind_label = st.selectbox("What kind of team is this?", list(_KIND_LABELS.keys()))
kind = _KIND_LABELS[kind_label]

# Size = how many owners are actually filled in above.
team_size = sum(1 for who in owners.values() if (who or "").strip()) or 1

rec_key, why = recommend(kind, team_size)
rec_style = comm_style(rec_key)
st.info(f"**Recommended for a {kind_label.lower()} of {team_size}: "
        f"{rec_style['name']}** — {why}")

# Let them choose (defaulting to the recommendation) and see what they picked costs.
_names = [s["name"] for s in COMM_STYLES]
_default_idx = next(i for i, s in enumerate(COMM_STYLES) if s["key"] == rec_key)
chosen_name = st.radio("Our communication style:", _names, index=_default_idx)
chosen = next(s for s in COMM_STYLES if s["name"] == chosen_name)
st.caption(f"⚖️ **Trade-offs:** speed {chosen['speed'].lower()} · record: "
           f"{chosen['record'].lower()} · scales: {chosen['scales'].lower()}. "
           f"**Watch out:** {chosen['watch_out']}")
if chosen["key"] != rec_key:
    st.warning(f"You picked **{chosen['name']}**, but for this team we'd suggest "
               f"**{rec_style['name']}**. That's fine — just go in with eyes open about "
               "the trade-off above.")

with st.expander("📊 Compare all 4 styles"):
    st.table([
        {"Style": s["name"], "Speed": s["speed"], "Leaves a record": s["record"],
         "Who's included": s["inclusion"], "Scales": s["scales"]}
        for s in COMM_STYLES
    ])

# ── Directness: interpersonal layer under the channel choice ──────────────
st.markdown("#### 4a. Communication directness")
st.caption("Same channel, different tone. Agreeing on how directly people speak "
           "prevents the #1 interpersonal friction: one person thinks they're being "
           "clear, the other thinks they're being rude (or vague).")
_d_names = [d["name"] for d in DIRECTNESS]
chosen_directness_name = st.radio(
    "How directly do we speak to each other?",
    _d_names, index=1,  # default: Balanced
    help="Direct = explicit asks and feedback. Indirect = suggestions and context "
         "before conclusions. Balanced = direct on facts, softer on people.")
chosen_directness = next(d for d in DIRECTNESS if d["name"] == chosen_directness_name)
st.caption(chosen_directness["detail"])

channel_tool = st.text_input(
    "Which channel/tool do we use, concretely?",
    value="One shared Slack/Discord/group chat for all team business — no side DMs "
          "for decisions. Respond within 24 hours or flag you're blocked.",
)
escalation = st.text_input(
    "When something is stuck or urgent, what do we do?",
    value="Tag the domain owner directly. If no response in 24 hours, the integrator "
          "steps in. Anything time-sensitive gets a call, not a message.",
)

st.markdown("#### 5. If someone goes quiet")
quiet = st.text_input(
    "Our rule:",
    value="We ask what's blocking them directly — coasting is often being lost. "
          "We don't silently do their work, and we loop in the organizer early.",
)

st.markdown("#### 6. Credit")
credit = st.text_input(
    "How is credit handled?",
    value="Each person presents the part they built. Contributions are recorded in "
          "Clearwork so the record is immutable.",
)

st.markdown("#### 7. Review date")
st.caption("Put it on the calendar so the agreement stays current.")
review_by = st.date_input("Revisit this whole agreement by:",
                          value=date.today() + timedelta(days=90))

st.divider()
if st.button("Generate working agreement", type="primary"):
    lines = [f"# Working agreement — {team_name or 'our team'}", ""]
    lines.append("## Domain owners")
    for r, who in owners.items():
        lines.append(f"- **{r}:** {who or '_unassigned — assign before starting_'}")
    lines += [
        "",
        f"## How we decide\n{decision}",
        f"\n## Scope & approval boundaries\n{boundaries}",
        f"\n## Change & review window\n{change_rule}",
        f"\n## Check-ins\n{checkins}",
        f"\n## Communication style\n**{chosen['name']}.** {channel_tool}\n\n"
        f"_Directness: {chosen_directness['name'].lower()}. {chosen_directness['detail']}_\n\n"
        f"_Trade-off: record {chosen['record'].lower()}; scales {chosen['scales'].lower()}. "
        f"Watch out — {chosen['watch_out']}_"
        + ("" if chosen["key"] == rec_key else
           f"\n\n_(Recommended for a {kind_label.lower()} of {team_size}: "
           f"{rec_style['name']} — {why})_"),
        f"\n## Escalation\n{escalation}",
        f"\n## If someone goes quiet\n{quiet}",
        f"\n## Credit\n{credit}",
        "",
        "## Decision log (start here)",
        "Write one line every time you decide something — this is what stops silent "
        "reversals and lost credit.",
        "",
        "| Date | Decision | Owner | Approved by | Shared on |",
        "|------|----------|-------|-------------|-----------|",
        "| _(example)_ | the decision you made | (owner) | (who signed off) | (where you shared it) |",
        "|  |  |  |  |  |",
        "",
        f"## 📅 Review by\nRevisit this whole agreement by **{review_by}** so it "
        "stays current.",
        "",
        "_Agreed by all members at kickoff. Revisit at the midpoint check-in and on "
        "the review date above._",
    ]
    md = "\n".join(lines)
    st.success("Copy this, paste it in your team channel, and have everyone react ✅.")
    st.code(md, language="markdown")

    unassigned = [r for r, who in owners.items() if not who]
    if unassigned:
        st.warning("Still unassigned: " + ", ".join(unassigned)
                   + ". A team with no owner for a role is structurally weak.")
