# VakeVahti

VakeVahti is an internal funding-opportunity monitoring and workflow application being built as a real workplace system, graduation project, and data-engineering portfolio project.

## Current milestone

Milestone 1 establishes the first thin vertical slice:

`STM website -> HTTP -> HTML parser -> validated FundingCallCandidate -> terminal output`

This deliberately proves extraction before adding PostgreSQL, scheduling, notifications, FastAPI endpoints, or the frontend.

## Why start this way?

The project uses incremental delivery: make one end-to-end path work, test it, understand it, then add persistence and workflow around it. This keeps the architecture understandable and catches source-specific problems early.

## Local setup

Requirements:

- Python 3.12+

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp ../.env.example ../.env
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health/live
```

Run the first STM discovery manually:

```bash
python -m app.cli scan-stm
```

Run tests:

```bash
pytest
```

## Engineering rules

Read [`AGENTS.md`](AGENTS.md) and [`docs/LEARNING_AND_ENGINEERING_CHARTER.md`](docs/LEARNING_AND_ENGINEERING_CHARTER.md) before making substantial changes.

## Next milestones

1. Persist funding calls in PostgreSQL.
2. Add stable deduplication and baseline import.
3. Detect new/changed calls.
4. Add notifications.
5. Add Sitra and Academy adapters.
6. Add Haeavustuksia eligibility rules.
7. Add EURA region + eligibility rules.
8. Add API/UI/review/reporting workflow.
