Deployment Guide
================

Docker Compose
--------------

* ``docker-compose.yml`` defines five services: ``db`` (Postgres) plus one container per FastAPI service.
* Each FastAPI container uses a dedicated Dockerfile under ``services/<name>/Dockerfile`` and exposes port 8000 internally. Compose maps host ports 8001--8004.
* Environment variables such as ``DATABASE_URL`` and ``JWT_SECRET_KEY`` are provided through the ``.env.docker`` file.

Startup Steps
-------------

#. Install Docker Desktop.
#. Run ``docker compose --env-file .env.docker up --build``.
#. Verify containers with ``docker compose ps``.
#. Access Swagger UIs at ``http://localhost:8001/docs`` (Users), ``http://localhost:8002/docs`` (Rooms), etc.

Testing with Postman
--------------------

The ``postman/`` folder contains a collection and environment. Import both into Postman, update environment tokens (e.g., ``jwt_token``), and execute the requests to validate the deployed stack.
