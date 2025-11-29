# Contributing

Thanks for helping with SmartMeetingRoom! The project follows a consistent layout across all microservices:

```
services/<service_name>/
├── app.py                # FastAPI app + global exception handlers
├── routers/              # APIRouter modules (all endpoints live here)
├── service.py            # Domain logic and DB access helpers
├── models.py             # SQLAlchemy models
├── schemas.py            # Pydantic schemas
└── cache.py (optional)   # e.g., rooms caching helpers
```

Shared utilities (auth, config, DB, exceptions) live under `common/` and should **never** be duplicated in services.

## Workflow
1. Create/activate a virtualenv, install deps from `requirements.txt`.
2. Add or update endpoints inside the appropriate router + service module. Keep business logic out of the app entry point.
3. Add or update tests under `tests/`. Reuse existing fixtures and patterns.
4. Run the formatter before committing:
   ```bash
   ./format.sh
   ```
   (This runs `isort` and `black` with the settings in `pyproject.toml`.)
5. Run `./pre_docker_check.sh` to execute pytest, coverage, and the profiling smoke checks.

When adding a new microservice or endpoint, follow the same structure (app.py + routers + service). Include type hints, basic logging (info/debug) for key operations, and rely on the `common/` modules for auth, DB, and exceptions.
