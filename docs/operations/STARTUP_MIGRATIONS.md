# Opt-in startup database migrations

`MIGRATE_DATABASE_ON_STARTUP` is disabled by default.

When explicitly set to `true`, the API runs `alembic upgrade head` against the configured `DATABASE_URL` before accepting traffic. The migration runs in a separate subprocess and suppresses subprocess output so connection credentials cannot leak through startup errors.

Use this only for the single-replica test deployment or another environment where one process owns migration startup. Keep it disabled for multi-replica production deployments, where migrations should be a separate release/deployment step.

For the Render test service, enable this flag only after `DATABASE_URL` has been bound to the Render PostgreSQL instance. If migration fails, application startup fails rather than serving against an unknown schema revision.
