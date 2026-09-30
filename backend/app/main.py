"""
FastAPI application entry point.

Run locally with:
    uvicorn app.main:app --reload

This file is intentionally minimal at this stage of Phase 15: it sets up the
app, logging, and a health check. Repository/indexing/query routers are
added in later steps once models.py has the status field they depend on.
"""

import logging
import sys

from fastapi import FastAPI

from app.api.schemas import HealthResponse
from app.api.repositories import router as repositories_router
from app.api.query import router as query_router
app.include_router(query_router)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
# Configured here, at the top of the entry point, so every module that does
# `logging.getLogger(__name__)` inherits this format/level automatically —
# no per-file logging setup needed anywhere else in the codebase.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

APP_VERSION = "0.15.0"  # bumped per phase for now; not a strict semver promise

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Codebase RAG API",
    description="Ask natural-language questions about a GitHub repository, with grounded citations.",
    version=APP_VERSION,
)

app.include_router(repositories_router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Codebase RAG API starting up (version=%s)", APP_VERSION)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Codebase RAG API shutting down")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """
    Basic liveness check.

    Deliberately does NOT check DB/Chroma connectivity yet — that's a
    reasonable next iteration (a "readiness" check vs this "liveness" check)
    but out of scope for the first working slice of Phase 15.
    """
    return HealthResponse(status="ok", version=APP_VERSION)