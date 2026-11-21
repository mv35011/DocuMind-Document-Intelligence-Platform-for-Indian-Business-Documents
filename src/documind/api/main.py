from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from documind.api.routers import admin, auth, chat, documents, health
from documind.core.config import get_settings
from documind.core.logging import get_logger, setup_logging

logger = get_logger("documind.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging("DEBUG" if settings.DEBUG else "INFO")
    logger.info("DocuMind API starting up", environment=settings.ENVIRONMENT)
    yield
    logger.info("DocuMind API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="DocuMind API",
        version="0.1.0",
        description="Document Intelligence Platform for Indian Business Documents",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(admin.router)

    return app


app = create_app()
