import json
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import EventLog
from app.schemas.event import EventCreate
from app.core.config import settings
from app.core.exceptions import NotFoundException


def create_event(db: Session, data: EventCreate, event_id: Optional[str] = None, request_id: Optional[str] = None) -> EventLog:
    if event_id is None:
        event_id = str(uuid.uuid4())
    if request_id is None:
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


def create_event_from_payload(db: Session, payload: dict) -> EventLog:
    event = EventLog(
        event_id=payload["event_id"],
        client_id=payload["client_id"],
        user_id=payload.get("user_id"),
        event_type=payload["event_type"],
        path=payload["path"],
        method=payload.get("method", "GET"),
        status_code=payload.get("status_code", 200),
        duration_ms=payload.get("duration_ms", 0),
        ip=payload.get("ip"),
        user_agent=payload.get("user_agent"),
        service_name=payload.get("service_name"),
        trace_id=payload.get("trace_id"),
        extra=payload.get("extra"),
        request_id=payload["request_id"],
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


def _build_kafka_payload(data: EventCreate, event_id: str, request_id: str) -> dict:
    return {
        "event_id": event_id,
        "client_id": data.client_id,
        "user_id": data.user_id,
        "event_type": data.event_type,
        "path": data.path,
        "method": data.method,
        "status_code": data.status_code,
        "duration_ms": data.duration_ms,
        "ip": data.ip,
        "user_agent": data.user_agent,
        "service_name": data.service_name,
        "trace_id": data.trace_id,
        "extra": json.dumps(data.extra) if data.extra else None,
        "request_id": request_id,
    }


def submit_event(db: Session, data: EventCreate) -> dict:
    event_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())

    if settings.EVENT_WRITE_MODE == "sync":
        create_event(db, data, event_id, request_id)
        return {"event_id": event_id, "request_id": request_id, "write_mode": "sync"}

    if settings.EVENT_WRITE_MODE == "kafka" and settings.KAFKA_PRODUCER_ENABLED:
        try:
            from app.kafka.producer import send_event_to_kafka

            payload = _build_kafka_payload(data, event_id, request_id)
            result = send_event_to_kafka(payload)
            return {
                "event_id": event_id,
                "request_id": request_id,
                "write_mode": "kafka",
                "kafka_topic": result["topic"],
                "kafka_partition": result["partition"],
                "kafka_offset": result["offset"],
            }
        except Exception as e:
            create_event(db, data, event_id, request_id)
            return {
                "event_id": event_id,
                "request_id": request_id,
                "write_mode": "sync_fallback",
                "fallback_reason": f"kafka send failed: {e}",
            }

    create_event(db, data, event_id, request_id)
    return {
        "event_id": event_id,
        "request_id": request_id,
        "write_mode": "sync_fallback",
        "fallback_reason": "producer disabled",
    }
