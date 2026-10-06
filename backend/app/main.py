# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.documents import router as documents_router
from app.api.routes.analysis_pipeline import (
    router as analysis_pipeline_router,
)

from app.core.config import settings
from app.core.database import Base, engine

# Import models so SQLAlchemy registers them with Base.metadata.
# Import models so SQLAlchemy registers them with Base.metadata.
from app.models import analysis
from app.models import document
from app.models import analysis_result


app = FastAPI(
    title="Indian Standards Recommendation Engine",
    description=(
        "AI-powered recommendation engine for identifying "
        "applicable Indian Standards for procurement specifications."
    ),
    version="1.0.0",
)


# ----------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------

app.include_router(
    health_router,
    prefix="/api",
    tags=["Health"],
)


app.include_router(
    analyses_router,
    prefix="/api/analyses",
    tags=["Analyses"],
)


app.include_router(
    documents_router,
    prefix="/api/documents",
    tags=["Documents"],
)


# IMPORTANT:
# analysis_pipeline.py already defines:
#
#     prefix="/api/analyses"
#
# Therefore do NOT add another prefix here.
app.include_router(
    analysis_pipeline_router,
)


# ----------------------------------------------------------------------
# Database initialization
# ----------------------------------------------------------------------

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(
        bind=engine
    )


# ----------------------------------------------------------------------
# Root
# ----------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": (
            "Indian Standards Recommendation Engine"
        ),
        "status": "running",
    }