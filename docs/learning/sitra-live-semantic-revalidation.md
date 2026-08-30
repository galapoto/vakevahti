# Sitra live semantic revalidation

Date: 2026-08-30

Status: corrected Sitra entity extraction live-validated; final multi-source/local quality rerun remains before PR #8 can leave draft.

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

## Remaining Milestone 4 gate

Before PR #8 leaves draft:

1. run `STM,SITRA,ACADEMY` twice using the corrected Sitra parser
2. confirm the second run is UNCHANGED for all three sources
3. rerun local Ruff, strict mypy and full PostgreSQL pytest
4. inspect current source counts and recent audit rows
5. update PR #8 with the final combined evidence
6. only then mark ready and merge using the project's professional merge convention
