"""FastAPI entry point for the Bookings service."""

from fastapi import FastAPI

from services.bookings_service import SERVICE_NAME

app = FastAPI(title="Bookings Service")


@app.get("/health")
async def health_check() -> dict:
    """Health probe used by orchestrators and tests."""
    return {"status": "ok", "service": SERVICE_NAME}
