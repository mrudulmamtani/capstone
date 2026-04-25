"""FastAPI entrypoint."""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, set_request_id
from app.scripts.seed_demo import seed_demo_if_needed


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log = get_logger("app")
    log.info("startup", env=settings.app_env, version=__version__)
    settings.ensure_dirs()
    if seed_demo_if_needed():
        log.info("demo.seed.ready")
    else:
        log.warning("demo.seed.skipped")
    yield
    log.info("shutdown")


app = FastAPI(
    title="VISION-SOP",
    description=(
        "Auto-generate, optimise, and enforce Standard Operating Procedures "
        "from existing CCTV using computer vision + LLMs."
    ),
    version=__version__,
    lifespan=lifespan,
    default_response_class=JSONResponse,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    set_request_id(rid)
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


app.include_router(api_router)
app.mount("/assets", StaticFiles(directory=str(settings.data_dir)), name="assets")


@app.get("/healthz", tags=["system"])
def healthz() -> dict:
    return {"status": "ok", "version": __version__, "env": settings.app_env}


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "service": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/healthz",
    }
