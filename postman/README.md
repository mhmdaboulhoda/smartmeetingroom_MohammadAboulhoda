# Postman Collection Usage

## Import steps
1. Open Postman.
2. Import `postman/SmartMeetingRoom.postman_collection.json`.
3. Import `postman/postman_environment.json` and select it when sending requests.

## Testing flow
1. **Register Admin/User** via `POST /api/v1/users/register`.
2. **Login** with `POST /api/v1/users/login` and copy the `access_token` into the environment variable `jwt_token`.
3. Update the `room_id`, `booking_id`, etc. as you create resources so dependent requests work.
4. Exercise Rooms, Bookings, Reviews endpoints in order: create room → create booking → create review → moderate review.
5. Admin-only endpoints require the `jwt_token` for an admin/facility manager account.

## Auth
Set the Authorization header using the env variable: `Authorization: Bearer {{jwt_token}}`. Update `jwt_token` after each login.
