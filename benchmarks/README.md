# Concurrent booking benchmark

Run the script only against an isolated local demo database. The seeded Ananya customer must have vehicle ID 1 and charger ID 1 must be online. Set the `BOOKING_CUSTOMER_EMAIL` and `BOOKING_CUSTOMER_PASSWORD` environment variables with the generated local demo credentials.

```sh
k6 run benchmarks/concurrent-reservations.js
```

The default run launches 20 virtual users, each posting the same slot once. It passes only if there is one HTTP 201 and 19 HTTP 409 responses. The test leaves one reservation in the demo database. For another run, use a fresh database or set `BOOKING_START` and `BOOKING_END` to a different future slot in ISO 8601 format. Use `BOOKING_BASE_URL` to select the isolated app if it differs from the default local port.

The November 24, 2026 run used a local Docker backend and PostgreSQL 18. It produced one accepted reservation, 19 conflicts and no unexpected HTTP errors. All-request p95, including setup login, was 1.53 seconds.
