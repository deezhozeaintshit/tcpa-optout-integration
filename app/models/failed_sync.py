from datetime import datetime, timezone
from sqlalchemy import Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class FailedSync(Base):
    __tablename__ = "failed_syncs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sync_task_id: Mapped[int] = mapped_column(ForeignKey("sync_tasks.id", ondelete="CASCADE"), index=True)
    error_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    sync_task = relationship("SyncTask")
