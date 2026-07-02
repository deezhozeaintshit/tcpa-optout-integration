from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import Optional, List


# Tokens/keys that the codebase uses as insecure defaults and which MUST be
# rotated away from before exposing the service to the public internet.
KNOWN_INSECURE_DEFAULTS = {
    "default_twilio_token_change_me",
    "secure_admin_api_key_change_me",
    "hubspot_mock_token",
    "gohighlevel_mock_token",
    "ghl_mock_token",
    "salesforce_mock_token",
    "mock",
    "default_gemini_key_change_me",
}


class Settings(BaseSettings):
    # --- Runtime environment ---
    ENVIRONMENT: str = "development"  # development | staging | production
    LOG_FORMAT: str = "console"      # console | json
    REQUIRE_STRICT_SECRETS: bool = False  # Set true (or ENVIRONMENT=production) to enforce placeholder-secret validation

    # --- HTTP / CORS ---
    ALLOWED_ORIGINS: List[str] = ["*"]  # Tighten to your domain(s) in production

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/data.db"
    SQLITE_WAL_MODE: bool = True  # PRAGMA journal_mode=WAL for concurrency

    # --- Auth / secrets ---
    ADMIN_API_KEY: str = "secure_admin_api_key_change_me"
    TWILIO_AUTH_TOKEN: str = "default_twilio_token_change_me"

    # --- Worker ---
    WORKER_POLL_INTERVAL: int = 5
    MAX_RETRIES: int = 5
    BACKOFF_FACTOR: int = 2
    WORKER_ENABLED: bool = True

    # --- AI / Gemini ---
    GEMINI_API_KEY: str = "mock"
    GEMINI_API_BASE_URL: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # --- Downstream CRM credentials ---
    HUBSPOT_ACCESS_TOKEN: Optional[str] = "hubspot_mock_token"
    SALESFORCE_INSTANCE_URL: Optional[str] = "https://mock.salesforce.com"
    SALESFORCE_ACCESS_TOKEN: Optional[str] = "salesforce_mock_token"
    GOHIGHLEVEL_ACCESS_TOKEN: Optional[str] = "gohighlevel_mock_token"
    GOHIGHLEVEL_LOCATION_ID: Optional[str] = "mock_location_123"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Convenience flags ---
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_strict(self) -> bool:
        """Strict means: refuse insecure defaults, disable mock-token shortcuts, fail-loud on misconfig."""
        return self.is_production or self.REQUIRE_STRICT_SECRETS

    # --- Validators ---
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        """ALLOWED_ORIGINS may be a comma-separated string in env files."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @model_validator(mode="after")
    def _enforce_strict_secrets(self):
        """When REQUIRE_STRICT_SECRETS (default True) and ENVIRONMENT=production,
        refuse to start with any of the well-known placeholder/default secrets.
        """
        if not self.is_strict:
            return self

        offenders = []
        checks = {
            "ADMIN_API_KEY": self.ADMIN_API_KEY,
            "TWILIO_AUTH_TOKEN": self.TWILIO_AUTH_TOKEN,
        }
        for name, val in checks.items():
            if val in KNOWN_INSECURE_DEFAULTS:
                offenders.append(name)

        if offenders:
            raise ValueError(
                "Refusing to start with insecure default secrets: "
                + ", ".join(offenders)
                + ". Set real values in your .env or disable REQUIRE_STRICT_SECRETS for development."
            )
        return self


settings = Settings()
