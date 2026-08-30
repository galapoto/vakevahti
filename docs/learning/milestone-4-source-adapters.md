# Milestone 4: Sitra and Suomen Akatemia source adapters

This record captures the engineering lessons and interview preparation created while expanding VakeVahti from STM to multiple independent funding sources.

## What was built

- `SitraScanner` for the Sitra funding service listing
- `AcademyScanner` for Suomen Akatemia open/upcoming calls
- shared scanner helpers for canonical URLs, stable source identities and conservative Finnish datetime parsing
- source registry entries for `STM`, `SITRA` and `ACADEMY`
- fixture-style unit tests that do not call live websites
- source-specific business rules while preserving one shared downstream `FundingCallCandidate` contract

## Lesson: source-specific extraction, source-independent downstream processing

The HTML semantics of STM, Sitra and Suomen Akatemia differ. Their adapters therefore own extraction rules, while persistence, change detection, audit and scheduling continue to consume the same `FundingCallCandidate` type.

### Interview question: Why not build one generic scraper for every funding website?

> A generic scraper can reduce code initially, but unrelated websites expose different semantics, lifecycle states and failure modes. I keep source-specific parsing inside adapters and normalize immediately into one domain contract. This contains website volatility without leaking it into persistence or business workflows.

### Technical question: What design pattern does the source registry resemble?

> It is a small factory/registry around a common protocol. Configuration selects source codes, the registry constructs adapters, and orchestration depends on the protocol rather than concrete scanner classes. This supports open-ended source growth without hardcoding branching logic into the worker.

## Lesson: stable identity should prefer canonical source links

Where a funding call exposes a canonical call link, the adapter derives its external key from the source code plus canonical URL. A title fallback is used only when a more durable source identity is unavailable.

### Interview question: Why is a canonical URL often a better identity than a title?

> Titles are presentation data and can be edited without changing the logical funding opportunity. A source-owned canonical URL is usually more stable. I separate identity from material content so title edits become CHANGED rather than creating false NEW records.

### Technical question: Why remove URL fragments before hashing identity?

> Fragments are client-side navigation state and normally do not identify a different server resource. Removing them avoids multiple identities for the same funding call when links differ only by anchors.

## Lesson: never invent time semantics

The normalized model stores timezone-aware datetimes. Many Finnish source pages publish a deadline date without a clock time. The parser deliberately leaves the datetime null unless the source explicitly states a time.

### Interview question: Why not convert a bare deadline date to 23:59?

> That would add information the source did not state. A guessed end-of-day value can make reminders, ordering and eligibility decisions wrong. I retain the textual source evidence and only populate the structured datetime when the source provides enough precision.

### Technical question: Why use `zoneinfo` rather than a fixed UTC offset?

> Europe/Helsinki observes daylight-saving rules. A fixed `+02:00` or `+03:00` offset is wrong for part of the year. `zoneinfo` models the named timezone and produces the correct offset for the date.

## Lesson: filtering belongs at the source boundary when the source exposes explicit lifecycle state

Sitra explicitly labels funding calls as `Haku käynnissä` or `Haku sulkeutunut`. The adapter recognizes both states but emits only currently open calls. Suomen Akatemia exposes an `Avoimet ja tulossa olevat haut` section and a separate preparation section; the adapter stops before the preparation section.

### Interview question: Why recognize closed records if you do not ingest them?

> Recognizing both open and closed markers proves that the parser still understands the page structure. If no lifecycle markers can be recognized, I fail loudly as a potential source-structure change instead of silently returning an empty scan.

## Lesson: parser tests should be deterministic and offline

Normal CI tests use representative HTML fixtures/strings and never depend on live websites. Live source validation is an operational/manual check because websites can be unavailable or change independently of the code under test.

### Interview question: Why avoid live website requests in ordinary CI?

> External availability would make CI nondeterministic and could cause rate or policy problems. Unit tests verify parsing against controlled fixtures, while separate operational checks validate the real source. This cleanly separates code correctness from external-system availability.

### Technical question: What should happen when a live source structure changes?

> The adapter should raise a source-structure error, the ingestion audit should record a FAILED run, and existing persisted funding records should remain untouched. A parser failure must never be interpreted as evidence that all previously known calls disappeared.

## Lesson: configuration enables staged rollout

Registering an adapter does not automatically enable it. `ENABLED_SOURCES` controls which adapters the worker executes. New sources can therefore be implemented and tested before being enabled in a production environment.

### Interview question: Why separate registration from enablement?

> Registration says the software knows how to construct a capability. Enablement is an operational decision. Keeping them separate supports staged rollout, rollback and environment-specific configuration without code changes.

## Follow-up risks and planned work

- live HTML validation is still required before declaring Sitra and Academy production-ready
- empty-but-valid source scans need explicit semantics before a source can legitimately have zero active calls
- source-specific application start/end semantics may later need date-only fields in addition to exact datetimes
- Haeavustuksia and EURA require more complex eligibility classification than the all-relevant rules used by STM, Sitra and Suomen Akatemia
