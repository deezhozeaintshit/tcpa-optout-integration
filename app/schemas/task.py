from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.schemas.optout import OptOutResponse
from app.schemas.integration import IntegrationResponse

class SyncTaskResponse(BaseModel):
    id: int
    opt_out_id: int
    integration_id: int
    status: str
    retry_count: int
    max_retries: int
    last_error: Optional[str] = None
    next_retry_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Nested response objects for full audit details
    opt_out: Optional[OptOutResponse] = None
    integration: Optional[IntegrationResponse] = None

    model_config = ConfigDict(from_attributes=True)
