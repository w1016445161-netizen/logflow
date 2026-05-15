from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.events import router as events_router
from app.api.routes.stats import router as stats_router

router = APIRouter(prefix="/api")
router.include_router(health_router, tags=["health"])
router.include_router(events_router, tags=["events"])
router.include_router(stats_router, tags=["stats"])
