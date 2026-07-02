from fastapi import APIRouter
from app.api.v1.endpoints import ingest, optouts, integrations, health

api_router = APIRouter()

# Health endpoints are mounted first and unauthenticated so that
# PaaS healthchecks (Render, Railway, Fly) can probe the service.
api_router.include_router(health.router)

api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion Webhooks"])
api_router.include_router(optouts.router, prefix="/optouts", tags=["Opt-Out Audits"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integration Targets"])
