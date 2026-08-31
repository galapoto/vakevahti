# Reusable GitHub project template — Data Engineering first

Use this template at the start of future GitHub projects when Data Engineering is the user's primary career/learning goal. Copy/adapt it into the new repository's `AGENTS.md`, `CONTRIBUTING.md`, or another authoritative project-instructions file.

## Project teaching priority

Treat this project primarily as a **Data Engineering learning and portfolio project**, even when it also contains backend, frontend, security, cloud, AI/ML or DevOps work.

Do not ignore other disciplines. Teach them when relevant, but connect them back to the data product and pipeline whenever that connection is real.

For DE-relevant slices, most of the learning/interview/assignment material should focus on Data Engineering, SQL, data modelling, data quality, pipeline reliability, lineage, orchestration and data serving.

## Mandatory learning cadence

For every significant implementation slice:

`implement -> test -> document -> explain -> technical assignments -> worked solutions -> interview/code questions -> continue`

Do not move on after simply generating code.

## Required Data Engineering questions

For each meaningful change, answer the applicable questions:

### Data flow
- What is the end-to-end data path?
- Which stage changed: extract, transform, validate, persist, serve, monitor?
- What are the source and target systems?

### Grain and model
- What does one row/document/event represent?
- What are the entities?
- What is the grain of each table?
- What are the primary, foreign, natural/business and external keys?
- What are the relationships/cardinalities?
- What does null mean for each nullable field?
- What constraints should the database enforce?
- What is normalized versus deliberately denormalized?
- How is history/current state represented?

### SQL and storage
- What SQL queries support this feature?
- What joins/aggregates/window functions are relevant?
- Are transactions required?
- What concurrency or locking problem can occur?
- What indexes are justified by the query pattern?
- How would you investigate the query plan if performance degrades?

### Quality and correctness
- How do we protect completeness, accuracy, validity, uniqueness, consistency and freshness?
- How are duplicates prevented?
- Is processing idempotent?
- What happens on replay/reprocessing?

### Lineage and governance
- Where did each derived value come from?
- Can the result be reproduced from stored evidence?
- What transformations occurred?
- What data is sensitive and who may access it?
- What audit information is required?

### Pipeline reliability
- Batch or streaming, and why?
- What triggers/schedules the pipeline?
- What happens on timeout/failure?
- Which failures are retryable?
- How are partial failures isolated?
- How are backfills performed?
- How are late/missing records handled?
- How do we know the pipeline stopped working?

### Schema evolution
- How will the schema change safely after real data exists?
- What migration/backfill is required?
- Is backward compatibility needed?

### Serving
- Is the consumer reading tables directly or through a contract/API/view?
- Is the physical database schema leaking into the external contract?
- How is pagination/order deterministic?
- Is this an operational read model or an analytical model?

## Technical assignments

For significant DE-relevant slices, produce at least **2-5 hands-on assignments** with complete worked answers. Larger milestones should include at least one realistic take-home/live-coding exercise.

Assignments should rotate through:

- SQL writing/debugging;
- relational modelling/ER design;
- schema normalization/denormalization;
- data-quality rules;
- idempotency/deduplication;
- change data/history modelling;
- transaction/concurrency scenarios;
- migration/backfill design;
- pipeline failure/retry debugging;
- orchestration design;
- Python data transformations;
- API/data-contract design;
- observability queries/metrics;
- performance/index/query-plan reasoning.

Do not only provide questions: include fully worked solutions, why they work, alternatives and common wrong-answer traps.

## Interview preparation priority

Prefer interview material in this order when applicable:

1. Data Engineering pipeline/system design
2. SQL
3. Data modelling
4. PostgreSQL/database internals and transactions
5. Data quality and lineage
6. Orchestration, retries, backfills and idempotency
7. Observability and production debugging
8. Data-serving contracts/APIs
9. Backend/software engineering supporting data systems
10. Security/privacy/governance
11. DevOps/cloud/platform
12. Frontend as a data consumer
13. AI/ML only where genuinely used

Include conceptual questions, SQL/code questions, debugging questions and scenario/system-design questions.

## ORM rule

Do not let the learner hide behind an ORM.

Whenever ORM code is important, also teach the underlying relational model and equivalent SQL where useful: keys, joins, constraints, transactions, indexes and query plans.

## UI rule

Do not invent fake DE relevance for purely visual changes. Instead state the true boundary. Examples:

- theme preference belongs in browser state, not the operational database;
- dashboard filtering is a data-serving/consumer concern;
- authentication affects governance/audit of data access;
- API changes affect downstream data contracts.

## Evidence rule

Continuously preserve safe evidence for DE portfolio/interview use:

- data-flow diagrams;
- ER/data-model diagrams;
- SQL examples;
- migrations;
- data-quality tests;
- idempotency/replay proofs;
- lineage examples;
- pipeline metrics;
- orchestration diagrams;
- CI database-integration results;
- recovery/backfill exercises;
- architecture decision records.

## Definition of success

The project is not complete merely because the software works. The learner should be able to explain without AI:

- the business problem;
- end-to-end data flow;
- data model and grain;
- keys and constraints;
- ingestion/transformation/validation strategy;
- history/current-state semantics;
- SQL/query patterns;
- idempotency/deduplication;
- data quality;
- lineage/provenance;
- transactions/concurrency;
- orchestration/retries/backfills;
- observability;
- schema evolution;
- serving contracts;
- important trade-offs and failures encountered.

Use this as a starting template and adapt it to the actual project rather than forcing irrelevant concepts.