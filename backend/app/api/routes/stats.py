from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.stats_service import get_overview
from app.core.response import success_response

router = APIRouter()


@router.get("/stats/overview")
def stats_overview(request: Request, db: Session = Depends(get_db)):
    stats = get_overview(db)
    return success_response(data=stats, request_id=request.state.request_id)
