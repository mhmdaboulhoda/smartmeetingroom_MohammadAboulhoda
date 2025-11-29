"""Users service FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from common.exceptions import AppError
from services.users_service.routers.users import router

logger = logging.getLogger(__name__)

app = FastAPI(title="Users Service")


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    """Normalize AppError responses."""

    logger.warning("AppError on %s: %s", request.url.path, exc.message)
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    """Return consistent payload for FastAPI HTTPException usage."""

    logger.warning(
        "HTTPException on %s: %s (status=%s)", request.url.path, exc.detail, exc.status_code
    )
    content = {"error_code": "HTTP_EXCEPTION", "message": exc.detail, "details": None}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    """Catch-all handler to keep responses predictable."""

    logger.exception("Unhandled exception on %s", request.url.path)
    content = {
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
        "details": None,
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)


app.include_router(router)
