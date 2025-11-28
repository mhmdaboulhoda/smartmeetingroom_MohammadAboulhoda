# smartmeetingroom_FirstLast_FirstLast

This repository hosts a microservice-based FastAPI backend used for the Smart Meeting Room university project. The goal of this scaffold is to keep each service independent while sharing foundational utilities via the `common/` package.

## Repository layout

- `services/`
  - `users_service/`, `rooms_service/`, `bookings_service/`, `reviews_service/`: four FastAPI apps that currently expose only a `/health` endpoint. They will eventually own business logic for user management, room inventory, booking workflows, and feedback, respectively.
- `common/`: package for shared helpers such as configuration loading, DB connections, and authentication utilities.
- `tests/`: pytest suite placeholder. Add integration tests per service as functionality lands.
- `requirements.txt`: shared dependencies for development, testing, profiling, and docs (Sphinx).

## Running a service locally

1. Create a virtual environment and install `requirements.txt`.
2. Pick the service you want to run, e.g. `users_service`, and launch it with uvicorn:

   ```bash
   uvicorn services.users_service.main:app --reload --port 8001
   ```

3. Probe the service health with `curl http://127.0.0.1:8001/health`.

Each service is intentionally minimal to keep the focus on architecture. Add routers, models, and persistence logic as the project evolves.
