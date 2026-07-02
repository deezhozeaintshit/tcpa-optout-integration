from datetime import datetime, timezone
from sqlalchemy import String, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Integration(Base):
    __tablename__ = "integrations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[str] = mapped_column(String(50))  # hubspot, salesforce, generic_webhook
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    credentials: Mapped[dict] = mapped_column(JSON)  # OAuth tokens, API keys, URLs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
