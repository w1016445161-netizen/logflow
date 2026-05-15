from fastapi import APIRouter, Request
from app.core.response import success_response

router = APIRouter()


@router.get("/health")
def health(request: Request):
    return success_response(
        data={"status": "ok", "service": "LogFlow"},
        request_id=request.state.request_id,
    )
