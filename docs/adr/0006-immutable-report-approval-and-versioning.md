# ADR 0006: Immutable funding-report approval decisions and successor versions

Date: 2026-09-15  
Status: Accepted for the standalone/staging Funding module

## Context

VakeVahti can compose and persist funding reports and place a draft into a coordinator approval queue. A public-sector workplace approval cannot be represented safely by changing one mutable status field. The system must be able to answer what exact content was reviewed, who asserted the decision, when it happened, why a report was returned or rejected, and whether later edits changed the approved material.

The future VakeTomatti platform provides the organization login boundary. Approval storage therefore must not depend on a browser-typed actor identifier. The follow-up identity slice now supplies actor context through the Funding authorization boundary; preview/development identities remain explicitly labelled non-production, while production accepts only the signed VakeTomatti gateway mode.

## Decision

Funding reports use an explicit state machine:

`DRAFT -> WAITING_APPROVAL -> APPROVED`

`WAITING_APPROVAL -> DRAFT` for `RETURN_FOR_EDIT`.

`WAITING_APPROVAL -> REJECTED` for `REJECT`.

A rejected report must be edited before it can be submitted again. An approved report is immutable.

Every coordinator decision appends a `funding_report_approval_events` row containing the decision, timestamp, actor assertion, optional comment, a canonical SHA-256 content hash, and the exact report composition snapshot reviewed at that moment. Returning or rejecting requires a comment.

Editing an approved report is prohibited. Continuing work creates one explicit successor report version with `version_number = previous + 1` and `supersedes_report_id = previous.id`. Repeating the revision command is idempotent: one approved report can have only one direct successor.

The approval queue is exposed through the Funding API rather than direct table access. This keeps VakeTomatti and future shells dependent on a published contract rather than Funding storage internals.

Approval decision bodies no longer accept actor identity. The service records the server-resolved actor source: `PREVIEW_FIXTURE`, `DEVELOPMENT_STATIC`, or `VAKETOMATTI_GATEWAY`. Production settings reject the development mode. The gateway identity is meaningful only when the approved upstream SSO/gateway, TLS/network restrictions and secret-management controls are deployed as documented in ADR 0007.

## Alternatives considered

### Overwrite the report status and editable fields

Rejected. It loses the exact approved composition and makes later edits indistinguishable from the material a coordinator actually reviewed.

### Store only a final `approved_by` and `approved_at` column

Rejected. It cannot represent return/reject cycles, comments, multiple review attempts, or immutable decision history.

### Duplicate the full report for every save before approval

Rejected for the current slice. Draft edits do not need immutable versions on every keystroke. Immutability starts at the approval boundary; approved content receives an explicit successor only when work continues.

### Wait for SSO before implementing approval

Rejected. The domain state machine, immutable snapshots, hashing, API contracts and database constraints are independent of the identity provider. Building those now reduces future SSO integration to supplying trusted actor context and permissions rather than redesigning approval storage.

## Consequences

- Approval history is append-only and explainable.
- A content hash can prove which composition a decision refers to without treating the hash as a digital signature.
- Approved versions remain inspectable after later revisions.
- Report lineage is explicit and queryable.
- Database constraints protect against accidental successor forks.
- Browser-supplied actor identity is not accepted. The remaining production task is connecting the signed gateway to the approved organization SSO/OIDC and role source.
- Existing email-delivery paths are not automatically approval-gated by this ADR. Transport authorization and the exact rule for which approved object may be sent must be completed before production enablement.
