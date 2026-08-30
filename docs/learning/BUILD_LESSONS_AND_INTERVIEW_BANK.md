# VakeVahti Build Lessons and Interview Bank

Purpose: preserve the engineering lessons and interview preparation produced while the system is built. This document is updated continuously rather than reconstructed at the end of the work trial.

## 1. Development environment and managed workstation

### Lesson: terminal, shell and virtual environment are different layers

Windows Terminal is the terminal user interface. PowerShell is the shell interpreting commands. The Python virtual environment selects an isolated project interpreter and dependency set. VakeVahti can use the virtual environment interpreter directly even when corporate PowerShell execution policy prevents `Activate.ps1`.

Example:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

This works without weakening organization security policy.

### Interview: What is the purpose of a Python virtual environment?

Strong answer:

> A virtual environment isolates a project's interpreter-level packages from system Python and other projects. It makes dependency versions reproducible and reduces machine-level conflicts. Activation is a convenience that adjusts the shell PATH; it is not technically required because the environment's Python executable can be invoked directly.

### Interview: How did you work within a locked-down corporate workstation?

Strong answer:

> I first discovered the approved environment rather than bypassing controls. When PowerShell script activation was blocked, I invoked the virtual-environment interpreter directly. When PostgreSQL and Docker were unavailable locally, I kept database-independent checks local and used a PostgreSQL service in CI for production-semantic integration tests.

## 2. Thin vertical slice before breadth

### Lesson

The first complete path was STM -> HTTP -> HTML parsing -> normalized Pydantic domain model -> validation -> CLI/UI. This proved one source end to end before adding many source-specific adapters.

### Interview: Why implement one source before five?

> A thin vertical slice tests architectural assumptions across the entire pipeline while source-specific complexity is still small. Once the shared normalization, validation, persistence and change-detection path is proven, additional adapters can reuse it instead of multiplying unfinished implementations.

## 3. Semantic parsing and fail-loud source behavior

### Lesson

The STM adapter identifies semantic button elements and title content instead of depending on visual color classes. If the expected source structure disappears, it raises `SourceStructureError` rather than returning an apparently valid empty dataset.

### Interview: Why is an empty result dangerous in a monitoring pipeline?

> An empty result can mean either the source genuinely has no records or the extractor broke. Treating parser failure as successful emptiness can cause false deletions, false notifications or silent data loss. I model source-structure failure explicitly and fail visibly.

## 4. Source-independent domain model

### Lesson

Every scanner produces `FundingCallCandidate`. Source adapters contain source-specific extraction, while downstream services consume one validated representation.

### Interview: Why normalize source data early?

> Early normalization creates a stable contract between ingestion and downstream processing. Persistence, change detection, APIs and reporting do not need to understand each website's HTML structure. It reduces coupling and lets new source adapters reuse the same downstream pipeline.

## 5. Identity versus state

### Lesson

`(source_code, external_key)` identifies the logical funding record. A separate deterministic content hash answers whether material state changed.

### Interview: Why keep identity out of the content hash?

> Identity answers which logical entity I am observing. The content hash answers whether that entity's material attributes changed. Keeping those responsibilities separate lets the same opportunity change title, deadline, description or relevance without becoming a different entity.

## 6. Deterministic change detection

### Lesson

Material fields are serialized canonically and hashed with SHA-256. Equal material content produces UNCHANGED; a different hash produces CHANGED and a new immutable version snapshot.

### Interview: Why hash instead of comparing every field ad hoc?

> A canonical hash gives one deterministic change token for the defined material state. It makes idempotency checks simple and testable while the canonical snapshot still preserves the actual fields for audit and diffing. The important part is defining and testing canonicalization, not merely choosing SHA-256.

## 7. PostgreSQL instead of SQLite substitution

### Lesson

The production design uses PostgreSQL, asyncpg, JSONB, transactions, locks and migrations. The managed PC has no PostgreSQL/Docker, so CI provides PostgreSQL 16 rather than silently changing integration semantics to SQLite.

### Interview: Why not use SQLite locally for everything?

> SQLite is useful for many applications, but substituting it would not validate PostgreSQL-specific behavior such as JSONB, locking and migration semantics. I prefer fast unit tests locally and real PostgreSQL integration tests in CI when the workstation cannot run the target database.

## 8. Current state plus immutable versions

### Lesson

`funding_calls` stores the current operational view. `funding_call_versions` stores snapshots for initial and materially changed versions. UNCHANGED observations update `last_seen_at` without creating needless versions.

### Interview: Why not keep only an append-only history table?

> An append-only history is valuable for audit, but operational reads frequently need the current state. Keeping current state plus immutable versions gives simple current queries while retaining historical traceability. The system deliberately avoids generating a new version for an unchanged observation.

## 9. Baseline import

### Lesson

The first successful scan of a source establishes baseline state. Existing opportunities are stored as NEW database entities but are not notification-eligible, preventing a first deployment from flooding users with historical "new" alerts.

### Interview: How do you avoid alert storms on first deployment?

> I model baseline explicitly at the source level. The first successful scan populates current state and versions but suppresses new/change notifications. Subsequent successful scans use normal NEW/UNCHANGED/CHANGED notification eligibility.

## 10. Transactions

### Lesson

`persist_candidates` does not commit internally. The caller owns the transaction boundary, allowing an entire successful source persistence operation and associated audit updates to commit atomically.

### Interview: Why should a lower-level persistence function avoid committing itself?

> The caller often needs several writes to succeed or fail as one unit. If a lower-level function commits internally, higher-level services cannot construct a correct atomic transaction. I let the application service define the unit of work and keep repository/persistence functions transaction-aware but not transaction-owning.

## 11. PostgreSQL concurrency control

### Lesson

Milestone 3 adds a transaction-scoped PostgreSQL advisory lock derived from `source_code` before source-state persistence. This serializes overlapping persistence for the same source and closes the first-baseline race.

### Interview: Why isn't a unique constraint alone enough for concurrent ingestion?

> A unique constraint protects final database integrity, but concurrent first runs could both observe missing state and one would fail late with a constraint violation. A per-source transaction lock serializes the critical state/version calculation so the second transaction sees the committed result and becomes idempotently UNCHANGED. The unique constraint remains a final invariant.

### Interview: Why use a per-source lock rather than a global lock?

> The consistency boundary is one source. Serializing STM should not prevent Sitra or another independent source from persisting. A source-scoped lock preserves correctness without unnecessary cross-source contention.

## 12. Operational scan audit

### Lesson

A source run now has its own audit identity and lifecycle: RUNNING -> SUCCEEDED or FAILED. The audit record captures trigger type, timestamps, baseline state, discovered and change counts, and bounded failure information.

### Interview: Why commit a RUNNING record before doing network I/O?

> It makes an attempted run observable even if the network/parser fails or the process dies mid-run. A crash can leave a stale RUNNING record, which is useful operational evidence and can later be detected and alerted on rather than disappearing from history.

### Interview: Why not store the full exception traceback in the database?

> Operational databases should avoid becoming an uncontrolled sink for secrets or sensitive runtime context. I store bounded error type/message for audit and use application logging for deeper diagnostics. Logging itself still needs redaction and access controls.

## 13. One business operation, many triggers

### Lesson

The source ingestion operation lives in `run_source_ingestion`. CLI, scheduled worker and future Vaketomate/API triggers invoke the same application service rather than reimplementing scan/persistence logic.

### Interview: How do you avoid differences between manual and scheduled runs?

> I separate the trigger from the business operation. The CLI, worker and future API only choose trigger context; the scanner, persistence, audit and change-detection behavior is shared. That makes tests meaningful and prevents trigger-specific business drift.

## 14. Separate web process and worker

### Lesson

Automatic monitoring is not embedded into the FastAPI web process. A separate worker runs one-shot or v1 interval mode. This avoids each web worker accidentally creating its own scheduler.

### Interview: Why not start the scheduler inside FastAPI startup?

> It is simple in development but dangerous when the API scales to multiple processes or replicas because each web instance can start duplicate scheduled jobs. I keep scheduled execution in a separate worker and make the actual ingestion operation reusable. A managed scheduler or Vaketomate scheduler can later invoke the same one-shot worker.

## 15. UI progressive disclosure

### Lesson

The mentor UI was simplified around source -> processing -> result. Funding rows alternate backgrounds for scanability and expand on demand for source details, preserving a clean overview.

### Interview: Why use expandable rows?

> It applies progressive disclosure: the user sees enough information to scan the list, then requests detail for one opportunity without forcing every record's metadata onto the screen. It improves clarity while keeping the detailed data available.

## 16. Upstream data quality controls downstream usefulness

### Lesson

The UI request for deadlines and summaries required improving the STM parser, not inventing frontend demo values. Real source accordion content is captured into `description_text` and evidence.

### Interview: How is frontend quality related to data engineering?

> The UI can only present trustworthy fields that the pipeline captured and normalized. Instead of fabricating missing data in the frontend, I improved source extraction and preserved provenance. Downstream usability is a direct consumer of upstream data quality.

## 17. CI as a production-semantic test environment

### Lesson

GitHub Actions runs Ruff, strict mypy, Alembic migrations and pytest against PostgreSQL 16. The CI database is not a substitute for production operations, but it proves migrations and integration semantics on the target engine.

### Interview: What does "tests pass" mean if local PostgreSQL tests are skipped?

> I distinguish environments. On the managed workstation, PostgreSQL integration tests are intentionally skipped because the prerequisite is absent. In CI, the workflow provisions PostgreSQL, applies migrations and executes those tests. A skip is not a pass; the quality gate is the combined local/CI strategy.

## 18. Vaketomate-ready product boundary

### Lesson

VakeVahti remains standalone for now. Its funding business logic must not depend on Vaketomate internals. Later it can consume shared identity, audit, scheduler, notifications and project-management contracts.

### Interview: How do you design a module that can later become a separate enterprise application?

> I define ownership and contracts before deployment boundaries. The funding product owns its domain and data, while cross-domain capabilities are accessed through published interfaces. Initially everything can be deployed together for simplicity, but callers do not reach into another domain's tables or internal classes. That makes later extraction primarily a deployment/integration change instead of a business rewrite.

### Interview: API or event?

> I use an API/command when a caller needs another capability to perform an operation and return a result, such as creating a project. I use an event to announce a business fact that already happened, such as a funding application being approved. Events let multiple consumers react without the publisher knowing all of them.

## 19. Security and code hygiene habits established so far

- no secrets committed to Git
- runtime configuration through environment settings
- public repository contains sanitized technical material only
- no anti-bot evasion
- unknown values remain unknown rather than guessed
- evidence/provenance is retained
- source failures fail visibly
- strict typing and linting remain CI gates
- database changes use Alembic migrations
- PostgreSQL constraints protect invariants
- audit/error content is bounded
- managed-workstation security policy is not bypassed

## 20. How to use this document

After each meaningful implementation slice:

1. add the engineering concept actually used
2. explain why the design was chosen
3. record at least one interview question
4. give a concise senior-level answer grounded in VakeVahti
5. add failure/trade-off notes where relevant

The goal is that the final training/interview package is produced continuously from real engineering work, not generic questions added after the project is finished.
