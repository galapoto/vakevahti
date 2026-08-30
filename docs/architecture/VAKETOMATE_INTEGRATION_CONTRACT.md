# VakeVahti -> Vaketomate Integration Contract

Status: architecture baseline, 2026-08-30

## 1. Purpose

VakeVahti continues to be built as an independently runnable funding-monitoring product. It is expected to become one application under the future Vaketomate platform without rewriting the funding domain.

The architectural objective is extraction readiness: VakeVahti may remain a Vaketomate module, or later become a separately deployed enterprise product while preserving its published contracts.

## 2. Ownership boundary

VakeVahti owns funding-domain behavior and data, including:

- funding-source adapters and source-specific parsing
- normalized funding opportunities
- relevance classification and evidence
- source scan state and scan-run audit history
- funding opportunity versions and change detection
- future funding applications, decisions, funding-project linkage, and funding-specific reporting

VakeVahti does not own generic platform capabilities merely because it consumes them.

Examples of capabilities expected to be owned by Vaketomate or another bounded product:

- organization identity / SSO
- platform-wide authorization policy
- platform audit aggregation
- notifications transport
- generic project/task/milestone/risk management
- shared document/file storage
- platform scheduler/orchestration

## 3. Non-negotiable dependency rule

A Vaketomate application may depend on another application's published contract, but not on that application's internal implementation.

Allowed:

`Funding application -> Project API -> create project`

Not allowed:

`Funding code -> direct SQL -> project.tasks`

Even when modules initially share one process or PostgreSQL server, cross-domain table access is prohibited. This is what keeps later extraction possible.

## 4. Contracts

### 4.1 HTTP/API

Public application capabilities will be versioned under an explicit API namespace, for example:

`/api/v1/funding/...`

The current `/api/demo/...` endpoints are development-only and are not integration contracts.

Breaking API changes require a version change or a documented compatibility migration.

### 4.2 Events

Domain events will describe facts that already happened. Event names are versioned, for example:

- `funding.opportunity.discovered.v1`
- `funding.opportunity.changed.v1`
- `funding.application.approved.v1` (future)
- `funding.project.linked.v1` (future)

A publisher must not need to know all event consumers.

### 4.3 Commands versus events

Use a synchronous API/application command when Funding needs another capability to perform an operation and needs a result, for example creating a Project.

Use an event when Funding announces a completed business fact, for example that a funding application was approved.

## 5. Identity, authorization and actor context

VakeVahti will accept authenticated identity from the approved Vaketomate/organization identity boundary rather than implementing a competing identity store when integrated.

Authorization remains explicit and domain-scoped. Example future permissions:

- `funding.opportunities.read`
- `funding.opportunities.review`
- `funding.applications.edit`
- `funding.applications.approve`
- `funding.admin`

"Authenticated" never automatically means "authorized for every Vaketomate app".

## 6. Audit and correlation

Every cross-app request/event should carry a correlation identifier. Source ingestion already uses a unique `source_scan_run.id`, which can be propagated into later logs, notifications and events.

Future user-initiated audit events should include, where applicable:

- event/action
- timestamp
- actor identity
- app/domain
- entity type and identifier
- before/after or version reference
- correlation ID
- result

Secrets, tokens, raw credentials and unnecessary personal data must not be placed in audit payloads.

## 7. Project-management integration

If a funding application becomes an approved project, VakeVahti should request creation/linking through the Project product contract rather than creating Project tables itself.

Conceptually:

`FundingApplication -> ProjectService.create_project(...) -> project_id`

VakeVahti stores the returned project reference and can present Project information through the Project API. The user may experience one seamless Vaketomate UI while the domains remain independently owned.

## 8. Scheduling integration

VakeVahti owns the business operation "run funding source ingestion". It does not require ownership of the enterprise scheduling platform.

Current standalone triggers may include:

- manual CLI
- one-shot worker
- v1 single-replica interval worker

Future Vaketomate can invoke the same ingestion operation from its shared scheduler. The business logic must not be duplicated in scheduler-specific code.

## 9. Persistence ownership

Current standalone tables are VakeVahti-owned. When moved into a shared Vaketomate PostgreSQL environment, logical ownership should remain explicit, preferably through a `funding` schema or equivalent ownership convention.

Other Vaketomate products must not directly update funding-owned tables.

## 10. Extraction path

The expected evolution is:

1. standalone VakeVahti product
2. VakeVahti presented inside the Vaketomate shell
3. shared Vaketomate identity/audit/scheduling/notification capabilities
4. optional independent Funding API/worker deployment
5. optional independent Funding database

If the contracts in this document are respected, steps 4-5 should be deployment changes rather than domain rewrites.

## 11. Definition of integration-ready

A feature is Vaketomate-ready when:

- domain ownership is clear
- business logic is not embedded in UI or scheduler triggers
- external calls use explicit interfaces
- database ownership is respected
- operations are auditable
- configuration comes from runtime settings
- secrets are externalized
- tests cover domain behavior and integration boundaries
- documentation states assumptions and failure behavior
