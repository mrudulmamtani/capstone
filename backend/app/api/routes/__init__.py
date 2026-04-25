from fastapi import APIRouter

from app.api.routes import alerts, analytics, monitor, sessions, sops

api_router = APIRouter(prefix="/api")
api_router.include_router(sops.router)
api_router.include_router(sessions.router)
api_router.include_router(alerts.router)
api_router.include_router(analytics.router)
api_router.include_router(monitor.router)
