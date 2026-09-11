# Live source test console

The live source test console is an opt-in diagnostic surface for development and test environments.

## Enable it

Set:

```text
ENABLE_LIVE_TEST_ROUTES=true
```

The browser console is then available at:

```text
/test/live-sources
```

## What it does

- Lists the funding source adapters compiled into the current build.
- Runs exactly one selected adapter directly against its public source.
- Shows the complete `RELEVANT`, `NEEDS_REVIEW`, and `NOT_RELEVANT` distribution.
- Returns each normalized candidate with its persisted-model-compatible relevance reason and source URL.
- Rejects a duplicate concurrent test for the same source.

## What it does not do

- It does not write to PostgreSQL.
- It does not create source scan audit rows.
- It does not create notification-outbox rows.
- It does not alter the employee dashboard or its persisted read model.
- It is disabled by default and must not be enabled on the employee production deployment.

This separation lets developers inspect current public-source parsing before the database-backed ingestion path is configured, while keeping the employee dashboard read-only.
