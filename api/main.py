"""OM Toolkit API: thin JSON layer over core/, plus static hosting of web/dist.

All domain validation lives in core/'s validate_* functions; they raise
ValueError with a human-readable message, which we surface as HTTP 422 so
the frontend can show it inline next to the offending input.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers import lot_sizing

app = FastAPI(title="OM Toolkit API")
app.include_router(lot_sizing.router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
