# VakeVahti -> Vaketomate Integration Contract

Status: architecture baseline, updated 2026-09-07

## 1. Purpose

VakeVahti is the **Funding bounded domain/module inside Vaketomate**. It is not treated as an unrelated side application that may or may not be integrated later.

The module remains independently runnable during development and may later be deployed independently, but that is a deployment choice rather than a product-ownership ambiguity. The user-facing product direction is one Vaketomate platform with Funding as a first-class capability.

The architectural objective is therefore twofold:

1. seamless Vaketomate integration now; and
2. extraction/deployment independence later without rewriting the funding domain.

## 2. Ownership boundary

Funding/VakeVahti owns funding-domain behavior and data, including:

- the authoritative five funding-source families: STM, Haeavustuksia.fi, EURA 2021, Sitra, and Suomen Akatemia;
- funding-source adapters and source-specific parsing;
- normalized funding opportunities;
- applicant eligibility / relevance classification and retained evidence;
- source scan state and scan-run audit history;
- funding opportunity versions and change detection;
- future funding applications, decisions, funding-project linkage, and funding-specific reporting.

Funding does not own generic platform capabilities merely because it consumes them.

Examples of capabilities expected to be owned by Vaketomate or another bounded product:

- organization identity / SSO;
- platform-wide authorization policy;
- platform audit aggregation;
- notifications transport;
- generic project/task/milestone/risk management;
- shared document/file storage;
- platform scheduler/orchestration.

## 3. Non-negotiable dependency rule

A Vaketomate module may depend on another module's published contract, but not on that module's internal implementation.

Allowed:

`Funding application -> Project API -> create project`

Not allowed:

`Funding code -> direct SQL -> project.tasks`

Even when modules initially share one process or PostgreSQL server, cross-domain table access is prohibited. This is what keeps later extraction possible.

## 4. Contracts

### 4.1 HTTP/API

Funding application capabilities should evolve toward an explicit versioned namespace:

`/api/v1/funding/...`

The current `/api/...` persisted endpoints are an internal transition contract. `/api/demo/...` endpoints are development-only and are never platform integration contracts.

Breaking API changes require a version change or a documented compatibility migration.

### 4.2 Events

Domain events describe facts that already happened. Event names are versioned, for example:

- `funding.opportunity.discovered.v1`
- `funding.opportunity.changed.v1`
- `funding.opportunity.review_required.v1`
- `funding.application.approved.v1` (future)
- `funding.project.linked.v1` (future)

A publisher must not need to know all event consumers.

### 4.3 Commands versus events

Use a synchronous API/application command when Funding needs another capability to perform an operation and needs a result, for example creating a Project.

Use an event when Funding announces a completed business fact, for example that a funding opportunity was discovered or an application was approved.

## 5. Identity, authorization and actor context

Funding accepts authenticated identity from the approved Vaketomate/organization identity boundary rather than implementing a competing identity store.

Authorization remains explicit and domain-scoped. Example permissions:

- `funding.opportunities.read`
- `funding.opportunities.review`
- `funding.applications.edit`
- `funding.applications.approve`
- `funding.admin`

"Authenticated" never automatically means "authorized for every Vaketomate module".

## 6. Audit and correlation

Every cross-module request/event should carry a correlation identifier. Source ingestion already uses a unique `source_scan_run.id`, which should propagate into downstream relevance review, notifications and events where practical.

Future user-initiated audit events should include, where applicable:

- event/action;
- timestamp;
- actor identity;
- app/domain;
- entity type and identifier;
- before/after or version reference;
- correlation ID;
- result.

Secrets, tokens, raw credentials and unnecessary personal data must not be placed in audit payloads.

## 7. Funding source ingestion inside Vaketomate

Funding owns the business operation:

`run funding source ingestion`

The platform scheduler may trigger it, but source adapters, normalization, eligibility rules, deduplication, versioning and source-health semantics remain Funding-domain logic.

The authoritative source set is documented in:

`docs/requirements/FUNDING_SOURCE_REQUIREMENTS.md`

Source-specific rules must not be flattened into one generic relevance rule:

- STM: every new call is relevant;
- Haeavustuksia: applicant eligibility must be proven from Myöntöperusteet / applicant evidence;
- EURA: first filter by Valtakunnallinen/Etelä-Suomi, then evaluate wellbeing-area participation evidence;
- Sitra: every new funding announcement is relevant;
- Suomen Akatemia: every new call is relevant.

## 8. Notification integration

The stakeholder outcome is event-driven notification rather than weekly manual monitoring.

Target flow:

`scheduled source scan -> normalized current snapshot -> NEW detection -> notification outbox -> Vaketomate notification transport -> email`

Funding owns the domain fact that a new eligible opportunity exists and the deduplication key that prevents duplicate notifications.

Vaketomate owns or may own the transport capability that delivers email/other notifications.

Directly sending email from parser code is prohibited.

The future notification boundary must support:

- first-baseline suppression;
- deduplication;
- retry without duplicating the domain event;
- delivery status/audit;
- correlation to `source_scan_run.id` and funding opportunity identity.

## 9. Project-management integration

If a funding application becomes an approved project, Funding should request creation/linking through the Project product contract rather than creating Project tables itself.

Conceptually:

`FundingApplication -> ProjectService.create_project(...) -> project_id`

Funding stores the returned project reference and can present Project information through the Project API. The user experiences one Vaketomate UI while the domains remain independently owned.

## 10. Scheduling integration

Current standalone triggers may include:

- manual CLI;
- one-shot worker;
- v1 single-replica interval worker.

Vaketomate may invoke the same ingestion operation from its shared scheduler. Business logic must not be duplicated in scheduler-specific code.

## 11. Persistence ownership

Current standalone tables are Funding-owned. When moved into a shared Vaketomate PostgreSQL environment, logical ownership should remain explicit, preferably through a `funding` schema or equivalent ownership convention.

Other Vaketomate modules must not directly update Funding-owned tables.

The current primary operational grains include:

- one row per logical funding opportunity in `funding_calls`;
- one row per immutable material version in `funding_call_versions`;
- one row per funding source in `source_states`;
- one row per ingestion attempt in `source_scan_runs`.

Future notification outbox/review tables must define their grain explicitly before implementation.

## 12. Data contracts and modelling discipline

Funding's API schema is not identical to its PostgreSQL schema.

Storage-only implementation fields such as hashes/internal keys must not become platform dependencies merely because they exist in a table.

Every new cross-module field requires an explicit contract decision:

- purpose;
- semantic meaning;
- nullability;
- stability/versioning expectation;
- source/provenance when derived;
- whether it is operational state, history, or presentation data.

## 13. Extraction path

The expected evolution is:

1. Funding/VakeVahti independently runnable while being designed as a Vaketomate bounded domain;
2. Funding presented inside the Vaketomate shell;
3. shared Vaketomate identity/audit/scheduling/notification capabilities;
4. optional independent Funding API/worker deployment;
5. optional independent Funding database.

If the contracts in this document are respected, steps 4-5 are deployment changes rather than domain rewrites.

## 14. Definition of integration-ready

A feature is Vaketomate-ready when:

- domain ownership is clear;
- business logic is not embedded in UI or scheduler triggers;
- external calls use explicit interfaces;
- database ownership is respected;
- operations are auditable;
- configuration comes from runtime settings;
- secrets are externalized;
- tests cover domain behavior and integration boundaries;
- source/provenance semantics are documented;
- API/event contracts are explicit;
- documentation states assumptions and failure behavior.

## 15. Product-quality rule

Funding is being built as a durable production domain, not as a disposable prototype that will be rewritten when Vaketomate arrives.

That means source adapters, data modelling, lineage, idempotency, schema evolution, notification dedupe, security boundaries, tests, operational health and interview/learning documentation should be designed correctly at the point they are introduced. Premature enterprise complexity is still avoided, but known future Vaketomate requirements must not be knowingly violated for short-term convenience.
