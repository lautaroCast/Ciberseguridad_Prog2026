"""FastAPI application entrypoint."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import health, reports
from app.routers.reports import ReportFileNotFoundError

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
app.include_router(reports.router)
