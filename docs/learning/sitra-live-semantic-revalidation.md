# Sitra live semantic revalidation

Date: 2026-08-30

Status: Milestone 4 live source, multi-source, local quality, persistence, uniqueness and version-state gates passed.

## What was validated

After the lifecycle-to-card parser fix, the known-invalid Sitra development state was removed in a source-scoped transaction:

- one invalid `funding_calls` row deleted
- one Sitra `source_states` row deleted
- STM and Suomen Akatemia state preserved
- historical `source_scan_runs` preserved

A fresh live Sitra run then produced one real funding opportunity:

`Tuottavuutta tekoälyllä – valmennusta julkiselle sektorille uudistumisen tueksi`

First corrected run:

- `baseline=True`
- `discovered=1`
- `new=1`
- `unchanged=0`
- `changed=0`

Immediate second run:

- `baseline=False`
- `discovered=1`
- `new=0`
- `unchanged=1`
- `changed=0`

The generic section title `Rahoitushaut` was no longer emitted.

The row persisted `application_deadline_at=2026-09-15 09:00:00+00`. The authoritative Sitra information page states that the call closes on 15 September 2026 at 12:00 Helsinki time. In September Helsinki is UTC+3, so the PostgreSQL UTC value is correct.

The live count of one actionable call is also consistent with Sitra's current state on 30 August 2026. The separate continuous breakthrough-renewal round ended on 28 August 2026 at 12:00 and Sitra states that the next round opens on 1 September 2026.

Backend CI run #58 passed Ruff, strict mypy, Alembic and PostgreSQL pytest on the semantic parser correction.

## Final corrected multi-source rerun

After pulling the corrected parser and the first live-validation documentation commit, the Linux development environment ran `STM,SITRA,ACADEMY` twice consecutively using the real PostgreSQL development database.

First combined run:

- STM: `new=0`, `unchanged=9`, `changed=0`
- SITRA: `new=0`, `unchanged=1`, `changed=0`
- ACADEMY: `new=0`, `unchanged=7`, `changed=0`

Second combined run:

- STM: `new=0`, `unchanged=9`, `changed=0`
- SITRA: `new=0`, `unchanged=1`, `changed=0`
- ACADEMY: `new=0`, `unchanged=7`, `changed=0`

This proves repeated multi-source orchestration remains idempotent after the Sitra semantic correction. No source produced a false NEW or CHANGED event on the immediate repeat.

The local quality gates then passed:

- Ruff: all checks passed
- strict mypy: no issues found in 24 source files
- pytest: 28 passed
- PostgreSQL integration tests included successful ingestion audit, failed-scan isolation, persistence idempotency and per-source concurrency serialization

One Starlette `TestClient`/`httpx` deprecation warning remains. It does not affect Milestone 4 correctness and is tracked separately in GitHub issue #9 rather than expanding the source-adapter PR at the merge boundary.

## Final PostgreSQL state inspection

The final developer-database inspection passed after the corrected Sitra baseline and repeated combined scans.

Current funding rows:

- ACADEMY: 7
- SITRA: 1
- STM: 9
- total current entities: 17

Stored immutable versions:

- ACADEMY: 7
- SITRA: 1
- STM: 9
- total stored versions: 17

The one-to-one relationship between current entities and versions at this point confirms that repeated UNCHANGED observations did not create unnecessary immutable history.

The corrected Sitra row is:

- title: `Tuottavuutta tekoälyllä – valmennusta julkiselle sektorille uudistumisen tueksi`
- source URL: `https://asiointi.sitra.fi/`
- deadline: `2026-09-15 09:00:00+00`
- current version: 1
- stored versions: 1

The duplicate-identity query grouped by `(source_code, external_key)` returned zero rows.

All source baselines exist and each source has a later `last_successful_scan_at` value:

- ACADEMY baseline: `2026-08-30 15:50:18.557908+00`; last success: `2026-08-30 16:51:30.945899+00`
- SITRA baseline: `2026-08-30 16:46:14.054322+00`; last success: `2026-08-30 16:51:30.77249+00`
- STM baseline: `2026-08-30 15:40:21.329981+00`; last success: `2026-08-30 16:51:29.02993+00`

Historical failed and pre-correction Sitra scan-audit records remain preserved by design. The final two combined worker executions already provide the six successful source-run outcomes needed for the release gate.

## Data Engineering lesson: validate against an independent authoritative representation

A parser should not be trusted merely because it returns plausible records. After extraction, high-value fields should be cross-checked against another authoritative representation when one exists.

For this validation, the actionable Power Pages listing proved which call was currently available, while Sitra's public call information page independently confirmed the deadline and lifecycle state.

This was not used as hidden production enrichment. It was an operational validation technique.

### Interview question: Why cross-check a live ingestion result against another official page?

> A pipeline can be internally consistent and still misinterpret the source. For high-value fields such as identity, lifecycle and deadlines, an independent representation from the same authoritative organization gives an external correctness check. In VakeVahti I used Sitra's public funding-call page to verify the entity and deadline produced from the application listing. I keep that validation distinct from the production parser so CI remains deterministic and the ingestion contract remains explicit.

## Timezone lesson: database timestamps should be interpreted, not visually compared

The database showed `09:00+00`, while the Sitra information page showed `12:00` Helsinki time. Those are the same instant because Helsinki is UTC+3 on 15 September 2026.

### Technical interview question: Why is `2026-09-15 09:00:00+00` correct when the source says 12:00?

> PostgreSQL stores a timezone-aware instant and commonly displays it in the database session timezone, which is UTC in this development environment. The source time is Europe/Helsinki. On that date Helsinki is UTC+3, so 12:00 local converts to 09:00 UTC. The important invariant is the instant, not whether the displayed clock value matches the source page.

### Data Engineering interview question: What is dangerous about storing a local time without timezone information?

> A naive timestamp loses the rules needed to interpret the instant. That becomes especially dangerous around daylight-saving transitions and when data is consumed across regions. VakeVahti parses explicit source times with the named `Europe/Helsinki` timezone and persists timezone-aware values.

## Database lesson: repair scope should follow the defect scope

The invalid Sitra row was known development data created by a parser defect. The repair deleted only Sitra funding state and its source baseline. It did not reset the entire database or erase historical scan audits.

The foreign-key cascade removed versions belonging to the deleted invalid funding row.

### Database interview question: Why preserve `source_scan_runs` for a run that produced invalid data?

> The audit table records what the system actually attempted and believed at that time. Rewriting it would destroy incident evidence. I corrected the invalid current funding state while preserving operational history. In production I would use an explicit audited repair procedure and link the incident or repair to affected records rather than casually deleting history.

## Observability lesson: success counters need semantic inspection

The earlier faulty parser had all the indicators operators normally like to see: HTTP 200, SUCCEEDED audit, baseline completion and an idempotent repeat. Only inspection of the persisted title exposed the defect.

This supports a future source-health model with multiple dimensions:

- transport health
- structural parser health
- semantic/data-quality health
- persistence health
- freshness

### System Design interview question: What would you add to source health beyond a green/red worker status?

> I would expose the last successful scan, duration, discovered/new/changed counts, baseline state, consecutive failures, freshness and selected semantic invariants. For important sources I would also surface suspicious changes such as an unexpected collapse in record count or generic page headings appearing as entity titles. A successful process exit should not be the only definition of healthy data.

## Identity lesson: actionable source URL versus canonical information URL

The Sitra application card currently does not expose a call-specific link through the parsed rendered card, so VakeVahti honestly stores the actionable source root and uses title fallback identity for this record.

Sitra separately publishes a stable information page for the call. That is a good future enrichment/canonical-identity candidate, but introducing cross-surface title matching at the end of Milestone 4 would add a new failure mode without evidence that it is required for the current worker contract.

The follow-up should evaluate a deterministic source-owned identifier or canonical-link discovery mechanism rather than silently scraping search results or guessing URL slugs.

### Backend interview question: Why not immediately replace the root URL with a URL found on another Sitra page?

> The current scanner's authoritative listing does not expose that URL directly. Joining two public surfaces by fuzzy title would create a new identity-matching problem. I prefer an honest fallback identity now and a separately designed enrichment step later, where matching rules, provenance and failure behavior can be tested explicitly.

## QA lesson: a live gate can invalidate a green implementation

The first browser-fallback implementation passed deterministic tests and CI but failed semantic inspection. The regression was then improved, CI passed again, and a second live validation proved the corrected entity.

### QA interview question: How do unit tests, integration tests and live source validation differ here?

> Unit tests prove deterministic parser behavior against controlled structures. PostgreSQL integration tests prove persistence, transactions and idempotency. Live validation proves that the current external website still satisfies the adapter assumptions. None replaces the others; together they cover code correctness, database semantics and external-contract reality.

## CI lesson: warnings and failures have different release semantics

The final local suite passed all 28 tests but emitted one deprecation warning from the test-client dependency stack. A warning is not equivalent to a failed invariant, but it is also not something to ignore indefinitely.

### DevOps/QA interview question: Why did you not upgrade the TestClient dependency inside PR #8?

> The warning is a future compatibility signal, not a failure of the funding-source milestone. Changing the HTTP test-client stack would add unrelated dependency risk at the merge boundary. I kept the current quality gate green, created a dedicated follow-up issue, and will handle the migration in a focused change where compatibility and regressions can be evaluated independently.

## Persistence lesson: current state, immutable history and uniqueness answer different questions

The final inspection showed 17 current funding records and exactly 17 stored versions. That does not happen automatically just because the current table has a uniqueness constraint. It is the combined result of source identity, change detection and version-writing rules.

### Data Engineering interview question: Why is one stored version per current row meaningful after repeated scans?

> Each source was scanned repeatedly, but unchanged observations did not create new historical versions. That proves the version table represents material state transitions rather than observation frequency. `last_seen_at` can move forward without polluting immutable change history.

### Database interview question: If `(source_code, external_key)` is unique, why still run a duplicate inspection query?

> A database uniqueness constraint protects the exact stored key, but an extractor could still generate two different keys for the same real-world entity. The duplicate-key query verifies the structural invariant, while live semantic inspection verifies that the identity function itself still represents the business entity correctly. They protect different failure modes.

### Backend interview question: What is the difference between idempotency and version discipline?

> Idempotency means repeating the same logical input does not produce unintended business changes. Version discipline is more specific: an unchanged observation must not append another immutable version. VakeVahti demonstrated both: the second combined run emitted only UNCHANGED outcomes, and the database still held one version per current entity.

## Milestone 4 completion gate

Milestone 4 is ready to leave draft because all required gates passed:

1. deterministic Sitra parser and browser-fallback regression tests pass
2. the semantic false positive was reproduced, understood and corrected
3. the known-invalid Sitra development state was repaired without erasing audit history
4. a fresh live Sitra baseline emits the correct funding entity
5. the immediate Sitra repeat is UNCHANGED
6. two complete `STM,SITRA,ACADEMY` runs are UNCHANGED across all three sources
7. Ruff and strict mypy pass
8. the full PostgreSQL pytest suite passes: 28 tests
9. current source counts are ACADEMY 7, SITRA 1, STM 9
10. version counts are ACADEMY 7, SITRA 1, STM 9
11. the duplicate-key query returns zero rows
12. all three source states have completed baselines and later successful scans
13. the non-blocking TestClient deprecation is tracked separately as issue #9

The next action is to mark PR #8 ready, perform the final PR/review-state check, and squash-merge it using the same milestone-style convention used for earlier VakeVahti merges.