# VakeVahti

VakeVahti is an internal funding-opportunity monitoring and workflow product being built as a real workplace system, graduation project, and data-engineering/software-engineering portfolio project.

It remains independently runnable now, but its architecture is being kept extraction-ready so it can later live under the Vaketomate automation platform without rewriting the funding domain.

## Current implemented flow

VakeVahti now implements the funding-monitoring path across the five authoritative source families:

`STM / Haeavustuksia.fi / EURA 2021 / Sitra / Suomen Akatemia`

Core data path:

`scheduled scan -> source adapter -> normalize/validate -> relevance classification -> PostgreSQL -> NEW / UNCHANGED / CHANGED -> immutable versions -> scan audit`

Operational behavior includes source-specific baselines, idempotent re-scans, source-health state, explicit `NEEDS_REVIEW` handling for ambiguous eligibility, and fail-visible parser behavior when a public source changes structure.

Downstream workflow now includes:

- persisted funding-call and source-health read APIs;
- a durable notification outbox with deduplication, lease-based claiming, retry state and delivery boundaries;
- persisted funding-report drafts, editable email content and a bounded coordinator-approval queue;
- auditable approve / return-for-edit / reject decisions with immutable content snapshots and SHA-256 hashes;
- immutable approved report versions with explicit successor lineage (`version_number` / `supersedes_report_id`);
- durable report-email delivery with retry semantics;
- stable funding `case_id` identities that survive funding-call content changes;
- versioned cross-app artifacts for Prosessikuvaus, Raportointi and later VakeTomatti modules;
- a unified funding-case workspace with automated workflow tasks and next-action guidance;
- automatic Prosessikuvaus and Raportointi starter drafts for new/reviewable cases; and
- a fixture-backed preview mode for UI/workflow validation without mutating production data.

The employee dashboard reads persisted application state. It does not trigger public-source scans when the page is opened.

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

The earlier source-ingestion/read-API/outbox priorities are complete. The next slices should move the system from a strong funding-monitoring workflow into an approved employee production workflow:

1. **Add approved organization identity and authorization.** Replace client-asserted approval actors and environment-variable write gates with the VakeTomatti/organization SSO boundary plus permissions such as read, review, edit, approve and administer. Authentication must not imply universal authorization.
2. **Connect approval policy to workplace delivery infrastructure.** Keep the existing outbox/retry contracts, but require the appropriate approved report/artifact version before production email/notification delivery and load secrets only through approved deployment configuration.
3. **Integrate real cross-app artifacts.** Replace starter-only Prosessikuvaus/Raportointi content with versioned artifacts produced by those modules; add authorized file/deep-link handling without copying confidential documents into unsafe locations.
4. **Expand opportunity -> application -> project lifecycle.** Add application ownership, decision/status history, deadlines and the published Project-service handoff when a funded application becomes a project.
5. **Integrate with the VakeTomatti shell.** Reuse shared identity, audit aggregation, scheduling, notification and project-management contracts while keeping Funding tables and business logic domain-owned.
6. **Production hardening and final employee UX.** Finish role-aware audit views, operational alerts/metrics, accessibility, deployment runbooks, backup/recovery expectations and the final employee-facing application shell.

Do not restart already completed source adapters, persisted read APIs or notification deduplication merely because older documentation lists them as future work.
