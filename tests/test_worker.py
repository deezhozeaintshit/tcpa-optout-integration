import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.models.optout import OptOut
from app.models.integration import Integration
from app.models.task import SyncTask
from app.core.worker import process_pending_tasks

@pytest.mark.anyio
async def test_worker_processing_success(db_session):
    """Verify that background worker updates tasks to COMPLETED upon successful mock dispatch."""
    # 1. Seed Integration (Mock HubSpot)
    integration = Integration(
        name="HubSpot Demo",
        type="hubspot",
        is_active=True,
        credentials={"access_token": "hubspot_mock_token"}
    )
    db_session.add(integration)
    await db_session.commit()

    # 2. Seed OptOut
    opt_out = OptOut(
        identifier="+14155551234",
        channel="sms",
        raw_payload={},
        reason="STOP"
    )
    db_session.add(opt_out)
    await db_session.commit()

    # 3. Queue task
    task = SyncTask(
        opt_out_id=opt_out.id,
        integration_id=integration.id,
        status="PENDING",
        max_retries=3
    )
    db_session.add(task)
    await db_session.commit()

    # Run worker poll
    await process_pending_tasks()

    # Refresh task state directly from database to reload changed fields
    await db_session.refresh(task)
    assert task.status == "COMPLETED"
    assert task.retry_count == 0
    assert task.last_error is None

@pytest.mark.anyio
async def test_worker_processing_failure_retry(db_session):
    """Verify that worker shifts failed dispatches to FAILED and computes exponential backoff."""
    # 1. Seed Integration with invalid web address to trigger network exceptions
    integration = Integration(
        name="Broken Webhook Target",
        type="generic_webhook",
        is_active=True,
        credentials={"url": "http://non-existent-domain-xyz-12345.com/webhook"}
    )
    db_session.add(integration)
    await db_session.commit()

    # 2. Seed OptOut
    opt_out = OptOut(
        identifier="optout@test.com",
        channel="email",
        raw_payload={},
        reason="unsubscribe"
    )
    db_session.add(opt_out)
    await db_session.commit()

    # 3. Queue task
    task = SyncTask(
        opt_out_id=opt_out.id,
        integration_id=integration.id,
        status="PENDING",
        max_retries=3
    )
    db_session.add(task)
    await db_session.commit()

    # Run worker cycle
    await process_pending_tasks()

    # Refresh task state directly from database
    await db_session.refresh(task)
    assert task.status == "FAILED"
    assert task.retry_count == 1
    assert task.last_error is not None
    assert task.next_retry_at > datetime.now(timezone.utc).replace(tzinfo=None)

@pytest.mark.anyio
async def test_worker_max_retries_exceeded(db_session):
    """Verify tasks are marked MAX_RETRIES_EXCEEDED when retry count matches max_retries limit."""
    # 1. Seed bad webhook integration
    integration = Integration(
        name="Failed CRM Integration",
        type="generic_webhook",
        is_active=True,
        credentials={"url": "http://non-existent-domain-xyz-12345.com/webhook"}
    )
    db_session.add(integration)
    await db_session.commit()

    # 2. Seed OptOut
    opt_out = OptOut(
        identifier="optout-max@test.com",
        channel="email",
        raw_payload={},
        reason="unsubscribe"
    )
    db_session.add(opt_out)
    await db_session.commit()

    # 3. Queue task that has already retried 2 times (max is 3)
    task = SyncTask(
        opt_out_id=opt_out.id,
        integration_id=integration.id,
        status="PENDING",
        retry_count=2,
        max_retries=3
    )
    db_session.add(task)
    await db_session.commit()

    # Run worker cycle (this is the 3rd attempt, matching max_retries)
    await process_pending_tasks()

    # Refresh task state directly from database
    await db_session.refresh(task)
    assert task.status == "MAX_RETRIES_EXCEEDED"
    assert task.retry_count == 3
