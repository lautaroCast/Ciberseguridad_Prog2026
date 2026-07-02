"""FastAPI application entrypoint for the Scanner Service."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.adapters.registry import AdapterNotFoundError
from app.routers import health, scans

logging.basicConfig(level="INFO")

app = FastAPI(
    title="VulnScan Scanner Service",
    description="Runs Nmap, WhatWeb, Nikto, Nuclei and OWASP ZAP against lab targets and returns raw results.",
    version="0.1.0",
)


@app.exception_handler(AdapterNotFoundError)
async def adapter_not_found_handler(request: Request, exc: AdapterNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"No adapter registered for tool '{exc}'. See GET /tools for the available set."
        },
    )


app.include_router(health.router)
app.include_router(scans.router)
