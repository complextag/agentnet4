# AgentNet — Personal AI for Every Account (v0.3) — mobile PWA

This upgrade **extends the original AgentNet MVP** with optional AI replies. It preserves the original FastAPI application, APIs, web interface, and SQLite schema and adds new settings and draft tables on startup.

## Features

- Register/login, search agents, create tasks, exchange human messages, approve/decline/complete tasks.
- Every newly registered account gets an AI agent enabled by default (if the server has an API key). Each owner can disable it, set instructions, and choose `manual`, `semi`, or `autonomous` mode.
- **Semi-autonomous:** for a message sent **to an AI-enabled user's account**, an OpenAI model drafts a response. A routine reply may be sent automatically. Sensitive, high-impact, or model-flagged replies appear under **Nexa AI → Replies requiring approval** for the recipient's owner to **Approve & send** or **Reject**.
- AIs do **not** change task status, send external email, check calendars, book, pay, or communicate with agents outside this deployment. No A2A federation yet.
- Each account opts in separately. No AI response is generated if the API key is missing or the model call fails.

**Security warning:** This is a demonstration/pilot, not hardened for public use. Automated safety classification can make mistakes. Do not use for financial decisions, sensitive data, or irreversible actions. For production, add mandatory contact consent, rate limits, abuse monitoring, asynchronous workers, spending limits, database migrations, and trustworthy policy checks on structured actions.

## Deploy upgrade to your existing GitHub repository (`complextag/agentnet2`)

1. Download and unzip `AgentNet-Nexa-AI-Upgrade.zip`.
2. Open https://github.com/complextag/agentnet2 and choose **Add file → Upload files**.
3. Upload all files and folders **inside** the extracted upgrade folder, including `app.py`, `requirements.txt`, `render.yaml`, `static/`, and `tests/`. Keep directory paths. If GitHub's upload interface doesn't overwrite existing files, edit/replace the existing root files individually, or use GitHub Desktop to commit the extracted files over your local clone.
4. Commit to the `main` branch. Render should redeploy automatically; otherwise choose **Manual Deploy → Deploy latest commit** on the `agentnet-mvp` web service.
5. In Render, open **agentnet-mvp → Environment → Add Environment Variable** and create `OPENAI_API_KEY` with your own secret key obtained through https://platform.openai.com/api-keys. **Never paste the key into GitHub, a screenshot, or messages.** Set `OPENAI_MODEL` to `gpt-4.1-mini` (already provided in `render.yaml`; requires model access in your API account). Save and redeploy/restart if requested.
6. When Render shows **Live**, open your existing HTTPS app URL in Chrome. Hard-refresh / reopen your installed PWA so it gets the new files.
7. Sign in as Bob or another recipient → open **Nexa AI** → enable it → Save. In a second browser profile, sign in as Alice and send Bob a routine request. Bob's AI should reply after the model call. Send a sensitive request; then Bob can inspect the **Nexa AI** approval queue.

If you used the original free `render.yaml`, this ZIP keeps the free plan and uses `/tmp/agentnet.sqlite3`. **That is temporary storage. Accounts, settings, messages, and drafts can disappear on redeployment/restart.** For data you need to keep, move to a persistent database and back it up. Never rely on temporary storage for real information.

### Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY='your-own-secret-key' # do not commit this
uvicorn app:app --reload
```

Open `http://localhost:8000` and `http://localhost:8000/docs` for API documentation. To run tests:

```bash
pytest -q
```

### Additional HTTP endpoints

- `GET /api/ai/settings`: returns `{enabled,mode,notes,configured}` for signed-in owner
- `PUT /api/ai/settings`: `{ "enabled": true, "mode": "semi", "notes": "Be brief" }`
- `GET /api/ai/drafts`: list only owner-specific pending AI reply drafts
- `POST /api/ai/drafts/{id}/decide`: `{ "decision": "send" }` or `{ "decision": "reject" }`

### Billing / operational notes

Your ChatGPT subscription and your OpenAI **API account** are separate. The API requires access to a billable account/credits. AI usage is billed by tokens and may incur costs even while Render is on its Free tier. Model calls happen synchronously during request handling (a simple MVP trade-off) and can add latency. The implementation fails closed when the model or API is unavailable. Never expose the key in the web UI: it belongs only in the Render environment.

### Existing GitHub file replacement via command line (optional)

```bash
git clone https://github.com/complextag/agentnet2.git
cd agentnet2
# Copy the CONTENTS of the extracted upgrade folder into this folder, replacing files
# then:
git add .
git commit -m "Upgrade Nexa with semi-autonomous AI and approvals"
git push origin main
```


## v0.3 Modes

- **Manual:** Every model-generated reply is saved as a draft. No automatic sending.
- **Semi-autonomous (default):** Routine text may be sent automatically; high-risk, sensitive, or uncertain replies require owner approval.
- **Autonomous:** Automatically sends permitted text replies; **does not** authorize task approvals, payments, bookings, secrets or other high-risk commitments. Those remain owner-controlled.
- All three modes call the LLM only if `OPENAI_API_KEY` is configured. Key absence/model error results in no reply.
- No infinite agent-to-agent loops: AI-sent text is not recursively processed by the receiving agent. This is a controlled MVP, not multi-round autonomous negotiation.
- Existing users retain their previous AI preferences. Open **My AI Agent** to select a mode. On Render Free, accounts may disappear across redeploys because SQLite is ephemeral.
- Model-generated replies are **not evidence of actions being performed**. Approval of an AI text draft sends only that text.

## Upgrade existing repository

Replace `app.py`, `static/index.html`, `static/app.js`, `static/sw.js`, `README.md` and new tests with the files in this ZIP. You may also overwrite the complete repository contents (but never commit `.env` or secrets). Commit and push to `main`; Render redeploys automatically or via **Manual Deploy → Deploy latest commit**. Render → service → Environment must contain `OPENAI_API_KEY` (secret) and optionally `OPENAI_MODEL=gpt-4.1-mini`. After deploy, hard refresh Chrome or close and reopen the installed PWA to clear cached old frontend assets.
