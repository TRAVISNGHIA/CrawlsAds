import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.logger import get_logger

from database.mongo import connect_db, disconnect_db
from utils.file_utils import ensure_storage_dirs

from services.Scheduler_service import (
    start_scheduler,
    stop_scheduler,
)

from api.health_api import router as health_router
from api.crawl_api import router as crawl_router
from api.result_api import router as result_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_storage_dirs()

        await connect_db()
        logger.info("MongoDB connected")

        start_scheduler()
        logger.info("Scheduler started")

        logger.info("SEM Checker API started")

        yield

    finally:
        logger.info("Shutting down SEM Checker API...")

        stop_scheduler()
        logger.info("Scheduler stopped")

        await disconnect_db()
        logger.info("MongoDB disconnected")
        logger.info("SEM Checker API stopped")


app = FastAPI(
    title="SEM Checker API",
    description="Automated Google SEM ad detection and monitoring tool",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
storage_dir = os.path.join(
    os.path.dirname(__file__),
    "storage",
)
os.makedirs(storage_dir, exist_ok=True)

app.mount(
    "/storage",
    StaticFiles(directory=storage_dir),
    name="storage",
)
app.include_router(health_router, prefix="/api")
app.include_router(crawl_router, prefix="/api")
app.include_router(result_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )