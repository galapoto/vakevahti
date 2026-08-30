# Persisted read API operations

Status: Milestone 5 validation

## Purpose

The persisted read API serves the current accepted PostgreSQL state. It does not perform live source scans.

Production read endpoints:

- `GET /api/funding-calls`
- `GET /api/funding-calls/{id}`
- `GET /api/sources/health`

The existing `/api/demo/stm-calls` endpoint is intentionally different: it calls the STM source live for development/demo use and must not be treated as the normal application read path.

## Funding list

Example:

```text
GET /api/funding-calls?source_code=STM&limit=25&offset=0
```

Rules:

- `source_code` is optional and normalized to uppercase
- `limit` defaults to 50 and is bounded to 1..100
- `offset` must be non-negative
- ordering is deadline ascending, null deadlines last, then id ascending
- `total` represents the full filtered count before pagination

## Funding detail

```text
GET /api/funding-calls/{id}
```

Returns 404 when the current-state row does not exist.

The API intentionally omits storage/internal fields including the persistence content hash and source external key from this first client contract.

## Source health

```text
GET /api/sources/health
```

The response is scoped to configured `ENABLED_SOURCES` and derives health from the latest persisted `source_scan_runs` row:

- `NEVER_SCANNED`: no audit row exists
- `RUNNING`: latest audit is RUNNING
- `HEALTHY`: latest audit is SUCCEEDED
- `FAILING`: latest audit is FAILED

The endpoint also reports baseline completion, last successful scan, current call count, latest run timing/counters and bounded error classification.

No `STALE` state exists yet because source-specific expected scan cadence/freshness policy has not been defined. Consumers should use the returned timestamps rather than inventing their own undocumented threshold.

## Database/runtime boundary

FastAPI owns one async SQLAlchemy engine/session factory in production. A session is opened per read request and closed after the request. The application factory accepts an injected session factory for deterministic PostgreSQL integration tests.

The API is read-only in this milestone. It does not commit transactions, trigger ingestion or mutate workflow state.

## Failure behavior

- invalid query bounds: FastAPI returns 422
- missing funding call: 404
- database/query failure: request fails rather than silently returning an empty success
- unknown persisted scan status: server error rather than guessed health

## Vaketomate boundary

Future Vaketomate components may consume these published API semantics or an explicitly versioned equivalent. They must not query VakeVahti tables directly.
