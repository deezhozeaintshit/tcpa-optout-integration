from datetime import datetime, timezone
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class OptOut(Base):
    __tablename__ = "optouts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    identifier: Mapped[str] = mapped_column(String(255), index=True)  # Normalized email or phone (E.164)
    channel: Mapped[str] = mapped_column(String(50))  # sms, email, web, api
    raw_payload: Mapped[dict] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)  # STOP, UNSUBSCRIBE, or custom
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
