# VakeVahti

VakeVahti is an internal funding-opportunity monitoring and workflow product being built as a real workplace system, graduation project, and data-engineering/software-engineering portfolio project.

It remains independently runnable now, but its architecture is being kept extraction-ready so it can later live under the Vaketomate automation platform without rewriting the funding domain.

## Current implemented flow

`STM -> HTTP -> semantic HTML parsing -> FundingCallCandidate -> validation -> persistence -> change detection -> audit`

Persistence:

`FundingCallCandidate -> canonical content hash -> PostgreSQL -> NEW / UNCHANGED / CHANGED -> immutable versions`

Operational ingestion:

`trigger -> shared ingestion service -> source scan -> PostgreSQL transaction -> source_scan_runs audit`

The managed workplace PC currently has no approved local PostgreSQL or Docker runtime. Database-independent checks and the mentor UI remain runnable locally; PostgreSQL migrations and integration behavior are validated in GitHub Actions against PostgreSQL 16.

## Development UI

A lightweight FastAPI-served mentor/demo dashboard is available at the application root. It deliberately has no Node.js requirement and only demonstrates currently implemented capabilities.

Windows managed-workstation setup:

```powershell
cd C:\Users\vitus.idi2\vakevahti\backend
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open:

`http://127.0.0.1:8000/`

API documentation:

`http://127.0.0.1:8000/docs`

Health check:

`http://127.0.0.1:8000/health/live`

## Manual STM discovery

This performs a live source scan without persistence:

```powershell
.\.venv\Scripts\python.exe -m app.cli scan-stm
```

## Persisted manual ingestion

Requires PostgreSQL and applied Alembic migrations:

```powershell
.\.venv\Scripts\python.exe -m app.cli scan-stm-persist
```

The persisted path records a source-run audit ID and uses the same ingestion service as scheduled execution.

## Automatic worker

One-shot invocation:

```powershell
.\.venv\Scripts\python.exe -m app.worker once
```

Standalone v1 interval worker:

```powershell
.\.venv\Scripts\python.exe -m app.worker loop
```

The loop interval is configured with `SCAN_INTERVAL_MINUTES` and should run as one scheduler-worker replica in v1. Enterprise deployment may instead schedule the one-shot worker using an approved managed scheduler or the future Vaketomate platform scheduler.

See [`docs/operations/SOURCE_INGESTION_WORKER.md`](docs/operations/SOURCE_INGESTION_WORKER.md).

## Linux/macOS local setup

Requirements:

- Python 3.12+
- PostgreSQL for persisted/integration execution

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp ../.env.example ../.env
uvicorn app.main:app --reload
```

## Quality checks

Windows:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app
.\.venv\Scripts\python.exe -m pytest -v
```

CI additionally provisions PostgreSQL, applies Alembic migrations and executes PostgreSQL integration tests.

## Architecture and engineering standards

Read before substantial changes:

- [`AGENTS.md`](AGENTS.md)
- [`docs/LEARNING_AND_ENGINEERING_CHARTER.md`](docs/LEARNING_AND_ENGINEERING_CHARTER.md)
- [`docs/architecture/VAKETOMATE_INTEGRATION_CONTRACT.md`](docs/architecture/VAKETOMATE_INTEGRATION_CONTRACT.md)
- [`SECURITY.md`](SECURITY.md)

The continually maintained learning/interview record is:

- [`docs/learning/BUILD_LESSONS_AND_INTERVIEW_BANK.md`](docs/learning/BUILD_LESSONS_AND_INTERVIEW_BANK.md)

## Vaketomate direction

VakeVahti owns the funding domain. When integrated into Vaketomate, it may consume shared platform capabilities such as identity, authorization, audit aggregation, scheduling, notifications and generic project management through published contracts. It must not directly manipulate another Vaketomate application's internal tables.

This keeps VakeVahti capable of growing from funding monitoring into a much larger funding/application/project-lifecycle product while still living under the Vaketomate umbrella.

## Next build priorities

1. Complete operational scan-run audit and scheduled ingestion validation.
2. Add persisted read APIs and source-health endpoints.
3. Add notification deduplication and delivery boundary.
4. Add Sitra and Suomen Akatemia adapters.
5. Add Haeavustuksia eligibility rules.
6. Add EURA region + eligibility rules.
7. Expand the funding lifecycle from opportunity monitoring toward application/project tracking.
8. Replace the development dashboard with the employee-facing application UI when backend workflows are ready.
