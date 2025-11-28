"""Smoke tests for service health endpoints."""

from services.bookings_service.app import health_check as bookings_health
from services.reviews_service.routers.reviews import health_check as reviews_health
from services.rooms_service.routers.rooms import health_check as rooms_health
from services.users_service.app import health_check as users_health


def test_health_functions_return_ok():
    checks = {
        "users": users_health,
        "rooms": rooms_health,
        "bookings": bookings_health,
        "reviews": reviews_health,
    }
    for name, func in checks.items():
        payload = func()
        assert payload["status"] == "ok", f"{name} health did not return ok"
