# ADR 0004: Separate source-ingestion worker from the web process

- Status: Accepted
- Date: 2026-08-30

## Context

VakeVahti must automatically monitor funding sources. Starting a scheduler inside FastAPI would be convenient in local development, but a production API commonly runs multiple processes or replicas. If every web instance started its own scheduler, the same source could be scanned repeatedly and notifications could be duplicated.

The future Vaketomate platform may also provide a shared scheduler, so funding business logic should not depend on a specific scheduling library or web-process lifecycle.

## Decision

Keep the business operation for source ingestion in a reusable application service and run automatic monitoring through a separate worker process.

The standalone v1 application supports:

- a one-shot worker that performs one persisted ingestion and exits
- a single-replica interval worker for simple standalone operation
- manual CLI execution through the same ingestion service

A future managed scheduler or Vaketomate scheduler may invoke the one-shot operation without changing funding-domain logic.

Database persistence for a source is serialized with a PostgreSQL transaction-scoped advisory lock, but this lock is not treated as a replacement for scheduler topology.

## Consequences

- Scaling the FastAPI web tier does not automatically multiply scheduled jobs.
- The same tested ingestion path is reused by CLI, worker and future platform triggers.
- Standalone loop mode must run as one scheduler replica.
- A managed scheduler can later replace loop mode without a business rewrite.
- Source scan attempts become independently auditable through `source_scan_runs`.
