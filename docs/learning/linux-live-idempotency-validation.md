# Linux live PostgreSQL and STM idempotency validation

This record captures a successful end-to-end local validation performed on Linux with Docker PostgreSQL 16 and the live STM source.

## Observed result

The environment used Python 3.12 and Docker PostgreSQL 16. Alembic successfully applied both current migrations. Ruff and strict mypy passed. The complete test suite executed against the isolated PostgreSQL test database with 18 tests passing.

After the runtime database was explicitly cleaned, the first real STM worker run produced:

- `baseline=True`
- `new=9`
- `unchanged=0`
- `changed=0`
- 9 STM rows persisted

A second run against the unchanged live source produced:

- `baseline=False`
- `new=0`
- `unchanged=9`
- `changed=0`

This is direct operational evidence that the source identity, content hashing, persistence and baseline logic behave idempotently for the observed live STM state.

## Lesson: prove idempotency with repeated real execution

Unit and integration tests establish deterministic expected behavior. Repeating the same real ingestion against a live source and persistent database validates that the components also compose correctly in an operational path.

### Interview question: How did you validate that your ingestion pipeline is idempotent?

> I tested idempotency at multiple levels. Integration tests persisted the same normalized candidate repeatedly and asserted NEW then UNCHANGED without duplicate rows. I then validated the full live path against STM and PostgreSQL: the first clean scan established a baseline with nine NEW records, and the immediate second scan returned nine UNCHANGED records with zero new or changed records. This showed that stable identity and deterministic content hashing worked through the complete ingestion path.

### Technical question: What does idempotency mean in this ingestion system?

> Reprocessing the same logical observation does not create duplicate entities, duplicate history versions or false change events. The current record may update observation metadata such as `last_seen_at`, but the logical state remains one record and an unchanged observation does not create a new material version.

## Lesson: baseline is business state, not just a first-row flag

The source-level baseline prevents historical calls discovered at deployment time from being treated as newly arrived notifications. The first successful source scan establishes the baseline; subsequent runs use ordinary NEW/UNCHANGED/CHANGED notification eligibility.

### Interview question: Why was `baseline=True` important in the first clean live run?

> It proved the source-state table was clean and the system correctly recognized this as the first successful observation of STM. The calls were persisted as new database entities, but baseline semantics can suppress a notification storm for records that already existed before monitoring began.

### Technical question: Why track baseline per source instead of globally?

> Sources are onboarded independently. STM may already have an established baseline while Sitra is scanned for the first time. A source-level baseline lets each adapter enter production safely without affecting the lifecycle of other sources.

## Lesson: local PostgreSQL improves the feedback loop

The managed workplace machine could not run PostgreSQL locally, so PostgreSQL integration behavior was initially verified in CI. On Linux, Docker provides the same major PostgreSQL version locally, enabling migrations, integration tests, database inspection and real worker execution before pushing changes.

### Interview question: Why keep CI PostgreSQL tests if local Docker now works?

> Local Docker shortens the development feedback loop, but CI remains an independent reproducible quality gate. A developer machine can have stale state or configuration; CI starts from a controlled environment and proves the repository can build, migrate and test without relying on local setup.

## Technical drill-down questions

### What protects against duplicate logical funding records?

The database unique identity is `(source_code, external_key)`, while the ingestion service also performs deterministic lookup and change classification before updating or versioning the record.

### What protects against overlapping first scans?

A PostgreSQL transaction-scoped advisory lock serializes persistence for the same source, preventing two concurrent first runs from both treating the source as uninitialized.

### Why does UNCHANGED not create another version row?

Version history represents material state changes, not observation frequency. Creating a version for every poll would add noise and storage without improving auditability; `last_seen_at` records repeated observation instead.

### What would make the second live scan legitimately return CHANGED?

Any material field included in canonical content hashing could change, such as title, source URL, application dates, description, relevance status/reason or evidence. The same external identity would then receive a new immutable version snapshot.
