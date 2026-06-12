"""OM Toolkit API: thin JSON layer over core/, plus static hosting of web/dist.

All domain validation lives in core/'s validate_* functions; they raise
ValueError with a human-readable message, which we surface as HTTP 422 so
the frontend can show it inline next to the offending input.
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from api.routers import cellular, line_balancing, lot_sizing, process_analysis, scheduling

app = FastAPI(title="OM Toolkit API")
app.include_router(cellular.router)
app.include_router(line_balancing.router)
app.include_router(lot_sizing.router)
app.include_router(process_analysis.router)
app.include_router(scheduling.router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


DIST_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"


@app.get("/{path:path}", include_in_schema=False)
async def spa(path: str):
    """Serve the built frontend; unknown paths fall back to index.html so
    client-side routes (e.g. /lot-sizing) survive refreshes and deep links."""
    if not DIST_DIR.exists():
        return JSONResponse(status_code=404, content={"detail": "Frontend not built."})
    file = DIST_DIR / path
    if path and file.is_file():
        return FileResponse(file)
    return FileResponse(DIST_DIR / "index.html")
