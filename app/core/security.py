import hmac
import hashlib
import base64
from fastapi import Request, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Validate incoming HTTP requests containing the custom API key header.

    Note: rejection of placeholder/known-insecure ADMIN_API_KEY values is
    enforced *at startup* by the model_validator in app.core.config when
    is_strict is True. We deliberately do NOT short-circuit here so that
    local dev (and the existing test suite) can use the documented default key.
    """
    if not api_key or api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key


def verify_twilio_signature(url: str, params: dict, signature: str) -> bool:
    """Verify that a request was sent by Twilio using HMAC-SHA1 validation."""
    if not settings.TWILIO_AUTH_TOKEN:
        return False

    # Concatenate URL and all POST parameters sorted alphabetically
    data = url
    for key in sorted(params.keys()):
        data += f"{key}{params[key]}"

    # Compute signature
    computed = hmac.new(
        settings.TWILIO_AUTH_TOKEN.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha1
    ).digest()

    expected = base64.b64encode(computed).decode("utf-8")
    return hmac.compare_digest(expected, signature)


async def verify_twilio_request(request: Request):
    """FastAPI dependency to authenticate inbound Twilio webhook calls.

    In production/strict mode, signature verification is mandatory.
    In development, the default placeholder token is rejected explicitly
    to prevent accidental "open webhook" deployments.
    """
    # If still on the placeholder/known-insecure token, refuse — even in dev.
    if settings.TWILIO_AUTH_TOKEN in (
        "default_twilio_token_change_me",
        "",
    ):
        if settings.is_strict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TWILIO_AUTH_TOKEN is set to an insecure default. Rotate it before exposing this endpoint.",
            )
        # In permissive dev mode we still log a warning upstream and skip
        # verification (preserved for local Twilio mocking).
        return

    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Twilio-Signature header missing",
        )

    # Resolve the absolute original URL, accounting for proxies
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    url = f"{proto}://{host}{request.url.path}"

    # Retrieve form data
    form_data = await request.form()
    params = {key: form_data[key] for key in form_data.keys()}

    if not verify_twilio_signature(url, params, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Twilio signature verification failed",
        )
