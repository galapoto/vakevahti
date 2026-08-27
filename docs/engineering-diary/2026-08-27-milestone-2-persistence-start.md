# Engineering diary: Milestone 2 persistence start

Date: 2026-08-27

## What was proven before this step

The managed Windows workstation successfully installed the Python project dependencies inside a
project-specific virtual environment. Ruff, mypy, and five tests passed. The live STM scanner then
discovered nine current funding calls.

## Environment finding

The workstation has no `psql`, PostgreSQL service, `pg_config`, or Docker executable, and no
`C:\Program Files\PostgreSQL` installation. Rather than bypassing workplace controls or switching
the application architecture to SQLite, PostgreSQL integration testing is moved to GitHub Actions
until IT provides an approved local runtime.

## Persistence design introduced

Milestone 2 adds:

- SQLAlchemy 2 async models and sessions;
- Alembic schema migration management;
- PostgreSQL tables for current funding calls, version snapshots, and per-source state;
- a unique `(source_code, external_key)` business identity;
- `first_seen_at` and `last_seen_at` freshness timestamps;
- deterministic content hashing over material fields;
- NEW / UNCHANGED / CHANGED classification;
- first-scan baseline semantics that suppress notification eligibility;
- PostgreSQL integration tests in CI.

## Learning notes

A successful HTTP fetch is not enough for a production data pipeline. The system now needs durable
state so it can distinguish observation from change. Idempotency is achieved by combining stable
source identity, a database uniqueness constraint, deterministic content hashing, and transaction
boundaries.

`first_seen_at` means when VakeVahti first observed a call, not necessarily when the funder
published it. That distinction prevents the application from inventing source facts.

The first import is a backfill/baseline problem: existing calls are stored but are not treated as
fresh notifications. Later unseen identities can become genuine NEW events.
