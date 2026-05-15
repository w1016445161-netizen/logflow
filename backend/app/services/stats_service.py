from sqlalchemy import func
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
        "top_paths": top_paths,
        "top_event_types": top_event_types,
    }
