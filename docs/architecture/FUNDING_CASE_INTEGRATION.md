# Funding case integration contract

## Purpose

A funding opportunity is the shared business object across VakeVahti and the wider
VakeTomatti application family. VakeVahti owns the authoritative funding-call identity
and assigns one stable `case_id` to every employee-visible opportunity. Other apps must
attach their outputs to that case instead of creating parallel copies of the funding call.

This lets a user open one case in the general dashboard and see the funding facts,
Prosessikuvaus, Raportointi, attachments, report drafts, approval state and email history
as one workflow.

## Stable case identity

`case_id` is deterministic from the authoritative source identity:

`source_code + external_key -> case_id`

The ID remains stable when the title, deadline, description or relevance explanation
changes. Existing relevant/reviewable funding calls are backfilled during migration, and
future successful source ingestions create cases automatically.

`NOT_RELEVANT` calls do not create new cases. If an existing case becomes not relevant,
its case state is changed away from `OPEN`; it is therefore excluded from the ordinary
open-case list while its history remains addressable.

## Cross-app artifact envelope

An app such as Prosessikuvaus or Raportointi registers an artifact against the funding
case using `POST /api/cases/{case_id}/artifacts`.

The artifact contract contains:

- `case_id`: VakeVahti funding case UUID.
- `source_app`: producer, for example `PROSESSIKUVAUS` or `RAPORTOINTI`.
- `artifact_type`: semantic type such as `PROCESS_DESCRIPTION`, `REPORTING`,
  `FUNDING_REPORT` or `ATTACHMENT`.
- `external_artifact_id`: stable identifier in the producing app.
- `version`: positive integer version.
- `status`: workflow state such as `DRAFT` or `APPROVED`.
- `title`, `summary`: employee-facing description.
- `content_url`: preferred secure internal deep link when the artifact is maintained by
  another app.
- `content_text`: optional bounded textual material that may be included in a report.
- `mime_type`, `checksum`, `metadata`: technical lineage and integration metadata.
- `approved_at`: optional approval timestamp.

Artifact content is immutable within one `(case, app, type, external id, version)` tuple.
The same content/version may be registered repeatedly and may be promoted from `DRAFT`
to `APPROVED`. Different content using an existing version is rejected; the producer must
publish a new version.

## Funding report approval and version lineage

Funding reports use a separate approval state machine from cross-app artifact status. A report
submitted for coordinator review becomes `WAITING_APPROVAL`; the coordinator may approve it,
return it for editing, or reject it. Every decision is retained as an append-only approval event
with the exact reviewed report snapshot and a canonical SHA-256 content hash.

An `APPROVED` funding report is immutable. Continued work creates a successor report version
with `supersedes_report_id` pointing to the approved version. Consumers should follow this
lineage instead of updating an approved row in place.

The current standalone actor field is client-asserted staging context. VakeTomatti must later
provide authenticated actor identity and authorization; callers must never be allowed to turn a
self-supplied identifier into trusted approval evidence.

## Case email package

`GET /api/cases/{case_id}/email-package` produces the default editable email subject and
body for one case. The package always contains the authoritative funding title, source,
deadline, source link and `Miksi VakeHyvälle` explanation.

By default, VakeVahti groups artifact versions by producer/type/external identifier and
chooses the newest `APPROVED` version. If no version has been approved, the newest version
is used so the user can still review a complete draft package.

`POST /api/cases/{case_id}/email` accepts recipients and optional subject/body/artifact
selection. It creates a case-linked funding report, snapshots the exact artifact IDs used,
and queues an immutable durable email delivery. The existing mail worker is responsible
for SMTP delivery and retries; the HTTP request does not depend on the mail provider being
available at that moment.

This supports both `send to myself` and `send to others`. In the workplace deployment the
general dashboard should pre-fill the signed-in user's email from the authenticated
identity rather than asking the user to type their own address repeatedly.

## Security boundary

Read-only case APIs are part of the persisted application. Artifact registration and
case-email queuing are disabled by default and require `ENABLE_CASE_WRITE_ROUTES=true`.
That setting is a staging integration gate, not the final production authentication
model.

Production integration must authenticate the calling VakeTomatti service/user through
the approved workplace identity boundary. Other apps must never write directly into
VakeVahti database tables.

Confidential documents should normally be represented by access-controlled internal
links. Automatic file attachment should only be enabled when the producing app exposes an
authorized file-fetch contract and the recipient/channel is allowed to receive the file.

## General dashboard contract

The VakeTomatti general dashboard should treat `case_id` as its primary navigation key.
For each case it can obtain:

- authoritative funding facts from `GET /api/cases/{case_id}`;
- every registered artifact and version from the same response;
- a ready-to-edit case email composition from `/email-package`;
- durable send acknowledgement from `POST /email`.

The intended employee workspace is one case page with sections for Yhteenveto,
Rahoitusraportti, Prosessikuvaus, Raportointi, Liitteet, Sähköposti and Tapahtumat.
The apps remain independently maintainable while the employee sees one continuous
workflow.
