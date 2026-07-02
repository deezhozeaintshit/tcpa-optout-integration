# TCPA / FCC Opt-Out Integration Layer — Commercial Edition

> **Stop losing leads to compliance gaps.** A turnkey, production-grade
> Python / FastAPI service that ingests opt-out signals from Twilio SMS,
> SendGrid Email, custom webhooks, and the dashboard, then writes the
> consent revocation back to HubSpot, Salesforce, GoHighLevel, or your
> own destination — *with state-tracked retries, an AI intent classifier,
> and a built-in admin console.*

---

## 🔥 Why this exists (the buyer's pain)

Every U.S. SMS / cold-email operator now carries multi-thousand-dollar
risk per missed opt-out under TCPA, FCC one-to-one consent rules, and
state-level DNC laws (especially Texas, Florida, Oklahoma, Washington).
Off-the-shelf CRMs do **not** reliably close the loop when a contact
texts "STOP" or replies "unsubscribe" to a forwarded mailbox, and most
agencies wire up one-off scripts that drop over half of those signals
on the floor.

This codebase is the production-tested bridge that closes that loop.

---

## 🎁 What's in the box

| Layer | What you get |
|---|---|
| **Ingestion** | Twilio SMS signature-verified webhook, SendGrid multipart parser, IMAP JSON, generic JSON with **dynamic dot-path mappings**, manual dashboard form. |
| **AI Intent Layer** | Google Gemini (`gemini-1.5-flash`) classifier with structured-output schema *and* a deterministic rule-based fallback — runs offline if you don't want a Gemini key. |
| **Normalization** | E.164 phone canonicalization (handles 10/11/+12 digit, parens, dashes, international), email to lowercase trimmed. |
| **State-Tracked Queue** | SQLAlchemy async, 5 states (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `MAX_RETRIES_EXCEEDED`), `failed_syncs` audit table, exponential backoff. |
| **Dispatchers** | HubSpot search+update, Salesforce contact+lead, GoHighLevel / LeadConnector upsert with `dnc` flag, generic webhook. Mock-token shortcuts for local dev. |
| **Console** | Glassmorphic dashboard with Chart.js, sync rate meters, manual override form, integration toggles, failed-sync diagnostics table. Auth = X-API-Key. |
| **Security** | Strict-mode secret validation (refuses to start with placeholder keys), configurable CORS, structured JSON logs, Docker healthcheck, SQLite WAL. |
| **Ship** | Dockerfile (multi-worker uvicorn), Render Blueprint, Railway config, Fly.io config, Heroku-style Procfile, docker-compose. |

---

## 🚀 Run the demo in 90 seconds

```bash
cp .env.example .env             # defaults already work for local dev
docker compose up -d --build     # → http://localhost:8000
# Open the dashboard, click "Trigger Ingestion", watch the queue drain.
```

Expected spend for a 7-day demo: **$0 - ~$5** for a single Fly.io /
Railway micro-instance with a 1 GB persistent volume.

---

## ⚙️ One-click production deploys

| Platform | File | Notes |
|---|---|---|
| **Render** | `render.yaml` | Blueprint → web service + persistent disk |
| **Railway** | `railway.toml` | Volume + Docker + healthcheck |
| **Fly.io** | `fly.toml` | Fly Machine + persistent volume |
| **Heroku-style** | `Procfile` | `web:` process |
| **Plain Docker** | `Dockerfile`, `docker-compose.yml` | Multi-worker `uvicorn` |

1. Push the repo to GitHub.
2. Open the platform, "New → Deploy from repo".
3. Set the secrets listed in the deploy file.
4. First boot surfaces `/api/v1/health` as green; the dashboard auto-seeds **zero** mock credentials in strict mode.

---

## 💼 License tiers (commercial)

| Tier | Price | Includes |
|---|---|---|
| **Starter** | $1,495 one-time + 1 hr setup call | Single team, single tenant, all 4 ingest channels, 1 CRM target. |
| **Agency** | $4,500 one-time + 4 hr setup | Multi-tenant friendly, all CRMs, all channels, branding swap rights. |
| **White-Label OEM** | $9,500 + ongoing 8% revshare | Rebrand, sublicense to your clients, priority patches. |

> See `LICENSE.txt` for the full commercial source license.

---

## ❓ FAQs

**Does it work without a Gemini API key?** Yes. The rule-based fallback
catches the dominant patterns (`STOP`, `UNSUBSCRIBE`, "take me off", …) and
you can tune the keyword list in `app/services/extraction.py`.

**Can it run on Postgres instead of SQLite?** Yes — set
`DATABASE_URL=postgresql+asyncpg://...` and the same SQLAlchemy ORM
will pick it up.

**What happens if Twilio sends a malformed body?** It is logged and
acknowledged with a 200 + empty TwiML (so Twilio doesn't retry-bomb you).
The strict endpoint refuses unsigned requests.

**Can I add a new CRM adapter?** Yes — drop a method onto
`IntegrationDispatcher` and an `<option>` into the dashboard.

---

## 🧪 Test suite

```bash
pip install -e ".[dev]"
pytest -q
```

7 integration tests covering signature validation, normalization,
extraction, queue retries, failed-sync logging, and the dispatcher
adapters.

---

## 📞 Buyer contact

DM / email `sales@your-vendor-domain.example` for demos, custom
quotes, and OEM bundles.
