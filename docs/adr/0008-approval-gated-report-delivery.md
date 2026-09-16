# ADR 0008: Approval-gated report delivery

Date: 2026-09-15  
Status: Accepted

## Context

VakeVahti already had durable email delivery with retries, but two paths could create a delivery before coordinator approval: the case-email endpoint and automatic post-scan report processing. A UI-only approval step is not enough because another API caller or worker can bypass it.

The business workflow requires the coordinator to approve the exact report/email composition before external delivery is queued.

## Decision

The delivery service enforces one invariant:

> A durable report email may be queued only from an `APPROVED` funding-report version.

`enqueue_report_email` rejects non-approved reports.

Case-email preparation now:

`case package -> report DRAFT -> WAITING_APPROVAL -> coordinator decision`

No delivery row exists before approval. When the decision becomes `APPROVED`, Funding snapshots/retains the approval event and creates the durable delivery from that same report version if recipients, subject and body are complete.

Automatic scan reports may be automatically submitted to the approval queue (`AUTOMATIC_REPORT_SUBMIT_FOR_APPROVAL=true`) but are never delivered directly from `DRAFT`.

Delivery state remains separate from report state:

`APPROVED report -> PENDING -> PROCESSING -> SENT / FAILED`

## Consequences

- Every outbound report delivery has a corresponding approved immutable report version.
- Frontend, API and worker callers cannot bypass approval by calling the delivery service directly.
- SMTP retry/failure does not change the approval event or approved report content.
- Case-email API acknowledgement now means “submitted for approval,” not “message queued for transport.”
- Production transport still needs approved SMTP/Graph configuration, sender policy, secret management and monitoring.

## Alternatives considered

### Hide/disable the Send button until approval

Rejected. UI state is not a business invariant and does not protect API/background callers.

### Queue delivery immediately but pause the worker until approval

Rejected. It creates a durable transport intent for unapproved content and makes queue inspection ambiguous. The safer grain is to create delivery only after approval.

### Combine approval and delivery into one status machine

Rejected. Approval is a business decision; delivery is an operational transport lifecycle. Keeping them separate makes audit and retry semantics clearer.
