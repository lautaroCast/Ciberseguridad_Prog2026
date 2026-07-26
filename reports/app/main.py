"""FastAPI application entrypoint."""

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import health, reports
from app.routers.reports import ReportFileNotFoundError
from app.security import verify_internal_token

app = FastAPI(
    title="VulnScan Reports Service",
    description="Renders scan data (pushed by the Backend) into PDF/HTML/Markdown/JSON reports.",
    version="0.1.0",
)


@app.exception_handler(ReportFileNotFoundError)
async def report_file_not_found_handler(
    request: Request, exc: ReportFileNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Report file '{exc}' not found."})


app.include_router(health.router)
app.include_router(reports.router, dependencies=[Depends(verify_internal_token)])
