"""Aereo Geospatial File Measurement API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import Base, engine
from app.routes.files import router as files_router
from app.middleware.logging_middleware import LoggingMiddleware
from app.utils.logging import setup_logging
from app.utils.config import settings

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    yield


app = FastAPI(
    title="Aereo Geospatial Measurement API",
    version="2.0.0",
    description="Upload geospatial files (Shapefile/KML) and receive area/length measurements with CRS handling.",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.include_router(files_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
