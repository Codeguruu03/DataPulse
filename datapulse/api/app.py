"""
FastAPI Application Factory for DataPulse Platform.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from datapulse import __version__
from datapulse.config import settings
from datapulse.api.routes.analytics import router as analytics_router
from datapulse.api.routes.quality import router as quality_router
from datapulse.api.routes.pipeline import router as pipeline_router


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    app = FastAPI(
        title="DataPulse API",
        description="Data Quality-Aware Cloud Data Engineering Platform API & Analytics Serving Layer",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API Routers
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    app.include_router(pipeline_router, prefix="/api/v1")

    # Static UI Dashboard
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/dashboard", StaticFiles(directory=str(static_dir), html=True), name="static")

    @app.get("/health", tags=["Health"])
    def health_check():
        return {
            "status": "HEALTHY",
            "version": __version__,
            "deployment_mode": settings.DEPLOYMENT_MODE,
            "storage_backend": settings.STORAGE_BACKEND,
            "warehouse_backend": settings.WAREHOUSE_BACKEND,
        }

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/dashboard/index.html")

    return app


app = create_app()
