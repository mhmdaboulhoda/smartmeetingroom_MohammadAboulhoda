Architecture Overview
=====================

Services
--------

The SmartMeetingRoom backend consists of four FastAPI microservices:

* **Users** (port 8001) handles registration, login, JWT issuance, and role management.
* **Rooms** (port 8002) maintains the catalog of rooms, their attributes, and health probes.
* **Bookings** (port 8003) manages availability, booking creation, listing, and cancellation flows.
* **Reviews** (port 8004) stores feedback with moderation and flagging actions.

All services expose versioned endpoints under ``/api/v1`` and share a PostgreSQL database via SQLAlchemy and Alembic-ready metadata. Each service lives in ``services/<name>`` with modules for routers, schemas, models, service logic, and optional cache helpers.

Database Schema
----------------

The database contains ``users``, ``rooms``, ``bookings``, and ``reviews`` tables. Foreign keys link bookings/reviews to both ``users`` and ``rooms``. Composite indexes (e.g., ``(room_id, start_time)``) accelerate frequent filters. See the ``Database Design`` section of the main report for complete field descriptions.

Execution Flow
--------------

#. A client authenticates via ``/api/v1/users/login`` and receives a JWT.
#. Subsequent requests include ``Authorization: Bearer <token>``.
#. Each router uses dependency injection to fetch a database session and the current user.
#. Business logic resides in ``service.py`` files, and any errors raise custom ``AppError`` subclasses.
#. Responses are serialized through Pydantic schemas and returned through FastAPI.
