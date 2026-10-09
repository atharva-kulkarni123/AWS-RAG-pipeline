import sys
import os
import logging

# Ensure retrieval modules import their own config before ingestion modules.
retrieval_path = os.path.join(os.path.dirname(__file__), "../RAG-Retrieval")
ingestion_path = os.path.join(os.path.dirname(__file__), "../RAG-Ingestion")
if retrieval_path not in sys.path:
    sys.path.insert(0, retrieval_path)
if ingestion_path not in sys.path:
    sys.path.insert(1, ingestion_path)

from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.routes import health, query, ingest
from api.middleware.logging import RequestLoggingMiddleware, setup_logging
from api.middleware.auth import CognitoAuthMiddleware

# Boot structured JSON logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the container starts.
    RAGService is expensive to initialise (DB connection pool,
    Bedrock client) so we do it once and attach it to app.state
    so every request reuses the same instance.
    """
    logger.info("startup: initialising RAGService")
    from rag_service import RAGService
    app.state.rag_service = RAGService()
    logger.info("startup: RAGService ready")
    yield
    # Cleanup on shutdown (connection pools etc.)
    logger.info("shutdown: cleaning up")


app = FastAPI(
    title="RAG Pipeline API",
    description="Production RAG pipeline on AWS",
    version="1.0.0",
    lifespan=lifespan,
    # Hide docs in prod by setting HIDE_DOCS=true
    docs_url=None if os.getenv("HIDE_DOCS") == "true" else "/docs",
    redoc_url=None if os.getenv("HIDE_DOCS") == "true" else "/redoc",
)

# Middleware — order matters: outer middleware runs first on request
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CognitoAuthMiddleware)

# Routes
app.include_router(health.router)
app.include_router(query.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")