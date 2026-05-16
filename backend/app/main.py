import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.router import router
from app.core.exceptions import AppException
from app.core.response import error_response
from app.core.logging import setup_logging, get_logger
from app.db.base import Base
from app.db.session import engine
from app.kafka.producer import close_kafka_producer
import app.db.models  # noqa: F401 - ensure models are registered for create_all

logger = get_logger("logflow.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    yield
    close_kafka_producer()


app = FastAPI(title="LogFlow", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    start = time.monotonic()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        log_extra = {
            "request_id": request.state.request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code if response else 500,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else "",
        }
        logger.info("request_completed", extra=log_extra)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning("app_exception", extra={
        "request_id": req_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": exc.status_code,
        "error": exc.message,
        "exception_type": type(exc).__name__,
    })
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=exc.code, message=exc.message, request_id=req_id, data=exc.data),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error("unhandled_exception", extra={
        "request_id": req_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": 500,
        "error": str(exc),
        "exception_type": type(exc).__name__,
    })
    return JSONResponse(
        status_code=500,
        content=error_response(code="INTERNAL_ERROR", message="internal server error", request_id=req_id),
    )
