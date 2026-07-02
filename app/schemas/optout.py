from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any, Dict

class OptOutBase(BaseModel):
    identifier: str = Field(..., description="Phone number (E.164) or email address")
    channel: str = Field(..., description="Ingestion channel: sms, email, web, or api")
    reason: Optional[str] = Field(None, description="Keywords such as STOP, UNSUBSCRIBE, CANCEL")
    ip_address: Optional[str] = Field(None, description="IP address of requester")

class OptOutCreate(OptOutBase):
    raw_payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Inbound raw payload dump")

class OptOutResponse(OptOutBase):
    id: int
    raw_payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
