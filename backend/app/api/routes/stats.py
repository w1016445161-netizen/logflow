from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.services.stats_service import (
    get_overview,
    get_top_paths,
    get_top_event_types,
    get_slow_requests,
    get_errors,
)
from app.services.cache_service import get_cached_or_compute
from app.core.response import success_response

router = APIRouter()
_ttl = settings.STATS_CACHE_TTL_SECONDS


@router.get("/stats/overview")
def stats_overview(request: Request, db: Session = Depends(get_db)):
    data = get_cached_or_compute(
        "logflow:stats:overview", _ttl,
        lambda: get_overview(db),
    )
    return success_response(data=data, request_id=request.state.request_id)


@router.get("/stats/top-paths")
def top_paths(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    data = get_cached_or_compute(
        f"logflow:stats:top_paths:limit:{limit}", _ttl,
        lambda: get_top_paths(db, limit),
    )
    return success_response(data=data, request_id=request.state.request_id)


@router.get("/stats/top-event-types")
def top_event_types(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    data = get_cached_or_compute(
        f"logflow:stats:top_event_types:limit:{limit}", _ttl,
        lambda: get_top_event_types(db, limit),
    )
    return success_response(data=data, request_id=request.state.request_id)


@router.get("/stats/slow-requests")
def slow_requests(
    request: Request,
    threshold_ms: int = Query(default=1000, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    data = get_cached_or_compute(
        f"logflow:stats:slow_requests:threshold:{threshold_ms}:limit:{limit}", _ttl,
        lambda: get_slow_requests(db, threshold_ms, limit),
    )
    return success_response(data=data, request_id=request.state.request_id)


@router.get("/stats/errors")
def errors(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    data = get_cached_or_compute(
        f"logflow:stats:errors:limit:{limit}", _ttl,
        lambda: get_errors(db, limit),
    )
    return success_response(data=data, request_id=request.state.request_id)
