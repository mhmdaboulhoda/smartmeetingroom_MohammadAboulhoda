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

## Docker Compose deployment

1. Copy `.env.docker` as needed and adjust secrets (the file ships with demo credentials).
2. Build and start everything:
   ```bash
   docker-compose up --build
   ```
3. Health checks (replace port with service port):
   ```bash
   curl http://localhost:8001/api/v1/users/health
   curl http://localhost:8002/api/v1/rooms/health
   ```
4. Swagger UI is available on each service at `/docs` (e.g. `http://localhost:8001/docs`).

## Contributing

See `CONTRIBUTING.md` for coding standards (service layout, formatting via `format.sh`, etc.) and for guidance on adding new endpoints.
