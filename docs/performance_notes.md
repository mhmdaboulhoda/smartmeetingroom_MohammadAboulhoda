# Performance Notes

This codebase relies on microservices that frequently read and filter relational data. We added the following indexes to keep those hot paths responsive:

- **users.username / users.email** – login, registration, and token validation depend on fast lookups by username or email. Indexing both fields avoids full scans when verifying uniqueness.
- **rooms.name / rooms.location / rooms.status** – the UI filters rooms by name, building, or status before creating bookings. Covering these columns keeps those search queries and availability checks under a few milliseconds.
- **bookings.user_id / (room_id, start_time)** – listing bookings for a user and detecting overlaps (`room_id` + `start_time`) happen on every booking mutation. These composite indexes allow the conflict check in `create_booking` to rely on a targeted range scan instead of scanning the entire table.
- **reviews.room_id / reviews.user_id / reviews.is_hidden** – fetching reviews for a room is part of the public API, while moderators repeatedly filter hidden/flagged content. Indexes on `room_id` and `is_hidden` keep both user-facing and moderation dashboards responsive.

These indexes directly support the performance optimization requirement by eliminating full-table scans on the highest-frequency queries (login, room search, booking conflict detection, and review moderation). As data grows, the indexes ensure request latency remains predictable without extra caching layers.
