import json
import uuid
from sqlalchemy.orm import Session
from app.db.models import EventLog
from app.schemas.event import EventCreate
from app.core.exceptions import NotFoundException


def create_event(db: Session, data: EventCreate) -> EventLog:
    event_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())

    event = EventLog(
        event_id=event_id,
        client_id=data.client_id,
        user_id=data.user_id,
        event_type=data.event_type,
        path=data.path,
        method=data.method,
        status_code=data.status_code,
        duration_ms=data.duration_ms,
        ip=data.ip,
        user_agent=data.user_agent,
        service_name=data.service_name,
        trace_id=data.trace_id,
        extra=json.dumps(data.extra) if data.extra else None,
        request_id=request_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: str) -> EventLog:
    event = db.query(EventLog).filter(EventLog.event_id == event_id).first()
    if not event:
        raise NotFoundException(message=f"Event {event_id} not found")
    return event
