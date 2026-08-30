# Milestone 5: persisted read APIs and source health

Date: 2026-08-30

Status: implementation, CI and live Linux read validation complete; ready to merge.

## Why this milestone comes after multi-source ingestion

By the end of Milestone 4, VakeVahti could retrieve, normalize, persist, version and audit multiple funding sources. The next useful system boundary is not another scraper. It is a stable read contract over the durable state already collected.

The application should normally read PostgreSQL for user-facing views. It should not rescan STM, Sitra or Suomen Akatemia every time somebody opens a page.

This separates two workloads:

- ingestion is source-facing, scheduled, failure-prone and relatively expensive
- reads are application-facing, repeatable, fast and based on the last accepted persisted state

## Architecture implemented

The read path is deliberately layered:

`PostgreSQL models -> read/query service -> API schemas -> FastAPI routes`

The route handlers do not contain SQL. SQLAlchemy models are not used as the external API contract. Response models explicitly choose what clients may rely on.

The first persisted endpoints are:

- `GET /api/funding-calls`
- `GET /api/funding-calls/{id}`
- `GET /api/sources/health`

The old `/api/demo/stm-calls` endpoint remains clearly separate because it performs a live source scan and serves a different purpose.

## Data Engineering lesson: ingestion and serving are different paths

A data system often has a write/ingestion path and a read/serving path with different operational properties.

### Interview question: Why not call the funding websites from the API request?

> Live sources are slower and less reliable than our own persisted state. They can change structure, time out or require browser rendering. VakeVahti therefore ingests externally on the worker path and serves accepted current state from PostgreSQL. That gives the UI predictable latency and prevents every user request from becoming a scraping job.

## Backend lesson: database schema is not an API contract

The database includes fields needed for persistence mechanics, including `content_hash` and `external_key`. The public read schemas intentionally do not expose those fields.

### Interview question: Why not return every database column?

> Once clients consume a field, removing or changing it becomes an API compatibility problem. `content_hash` is an implementation detail of change detection and `external_key` is source identity plumbing. I expose fields because a client needs them, not because the table happens to contain them. That reduces accidental coupling between storage and API evolution.

## Pagination lesson: stable ordering is part of correctness

The list API uses bounded `limit`/`offset` pagination and a deterministic order:

1. application deadline ascending, nulls last
2. database id ascending as a tie-breaker

Without a deterministic tie-breaker, two requests for adjacent pages can repeat or skip records when values are equal.

### Backend interview question: Why is `ORDER BY deadline` alone not enough for pagination?

> Deadlines are not unique. If several rows share the same deadline, PostgreSQL is free to return those tied rows in different relative orders. Adding the id as a second key gives a total deterministic ordering for offset pagination.

### System Design question: Would you keep offset pagination forever?

> Not necessarily. Offset pagination is simple and appropriate for the current small internal dataset. At large scale or deep pages I would prefer cursor/keyset pagination over the same stable sort keys because it avoids scanning large offsets and behaves better under concurrent inserts.

## Source-health semantics

Milestone 5 deliberately distinguishes observed operational health from freshness policy.

Current health states are derived from the latest persisted scan audit:

- `NEVER_SCANNED`: there is no scan run
- `RUNNING`: latest run is still running
- `HEALTHY`: latest run succeeded
- `FAILING`: latest run failed

The API also exposes current call count, baseline completion, last successful scan and latest run counters.

It does not yet invent `STALE`.

### Observability interview question: Why not mark data stale after an arbitrary number of hours?

> Freshness is a contract relative to an expected cadence or SLA. A source scanned daily and a source scanned hourly cannot share an arbitrary threshold. Until the product defines source-specific expected intervals, VakeVahti reports factual timestamps and latest-run health rather than presenting an invented freshness policy as truth.

### System Design interview question: Health and freshness are both green/red concepts. Why separate them?

> A source can be operationally healthy but stale if the scheduler stopped running it, and it can have a recent failed scan while still serving sufficiently fresh data from the previous success. They answer different questions, so combining them into one status hides useful diagnosis.

## Query design: source health is a read model

`source_states`, `source_scan_runs` and `funding_calls` were designed for ingestion and audit concerns. The source-health response composes those tables into an operator-facing read model.

For each configured source it combines:

- baseline state
- last successful scan
- latest audit run
- latest run counters/error type
- current funding-call count

### Data Engineering interview question: Why create a read model instead of letting the frontend join tables?

> The frontend should not know database topology or reproduce operational semantics. The backend owns the meaning of source health and can evolve storage independently. This is also the contract boundary Vaketomate can consume later without cross-application table access.

## PostgreSQL-specific query choice

The service asks PostgreSQL for the latest scan per configured source and current counts rather than loading the entire audit history and filtering in Python.

### Database interview question: Why aggregate in SQL instead of reading all rows into the application?

> Databases are optimized for filtering, grouping and ordering close to the data. Moving complete audit histories into Python increases network transfer and memory use and creates more application code. The service asks PostgreSQL only for the state needed by the API response.

## Dependency injection and application lifecycle

`create_app()` accepts an optional session factory. Production creates and owns an async SQLAlchemy engine; tests inject a session factory pointing at the isolated PostgreSQL test database.

Production disposes only the engine it owns.

### Backend interview question: Why inject a session factory rather than monkeypatch a global engine?

> Injection makes resource ownership explicit. The application can be tested against a real isolated database without mutating hidden globals, and production still manages its own connection pool lifecycle. It also makes future composition easier if another host, such as Vaketomate, needs to instantiate the application boundary differently.

## CI lesson: framework idioms still have to satisfy static analysis

The first Milestone 5 CI run stopped at Ruff rule `B008`. The initial routes used FastAPI's older-looking dependency style:

`session: AsyncSession = Depends(get_db_session)`

That creates a function call in a default argument. Rather than disabling the lint rule, the routes were rewritten with `typing.Annotated` aliases, for example:

`SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]`

Backend CI #66 then passed Ruff, strict mypy, Alembic and PostgreSQL pytest.

### Backend interview question: Why not add `# noqa: B008` for FastAPI dependencies?

> A lint suppression would make the current code pass without improving the contract. FastAPI supports `Annotated`, which cleanly separates the Python type from dependency metadata and avoids an executable default. I chose the framework-supported representation that satisfies both FastAPI and the project's static-analysis rules instead of creating an exception we would need to maintain.

### Python technical question: What is the underlying concern with function calls in default arguments?

> Python evaluates default argument expressions when the function is defined, not each time it is called. Many frameworks intentionally use sentinel objects in defaults, but general executable defaults can create surprising shared state or side effects. `Annotated` lets us express dependency metadata without relying on that pattern in the route signature.

## Testing strategy

The API integration tests use ASGI transport and the real PostgreSQL test database. They do not mock the read service.

Coverage includes:

- source-code normalization
- bounded pagination
- deterministic page ordering
- total counts
- detail serialization
- 404 behavior
- request validation for excessive limit
- hiding internal ORM fields
- source HEALTHY state
- source FAILING state
- source RUNNING state
- NEVER_SCANNED state
- current funding-call counts

### QA interview question: Why is this an integration test rather than only unit tests for the query functions?

> A unit test could prove a function builds the expected objects, but the failure surface here includes FastAPI validation, dependency injection, SQLAlchemy queries, PostgreSQL behavior and Pydantic serialization. The integration test exercises the actual HTTP contract over the actual database boundary.

## Live Linux validation

The final developer-machine validation ran against the populated PostgreSQL database created by the completed multi-source ingestion milestone.

Local quality gates on the correct `feature/read-api-source-health` branch:

- Ruff: passed
- strict mypy: passed across 29 source files
- pytest: 30/30 passed
- two new PostgreSQL API integration tests passed

The real running FastAPI application then returned:

- total persisted funding calls: 17
- STM: 9
- SITRA: 1
- ACADEMY: 7

The live Sitra list response exposed the corrected individual opportunity, `Tuottavuutta tekoälyllä – valmennusta julkiselle sektorille uudistumisen tueksi`, with `current_version=1` and the normalized UTC deadline `2026-09-15T09:00:00Z`. It did not emit the earlier invalid `Rahoitushaut` section heading.

The live `/api/sources/health` response reported all three configured sources as `HEALTHY`, with matching current call counts and latest successful scheduled scan audits:

- STM: 9 calls, latest scan `SUCCEEDED`, 9 unchanged
- SITRA: 1 call, latest scan `SUCCEEDED`, 1 unchanged
- ACADEMY: 7 calls, latest scan `SUCCEEDED`, 7 unchanged

The developer also proved that the old 28-test result had been caused by running the previous feature branch. Once the correct remote branch was tracked locally, the suite collected 30 tests and the persisted API route existed as expected.

The separate detail/pagination behaviors do not require another ceremonial live check because they are already exercised end-to-end through ASGI against PostgreSQL in `test_funding_list_filters_paginates_and_reads_detail`: lowercase source filtering, two adjacent pages, deterministic ordering, detail serialization, 404 behavior, and the 100-record request bound are all part of the green 30-test suite. The live database check adds the complementary proof that those routes are wired to the real 17-record application state.

### Git/DevOps interview question: What did the earlier 404 reveal about branch state?

> The API returned 404 because I had not actually switched to the Milestone 5 branch. `git switch` failed because the local branch did not exist, then `git pull origin feature/read-api-source-health` attempted to integrate that remote branch into the still-current Milestone 4 branch and `--ff-only` correctly refused. The old 28-test collection count was another clue. I fixed it by explicitly creating a local tracking branch from `origin/feature/read-api-source-health`, after which the expected 30 tests and persisted routes were present.

### DevOps interview question: Why was `--ff-only` useful in that incident?

> It prevented an accidental merge between two feature branches. Instead of silently creating an unintended history edge, Git failed loudly. That is exactly the behavior I want for disciplined milestone branches.

## Security/privacy lesson: diagnostics should be bounded

The health endpoint exposes `error_type` but not the full persisted `error_message`. Full exception messages can contain URLs, infrastructure details or unexpected upstream content.

### Security interview question: Why expose error type but not full error message?

> Operators need a useful classification such as `SourceStructureError` or `HTTPStatusError`, but a general API response should not automatically echo arbitrary exception text. Detailed diagnostics belong in controlled logs/audit views with appropriate access. This follows least-exposure principles while preserving actionable health information.

## Portfolio explanation

A concise interview narrative for this milestone:

> After building multi-source ingestion, I separated the serving path from the source-facing worker. I added PostgreSQL-backed read APIs with typed response contracts, bounded deterministic pagination, detail reads and an operational source-health read model. Health is derived from persisted scan audits without inventing freshness SLAs. I used an injectable async session boundary and integration-tested the HTTP contract against PostgreSQL rather than mocking the database. CI caught an executable-default dependency pattern, so I migrated the routes to FastAPI's `Annotated` dependency style instead of suppressing the lint rule. I then validated the running API against the real 17-record development database and confirmed that the serving layer reflected the corrected multi-source state exactly.
