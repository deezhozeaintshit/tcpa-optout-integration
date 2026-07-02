import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.optout import OptOut
from app.models.integration import Integration
from app.models.task import SyncTask
from app.schemas.optout import OptOutCreate
from app.core.normalizer import normalize_phone, normalize_email

logger = logging.getLogger("optout_service")

class OptOutService:
    """Manages recording opt-out requests and staging sync tasks across target integrations."""

    async def create_optout(self, db: AsyncSession, obj_in: OptOutCreate) -> OptOut:
        identifier = obj_in.identifier.strip()
        
        # Detect type of identifier and normalize
        if "@" in identifier:
            normalized = normalize_email(identifier)
        else:
            normalized = normalize_phone(identifier)
            
        # Write OptOut audit log
        db_obj = OptOut(
            identifier=normalized,
            channel=obj_in.channel,
            raw_payload=obj_in.raw_payload or {},
            reason=obj_in.reason,
            ip_address=obj_in.ip_address
        )
        db.add(db_obj)
        await db.flush()  # Flush to generate primary key ID
        
        # Find active integrations to dispatch the updates to
        stmt = select(Integration).where(Integration.is_active == True)
        res = await db.execute(stmt)
        active_integrations = res.scalars().all()
        
        # Queue tasks for background worker loop
        for integration in active_integrations:
            task = SyncTask(
                opt_out_id=db_obj.id,
                integration_id=integration.id,
                status="PENDING",
                retry_count=0
            )
            db.add(task)
            
        await db.flush()
        await db.refresh(db_obj)
        logger.info(f"Saved opt-out for '{normalized}' from channel '{obj_in.channel}'. Staged {len(active_integrations)} integration tasks.")
        
        # Trigger background worker to run immediately
        from app.core.worker import trigger_worker
        trigger_worker()
        
        return db_obj

optout_service = OptOutService()
