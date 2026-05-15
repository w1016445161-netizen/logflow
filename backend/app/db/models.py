import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.base import Base


class EventLog(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=True)
    event_type = Column(String(50), nullable=False)
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False, default="GET")
    status_code = Column(Integer, nullable=False, default=200)
    duration_ms = Column(Integer, nullable=False, default=0)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    service_name = Column(String(100), nullable=True)
    trace_id = Column(String(36), nullable=True)
    extra = Column(Text, nullable=True)
    request_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
