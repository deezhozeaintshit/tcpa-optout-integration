import pytest
import json
from datetime import datetime
from sqlalchemy import select
from app.models.optout import OptOut
from app.models.integration import Integration
from app.models.task import SyncTask
from app.models.failed_sync import FailedSync
from app.services.extraction import extraction_service
from app.core.worker import process_pending_tasks

@pytest.mark.anyio
async def test_extraction_service_fallback():
    """Verify that extraction service fallback performs correctly when Gemini API is unconfigured/mocked."""
    # Test opt-out sms keyword matches
    res1 = await extraction_service.extract_intent("Please stop sending me messages")
    assert res1.is_opt_out is True
    assert res1.confidence_score > 0.8
    
    # Test non-opt-out sms keyword
    res2 = await extraction_service.extract_intent("Hello, when will my order arrive?")
    assert res2.is_opt_out is False
    assert res2.confidence_score == 0.0
    
    # Test target extraction (email)
    res3 = await extraction_service.extract_intent("Please remove test@example.com from your list")
    assert res3.is_opt_out is True
    assert res3.extracted_target == "test@example.com"
    assert res3.target_type == "email"
    
    # Test target extraction (phone)
    res4 = await extraction_service.extract_intent("Please take +14155552671 off your list")
    assert res4.is_opt_out is True
    assert res4.extracted_target == "+14155552671"
    assert res4.target_type == "phone"

@pytest.mark.anyio
async def test_twilio_sms_ingest_intent(client, db_session):
    """Verify that Twilio webhooks call the extraction pipeline and persist the opt-outs properly."""
    # Seed integration
    integration = Integration(
        name="HubSpot Mock",
        type="hubspot",
        is_active=True,
        credentials={"access_token": "hubspot_mock_token"}
    )
    db_session.add(integration)
    await db_session.commit()

    # Ingestion check with opt-out
    resp = await client.post(
        "/api/v1/ingest/twilio",
        data={"From": "+14155559999", "To": "+18885551111", "Body": "Please stop calling me", "MessageSid": "SM12345"}
    )
    assert resp.status_code == 200
    assert "You have been successfully opted out" in resp.text

    # Verify db record exists
    res = await db_session.execute(select(OptOut).where(OptOut.identifier == "+14155559999"))
    record = res.scalars().first()
    assert record is not None
    assert record.channel == "sms"
    assert record.raw_payload["MessageSid"] == "SM12345"

@pytest.mark.anyio
async def test_email_ingest_formats(client, db_session):
    """Verify that /email accepts both JSON (IMAP) and multipart (SendGrid) formats and processes them."""
    # 1. Test SendGrid multipart/form-data format
    resp1 = await client.post(
        "/api/v1/ingest/email",
        data={
            "from": "Alice <alice@test.com>",
            "to": "support@yourdomain.com",
            "subject": "UNSUBSCRIBE me please",
            "text": "Please take Alice off your list"
        }
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "processed"
    assert resp1.json()["identifier"] == "alice@test.com"

    # 2. Test IMAP JSON format
    resp2 = await client.post(
        "/api/v1/ingest/email",
        json={
            "from": "Bob <bob@test.com>",
            "to": "support@yourdomain.com",
            "subject": "Stop sending mail",
            "text": "Take me off your mailing list",
            "timestamp": "2026-07-02T10:00:00Z"
        }
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "processed"
    assert resp2.json()["identifier"] == "bob@test.com"

    # Verify records in database
    res = await db_session.execute(select(OptOut).where(OptOut.channel == "email"))
    records = res.scalars().all()
    assert len(records) == 2
    identifiers = [r.identifier for r in records]
    assert "alice@test.com" in identifiers
    assert "bob@test.com" in identifiers

@pytest.mark.anyio
async def test_generic_json_mapping_paths(client, db_session):
    """Verify generic webhook dynamic path parameter lookups."""
    # Custom nested JSON payload
    payload = {
        "contact": {
            "user_phone": "+14155557711",
            "email_addr": "clara@test.com"
        },
        "meta": {
            "message": "remove me from your list"
        }
    }
    
    headers = {"X-API-Key": "secure_admin_api_key_change_me"}
    
    # Post with custom query parameters for path lookup
    resp = await client.post(
        "/api/v1/ingest/generic?phone_key=contact.user_phone&email_key=contact.email_addr&text_key=meta.message",
        json=payload,
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processed"
    assert data["identifier"] == "clara@test.com"  # prioritize email in mapping extraction

    # Verify database
    res = await db_session.execute(select(OptOut).where(OptOut.identifier == "clara@test.com"))
    record = res.scalars().first()
    assert record is not None
    assert record.channel == "api"
    assert record.reason == "remove me from your list"

@pytest.mark.anyio
async def test_gohighlevel_dispatcher_and_failure_logging(db_session):
    """Verify GoHighLevel adapter dispatching and recording errors to failed_syncs table."""
    # 1. Setup GoHighLevel Mock Integration
    ghl_integration = Integration(
        name="GHL Main",
        type="gohighlevel",
        is_active=True,
        credentials={"access_token": "gohighlevel_mock_token", "location_id": "loc_123"}
    )
    db_session.add(ghl_integration)
    
    # 2. Setup Broken Webhook Integration (to trigger failure)
    broken_integration = Integration(
        name="Broken Webhook",
        type="generic_webhook",
        is_active=True,
        credentials={"url": "http://broken-destination-xyz.com/webhook"}
    )
    db_session.add(broken_integration)
    await db_session.commit()
    
    # 3. Create OptOut record
    opt_out = OptOut(
        identifier="+14155550000",
        channel="sms",
        raw_payload={},
        reason="STOP"
    )
    db_session.add(opt_out)
    await db_session.commit()
    
    # 4. Stage sync tasks
    task_ghl = SyncTask(
        opt_out_id=opt_out.id,
        integration_id=ghl_integration.id,
        status="PENDING"
    )
    task_broken = SyncTask(
        opt_out_id=opt_out.id,
        integration_id=broken_integration.id,
        status="PENDING"
    )
    db_session.add(task_ghl)
    db_session.add(task_broken)
    await db_session.commit()
    
    # Run queue processing worker loop
    await process_pending_tasks()
    
    # Refresh tasks state
    await db_session.refresh(task_ghl)
    await db_session.refresh(task_broken)
    
    # GHL mock token should result in COMPLETED
    assert task_ghl.status == "COMPLETED"
    
    # Broken webhook should result in FAILED status and write a record to failed_syncs table
    assert task_broken.status == "FAILED"
    assert task_broken.retry_count == 1
    assert task_broken.last_error is not None
    
    # Check failed_syncs table record
    res = await db_session.execute(select(FailedSync).where(FailedSync.sync_task_id == task_broken.id))
    failed_record = res.scalars().first()
    assert failed_record is not None
    assert failed_record.error_payload["error"] is not None
    assert failed_record.error_payload["integration"]["name"] == "Broken Webhook"

@pytest.mark.anyio
async def test_failed_syncs_endpoint(client, db_session):
    """Verify that failed-syncs endpoint requires API key and returns failed sync records."""
    # 1. Create a failed sync record directly in the DB session
    failed_sync = FailedSync(
        sync_task_id=99,
        error_payload={"error": "Something went wrong", "integration": {"name": "Mock CRM"}}
    )
    db_session.add(failed_sync)
    await db_session.commit()

    # 2. Query without API key -> should fail with 401
    resp_unauth = await client.get("/api/v1/optouts/failed-syncs")
    assert resp_unauth.status_code == 401

    # 3. Query with incorrect API key -> should fail with 401
    resp_wrong = await client.get("/api/v1/optouts/failed-syncs", headers={"X-API-Key": "wrong"})
    assert resp_wrong.status_code == 401

    # 4. Query with correct API key -> should return the failure logs
    resp_auth = await client.get(
        "/api/v1/optouts/failed-syncs",
        headers={"X-API-Key": "secure_admin_api_key_change_me"}
    )
    assert resp_auth.status_code == 200
    data = resp_auth.json()
    assert len(data) == 1
    assert data[0]["sync_task_id"] == 99
    assert data[0]["error_payload"]["error"] == "Something went wrong"
