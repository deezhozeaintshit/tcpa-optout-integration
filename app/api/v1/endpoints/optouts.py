from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.optout import OptOut
from app.models.task import SyncTask
from app.models.failed_sync import FailedSync
from app.schemas.optout import OptOutResponse, OptOutCreate
from app.schemas.task import SyncTaskResponse
from app.schemas.failed_sync import FailedSyncResponse
from app.services.optout_service import optout_service

router = APIRouter()

@router.get("/failed-syncs", response_model=List[FailedSyncResponse], dependencies=[Depends(verify_api_key)])
async def list_failed_syncs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed logs of sync task failures from SQLite."""
    stmt = select(FailedSync).order_by(desc(FailedSync.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=OptOutResponse, dependencies=[Depends(verify_api_key)])
async def create_manual_optout(
    payload: OptOutCreate,
    db: AsyncSession = Depends(get_db)
):
    """Manually insert a phone/email opt-out record and trigger downstream target updates."""
    return await optout_service.create_optout(db, payload)

@router.get("/", response_model=List[OptOutResponse])
async def list_optouts(
    q: str = Query(None, description="Search phone number or email substring"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve list of registered opt-outs (audit trail) with optional search filter."""
    stmt = select(OptOut)
    if q:
        stmt = stmt.where(OptOut.identifier.contains(q.strip()))
    stmt = stmt.order_by(desc(OptOut.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/tasks", response_model=List[SyncTaskResponse])
async def list_sync_tasks(
    status: str = Query(None, description="Filter queue tasks by state (PENDING, COMPLETED, FAILED)"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve integration dispatch history and task queue metrics."""
    stmt = select(SyncTask)
    if status:
        stmt = stmt.where(SyncTask.status == status)
    stmt = stmt.order_by(desc(SyncTask.updated_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
