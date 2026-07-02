"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import health, targets
from app.services.target_service import (
    TargetNameConflictError,
    TargetNotAllowedError,
    TargetNotFoundError,
)

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


# Domain-exception -> HTTP-response translation lives here, once, instead of
# being re-implemented in every router. New resources (scans, findings, ...)
# only need to raise these same exception types to get consistent responses.
@app.exception_handler(TargetNotFoundError)
async def target_not_found_handler(request: Request, exc: TargetNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Target '{exc}' not found."})


@app.exception_handler(TargetNotAllowedError)
async def target_not_allowed_handler(request: Request, exc: TargetNotAllowedError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": (
                f"Host '{exc}' is not part of the local lab whitelist. "
                "Only hosts defined in lab/ (Módulo 2) can be registered as targets."
            )
        },
    )


@app.exception_handler(TargetNameConflictError)
async def target_name_conflict_handler(
    request: Request, exc: TargetNameConflictError
) -> JSONResponse:
    return JSONResponse(
        status_code=409, content={"detail": f"A target named '{exc}' already exists."}
    )


app.include_router(health.router)
app.include_router(targets.router)
