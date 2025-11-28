"""FastAPI entry point for the Reviews service."""

from fastapi import FastAPI

from services.reviews_service import SERVICE_NAME

app = FastAPI(title="Reviews Service")


@app.get("/health")
async def health_check() -> dict:
    """Health probe used by orchestrators and tests."""
    return {"status": "ok", "service": SERVICE_NAME}
