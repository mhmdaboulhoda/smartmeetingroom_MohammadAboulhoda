"""Ensure every service exposes versioned API routes."""

from fastapi.routing import APIRoute

from services.bookings_service.app import app as bookings_app
from services.reviews_service.app import app as reviews_app
from services.rooms_service.app import app as rooms_app
from services.users_service.app import app as users_app

APP_REGISTRY = {
    "users_service": users_app,
    "rooms_service": rooms_app,
    "bookings_service": bookings_app,
    "reviews_service": reviews_app,
}


def test_all_routes_are_versioned():
    offenders = []
    for service_name, fastapi_app in APP_REGISTRY.items():
        for route in fastapi_app.routes:
            if not isinstance(route, APIRoute):
                continue
            path = route.path
            if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
                continue
            if not path.startswith("/api/v1/"):
                offenders.append((service_name, path))
    assert not offenders, f"Unversioned routes detected: {offenders}"
