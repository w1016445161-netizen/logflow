from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.event import EventCreate
from app.services.event_service import submit_event, get_event
from app.services.rate_limit_service import check_rate_limit
from app.core.exceptions import RateLimitException
from app.core.response import success_response

router = APIRouter()


@router.post("/events")
def create_event_endpoint(data: EventCreate, request: Request, db: Session = Depends(get_db)):
    result = check_rate_limit(data.client_id, data.ip)
    if result["limited"]:
        raise RateLimitException(data={
            "limit": result["limit"],
            "window_seconds": result["window_seconds"],
            "current_count": result["current_count"],
        })

    resp_data = submit_event(db, data)
    return success_response(data=resp_data, request_id=request.state.request_id)


@router.get("/events/{event_id}")
def get_event_endpoint(event_id: str, request: Request, db: Session = Depends(get_db)):
    event = get_event(db, event_id)
    return success_response(
        data={
            "event_id": event.event_id,
            "client_id": event.client_id,
            "user_id": event.user_id,
            "event_type": event.event_type,
            "path": event.path,
            "method": event.method,
            "status_code": event.status_code,
            "duration_ms": event.duration_ms,
            "ip": event.ip,
            "user_agent": event.user_agent,
            "service_name": event.service_name,
            "trace_id": event.trace_id,
            "extra": event.extra,
            "request_id": event.request_id,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        },
        request_id=request.state.request_id,
    )
