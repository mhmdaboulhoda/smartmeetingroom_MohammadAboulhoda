"""FastAPI entry point for the Rooms service."""

from fastapi import FastAPI

from services.rooms_service import SERVICE_NAME

app = FastAPI(title="Rooms Service")


@app.get("/health")
async def health_check() -> dict:
    """Health probe used by orchestrators and tests."""
    return {"status": "ok", "service": SERVICE_NAME}
