"""Ensure services use the shared common modules."""

from fastapi import FastAPI

from services.bookings_service.app import app as bookings_app
from services.reviews_service.app import app as reviews_app
from services.rooms_service.app import app as rooms_app
from services.users_service.app import app as users_app


def _collect_handlers(app: FastAPI):
    return {handler.__name__ for handler in app.exception_handlers.values()}


def _assert_common_handlers(app: FastAPI):
    handlers = _collect_handlers(app)
    assert "handle_app_error" in handlers
    assert "handle_http_exception" in handlers
    assert "handle_generic_exception" in handlers


def test_apps_register_common_exception_handlers():
    for fastapi_app in (bookings_app, reviews_app, rooms_app, users_app):
        _assert_common_handlers(fastapi_app)


def test_apps_import_common_auth_and_db():
    for fastapi_app in (bookings_app, reviews_app, rooms_app, users_app):
        deps = set()
        for route in fastapi_app.routes:
            dependant = getattr(route, "dependant", None)
            if not dependant:
                continue
            for call in dependant.dependencies:
                dep = getattr(call, "call", None)
                if dep:
                    deps.add(dep)
        assert any(getattr(dep, "__module__", "").startswith("common.auth") for dep in deps), "Missing common.auth usage"
        assert any(getattr(dep, "__module__", "") == "common.db" for dep in deps), "Missing common.db usage"
