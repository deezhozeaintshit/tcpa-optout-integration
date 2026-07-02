# Deployment Run-Book

This document captures everything needed to deploy the TCPA Opt-Out
Integration Layer to Render, Railway, Fly.io, or a generic VPS.

---

## 0. Pre-requisites (all platforms)

1. Copy `.env.example` to `.env` and fill in real values for at least:
   - `ADMIN_API_KEY`
   - `TWILIO_AUTH_TOKEN`
   - The CRM tokens you actually use (`HUBSPOT_ACCESS_TOKEN`, etc.)
2. Generate a strong API key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
3. Decide what `ALLOWED_ORIGINS` should be (comma-separated). Do NOT
   ship `"*"` in production.

---

## 1. Render (recommended for first deploy)

1. Push the repo to GitHub.
2. In Render: **New → Blueprint → Connect repo → pick `render.yaml`**.
3. In the **Environment** tab, paste the secret values (anything marked
   `sync: false` in `render.yaml`).
4. Render will:
   - Build the Dockerfile (multi-worker uvicorn).
   - Mount a 1 GB persistent disk at `/workspace/data`.
   - Probe `/api/v1/health`.
5. After the first green deploy, open the URL + `:8000` for the
   dashboard, `:8000/api/v1/docs` for FastAPI Swagger.

**Gotchas** — Render stops the instance on deploy while the disk is
attached (no zero-downtime). For true zero-downtime you'd separate the
web and worker into two services (future work — single-image today
runs the in-process background worker).

---

## 2. Railway

```bash
# 1. Connect repo
railway link
# 2. Create the persistent volume (1 GB)
railway volume create --size 1 --name tcpa-data --mount /workspace/data
# 3. Set environment variables
railway variables set ADMIN_API_KEY=... TWILIO_AUTH_TOKEN=... ENVIRONMENT=production
# 4. Deploy
railway up
```

Railway auto-detects `railway.toml` and the `Dockerfile`.

---

## 3. Fly.io

```bash
# 1. Launch the app
fly launch --copy-config --name tcpa-optout-api
# 2. Create the persistent volume BEFORE first deploy
fly volumes create tcpa_data --size 1 --region iad
# 3. Set secrets
fly secrets set ADMIN_API_KEY=... TWILIO_AUTH_TOKEN=...
# 4. Deploy
fly deploy
```

`fly.toml` mounts the volume, configures the healthcheck, and forces
HTTPS.

---

## 4. Generic VPS / Docker

```bash
git clone <repo>
cp .env.example .env  &&  $EDITOR .env
docker compose up -d --build
```

The compose file ships with healthcheck and a named volume
(`tcpa_data`) so SQLite survives restarts.

---

## Health & readiness

- `GET /api/v1/health` — liveness, unauthenticated. Used by PaaS.
- `GET /api/v1/ready` — readiness probe; checks DB roundtrip.

Both return JSON `{"status": "ok", ...}`.

---

## Observability

- Set `LOG_FORMAT=json` to emit one structured record per line for
  Datadog / GCP Cloud Logging / Loki / etc.
- Set `ENVIRONMENT=production` to flip `is_strict=True` — the app
  will refuse to start with placeholder secrets and will not seed
  mock integrations.

---

## Scaling notes

| Concern | Today (single instance) | Future (multi-instance) |
|---|---|---|
| API request handling | `WEB_CONCURRENCY` uvicorn workers (default 2). | Increase on Render/Railway; on Fly add machines. |
| Background worker | In-process asyncio loop. | Disabled via `WORKER_ENABLED=false` on the API process, then run a second container / service dedicated to the worker. |
| SQLite | WAL mode + busy_timeout=5s handles modest concurrency. | Migrate to Postgres (`DATABASE_URL=postgresql+asyncpg://...`). |
| Sessions / state | Local SQLite file. | Move to Postgres when going multi-instance. |

---

## Common gotchas

- **Mock tokens in production.** If a buyer accidentally leaves a
  `*_mock_token` value in `HUBSPOT_ACCESS_TOKEN`, dispatch now FAILS
  LOUDLY with a clear error (instead of silently succeeding).
- **CORS wildcard.** `ALLOWED_ORIGINS=*` is rejected at linters /
  review time. Production should be a comma-separated allowlist.
- **Twilio signature bypass removed.** A placeholder
  `TWILIO_AUTH_TOKEN` no longer grants unauthenticated access; the
  service refuses to start in strict mode.
- **CDN / reverse proxies.** If you put Cloudflare / a TLS terminator
  in front, ensure `X-Forwarded-Proto` and `X-Forwarded-Host` reach
  the app so Twilio signature verification reconstructs the correct
  URL.
