import math
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.db.models import EventLog


def get_overview(db: Session) -> dict:
    total_events = db.query(EventLog).count()
    total_clients = db.query(func.count(func.distinct(EventLog.client_id))).scalar() or 0
    total_users = db.query(func.count(func.distinct(EventLog.user_id))).scalar() or 0
    error_events = db.query(EventLog).filter(EventLog.status_code >= 400).count()

    error_rate = (error_events / total_events) if total_events > 0 else 0.0

    avg_duration = db.query(func.avg(EventLog.duration_ms)).scalar()
    avg_duration_ms = round(avg_duration, 2) if avg_duration else 0

    # P95: fetch all duration values and compute in Python
    duration_rows = db.query(EventLog.duration_ms).all()
    duration_values = [row[0] for row in duration_rows]
    n = len(duration_values)
    if n == 0:
        p95_duration_ms = 0.0
    else:
        duration_values.sort()
        index = math.ceil(0.95 * n) - 1
        p95_duration_ms = float(duration_values[index])

    slow_request_count = db.query(EventLog).filter(EventLog.duration_ms >= 1000).count()

    top_paths_rows = (
        db.query(EventLog.path, func.count(EventLog.id).label("count"))
        .group_by(EventLog.path)
        .order_by(func.count(EventLog.id).desc())
        .limit(5)
        .all()
    )
    top_paths = [{"path": row.path, "count": row.count} for row in top_paths_rows]

    top_event_types_rows = (
        db.query(EventLog.event_type, func.count(EventLog.id).label("count"))
        .group_by(EventLog.event_type)
        .order_by(func.count(EventLog.id).desc())
        .limit(5)
        .all()
    )
    top_event_types = [{"event_type": row.event_type, "count": row.count} for row in top_event_types_rows]

    return {
        "total_events": total_events,
        "total_clients": total_clients,
        "total_users": total_users,
        "error_events": error_events,
        "error_rate": round(error_rate, 4),
        "avg_duration_ms": avg_duration_ms,
        "p95_duration_ms": p95_duration_ms,
        "slow_request_count": slow_request_count,
        "top_paths": top_paths,
        "top_event_types": top_event_types,
    }


def get_top_paths(db: Session, limit: int) -> list:
    rows = (
        db.query(
            EventLog.path,
            func.count(EventLog.id).label("count"),
            func.avg(EventLog.duration_ms).label("avg_duration_ms"),
            func.sum(case((EventLog.status_code >= 400, 1), else_=0)).label("error_count"),
        )
        .group_by(EventLog.path)
        .order_by(func.count(EventLog.id).desc())
        .limit(limit)
        .all()
    )
    result = []
    for row in rows:
        count = row.count
        error_count = row.error_count or 0
        result.append({
            "path": row.path,
            "count": count,
            "avg_duration_ms": round(row.avg_duration_ms, 2) if row.avg_duration_ms else 0.0,
            "error_count": error_count,
            "error_rate": round(error_count / count, 4) if count > 0 else 0.0,
        })
    return result


def get_top_event_types(db: Session, limit: int) -> list:
    rows = (
        db.query(
            EventLog.event_type,
            func.count(EventLog.id).label("count"),
            func.avg(EventLog.duration_ms).label("avg_duration_ms"),
        )
        .group_by(EventLog.event_type)
        .order_by(func.count(EventLog.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "event_type": row.event_type,
            "count": row.count,
            "avg_duration_ms": round(row.avg_duration_ms, 2) if row.avg_duration_ms else 0.0,
        }
        for row in rows
    ]


def get_slow_requests(db: Session, threshold_ms: int, limit: int) -> list:
    events = (
        db.query(EventLog)
        .filter(EventLog.duration_ms >= threshold_ms)
        .order_by(EventLog.duration_ms.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "event_id": e.event_id,
            "client_id": e.client_id,
            "user_id": e.user_id,
            "event_type": e.event_type,
            "path": e.path,
            "method": e.method,
            "status_code": e.status_code,
            "duration_ms": e.duration_ms,
            "trace_id": e.trace_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


def get_errors(db: Session, limit: int) -> dict:
    total_all = db.query(EventLog).count()
    total_error = db.query(EventLog).filter(EventLog.status_code >= 400).count()
    error_rate = (total_error / total_all) if total_all > 0 else 0.0

    top_error_paths_rows = (
        db.query(EventLog.path, func.count(EventLog.id).label("count"))
        .filter(EventLog.status_code >= 400)
        .group_by(EventLog.path)
        .order_by(func.count(EventLog.id).desc())
        .limit(5)
        .all()
    )
    top_error_paths = [{"path": r.path, "count": r.count} for r in top_error_paths_rows]

    recent_rows = (
        db.query(EventLog)
        .filter(EventLog.status_code >= 400)
        .order_by(EventLog.created_at.desc())
        .limit(limit)
        .all()
    )
    recent_errors = [
        {
            "event_id": e.event_id,
            "client_id": e.client_id,
            "path": e.path,
            "method": e.method,
            "status_code": e.status_code,
            "duration_ms": e.duration_ms,
            "trace_id": e.trace_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in recent_rows
    ]

    return {
        "total_error_events": total_error,
        "error_rate": round(error_rate, 4),
        "top_error_paths": top_error_paths,
        "recent_errors": recent_errors,
    }
