# Data Engineering First mentoring contract

Status: **Authoritative learning rule for VakeVahti**

Applies to: every AI agent, coding assistant, developer, reviewer, and future maintainer working in this repository.

## 1. Primary career/teaching lens

VakeVahti is taught primarily as a **Data Engineering project**.

Backend, frontend, security, DevOps, system design and AI/ML topics still matter and must be taught when the project touches them, but the default question for every significant feature is:

> What is the Data Engineering meaning of this change, and what does it teach about data systems, data modelling, storage, quality, lineage, orchestration, reliability or serving?

Do not force fake Data Engineering relevance onto a purely visual change. If the direct DE relevance is small, state that clearly and explain the nearest real boundary, such as the API/data-serving contract consumed by the UI.

For data-heavy slices, most of the teaching/interview/assignment material should be Data Engineering focused. A useful target is **at least 60%** of the learning material for a DE-relevant slice covering data pipelines, SQL, modelling, data quality, storage, orchestration, reliability or data serving.

## 2. Required Data Engineering analysis for every significant slice

Before or immediately after implementing a meaningful change, document the following where applicable.

### 2.1 Data flow

Show the before/after path of the data:

`source -> ingestion -> extraction -> normalization -> validation -> persistence -> change detection -> enrichment -> serving -> consumer`

Identify which arrow changed and why.

### 2.2 Source and target grain

State the grain explicitly.

Examples:

- one row per funding call;
- one row per funding-call version;
- one row per source scan run;
- one row per source state;
- one API item per current funding opportunity.

The developer must learn to ask: **What does one row represent?**

### 2.3 Data model

For affected entities, teach:

- entity purpose;
- primary key;
- business/natural/external key;
- foreign keys;
- relationships and cardinality;
- nullability;
- uniqueness constraints;
- check constraints where useful;
- normalization versus deliberate denormalization;
- mutable versus immutable fields;
- current-state versus historical-state representation;
- lifecycle/state-machine semantics;
- whether the design resembles snapshotting, event history, SCD concepts or another temporal model.

Do not use dimensional-modelling terminology mechanically. Teach facts/dimensions, star schemas, SCDs and analytical modelling when they genuinely apply.

### 2.4 SQL

Whenever the feature touches persistence or querying, include practical SQL teaching.

Cover as relevant:

- SELECT/filter/order;
- JOINs and cardinality;
- GROUP BY/aggregates;
- window functions;
- CTEs;
- subqueries;
- INSERT/UPDATE/UPSERT;
- transaction boundaries;
- locking/concurrency;
- constraints;
- indexes;
- query plans/performance;
- pagination;
- migration/backfill SQL.

At least one SQL exercise should be produced for database-heavy slices, with a fully worked answer.

### 2.5 Data quality

Evaluate relevant dimensions:

- completeness;
- accuracy;
- validity;
- uniqueness;
- consistency;
- freshness/timeliness.

Explain how the system detects or prevents each relevant failure. A successful HTTP request is not proof of data quality.

### 2.6 Identity, deduplication and idempotency

Teach:

- stable external identity;
- natural/business keys versus surrogate keys;
- uniqueness constraints;
- canonicalization;
- content hashes;
- replay safety;
- duplicate observations versus duplicate entities;
- notification dedupe where applicable.

The developer must be able to explain what happens if the same input is processed twice.

### 2.7 Temporal/history modelling

Teach the difference between:

- current entity state;
- immutable content versions;
- source snapshot membership;
- audit history;
- scan metadata.

For VakeVahti specifically, preserve and teach the invariant that current operational membership can be a **projection over retained history**, rather than destructive deletion.

### 2.8 Lineage and provenance

For transformed or derived values, answer:

- where did the value come from?;
- which source URL/page/section supported it?;
- when was it observed?;
- which transformation produced it?;
- can the decision be reproduced?;
- was it deterministic, AI-assisted or manual?;
- what evidence is retained?

### 2.9 Orchestration and pipeline reliability

Teach as relevant:

- schedules/triggers;
- batch versus streaming;
- retries;
- retryability classification;
- timeout behavior;
- failure isolation;
- backfills;
- baselines;
- reprocessing/replay;
- late or missing data;
- stuck jobs;
- source-specific cadence;
- exactly-once versus at-least-once reasoning where applicable.

### 2.10 Transactions and concurrency

When persistence is involved, explain:

- transaction boundaries;
- atomicity;
- isolation expectations;
- race conditions;
- locks/advisory locks;
- concurrent first-write problems;
- what happens on rollback.

### 2.11 Schema evolution

For model changes, teach:

- Alembic migration design;
- backward compatibility;
- nullability rollout;
- defaults;
- backfills;
- data repair versus schema migration;
- why existing production data must not simply be discarded.

### 2.12 Data serving

When APIs/dashboard/reporting are changed, explain:

- the serving model;
- API contract versus physical database schema;
- why internal implementation columns should or should not be exposed;
- pagination/order determinism;
- read models;
- caching when relevant;
- consumer coupling;
- analytical versus operational serving.

### 2.13 Observability

Teach how to know the pipeline is healthy using facts such as:

- scan/job IDs;
- source status;
- last success/failure;
- discovered/new/changed counts;
- duration;
- failure classes;
- freshness once a real cadence/SLA exists;
- data-quality counters;
- alert thresholds.

## 3. Required teaching package after meaningful implementation

Use this sequence:

`implement -> test -> document -> explain -> assignments -> worked solutions -> interview drills -> continue`

For a significant DE-relevant slice, produce:

1. what changed and why;
2. end-to-end data flow;
3. affected data model and grain;
4. key/constraint/cardinality explanation;
5. SQL/query implications;
6. data-quality implications;
7. lineage/provenance implications;
8. orchestration/reliability/failure behavior;
9. tests and what each proves;
10. **2-5+ hands-on technical assignments**, mostly Data Engineering when relevant;
11. complete worked solutions;
12. conceptual DE interview questions;
13. SQL/code-reading/debugging interview questions;
14. at least one realistic take-home/live-coding exercise for larger milestones;
15. a concise portfolio/interview story based only on real work.

Do not merely list questions. Provide consultant/senior-quality worked answers and explain common traps.

## 4. Interview preparation priority

Prioritize questions in this order when relevant:

1. Data Engineering / pipeline design;
2. SQL and relational data modelling;
3. PostgreSQL, transactions and performance;
4. data quality, lineage and governance;
5. orchestration, idempotency, retries and backfills;
6. data-serving/API contracts;
7. system design and observability;
8. backend/software engineering supporting the pipeline;
9. security/privacy as it affects data;
10. DevOps/platform/MLOps where relevant;
11. frontend only to the degree it consumes or presents the data product;
12. AI/ML only where the pipeline genuinely uses semantic/probabilistic processing.

## 5. Data modelling questions that must recur

Whenever the model changes, the student should be challenged with questions such as:

- What is the grain of this table?
- Why is this the primary key?
- What is the stable business/external key?
- What cardinality exists between these entities?
- Which fields may be null, and what does null mean?
- Which constraints belong in PostgreSQL rather than application code?
- Why normalize or denormalize this field?
- How do we represent history?
- What happens when a call disappears and later reappears?
- How would this model handle a backfill?
- What indexes are justified by actual query patterns?
- How would this schema evolve after production data exists?
- What would change for analytics/BI versus operational serving?

## 6. Current VakeVahti DE examples

Existing features should be taught through DE concepts, for example:

- STM/Sitra/Academy scanners -> heterogeneous-source ingestion and adapter contracts;
- parser validation -> schema/data-quality validation;
- `external_key` -> stable source identity;
- `content_hash` -> change detection;
- `funding_calls` -> current entity/state store;
- immutable versions -> historical/temporal modelling;
- `source_scan_runs` -> pipeline metadata/audit table;
- `source_states` -> source watermark/state table;
- source advisory lock -> concurrency control;
- successful empty scan -> authoritative empty snapshot;
- failed scan -> preserve last successful snapshot;
- `last_seen_at == last_successful_scan_at` -> current-snapshot membership projection;
- `/api/funding-calls` -> operational data-serving contract;
- `/api/sources/health` -> observability/read model;
- Windows preview mode -> consumer/provider contract separation, **not** replacement of PostgreSQL architecture;
- dashboard relevance reason -> serving persisted lineage/explainability to a human consumer.

## 7. UI/backend/security changes must still be connected to the data product

Examples:

A dark-mode change has little direct DE content. Say so. Its relevant architecture lesson is that presentation state belongs in the browser and should not pollute operational business tables.

An authentication change has strong data-governance relevance: identity affects who may read or modify which data, audit attribution, least privilege and access logging.

An API change has strong data-serving relevance: contracts determine how downstream consumers depend on data without direct table access.

A deployment change has DE relevance through reproducible infrastructure, database connectivity, migrations, job scheduling and observability.

## 8. Do not hide the modelling behind ORM code

When SQLAlchemy models or Pydantic schemas are introduced or changed, also teach the underlying relational concepts and, where useful, the equivalent SQL.

The developer should never finish the project knowing only how to call ORM methods without understanding:

- tables;
- rows;
- keys;
- joins;
- constraints;
- transactions;
- indexes;
- query plans;
- temporal/history semantics.

## 9. Graduation and portfolio evidence

Continuously preserve sanitized evidence of DE competence:

- architecture/data-flow diagrams;
- ER/data-model diagrams;
- migration history;
- representative SQL queries;
- data-quality tests;
- idempotency proofs;
- lineage/provenance examples;
- CI PostgreSQL integration evidence;
- scan metrics;
- source-health screenshots;
- backfill/recovery exercises;
- ADRs explaining major data choices.

## 10. Rule for future GitHub projects

A reusable template is stored in `docs/learning/GITHUB_PROJECT_DATA_ENGINEERING_TEMPLATE.md`.

For future GitHub projects where the user's main career/learning goal is Data Engineering, copy/adapt that template into the new repository's root `AGENTS.md` or equivalent project instructions **at the beginning of the project** so future agents inherit the same teaching priorities.

This repository-specific contract supplements `AGENTS.md` and `docs/LEARNING_AND_ENGINEERING_CHARTER.md`. When they overlap, interpret the teaching priority as **Data Engineering first**, while still respecting security, correctness, workplace value and confidentiality rules.