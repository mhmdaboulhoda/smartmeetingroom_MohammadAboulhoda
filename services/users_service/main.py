"""FastAPI entry point for the Users service."""

from fastapi import FastAPI

from services.users_service import SERVICE_NAME

app = FastAPI(title="Users Service")


@app.get("/health")
async def health_check() -> dict:
    """Health probe used by orchestrators and tests."""
    return {"status": "ok", "service": SERVICE_NAME}
