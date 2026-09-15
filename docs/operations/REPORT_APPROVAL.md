# Funding report approval operations

## Purpose

The approval workflow turns a mutable funding-report draft into an auditable workplace decision without losing earlier decisions or silently changing approved content.

## State machine

| Current state | Action | Next state | Notes |
| --- | --- | --- | --- |
| `DRAFT` | submit | `WAITING_APPROVAL` | idempotent while already waiting |
| `WAITING_APPROVAL` | approve | `APPROVED` | immutable approval event + composition snapshot |
| `WAITING_APPROVAL` | return for edit | `DRAFT` | comment required; decision remains in history |
| `WAITING_APPROVAL` | reject | `REJECTED` | comment required; decision remains in history |
| `REJECTED` | edit | `DRAFT` | explicit rework is required before resubmission |
| `APPROVED` | revise | new `DRAFT` version | original approved report is unchanged |

Direct editing of `APPROVED` returns HTTP 409. Direct submission of `REJECTED` or `APPROVED` returns HTTP 409.

## API contract

- `GET /api/reports?status=WAITING_APPROVAL&limit=25&offset=0` — bounded coordinator queue.
- `POST /api/reports/{id}/submit` — submit a draft for review.
- `POST /api/reports/{id}/decision` — `APPROVE`, `RETURN_FOR_EDIT`, or `REJECT`.
- `POST /api/reports/{id}/revise` — create/reuse the next draft version of an approved report.
- `GET /api/reports/{id}` — inspect current report fields, lineage and approval events.

Return/reject decision bodies require a `comment`. The API currently accepts `actor_id` and optional `actor_display_name` as staging inputs.

## Approval evidence grain

`funding_report_approval_events` grain: **one immutable coordinator decision about one exact report composition at one point in time**.

Each event stores:

- report ID;
- decision;
- actor assertion and actor source;
- optional/required comment according to decision type;
- decision timestamp;
- SHA-256 hash of canonical report composition;
- JSON snapshot of the exact composition, including selected funding-call snapshots and report version lineage.

The hash detects a different composition. It is not a cryptographic signature and does not prove who made the decision.

## Version lineage

An approved report may not be mutated. `POST /revise` produces:

`approved report vN -> draft report vN+1`

The successor stores `supersedes_report_id`. A uniqueness constraint ensures one direct successor per approved version, and the service returns that same successor when a revision request is retried.

## Actor trust boundary

`CLIENT_ASSERTED` means the actor identifier came from the current API request. It is **not trusted organization identity**. It is retained so the data model and UI can be exercised before SSO integration.

Production approval must replace this with identity derived from the approved VakeTomatti/organization OIDC or equivalent boundary, then enforce authorization such as `funding.reports.approve`. The client must not be allowed to choose its own trusted actor identity.

## Delivery boundary

The approval workflow does not yet claim that every email path is approval-gated. In particular, the existing case-email queue was built as a staging integration path and can create a durable delivery from a case composition independently of this report approval state machine.

Before workplace production enablement, define and test the policy connecting approved report/artifact versions to notification/email transport, and derive recipient/actor permissions from trusted identity. Do not use `ENABLE_*_WRITE_ROUTES` as a substitute for authorization.

## Operational checks

For an approval incident, inspect in this order:

1. report state and `version_number`;
2. `supersedes_report_id` lineage;
3. ordered approval events;
4. event `content_hash` and stored snapshot;
5. actor source (`CLIENT_ASSERTED`, `PREVIEW_FIXTURE`, later trusted SSO source);
6. application logs/correlation context;
7. delivery records separately if the report was sent.

A missing or conflicting decision should fail visibly; do not manufacture an approval from UI state.
