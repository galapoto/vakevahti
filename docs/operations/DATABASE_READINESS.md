# Database readiness

VakeVahti exposes two distinct health probes:

- `/health/live` proves the API process is running.
- `/health/ready` proves the API can connect to the configured PostgreSQL database.

A database failure returns HTTP 503 from `/health/ready` with a non-sensitive error type while `/health/live` remains HTTP 200. This prevents a running web process from being mistaken for a fully usable persisted deployment.
