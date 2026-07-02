from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any, Dict

class IntegrationBase(BaseModel):
    name: str = Field(..., description="Unique user-friendly name of this target integration")
    type: str = Field(..., description="Target system type: hubspot, salesforce, gohighlevel, generic_webhook")
    is_active: bool = Field(True, description="Whether this integration route is currently enabled")
    credentials: Dict[str, Any] = Field(..., description="Configuration dictionary containing URLs, tokens, headers")

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    credentials: Optional[Dict[str, Any]] = None

class IntegrationResponse(IntegrationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
