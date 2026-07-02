import pytest
from app.core.normalizer import normalize_phone, normalize_email
from app.models.integration import Integration
from app.models.optout import OptOut
from app.models.task import SyncTask
from sqlalchemy import select

def test_normalization():
    """Verify phone E.164 formatting and email lowercasing logic."""
    # Phone numbers
    assert normalize_phone("415-555-1234") == "+14155551234"
    assert normalize_phone("+1 (415) 555-1234") == "+14155551234"
    assert normalize_phone("14155551234") == "+14155551234"
    assert normalize_phone("+447911123456") == "+447911123456"
    assert normalize_phone(None) is None
    
    # Emails
    assert normalize_email(" TEST@Example.Com ") == "test@example.com"
    assert normalize_email(None) is None

@pytest.mark.anyio
async def test_twilio_sms_ingestion(client, db_session):
    """Verify that Twilio webhooks successfully parse opt-out requests and queue sync tasks."""
    # Seed an active integration
    integration = Integration(
        name="HubSpot CRM",
        type="hubspot",
        is_active=True,
        credentials={"access_token": "hubspot_mock_token"}
    )
    db_session.add(integration)
    await db_session.commit()

    # Post Twilio webhook (non-optout message)
    resp = await client.post(
        "/api/v1/ingest/twilio",
        data={"From": "+14155551234", "To": "+18885551111", "Body": "Hello there"}
    )
    assert resp.status_code == 200
    assert "Response" in resp.text
    assert "Message" not in resp.text  # No reply should be triggered for neutral messages

    # Post Twilio webhook (opt-out message "STOP")
    resp_stop = await client.post(
        "/api/v1/ingest/twilio",
        data={"From": "+14155551234", "To": "+18885551111", "Body": " STOP "}
    )
    assert resp_stop.status_code == 200
    assert "You have been successfully opted out" in resp_stop.text

    # Verify database state
    optouts_result = await db_session.execute(select(OptOut))
    optouts = optouts_result.scalars().all()
    assert len(optouts) == 1
    assert optouts[0].identifier == "+14155551234"
    assert optouts[0].channel == "sms"
    assert optouts[0].reason == "STOP"

    # Verify background task was queued
    tasks_result = await db_session.execute(select(SyncTask))
    tasks = tasks_result.scalars().all()
    assert len(tasks) == 1
    assert tasks[0].status == "PENDING"
    assert tasks[0].integration_id == integration.id

@pytest.mark.anyio
async def test_sendgrid_email_ingestion(client, db_session):
    """Verify that SendGrid inbound parse webhook handles email opt-out requests."""
    # Seed an active integration
    integration = Integration(
        name="Salesforce Enterprise",
        type="salesforce",
        is_active=True,
        credentials={"instance_url": "https://mock.salesforce.com", "access_token": "salesforce_mock_token"}
    )
    db_session.add(integration)
    await db_session.commit()

    # SendGrid format: from, to, subject, text
    resp = await client.post(
        "/api/v1/ingest/sendgrid",
        data={
            "from": "John Doe <John.Doe@Example.com>",
            "to": "optout@yourcompany.com",
            "subject": "Please unsubscribe me from mailing list",
            "text": "Hi, stop sending me emails. Thanks."
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processed"
    assert data["identifier"] == "john.doe@example.com"

    # Verify DB entry
    optouts_result = await db_session.execute(select(OptOut))
    optouts = optouts_result.scalars().all()
    assert len(optouts) == 1
    assert optouts[0].identifier == "john.doe@example.com"
    assert optouts[0].channel == "email"

@pytest.mark.anyio
async def test_generic_json_ingestion(client, db_session):
    """Verify API Key authentication and JSON payload parsing on the generic ingest endpoint."""
    integration = Integration(
        name="Webhook CRM",
        type="generic_webhook",
        is_active=True,
        credentials={"url": "https://mock.crm.com/optout"}
    )
    db_session.add(integration)
    await db_session.commit()

    payload = {
        "identifier": "+15556667777",
        "channel": "web",
        "reason": "PORTAL_FORM"
    }

    # Test missing API key
    resp_unauth = await client.post("/api/v1/ingest/generic", json=payload)
    assert resp_unauth.status_code == 401

    # Test correct API key
    headers = {"X-API-Key": "secure_admin_api_key_change_me"}
    resp = await client.post("/api/v1/ingest/generic", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processed"
    assert data["identifier"] == "+15556667777"
    assert data["channel"] == "web"
