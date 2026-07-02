import logging
import httpx
from datetime import datetime
from app.models.task import SyncTask
from app.core.config import settings

logger = logging.getLogger("optout_integration")

# Tokens that the dispatcher treats as a "dry-run" shortcut for local dev.
# These are rejected outright in strict (production) mode.
_MOCK_PREFIXES = ("_mock_token", "mock_", "_mock")


def _is_mock_token(value: str) -> bool:
    if not value:
        return False
    low = value.lower()
    return any(low.endswith(suffix) for suffix in ("_mock_token",)) or low in {
        "mock", "gohighlevel_mock_token", "ghl_mock_token",
        "hubspot_mock_token", "salesforce_mock_token",
    }


class IntegrationDispatcher:
    """Dispatches opt-out updates to various downstream CRM, Dialer, or Webhook target APIs."""

    def __init__(self):
        # Reuse HTTP client to leverage connection pooling
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def dispatch(self, task: SyncTask) -> bool:
        """Executes a dispatch task to a downstream system.
        Returns True on success. Raises exceptions on failure to trigger retries.
        """
        integration = task.integration
        opt_out = task.opt_out

        if not integration.is_active:
            logger.info(f"Skipping dispatch for deactivated integration: {integration.name}")
            return True

        # Strict-mode guard: never silently swallow a "mock" credential in production.
        token = (integration.credentials or {}).get("access_token")
        if settings.is_strict and token and _is_mock_token(token):
            raise RuntimeError(
                f"Refusing to dispatch to integration '{integration.name}' with mock credentials. "
                "Rotate to a real access token before deploying."
            )

        logger.info(
            f"Dispatching task {task.id} (Identifier: {opt_out.identifier}) to "
            f"{integration.name} ({integration.type})"
        )

        # HubSpot integration
        if integration.type == "hubspot":
            return await self._dispatch_to_hubspot(integration, opt_out)

        # GoHighLevel integration
        elif integration.type == "gohighlevel":
            return await self._dispatch_to_gohighlevel(integration, opt_out)

        # Salesforce integration
        elif integration.type == "salesforce":
            return await self._dispatch_to_salesforce(integration, opt_out)

        # Generic webhook destination
        elif integration.type == "generic_webhook":
            return await self._dispatch_to_generic_webhook(integration, opt_out)

        else:
            raise ValueError(f"Unsupported integration type: {integration.type}")

    async def _dispatch_to_hubspot(self, integration, opt_out) -> bool:
        token = integration.credentials.get("access_token")

        # Short-circuit if mock token is detected (only in non-strict / dev mode)
        if not settings.is_strict and token == "hubspot_mock_token":
            logger.info("[Mock HubSpot] Successfully updated contact preference.")
            return True

        # Real HTTP Ingestion
        # 1. Search contact by email or phone
        search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        is_email = "@" in opt_out.identifier
        filter_property = "email" if is_email else "phone"

        search_query = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": filter_property,
                    "operator": "EQ",
                    "value": opt_out.identifier
                }]
            }],
            "properties": ["hs_do_not_email", "hs_do_not_call"]
        }

        response = await self.client.post(search_url, json=search_query, headers=headers)
        if response.status_code == 404:
            logger.warning(f"HubSpot endpoint not found: {response.text}")
            response.raise_for_status()
        elif response.status_code >= 400:
            logger.error(f"HubSpot Search API Error: {response.text}")
            response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        # If Contact exists, update the specific preference fields
        if results:
            contact_id = results[0]["id"]
            update_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"

            update_payload = {
                "properties": {
                    "hs_do_not_email": "true" if is_email else "false",
                    "hs_do_not_call": "false" if is_email else "true"
                }
            }
            update_resp = await self.client.patch(update_url, json=update_payload, headers=headers)
            update_resp.raise_for_status()
            logger.info(f"HubSpot Contact {contact_id} updated successfully.")
        else:
            # Contact not found. Create a new contact representing the opt-out preference
            create_url = "https://api.hubapi.com/crm/v3/objects/contacts"
            create_payload = {
                "properties": {
                    filter_property: opt_out.identifier,
                    "hs_do_not_email": "true" if is_email else "false",
                    "hs_do_not_call": "false" if is_email else "true"
                }
            }
            create_resp = await self.client.post(create_url, json=create_payload, headers=headers)
            create_resp.raise_for_status()
            logger.info(f"HubSpot contact created with opt-out settings: {opt_out.identifier}")

        return True

    async def _dispatch_to_salesforce(self, integration, opt_out) -> bool:
        instance_url = integration.credentials.get("instance_url", settings.SALESFORCE_INSTANCE_URL or "https://mock.salesforce.com")
        token = integration.credentials.get("access_token")

        if not settings.is_strict and token == "salesforce_mock_token":
            logger.info("[Mock Salesforce] Successfully logged opt-out contact record update.")
            return True

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        is_email = "@" in opt_out.identifier

        # 1. Query Salesforce contact by email or phone
        # Using SOSL / SOQL API
        query_prop = "Email" if is_email else "Phone"
        soql = f"SELECT Id, HasOptedOutOfEmail, DoNotCall FROM Contact WHERE {query_prop} = '{opt_out.identifier}' LIMIT 1"
        query_url = f"{instance_url}/services/data/v58.0/query/?q={soql}"

        response = await self.client.get(query_url, headers=headers)
        response.raise_for_status()

        records = response.json().get("records", [])

        if records:
            contact_id = records[0]["Id"]
            update_url = f"{instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"

            update_payload = {}
            if is_email:
                update_payload["HasOptedOutOfEmail"] = True
            else:
                update_payload["DoNotCall"] = True

            update_resp = await self.client.patch(update_url, json=update_payload, headers=headers)
            update_resp.raise_for_status()
            logger.info(f"Salesforce Contact {contact_id} updated successfully.")
        else:
            # Try searching lead table if contact doesn't exist
            soql_lead = f"SELECT Id FROM Lead WHERE {query_prop} = '{opt_out.identifier}' LIMIT 1"
            lead_query_url = f"{instance_url}/services/data/v58.0/query/?q={soql_lead}"
            lead_resp = await self.client.get(lead_query_url, headers=headers)
            lead_resp.raise_for_status()
            lead_records = lead_resp.json().get("records", [])

            if lead_records:
                lead_id = lead_records[0]["Id"]
                update_lead_url = f"{instance_url}/services/data/v58.0/sobjects/Lead/{lead_id}"
                update_payload = {}
                if is_email:
                    update_payload["HasOptedOutOfEmail"] = True
                else:
                    update_payload["DoNotCall"] = True

                update_resp = await self.client.patch(update_lead_url, json=update_payload, headers=headers)
                update_resp.raise_for_status()
                logger.info(f"Salesforce Lead {lead_id} updated successfully.")
            else:
                # Optional: create a lead with opt-out status
                create_url = f"{instance_url}/services/data/v58.0/sobjects/Lead"
                create_payload = {
                    "LastName": "OptOut-Contact",
                    "Company": "OptOut-AutoCreated",
                    query_prop: opt_out.identifier
                }
                if is_email:
                    create_payload["HasOptedOutOfEmail"] = True
                else:
                    create_payload["DoNotCall"] = True

                create_resp = await self.client.post(create_url, json=create_payload, headers=headers)
                create_resp.raise_for_status()
                logger.info(f"Salesforce Lead created with opt-out settings: {opt_out.identifier}")

        return True

    async def _dispatch_to_gohighlevel(self, integration, opt_out) -> bool:
        token = integration.credentials.get("access_token")
        location_id = integration.credentials.get("location_id")

        # Support simulation/mocking (only outside strict/production mode)
        if not settings.is_strict and token in ["gohighlevel_mock_token", "ghl_mock_token"]:
            logger.info("[Mock GoHighLevel] Successfully updated contact preference.")
            return True

        if not token:
            raise ValueError("GoHighLevel access token missing from credentials configuration")

        # GHL V2 API expects upsert to set dnc DNC flag
        url = "https://services.leadconnectorhq.com/contacts/upsert"
        headers = {
            "Authorization": f"Bearer {token}",
            "Version": "2021-04-15",
            "Content-Type": "application/json"
        }

        is_email = "@" in opt_out.identifier
        payload = {
            "dnc": True
        }
        if location_id:
            payload["locationId"] = location_id

        if is_email:
            payload["email"] = opt_out.identifier
        else:
            payload["phone"] = opt_out.identifier

        response = await self.client.post(url, json=payload, headers=headers)

        if response.status_code >= 400:
            logger.error(f"GoHighLevel Upsert API Error: Status={response.status_code}, Body={response.text}")
            response.raise_for_status()

        logger.info(f"GoHighLevel Contact updated/upserted successfully for {opt_out.identifier}")
        return True

    async def _dispatch_to_generic_webhook(self, integration, opt_out) -> bool:
        url = integration.credentials.get("url")
        custom_headers = integration.credentials.get("headers", {})

        if not url:
            raise ValueError("Generic webhook URL missing from credentials configuration")

        payload = {
            "identifier": opt_out.identifier,
            "channel": opt_out.channel,
            "reason": opt_out.reason,
            "timestamp": opt_out.created_at.isoformat()
        }

        headers = {
            "Content-Type": "application/json",
            **custom_headers
        }

        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Generic webhook dispatched successfully to {url}")
        return True


# Singleton dispatcher
dispatcher = IntegrationDispatcher()
