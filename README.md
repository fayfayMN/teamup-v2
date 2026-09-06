# 🤝 TeamUp — Version 2

Form a great team for your competition or project — matched on complementary
skills, shared availability, and aligned commitment. Takes about 10 minutes
from "strangers" to "we have a working agreement."

**👉 Open the app: [https://teamup-frsxgpqc2hqw8wizwsq8rs.streamlit.app](https://teamup-v2-arbppub2gxhxtwqlmx6p8g.streamlit.app/)**

> **This is Version 2** — the current, recommended app. It adds shared
> room-scoped pools, an organizer gate, broad availability buckets (weekday /
> weekend × morning / daytime / evening) instead of a fiddly day-by-day grid,
> and downloadable outputs on every page (roster CSV, room backup JSON, team
> plan HTML, working agreement HTML/Markdown).
> The original prototype (v1) is archived at
> [github.com/fayfayMN/teamup](https://github.com/fayfayMN/teamup).

---

## How to use it

### Step 1 — Join the pool

Open the app and go to the **Join** page. Fill in:

- **What you're good at** — pick your real strengths. Be honest; the match
  depends on it.
- **What you want to learn** — optional, but helps pair you with someone who
  can mentor you.
- **When you're available** — pick every slot that works for you. No shared
  availability = no match.
- **Hours per week** you can commit.
- **How serious are you?** — choose honestly between *here to learn*,
  *will contribute*, or *here to win*. Landing on a team with mismatched
  expectations is the #1 thing that quietly breaks teams.

Click **Add me to the pool**. You only do this once.

### Step 2 — Form teams

Once everyone has joined, the organizer goes to the **Match** page and clicks
**Form teams**. You'll see each proposed team with:

- Which roles are covered (Build, Design, Pitch, Organize)
- Any gaps — e.g. "no one to present" — flagged before you start
- Schedule overlap and commitment alignment

Teams are locked when the organizer clicks **Lock these teams**.

### Step 3 — Run your team kickoff

Each team opens the **Team Kickoff** page together — takes about 10 minutes.
You'll agree on:

- Who owns each part of the project (one person per role, not one leader for
  everything)
- How you make decisions when you're stuck
- When you check in with each other
- What happens if someone goes quiet
- How credit is handled at the end

Click **Generate working agreement** and paste it into your team channel.
Have everyone react ✅. That's your shared contract — and your defense against
free riders and credit-takers.

---

## Running it for a real competition (organizer notes)

**One shared pool via room codes.** Everyone who enters the same **room code**
(sidebar, e.g. `MUDAC26`) joins one shared pool — so a whole cohort's joins show
up for the organizer on the Match page. Use a fresh code per event so last time's
pool never leaks in. The pool is shared in-memory across all users on the app's
(single) Streamlit Community Cloud replica.

**Lock forming/clearing to the organizer.** Set an `organizer_pass` in the app's
Streamlit secrets (Manage app → Settings → Secrets):

```toml
organizer_pass = "choose-something"
```

With it set, participants can still **Join**, but only someone who unlocks in the
sidebar can **Form / Lock / Clear / Restore** teams. With no passphrase set, the
app stays fully open (a note says so).

**Download everything.**
- **Join** → *Download roster (CSV)*
- **Match** → *Download teams (CSV)*, plus *Organizer: back up / restore this room*
  (download the whole room as JSON and re-upload to restore)
- **Team Kickoff** → download the working agreement (HTML or Markdown)

**Durability note.** The pool survives app *restarts* via an on-disk backup, but a
full redeploy/sleep on the free tier can wipe it. Before/near the event, click
**Download room backup (JSON)** on the Match page; re-upload it to restore instantly.

---

## After the competition

Each team member can use **Clearwork** to turn their tracked contributions into
a verified project card for their resume — proof of what they actually did,
confirmed by teammates.
