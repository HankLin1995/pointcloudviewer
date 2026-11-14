from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes.projects import router as projects_router
from backend.app.config import Settings
from backend.app.db.database import Database
from backend.app.logging_config import configure_logging
from backend.app.schemas.project import HealthResponse
from backend.app.services.project_service import ProjectService


logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    configure_logging(settings.log_level)
    database = Database(settings.database_path)
    project_service = ProjectService(
        database=database,
        pointcloud_dir=settings.pointcloud_dir,
        project_slug=settings.public_project_slug,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database.initialize()
        project_service.seed_public_project()
        logger.info("Application ready pointcloud_dir=%s", settings.pointcloud_dir)
        yield
        logger.info("Application stopped")

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.database = database
    app.state.project_service = project_service

    @app.middleware("http")
    async def response_headers(request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled request failure path=%s", request.url.path)
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "frame-ancestors 'self' http://localhost:8501 http://127.0.0.1:8501"
        )
        if request.url.path.startswith("/pointclouds/"):
            response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    api = APIRouter(prefix="/api/v1")

    @api.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        database_status = "ready" if settings.database_path.exists() else "missing"
        pointcloud_status = (
            "ready" if (settings.pointcloud_dir / "ept.json").is_file() else "missing"
        )
        status = (
            "ok"
            if database_status == "ready" and pointcloud_status == "ready"
            else "degraded"
        )
        return HealthResponse(
            status=status,
            database=database_status,
            pointcloud=pointcloud_status,
        )

    api.include_router(projects_router)
    app.include_router(api)

    app.mount(
        f"/pointclouds/{settings.public_project_slug}",
        StaticFiles(directory=settings.pointcloud_dir, check_dir=True),
        name="pointcloud",
    )
    app.mount(
        "/",
        StaticFiles(directory=settings.frontend_dir, html=True, check_dir=True),
        name="frontend",
    )
    return app


app = create_app()
