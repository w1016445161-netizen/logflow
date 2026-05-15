from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    client_id: str
    user_id: Optional[str] = None
    event_type: str
    path: str
    method: str = "GET"
    status_code: int = 200
    duration_ms: int = 0
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    service_name: Optional[str] = "gateway-service"
    trace_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
