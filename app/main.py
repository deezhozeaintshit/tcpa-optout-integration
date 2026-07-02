import os
import json
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.worker import start_background_worker, stop_background_worker
from app.api.v1.router import api_router
from app.models.integration import Integration


class _JsonFormatter(logging.Formatter):
    """Emit one log record per line as JSON (for log aggregators)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _configure_logging() -> None:
    """Configure root logging once, in the requested format."""
    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT.lower() == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


_configure_logging()
logger = logging.getLogger("optout_main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup banner
    logger.info(
        "Starting TCPA Opt-Out Integration Layer "
        f"(env={settings.ENVIRONMENT}, strict={settings.is_strict}, "
        f"log_format={settings.LOG_FORMAT}, worker={settings.WORKER_ENABLED})"
    )

    # 1. Startup: Create SQLite tables if they do not exist.
    #    Race-safe against concurrent worker subprocesses: when uvicorn runs
    #    with --workers > 1, multiple PIDs call lifespan() at the same moment.
    #    SQLAlchemy's create_all uses checkfirst=True which has a TOCTOU race
    #    — two workers can both see "table missing", both attempt CREATE TABLE,
    #    and SQLite serializes the writes so the loser sees "already exists".
    #    The schema is what we wanted either way; swallow that specific error.
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except OperationalError as exc:
        if "already exists" not in str(exc).lower():
            raise
    logger.info("SQLite database tables verified/created successfully.")

    # 2. Seed initial mock integrations for out-of-the-box demo if database is empty.
    #    Skipped entirely in strict mode so production starts clean.
    if not settings.is_strict:
        async with AsyncSessionLocal() as db:
            stmt = select(Integration)
            res = await db.execute(stmt)
            existing = res.scalars().all()
            if not existing:
                hubspot_mock = Integration(
                    name="HubSpot CRM Integrator",
                    type="hubspot",
                    is_active=True,
                    credentials={"access_token": settings.HUBSPOT_ACCESS_TOKEN or "hubspot_mock_token"}
                )
                gohighlevel_mock = Integration(
                    name="GoHighLevel CRM Outbound",
                    type="gohighlevel",
                    is_active=True,
                    credentials={
                        "access_token": settings.GOHIGHLEVEL_ACCESS_TOKEN or "gohighlevel_mock_token",
                        "location_id": settings.GOHIGHLEVEL_LOCATION_ID or "mock_location_123"
                    }
                )
                webhook_mock = Integration(
                    name="Generic Outbound Webhook",
                    type="generic_webhook",
                    is_active=True,
                    credentials={
                        "url": "https://httpbin.org/post"
                    }
                )
                db.add(hubspot_mock)
                db.add(gohighlevel_mock)
                db.add(webhook_mock)
                await db.commit()
                logger.info("Seeded default mock integrations for HubSpot, GoHighLevel, and Generic Webhook.")
    else:
        logger.info("Strict mode: no mock integrations seeded. Use the dashboard to add real CRM targets.")

    # 3. Spawn state-tracked background queue worker
    if settings.WORKER_ENABLED:
        start_background_worker()

    yield

    # 4. Shutdown: Gracefully stop background worker tasks and close dispatch connections
    if settings.WORKER_ENABLED:
        await stop_background_worker()


app = FastAPI(
    title="Multi-Channel TCPA/FCC Opt-Out Integration Layer",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Policy (configurable via ALLOWED_ORIGINS env var).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect API Routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse, tags=["Visual Control Panel"])
async def read_dashboard():
    """Serves the visual control panel dashboard interface."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "templates", "index.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error(f"Dashboard HTML file not found at: {template_path}")
        return HTMLResponse(
            content="<h1>Visual Control Panel File Missing</h1>",
            status_code=500
        )
