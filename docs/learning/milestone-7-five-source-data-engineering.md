# Milestone 7 — Five-source coverage: Data Engineering lessons and assignments

Status: active; implementation and live validation still in progress

Issue: #15

Primary career lens: **Data Engineering**

## 1. What changed

The stakeholder-defined funding source set contains five source families:

1. STM
2. Haeavustuksia.fi
3. EURA 2021
4. Sitra
5. Suomen Akatemia

The original persisted system implemented STM, Sitra and Suomen Akatemia. Milestone 7 adds Haeavustuksia and EURA, whose business rules are materially different because relevance is not "all calls".

Haeavustuksia requires applicant-eligibility evidence from `Myöntöperusteet` / `Kenelle/mille avustusta voidaan myöntää`.

EURA requires two-stage evaluation:

`region scope -> applicant eligibility`

Only `Valtakunnallinen` and `Etelä-Suomi` notices proceed to wellbeing-area eligibility evaluation.

## 2. End-to-end data flow

### Original all-relevant sources

```text
public listing
  -> discover call entities
  -> normalize FundingCallCandidate
  -> relevance = RELEVANT
  -> persist current entity + immutable version
  -> serve current snapshot
```

### Haeavustuksia

```text
Haeavustuksia listing
  -> discover canonical /fi/haku/<id> URLs
  -> bounded concurrent detail fetch
  -> extract title/window
  -> extract Myöntöperusteet applicant section
  -> match stakeholder eligibility vocabulary
  -> RELEVANT / NOT_RELEVANT / NEEDS_REVIEW
  -> persist decision + evidence
  -> operator read model hides proven NOT_RELEVANT
```

### EURA

```text
EURA listing
  -> discover /hakuilmoitukset/hakuilmoitus/<uuid>
  -> bounded concurrent detail fetch
  -> extract Haun kohdealue
  -> region filter
       out of scope -> NOT_RELEVANT
       target region -> inspect description/additional info
  -> applicant evidence
  -> RELEVANT / NEEDS_REVIEW
  -> persist decision + evidence
  -> operator read model hides proven NOT_RELEVANT
```

## 3. Data grain

Always ask: **what does one row represent?**

### `funding_calls`

Grain: one row per logical source-specific funding opportunity.

A row is not one scan observation. Repeated observations of the same logical call update the same current entity.

### `funding_call_versions`

Grain: one row per immutable material content version of one funding opportunity.

### `source_states`

Grain: one row per configured funding source.

### `source_scan_runs`

Grain: one row per source ingestion attempt.

These grains deliberately separate business entities from pipeline metadata.

## 4. Identity model

The table uses a surrogate database primary key (`funding_calls.id`) but logical source identity is protected by:

```text
(source_code, external_key)
```

For the new sources:

- Haeavustuksia external identity should derive from the stable `/fi/haku/<id>` call identifier;
- EURA external identity should derive from the notice UUID/stable notice identifier.

The title is display/content data, not the preferred business key when a stronger source identifier exists.

### Why keep both surrogate and business identity?

The surrogate integer PK is efficient for internal foreign keys and database relationships. The source-specific business identity is required for idempotent ingestion and deduplication across repeated scans.

---

# Assignment 1 — Identify the grain

## Task

For each table below, state the grain and explain why combining them into one giant table would be poor modelling:

- `funding_calls`
- `funding_call_versions`
- `source_states`
- `source_scan_runs`

## Worked solution

`funding_calls`: one row per logical funding opportunity.

`funding_call_versions`: one row per immutable material version of an opportunity. Relationship: one `funding_call` to many versions.

`source_states`: one row per source, containing source-level current-snapshot watermarks/baseline facts.

`source_scan_runs`: one row per execution attempt, so a source has many scan runs.

Combining them would mix multiple grains. One funding call can have many versions and many scan runs happen independently of any one call. A single denormalized table would duplicate call fields, make updates error-prone and confuse entity state with pipeline execution metadata.

### Interview question

**What does grain mean in data modelling?**

> Grain defines what one row represents. I establish grain before keys and measures because mixing grains creates duplication and ambiguous semantics.

---

# Assignment 2 — Business key versus surrogate key

## Task

Why should EURA not use its funding-call title as the external key when the URL contains a UUID?

## Worked solution

Titles can be edited, translated or reused. A UUID is designed to identify the source notice independently of mutable display text.

Use:

```text
source_code = EURA
external identity = notice UUID
```

and enforce logical uniqueness through:

```sql
UNIQUE (source_code, external_key)
```

The database's `id` remains a surrogate key for internal relationships.

### Interview answer

> I distinguish internal surrogate identity from source/business identity. The surrogate PK supports efficient relationships, while `(source_code, external_key)` guarantees idempotent source ingestion.

---

# Assignment 3 — Design Haeavustuksia eligibility as data, not UI logic

## Task

A Haeavustuksia call says:

```text
Kenelle/mille avustusta voidaan myöntää:
Avustusta voidaan myöntää hyvinvointialueelle tai julkisoikeudelliselle yhteisölle.
```

Where should eligibility be decided?

A. Browser JavaScript
B. Ingestion/domain transformation
C. CSS
D. Email template

Explain.

## Worked solution

**B. Ingestion/domain transformation.**

Eligibility is a domain-derived data fact. It needs to be reproducible, persisted, versioned and available to every consumer, not recalculated independently by each UI/email/report.

The normalized candidate stores:

```text
relevance_status = RELEVANT
relevance_reason = matched applicant rule
Evidence(section, text, source_url)
```

The dashboard only presents that stored result.

### DE connection

This is transformation + lineage: raw source text becomes a normalized derived attribute with retained evidence.

---

# Assignment 4 — Why `NEEDS_REVIEW` exists

## Task

A Haeavustuksia eligibility section is present but contains none of the currently known stakeholder phrases. Should the pipeline classify it `NOT_RELEVANT`?

## Worked solution

Not automatically.

Absence of a known positive phrase is not proof of ineligibility because the vocabulary may be incomplete. Automatically converting unknown language to `NOT_RELEVANT` creates a false-negative risk, which directly violates the business goal of not missing funding.

Use:

```text
NEEDS_REVIEW
```

unless the source gives defensible exclusion evidence.

### Data quality dimension

This is primarily **accuracy** and **completeness/recall** of the relevant-opportunity dataset.

### Interview question

**How did you reduce false negatives in rule-based eligibility classification?**

> I separated unknown from negative. Explicit evidence can classify relevant or excluded cases, but ambiguous cases become NEEDS_REVIEW rather than being silently discarded.

---

# Assignment 5 — Two-stage EURA filtering

## Task

Why filter EURA by region before applicant-text eligibility?

## Worked solution

Region is a cheap, deterministic, high-confidence rule. Applicant eligibility requires more variable text interpretation.

Pipeline:

```text
all EURA notices
  -> Haun kohdealue filter
       -> not Valtakunnallinen/Etelä-Suomi => NOT_RELEVANT
       -> target region => applicant evidence evaluation
```

Benefits:

- fewer expensive detail/classification operations if discovery later supports staged fetching;
- simpler reasoning;
- clearer lineage (region reason separate from applicant reason);
- avoids asking a semantic classifier questions whose answer cannot change the regional exclusion.

This is predicate pushdown as a pipeline-design idea: apply cheap selective deterministic filters early.

---

# Assignment 6 — Persistence truth versus serving truth

## Task

Why persist `NOT_RELEVANT` calls at all if employees should not see them in the opportunity list?

## Worked solution

Persistence has broader audit/lineage responsibilities than the employee-facing read model.

Persisting excluded calls allows the system to answer:

- Was the source call observed?
- Why was it excluded?
- What evidence supported that exclusion?
- Did the source later change eligibility?
- Did our rules change?

The serving model applies:

```text
current snapshot
AND relevance_status != NOT_RELEVANT
```

This is intentional separation between the operational storage model and a consumer-specific read model.

---

# Assignment 7 — SQL: current operator-visible opportunities

## Task

Write SQL that returns only calls belonging to each source's latest successful snapshot and excludes proven `NOT_RELEVANT` calls.

## Worked solution

```sql
SELECT fc.*
FROM funding_calls AS fc
JOIN source_states AS ss
  ON ss.source_code = fc.source_code
WHERE fc.last_seen_at = ss.last_successful_scan_at
  AND fc.relevance_status <> 'NOT_RELEVANT'
ORDER BY fc.application_deadline_at ASC NULLS LAST,
         fc.id ASC;
```

### What does each predicate mean?

`fc.last_seen_at = ss.last_successful_scan_at`

ensures current snapshot membership.

`relevance_status <> 'NOT_RELEVANT'`

implements the operator-serving projection while retaining excluded records physically.

### Interview follow-up

**Why add `fc.id` to ORDER BY?**

Deadlines are not unique. The ID is a deterministic tie-breaker, making offset pagination stable for a fixed snapshot.

---

# Assignment 8 — SQL: classification distribution by source

## Task

Write a query showing current counts by source and relevance status, including excluded records.

## Worked solution

```sql
SELECT
    fc.source_code,
    fc.relevance_status,
    COUNT(*) AS calls
FROM funding_calls AS fc
JOIN source_states AS ss
  ON ss.source_code = fc.source_code
WHERE fc.last_seen_at = ss.last_successful_scan_at
GROUP BY fc.source_code, fc.relevance_status
ORDER BY fc.source_code, fc.relevance_status;
```

This is useful for pipeline observability. A sudden jump in `NEEDS_REVIEW` may indicate source-language drift or insufficient rules even when the scan technically succeeded.

---

# Assignment 9 — Data quality dimensions

## Task

Give one failure example for each dimension in the new sources:

- completeness
- accuracy
- validity
- uniqueness
- consistency
- freshness

## Worked solution

**Completeness:** EURA region exists on the source page but parser stores no region evidence.

**Accuracy:** Haeavustuksia eligibility text says "hyvinvointialue" but classification becomes NOT_RELEVANT.

**Validity:** malformed/unknown application date is silently converted to an invented timestamp.

**Uniqueness:** multiple section links for one Haeavustuksia call create multiple logical records.

**Consistency:** the same logical call has inconsistent external identity across scans.

**Freshness:** the source has not completed a successful scan according to its expected cadence, but users still assume the dataset is current. (A real stale threshold requires a defined cadence/SLA; do not invent one.)

---

# Assignment 10 — Detail-fetch concurrency

## Task

Why use bounded concurrency rather than fetching hundreds of detail pages simultaneously with `asyncio.gather` and no semaphore?

## Worked solution

Unbounded concurrency can overload the public source, exhaust local sockets/memory, trigger rate limiting and create unpredictable failures.

The scanner uses a semaphore conceptually:

```python
semaphore = asyncio.Semaphore(6)

async def fetch_detail(url: str):
    async with semaphore:
        return await client.get(url)
```

All tasks can still be scheduled, but only a bounded number perform network work concurrently.

### DE connection

Parallelism is an ingestion throughput control, not "more is always faster". Production data pipelines need backpressure/respect for source capacity.

---

# Assignment 11 — Partial source failure and atomicity

## Task

Suppose a source listing contains 80 calls. 79 detail fetches succeed and one returns a structural parsing error. Should the source snapshot be persisted as 79 current calls?

## Worked solution

Not by default.

A partial successful snapshot could incorrectly retire the missing call(s) because current membership is authoritative at source-scan level. The safer behavior is to fail the scan and preserve the previous successful snapshot unless the source supports explicit per-record partial-snapshot semantics.

This is why `asyncio.gather` propagating a detail failure can be desirable here: it prevents a partial source snapshot from masquerading as complete truth.

### Interview answer

> Because our current-state watermark treats a successful scan as authoritative membership, I prefer source-scan atomicity. If one required detail cannot be safely interpreted, the scan fails and the last successful snapshot remains served.

---

# Assignment 12 — Replay/idempotency

## Task

The same Haeavustuksia listing is processed twice with identical content. What should happen?

## Worked solution

The stable call identity maps each source record to the same logical entity.

Expected second scan:

```text
no duplicate funding_calls rows
no new immutable content versions
last_seen_at advances to the latest successful observation
result classified as UNCHANGED
no duplicate notification
```

The database uniqueness constraint protects identity even if application code has a bug/race.

---

# Assignment 13 — Content change versus classification change

## Task

A call's eligibility text changes from ambiguous to explicit `hyvinvointialue`. Is that material?

## Worked solution

Yes. Eligibility/relevance evidence is material domain content because it changes whether the opportunity should be surfaced/notified.

The normalized candidate's relevance status/reason/evidence contributes to material content hashing/snapshot versioning (verify exact hash contract in the persistence/change-detection implementation). The new observation should become a new version if the canonical material snapshot changed.

This creates an auditable transition:

```text
version N: NEEDS_REVIEW
version N+1: RELEVANT
```

The notification policy must then decide whether becoming newly relevant is notification-eligible even if the source call itself was previously known. That rule should be explicit rather than assumed.

---

# Assignment 14 — Notification outbox modelling (next slice)

## Task

Design the grain for a future notification outbox so a repeated scan cannot send the same "new funding opportunity" email twice.

## Worked solution direction

A candidate model could use one row per logical notification intent, for example:

```text
notification_outbox
-------------------
id (surrogate PK)
dedupe_key UNIQUE
event_type
funding_call_id
funding_call_version
source_scan_run_id
recipient_scope / destination reference
status
attempt_count
created_at
next_attempt_at
sent_at
last_error
```

A dedupe key might derive from the business event, for example:

```text
funding.opportunity.discovered.v1|<funding_call_id>|<notification-scope>
```

Exact grain depends on whether one outbox row represents one event or one event-recipient delivery. Define that before table creation.

### Key DE concept

The outbox separates durable event intent from unreliable external delivery. Database commit and email delivery cannot usually be one ACID transaction.

---

# Assignment 15 — Data modelling challenge

## Task

Should region and applicant-eligibility evidence remain only inside the generic JSON `evidence` column forever?

Discuss when to normalize them into dedicated columns/tables.

## Worked solution

JSON evidence is appropriate while source-specific evidence is heterogeneous and mainly needed for traceability.

Promote fields into structured columns/tables when they become stable cross-source business dimensions used for querying, constraints, reporting or workflows.

Examples:

- if operators frequently filter by region, a normalized region attribute may be justified;
- if manual eligibility review becomes a first-class workflow with reviewer, decision, timestamp and reason, model that workflow explicitly rather than burying it in JSON;
- raw source snippets/provenance can remain JSON-like evidence even when selected normalized dimensions are promoted.

This is not "JSON bad, normalization good". The decision follows access patterns, semantic stability and integrity requirements.

---

## 5. Interview drill: explain this milestone in 60 seconds

> VakeVahti originally ingested three sources where every discovered opportunity was relevant. I expanded the design to Haeavustuksia and EURA, which required evidence-backed eligibility modelling. Haeavustuksia uses a stable source call ID and extracts the applicant section from Myöntöperusteet. EURA uses a region-first filter for Valtakunnallinen and Etelä-Suomi, followed by applicant evidence from variable text sections. I introduced a three-state relevance model in practice: relevant, proven not relevant and needs review to avoid false negatives. All states are persisted for lineage, while the operator read model filters proven non-relevant calls. The pipeline preserves source-snapshot atomicity, bounded concurrent detail retrieval, stable identity, idempotency and evidence for every derived decision.

## 6. Portfolio evidence from this milestone

Safe evidence to retain:

- five-source architecture diagram;
- source-specific rule matrix;
- sanitized parser fixtures;
- SQL current/read-model examples;
- tests proving ambiguous cases are not discarded;
- tests proving NOT_RELEVANT remains stored but hidden from operator reads;
- CI results;
- live validation counts by relevance status;
- source-health screenshot after five-source ingestion;
- ADR/requirements showing why deterministic rules precede AI enrichment.

Do not claim Haeavustuksia/EURA production completeness until live scans against current source structures pass and are documented.
