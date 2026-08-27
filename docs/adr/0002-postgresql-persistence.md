# ADR 0002: PostgreSQL as the durable persistence layer

- Status: Accepted
- Date: 2026-08-27

## Context

Milestone 1 proved that VakeVahti can retrieve STM HTML and normalize funding calls into
`FundingCallCandidate`. The next requirement is durable state: repeated scans must not create
duplicates, material changes must be detected, and history must remain auditable.

The workplace development PC currently has neither PostgreSQL nor Docker installed. That is an
environment constraint, not a reason to replace the intended production database with a different
database engine.

## Decision

Use PostgreSQL 16+ as the durable store, SQLAlchemy 2 for typed persistence, asyncpg for the async
driver, and Alembic for schema migrations.

Use an internal numeric primary key while enforcing `(source_code, external_key)` as a unique
source-scoped business identity.

Store current normalized state in `funding_calls`, material snapshots in
`funding_call_versions`, and per-source baseline/freshness state in `source_states`.

A deterministic SHA-256 hash of material fields decides whether a known record is unchanged or
changed. The first successful source import establishes a baseline and suppresses notification
eligibility for pre-existing calls.

GitHub Actions provides PostgreSQL for migration and integration testing until an approved local
PostgreSQL or Docker runtime is available.

## Consequences

- Repeated scans can be made idempotent at both application and database layers.
- Schema changes become explicit, reviewable migrations.
- History supports auditability and later change explanations.
- CI validates real PostgreSQL behavior instead of substituting SQLite semantics.
- Developers without local PostgreSQL can still run unit tests, while integration tests are skipped
  unless `TEST_DATABASE_URL` is configured.
- Local end-to-end persistence cannot be validated on the managed workstation until PostgreSQL or
  Docker is approved.
