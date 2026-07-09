# TeamUp — owner & deployment guide

This file is for whoever owns and deploys the app. Members never need to read
this — they just open the link you share with them.

---

## Run locally (dev / testing)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. The pool starts empty. Click **Load demo
data** on the Join page to add 8 sample people and try matching. Click
**Clear pool** to reset.

Data is saved to `teamup_state.json` locally and survives restarts.

---

## Deploy to Streamlit Community Cloud

You deploy once. Members get a public URL and use it in their browser — no
install, no account.

Streamlit Cloud's filesystem is ephemeral — the JSON file gets wiped on every
sleep or redeploy. Wire up Google Sheets first so signup data persists.

### Step 1 — Create the Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a new blank spreadsheet. Name it **TeamUp**.
2. Create two worksheets (tabs at the bottom):
   - Rename **Sheet1** → `Pool`
   - Add a second tab, name it `Teams`
3. In the **Pool** tab, add these exact headers in row 1 (one per column, A–G):

   ```
   id   name   skills   wants_to_learn   availability   hours_per_week   commitment
   ```

4. In the **Teams** tab, add these headers in row 1:

   ```
   team_number   members_json
   ```

5. Copy the spreadsheet URL — you'll need it in Step 4.

### Step 2 — Create a Google Cloud service account

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project (name it anything, e.g. `teamup`).
2. Search for **Google Sheets API** → Enable.
3. Search for **Google Drive API** → Enable.
4. Go to **IAM & Admin → Service Accounts → Create Service Account**.
   - Give it any name (e.g. `teamup`), click through, click **Done**.
5. Click the service account → **Keys** tab → **Add Key → Create new key → JSON**.
   A `.json` file downloads — keep it safe, you'll copy values from it next.

### Step 3 — Share the sheet with the service account

1. Open the downloaded JSON file and copy the `client_email` value
   (looks like `teamup@your-project.iam.gserviceaccount.com`).
2. Open your Google Sheet → **Share** → paste that email → **Editor** → **Send**.

### Step 4 — Set up secrets

**Locally:**

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Fill in `.streamlit/secrets.toml`:

```toml
[connections.gsheets]
spreadsheet    = "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit"
type           = "service_account"
private_key_id = "..."
private_key    = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email   = "teamup@your-project.iam.gserviceaccount.com"
client_id      = "..."
token_uri      = "https://oauth2.googleapis.com/token"
```

Copy each value from the JSON key file. **Never commit `secrets.toml`** — it's gitignored.

**On Streamlit Cloud:**

App dashboard → **Settings → Secrets** → paste the same content → **Save**.

### Step 5 — Deploy

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, branch `main`, main file `app.py` → **Deploy**.

Streamlit gives you a URL like `https://teamup-mac.streamlit.app`. Share that
link with your members — they open it in a browser and fill in the form.
Every submission writes a permanent row into your Google Sheet.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| App / UI | Streamlit (multipage) |
| Matching | Pure Python (`teamup/match.py`) — no API, no LLM |
| Persistence — local | JSON file (`teamup_state.json`) |
| Persistence — deployed | Google Sheets (`st-gsheets-connection`) |

## Tests

```bash
python -m unittest discover tests
```
