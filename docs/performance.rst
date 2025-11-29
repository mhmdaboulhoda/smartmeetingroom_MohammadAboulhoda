Performance Features
====================

Room List Caching
-----------------

The Rooms service wraps ``list_rooms`` with a lightweight in-memory cache implemented in :mod:`services.rooms_service.cache`. Keys consist of ``(location, min_capacity, status)`` tuples, and entries expire after 60 seconds. Cache invalidation happens when rooms are created, updated, or deleted.

Database Indexing
-----------------

Database indexes are declared in the SQLAlchemy models to accelerate frequent queries:

* ``users``: indexes on ``username`` and ``email`` for quick lookups.
* ``rooms``: indexes on ``name``, ``location``, and ``status`` for filtering.
* ``bookings``: composite index on ``(room_id, start_time)`` plus ``user_id``.
* ``reviews``: indexes on ``room_id``, ``user_id``, and ``is_hidden``.

Profiling
---------

Profiling scripts live inside the ``profiling/`` directory:

* ``run_line_profile.sh`` uses ``kernprof`` to generate line-level timing.
* ``run_memory_profile.py`` uses ``memory_profiler`` decorators for peak allocation tracking.
* ``run_coverage.sh`` executes pytest with coverage.
* ``demo_rooms_cache_timing.py`` demonstrates the cache effect by timing two sequential room list calls.
