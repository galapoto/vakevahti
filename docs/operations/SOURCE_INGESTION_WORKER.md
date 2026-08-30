# Source Ingestion Worker and Scheduling

Status: Milestone 3 operational baseline

## Purpose

VakeVahti must monitor funding sources without depending on an employee pressing a button. The ingestion business operation therefore lives in a reusable service and can be invoked by different triggers.

Current trigger model:

- development UI: live source demonstration only
- CLI: manual persisted ingestion
- worker `once`: one scheduled-style persisted ingestion then exit
- worker `loop`: single-replica interval polling for the standalone v1 application
- future Vaketomate scheduler: call the same ingestion service

No business persistence logic is duplicated between these triggers.

## Commands

From `backend/`:

Windows managed workstation:

```powershell
.\.venv\Scripts\python.exe -m app.cli scan-stm
.\.venv\Scripts\python.exe -m app.cli scan-stm-persist
.\.venv\Scripts\python.exe -m app.worker once
.\.venv\Scripts\python.exe -m app.worker loop
```

Linux/macOS:

```bash
python -m app.cli scan-stm
python -m app.cli scan-stm-persist
python -m app.worker once
python -m app.worker loop
```

Persisted commands require PostgreSQL and applied Alembic migrations.

## Configuration

`SCAN_INTERVAL_MINUTES` controls the v1 loop interval and is constrained to 5-1440 minutes.

`SCAN_RUN_ON_STARTUP=true` means loop mode starts with an immediate scan. If false, the worker waits one interval before the first run.

The source URL and database credentials remain runtime configuration, not source-code secrets.

## Deployment recommendation

The standalone v1 loop worker must run as a single scheduler replica. The application-level PostgreSQL source lock protects persistence from overlapping manual/scheduled writes, but running many loop workers would still waste source requests.

Preferred enterprise deployments can use a platform scheduler to invoke `python -m app.worker once`, for example:

- managed scheduled job
- cron/systemd timer
- Kubernetes CronJob
- future Vaketomate scheduler

This avoids coupling the funding domain to one scheduling product.

## Failure semantics

Each persisted ingestion creates a `source_scan_runs` audit row before external network I/O.

A successful run records:

- source
- trigger type
- start/completion time
- baseline flag
- discovered count
- NEW / UNCHANGED / CHANGED counts

A failed run records a bounded error type/message and remains visible as `FAILED`.

A parser/source failure is never treated as an empty successful scan and never causes missing source results to be interpreted as deletions.

If the process is killed after the RUNNING row is committed but before completion, the row can remain `RUNNING`. Future operational work should add stale-run detection/health alerting rather than silently rewriting history.

## Concurrency

Persistence takes a PostgreSQL transaction-scoped advisory lock derived from `source_code` before reading/updating source state. This serializes persistence for the same source and closes the first-run race around `source_states` and version numbers.

Different sources can still persist independently.

The lock protects database state; it is not a distributed scheduler by itself.

## Observability roadmap

Next operational additions should include:

- stale RUNNING-run detection
- structured JSON logs in deployed environments
- source-health API/dashboard
- metrics for run duration, failures, discovered/new/changed counts
- notification deduplication keyed by source/entity/version
- alerting after repeated source failures
