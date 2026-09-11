# Funding notification outbox

Status: implemented Funding-domain handoff; transport intentionally external

## Purpose

Funding must not lose a newly discovered opportunity merely because email or another
notification channel is temporarily unavailable. The outbox therefore stores the
notification intent in PostgreSQL in the same transaction as the authoritative funding
snapshot and successful source-run update.

The Funding module owns event creation and deduplication. Vaketomate/platform owns the
actual delivery transport.

## Grain

`notification_outbox` grain: **one durable Funding event intent for one funding call in
one source-scan occurrence**.

The unique `dedupe_key` is derived from:

```text
<event_type>|<funding_call_id>|<source_scan_run_id>
```

This permits an explicit reappearance in a later authoritative snapshot to become a new
business occurrence while preventing duplicate rows for the same call/event/run.

## Event policy

The first successful source baseline never creates notification intents.

After baseline:

- `NEW + RELEVANT` -> `funding.opportunity.discovered.v1`
- `NEW + NEEDS_REVIEW` -> `funding.opportunity.review_required.v1`
- `CHANGED + RELEVANT` -> `funding.opportunity.changed.v1`
- `CHANGED + NEEDS_REVIEW` -> `funding.opportunity.review_required.v1`
- `NOT_RELEVANT` -> no notification intent
- `UNCHANGED` -> no notification intent

The outbox payload includes funding call identity/version, source code, public source URL,
relevance status/reason, source-scan correlation ID, and observation time. It does not
contain credentials or a provider-specific email schema.

## Transaction boundary

`run_source_ingestion()` first creates a committed `RUNNING` scan audit row. The following
operations then happen in one PostgreSQL transaction:

```text
persist funding snapshot
+ create immutable call versions
+ create eligible notification_outbox rows
+ mark source scan SUCCEEDED
```

If that transaction fails, neither the funding changes nor notification intents commit.
The already-created scan row is then marked `FAILED` by the failure audit path.

## Provider-neutral delivery lease

A transport worker uses the Funding service boundary rather than updating the table with
ad-hoc SQL:

- `claim_notification_intents(...)`
- deliver the returned event through the approved platform transport
- `mark_notification_sent(...)`, or
- `mark_notification_failed(..., next_attempt_at=...)`

Claims use PostgreSQL `FOR UPDATE SKIP LOCKED`, allowing multiple workers to process
different rows concurrently. A claim has a token and expiration time. If a worker dies,
the expired `PROCESSING` row becomes reclaimable. A stale worker cannot settle a row
after another worker has reclaimed it because acknowledgement requires the current claim
token.

## Status lifecycle

```text
PENDING
  -> PROCESSING
       -> SENT
       -> FAILED -> PROCESSING -> ...

PROCESSING --lease expires--> PROCESSING under a new claim token
```

`attempt_count` increments when a delivery is claimed, not when an intent is created.
`last_error` and `next_attempt_at` support transport-controlled retry/backoff.

## What is deliberately not implemented here

Funding does not choose SMTP, Microsoft Graph, Azure Communication Services, Teams,
Slack, or another delivery provider. It also does not own organization-wide recipient
policy. Those belong behind the Vaketomate/platform notification contract.

This means the Funding domain can be tested and deployed independently while the same
outbox contract can later feed whichever approved organization transport is selected.
