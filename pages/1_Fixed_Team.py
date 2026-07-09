"""Fixed Team — you can't always pick your teammates. Make the best of the team
you HAVE: explain the scores, assign who owns what, and coach the gaps."""

import streamlit as st

from teamup.match import Profile, SKILLS, COMMITMENT, coach_team
from teamup.report import team_report_html
from teamup import scenarios
from teamup.comm import style as comm_style
from teamup.store import init_state

st.set_page_config(page_title="Fixed Team · TeamUp", page_icon="🧭", layout="wide")
init_state(st)
st.session_state.setdefault("fixed_team", [])

st.title("🧭 Make our team work")
st.caption("Already stuck with a group — an assigned class team, the squad you landed in, "
           "the volunteers who showed up? Enter who you've got and we'll make the best team "
           "possible from it: who should own what, where the gaps are, and how to close them.")

SLOTS = ["Mon evening", "Tue evening", "Wed evening", "Thu evening",
         "Fri evening", "Sat daytime", "Sun daytime"]


def _sample():
    """A realistic, deliberately gappy team: strong build, no designer, one coaster."""
    return [
        Profile("ft1", "Ana", skills=["Python / coding"], wants_to_learn=["UI/UX design"],
                availability=["Mon evening", "Sat daytime"], commitment=3),
        Profile("ft2", "Ben", skills=["Data / ML"], availability=["Sat daytime"], commitment=1),
        Profile("ft3", "Cara", skills=["Python / coding", "Project management"],
                availability=["Mon evening", "Wed evening"], commitment=2),
        Profile("ft4", "Dan", skills=["Writing / storytelling"],
                availability=["Sun daytime"], commitment=2),
    ]


# ── Scenario ───────────────────────────────────────────────────────────────────
scen_label = st.selectbox("What is this team for?", scenarios.LABELS)
scen = scenarios.by_label(scen_label)
st.caption(f"**Needs covered:** {', '.join(scen['required_roles'])} · "
           f"**Usual size:** {scen['ideal_size'][0]}–{scen['ideal_size'][1]} · "
           f"⚠️ {scen['top_risk']}")

st.divider()
left, right = st.columns([1, 1])

# ── Add a teammate ─────────────────────────────────────────────────────────────
with left:
    st.markdown("#### Who's on the team?")
    with st.form("add_member", clear_on_submit=True):
        name = st.text_input("Name")
        skills = st.multiselect("What they're good at", SKILLS)
        learn = st.multiselect("What they want to learn (optional)", SKILLS)
        avail = st.multiselect("When they're free", SLOTS)
        commit = st.select_slider("How serious are they?", options=list(COMMITMENT),
                                  format_func=lambda k: COMMITMENT[k], value=2)
        if st.form_submit_button("➕ Add to team") and name:
            st.session_state.fixed_team.append(Profile(
                id=f"ft{len(st.session_state.fixed_team)+1}", name=name, skills=skills,
                wants_to_learn=learn, availability=avail or ["flexible"], commitment=commit))
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("Load a sample team", help="A realistic, gappy 4-person team"):
        st.session_state.fixed_team = _sample()
        st.rerun()
    if c2.button("Clear"):
        st.session_state.fixed_team = []
        st.rerun()

# ── Roster ─────────────────────────────────────────────────────────────────────
with right:
    st.markdown("#### Your roster")
    team = st.session_state.fixed_team
    if not team:
        st.info("Add teammates on the left, or load a sample.")
    for i, m in enumerate(team):
        cols = st.columns([5, 1])
        cols[0].write(f"**{m.name}** — {', '.join(sorted(m.roles())) or 'no role tags'} · "
                      f"{COMMITMENT[m.commitment]}")
        if cols[1].button("✕", key=f"rm{i}"):
            st.session_state.fixed_team.pop(i)
            st.rerun()

st.divider()

# ── Analysis ───────────────────────────────────────────────────────────────────
if len(st.session_state.fixed_team) < 2:
    st.warning("Add at least 2 teammates to analyze the team.")
    st.stop()

team_name = st.text_input("Team name (for the report)", value="Our team")
if st.button("🔍 Analyze this team", type="primary"):
    r = coach_team(st.session_state.fixed_team, scen)

    st.markdown("### 📊 How your team scored — and why")
    for line in r["explanations"]:
        st.markdown(f"- {line}")
    if r["size_note"]:
        st.caption("👥 " + r["size_note"])

    st.markdown("### 🧩 Who should own what (day one)")
    for a in r["assignments"]:
        owner = a["owner"] or "— recruit / drop scope —"
        tag = " · **stretch**" if a["stretch"] else ""
        st.markdown(f"- **{a['role']}** → {owner}{tag}  \n  <small>{a['why']}</small>",
                    unsafe_allow_html=True)

    if r["advice"]:
        st.markdown("### 🛠️ Make the best of it")
        for ad in r["advice"]:
            (st.error if ad["sev"] == "high" else st.warning)(
                f"**{ad['title']}.** {ad['body']}")

    cs = comm_style(r["comm"]["style"])
    st.markdown("### 📡 How to communicate")
    st.success(f"**{cs['name']}** — {r['comm']['why']}")

    slug = team_name.lower().strip().replace(" ", "-") or "our-team"
    st.download_button(
        "📄 Download this team plan (HTML — opens in browser, print to PDF)",
        data=team_report_html(team_name, scen, r),
        file_name=f"team-plan-{slug}.html", mime="text/html")
    st.caption("Then head to **Team Kickoff** to turn this into a signed working agreement.")
