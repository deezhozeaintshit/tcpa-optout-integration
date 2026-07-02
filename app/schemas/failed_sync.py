from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FailedSyncResponse(BaseModel):
    id: int
    sync_task_id: int
    error_payload: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
