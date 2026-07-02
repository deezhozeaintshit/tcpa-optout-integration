import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, or_, and_
from app.core.database import AsyncSessionLocal
from app.models.task import SyncTask
from app.models.failed_sync import FailedSync
from app.core.config import settings
from app.services.integration_dispatcher import dispatcher

logger = logging.getLogger("optout_worker")
worker_task = None
worker_running = True
_worker_event = asyncio.Event()

def trigger_worker():
    """Wake up the worker loop to process tasks immediately."""
    _worker_event.set()

async def run_worker_loop():
    """Background polling worker process for handling queued integration tasks."""
    global worker_running
    logger.info("Background state-tracked task queue worker started.")
    
    # Wait a few seconds on startup to let the app fully initialize
    await asyncio.sleep(2)
    
    while worker_running:
        try:
            await process_pending_tasks()
        except Exception as e:
            logger.exception("Error occurred in background task processing loop")
        
        # Wait for trigger event or poll interval timeout
        try:
            await asyncio.wait_for(_worker_event.wait(), timeout=float(settings.WORKER_POLL_INTERVAL))
            _worker_event.clear()
        except asyncio.TimeoutError:
            pass
            
    logger.info("Background state-tracked task queue worker stopped.")

async def process_pending_tasks():
    """Polls database for ready sync tasks, locks them, and processes them."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Select PENDING tasks or FAILED tasks whose backoff window has expired
        stmt = select(SyncTask).where(
            or_(
                SyncTask.status == "PENDING",
                and_(
                    SyncTask.status == "FAILED",
                    SyncTask.retry_count < SyncTask.max_retries,
                    SyncTask.next_retry_at <= now
                )
            )
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        
        if not tasks:
            return
            
        logger.info(f"Worker polling: Found {len(tasks)} eligible tasks to sync.")
        
        # Optimistic locking: mark tasks as PROCESSING so other instances/loops don't run them concurrently
        for task in tasks:
            task.status = "PROCESSING"
            db.add(task)
        await db.commit()

    # Process each task in its own transactional context
    for task in tasks:
        async with AsyncSessionLocal() as run_db:
            stmt_run = select(SyncTask).where(SyncTask.id == task.id)
            res_run = await run_db.execute(stmt_run)
            db_task = res_run.scalars().first()
            if not db_task:
                continue
            
            try:
                # Dispatch update to configured external CRM / webhook
                success = await dispatcher.dispatch(db_task)
                if success:
                    db_task.status = "COMPLETED"
                    db_task.last_error = None
                else:
                    raise Exception("Integration dispatcher returned non-success indicator")
            except Exception as exc:
                db_task.retry_count += 1
                db_task.last_error = str(exc)
                
                # Log dispatch failure details to failed_syncs table
                try:
                    error_payload = {
                        "error": str(exc),
                        "retry_count": db_task.retry_count,
                        "max_retries": db_task.max_retries,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "integration": {
                            "id": db_task.integration.id if db_task.integration else None,
                            "name": db_task.integration.name if db_task.integration else None,
                            "type": db_task.integration.type if db_task.integration else None
                        },
                        "opt_out": {
                            "id": db_task.opt_out.id if db_task.opt_out else None,
                            "identifier": db_task.opt_out.identifier if db_task.opt_out else None,
                            "channel": db_task.opt_out.channel if db_task.opt_out else None
                        }
                    }
                    failed_sync = FailedSync(
                        sync_task_id=db_task.id,
                        error_payload=error_payload
                    )
                    run_db.add(failed_sync)
                except Exception as db_err:
                    logger.error(f"Failed to log to failed_syncs table: {db_err}")

                if db_task.retry_count >= db_task.max_retries:
                    db_task.status = "MAX_RETRIES_EXCEEDED"
                    logger.error(f"Task {db_task.id} failed permanently after {db_task.retry_count} retries. Error: {exc}")
                else:
                    db_task.status = "FAILED"
                    # Exponential backoff calculation
                    backoff_seconds = settings.BACKOFF_FACTOR * (2 ** db_task.retry_count)
                    db_task.next_retry_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=backoff_seconds)
                    logger.warning(f"Task {db_task.id} failed. Scheduling retry {db_task.retry_count}/{db_task.max_retries} in {backoff_seconds}s. Error: {exc}")
            
            # Record status updates and commit transaction
            db_task.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run_db.add(db_task)
            await run_db.commit()

def start_background_worker():
    """Spawns the background worker task."""
    global worker_task, worker_running
    worker_running = True
    worker_task = asyncio.create_task(run_worker_loop())

async def stop_background_worker():
    """Gracefully terminates and cleans up the background worker task."""
    global worker_task, worker_running
    logger.info("Stopping background worker...")
    worker_running = False
    if worker_task:
        try:
            await asyncio.wait_for(worker_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Background worker failed to exit cleanly within timeout. Cancelling...")
            worker_task.cancel()
        await dispatcher.close()
