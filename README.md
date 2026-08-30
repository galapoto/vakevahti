# VakeVahti

VakeVahti is an internal funding-opportunity monitoring and workflow application being built as a real workplace system, graduation project, and data-engineering portfolio project.

## Current milestone

The first ingestion slice is proven and Milestone 2 is adding durable PostgreSQL persistence and change detection.

Current implemented flow:

`STM website -> HTTP -> HTML parser -> validated FundingCallCandidate -> development UI`

Persistence foundation:

`FundingCallCandidate -> content hash -> PostgreSQL -> NEW / UNCHANGED / CHANGED -> version history`

The managed workplace PC currently has no approved local PostgreSQL or Docker runtime, so PostgreSQL integration behavior is validated in GitHub Actions while unit tests and the development UI remain runnable locally.

## Development UI

A lightweight FastAPI-served mentor/demo dashboard is available at the application root. It deliberately has no Node.js requirement and shows only currently implemented capabilities. It can trigger the real STM adapter and display the validated live funding calls.

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

## Linux/macOS local setup

Requirements:

- Python 3.12+

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp ../.env.example ../.env
uvicorn app.main:app --reload
```

## Manual STM discovery

Windows without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m app.cli scan-stm
```

Linux/macOS:

```bash
python -m app.cli scan-stm
```

## Quality checks

Windows:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app
.\.venv\Scripts\python.exe -m pytest
```

## Engineering rules

Read [`AGENTS.md`](AGENTS.md) and [`docs/LEARNING_AND_ENGINEERING_CHARTER.md`](docs/LEARNING_AND_ENGINEERING_CHARTER.md) before making substantial changes.

## Next milestones

1. Complete PostgreSQL persistence and baseline import.
2. Verify idempotent NEW / UNCHANGED / CHANGED behavior in CI.
3. Add notifications.
4. Add Sitra and Academy adapters.
5. Add Haeavustuksia eligibility rules.
6. Add EURA region + eligibility rules.
7. Replace the development dashboard with the employee-facing application UI and review/reporting workflow.
