"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, targets

settings = get_settings()
logging.basicConfig(level=settings.backend_log_level.upper())

app = FastAPI(
    title="VulnScan Platform API",
    description="Orchestrates target registration, scanning, and findings for the local lab.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(targets.router)
