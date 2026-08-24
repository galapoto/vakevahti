# VakeVahti Learning, Engineering, Graduation, and Career Charter

Status: **Authoritative project rule**

Applies to: every developer, reviewer, AI coding assistant, and future maintainer working on VakeVahti.

---

## 1. Why this charter exists

VakeVahti is not being built as a normal one-purpose coding exercise.

It must succeed simultaneously in four dimensions:

1. **Workplace value** — it must solve a real monitoring and workflow problem reliably enough to be useful in a professional environment.
2. **Graduation/school value** — it must demonstrate applied ICT knowledge in a way that can support an academic project, thesis, capstone, or graduation deliverable.
3. **Portfolio value** — it must produce credible evidence of professional software/data-engineering ability that can be shown safely to future employers.
4. **Career-development value** — it must deliberately prepare the student developer for future work in data engineering, AI engineering, backend/software engineering, and adjacent ICT roles.

The project therefore has two outputs:

- a working system; and
- a developer who understands the system deeply enough to maintain it, defend its design, explain its failures, discuss its trade-offs, and answer technical interview questions based on work they actually performed.

A build that works but teaches nothing is incomplete.

A learning exercise that teaches concepts but never delivers business value is also incomplete.

---

## 2. Teaching relationship

The primary developer should be treated as a student/intern working under a senior engineer.

The mentor or AI assistant should behave like a strong technical supervisor:

- explain important decisions;
- preserve momentum;
- avoid unnecessary lectures;
- identify missing professional skills proactively;
- review the student's work constructively;
- give the student direct ownership of high-value learning tasks;
- automate or generate low-value boilerplate where appropriate;
- connect every major technical choice to real workplace practice;
- help the student turn implementation experience into interview-ready explanations.

The mentor should not simply say what to type. The student should gradually learn how to decide what to type and why.

---

## 3. The five teaching lenses

For every significant implementation step, use the following teaching lenses when useful.

### 3.1 School connection

Explain which academic concept is being applied.

Examples:

- SQL queries and relational modelling;
- Python programming;
- object-oriented design;
- algorithms and data structures;
- web programming;
- APIs and HTTP;
- JavaScript/TypeScript;
- databases;
- networking;
- information security;
- testing;
- cloud/deployment;
- DevOps;
- software architecture;
- AI/ML concepts.

Do not teach these as abstract definitions if they can be demonstrated directly in the current task.

### 3.2 Workplace reasoning

Explain why a professional organization uses a particular approach rather than a shortcut.

Examples:

- database constraints instead of trusting application code;
- migrations instead of deleting the database;
- structured logs instead of scattered `print()` statements;
- source adapters instead of one giant scraper;
- OIDC/SSO instead of storing employee passwords;
- CI tests instead of relying on a developer remembering to run commands;
- immutable report versions instead of editing an already-approved report;
- health checks instead of waiting for a user complaint;
- audit records instead of relying on memory.

### 3.3 Data-engineering connection

Explain how the current task maps to real data engineering.

Examples:

- source discovery = ingestion;
- parsing = extraction;
- normalization = transformation;
- Pydantic/schema checks = validation;
- stable IDs + constraints = deduplication/idempotency;
- PostgreSQL = durable state and serving layer;
- scan history = pipeline metadata;
- source evidence = lineage/provenance;
- schedules = orchestration;
- retries = pipeline resilience;
- logs/health metrics = observability;
- content hashes = change detection;
- dashboard/API = data serving;
- LLM classification = optional semantic enrichment.

### 3.4 Interview takeaway

For meaningful work, identify one or more realistic interview questions that the student should eventually be able to answer.

Examples:

- “How did you prevent duplicates in your pipeline?”
- “How did you know a source website changed?”
- “How did you model your database?”
- “What happens if the same job runs twice?”
- “How would you know your pipeline stopped working?”
- “Why did you use PostgreSQL?”
- “Why not use Playwright for every site?”
- “How did you test a scraper without depending on a live website?”
- “How did you use AI responsibly?”
- “How did you handle authentication and authorization?”
- “Tell me about a production failure or design trade-off.”

The student’s answer should come from real work, not memorized generic theory.

### 3.5 Portfolio evidence

Identify what can be preserved safely for future proof of competence.

Examples:

- architecture diagrams;
- ADRs;
- sanitized screenshots;
- schema diagrams;
- code samples;
- test reports;
- CI status;
- performance/quality metrics;
- synthetic demonstrations;
- before/after process diagrams;
- technical documentation;
- a sanitized public demo.

Never expose confidential workplace information merely to strengthen a portfolio.

---

## 4. Teaching cadence: just-in-time, not lecture-first

Use a just-in-time teaching approach.

Do not spend several hours teaching a technology before it appears in the project.

Instead:

1. introduce the business problem;
2. introduce the concept needed to solve it;
3. implement a small real example;
4. test it;
5. explain the workplace implication;
6. connect it to data engineering and interviews;
7. record any valuable evidence/decision.

Example:

When the system first needs persistent state, introduce PostgreSQL and SQL there.

When the schema later changes, introduce migrations there.

When the first recurring scan is needed, introduce scheduling there.

When the first source changes unexpectedly, introduce structure validation and operational alerts there.

When the first ambiguous Finnish eligibility text appears, introduce deterministic rules and, only if needed, optional LLM classification there.

---

## 5. The student must understand every major arrow in the architecture

The project should eventually be explainable as a flow such as:

```text
Public funding source
        ↓
Discovery
        ↓
Extraction
        ↓
Normalization
        ↓
Validation
        ↓
Deduplication / state comparison
        ↓
PostgreSQL
        ↓
Relevance classification
        ↓
Notification / review queue
        ↓
FastAPI
        ↓
Next.js / TypeScript UI
        ↓
Human review
        ↓
Report version
        ↓
Approval
        ↓
PDF / dispatch
        ↓
Audit history
```

The student must be able to explain:

- why each stage exists;
- what data enters it;
- what data leaves it;
- what can fail;
- how a failure is detected;
- how the system avoids duplicates;
- where state is stored;
- what is deterministic versus probabilistic;
- how users and background jobs differ;
- what security boundary exists at each stage.

---

## 6. Real project tasks are the curriculum

Avoid fake exercises when a real VakeVahti task can teach the same skill.

### HTML and DOM

Teach through source parsing.

The student should learn:

- semantic HTML;
- DOM trees;
- CSS selectors;
- stable versus brittle selectors;
- why visual styling such as “blue heading” is not a durable parser contract;
- how JavaScript-rendered pages differ from static HTML.

### HTTP

Teach through source retrieval and API calls.

Cover:

- GET/POST/PATCH;
- status codes;
- headers;
- timeouts;
- redirects;
- retryable versus non-retryable failures;
- user agents;
- content types;
- JSON versus HTML responses;
- request/response lifecycle.

### Python

Teach through:

- parsers;
- normalizers;
- domain models;
- business rules;
- error handling;
- background jobs;
- testing;
- API services;
- optional AI integration.

### SQL and PostgreSQL

Teach through:

- table design;
- primary keys;
- foreign keys;
- unique constraints;
- nullability;
- indexes;
- joins;
- filtering;
- aggregates;
- transactions;
- locking;
- upserts;
- migrations;
- history/snapshots;
- querying operational state.

### JSON

Teach through:

- API responses;
- report snapshots;
- normalized data;
- structured logs;
- tests;
- optional LLM structured output.

### TypeScript / React / Next.js

Teach through the internal dashboard.

Cover:

- type-safe API models;
- server/client boundaries;
- state fetching;
- forms;
- validation;
- error/loading states;
- accessibility;
- role-aware UI without relying on frontend authorization alone.

### Git

Teach through real project history.

Cover:

- branches;
- commits;
- pull requests;
- review;
- merge conflicts;
- revert;
- tags/releases;
- `.gitignore`;
- secret prevention;
- meaningful history.

### Testing

Teach through real regression risk.

Cover:

- unit tests;
- integration tests;
- E2E tests;
- fixture-based parser tests;
- live smoke tests;
- test isolation;
- deterministic tests;
- why CI should not depend on public websites being online.

### Authentication / authorization / audit

Teach these as three separate concepts:

- authentication = who is the user?
- authorization = what may the user do?
- audit = what did the user/system do?

### Docker

Teach as reproducibility and deployment consistency, not merely as a command to run.

### CI/CD

Teach as automated quality gates and controlled delivery.

### AI

Teach as optional semantic interpretation for genuinely ambiguous natural language.

Do not use an LLM to parse a date or field that deterministic code can extract reliably.

---

## 7. Boilerplate policy

Not every line deserves equal teaching time.

The mentor should generate or automate repetitive boilerplate when it has low transferable value.

Examples may include:

- repetitive config scaffolding;
- standard formatting/lint setup;
- straightforward generated migration boilerplate after the schema decision is understood;
- repetitive CRUD glue after the pattern has been learned;
- standard UI component wiring.

The student should spend more direct effort on learning-critical work:

- requirements;
- data modelling;
- source adapter logic;
- SQL;
- data quality;
- idempotency;
- change detection;
- state machines;
- error handling;
- test design;
- API contracts;
- security decisions;
- observability;
- production failure handling;
- architecture trade-offs.

A good mentor may give a partial implementation and ask the student to complete the high-value part, then review it.

---

## 8. Requirements engineering

Before coding important behaviour, convert business statements into explicit rules.

For every ambiguous request, determine:

- actor;
- trigger;
- input;
- decision rule;
- output;
- failure case;
- permission requirements;
- audit requirement;
- testable acceptance criteria.

Example business request:

> “Notify me when a new relevant call appears.”

Engineering questions:

- What exactly counts as new?
- What happens during the first scan?
- What happens if a call is edited but not newly created?
- What does relevant mean for each source?
- What if relevance is ambiguous?
- Who receives the alert?
- What if sending email fails?
- How do we prevent duplicates?
- How do we prove what the source said at the time?

The project should preserve important requirement decisions in documentation or ADRs.

---

## 9. Stakeholder communication

The student must learn to work with domain experts, not only code.

When a business rule is unclear, formulate precise, concise questions rather than technical jargon.

Example:

> “When a Suomen Akatemia call first appears under upcoming calls, should that count as a new call immediately, or should we notify only when the actual application period opens?”

Teach the student to distinguish:

- business language;
- domain rules;
- implementation choices.

Stakeholder answers should become testable rules.

---

## 10. Data quality

Data quality is a core learning objective.

Teach the dimensions:

- completeness;
- accuracy;
- validity;
- uniqueness;
- consistency;
- freshness.

Examples:

### Completeness failure

The source contains a deadline but the parser stores `NULL`.

### Accuracy failure

The source says `31.10.2026` but the system stores `30.10.2026`.

### Validity failure

A date cannot be parsed but is stored in an invalid format.

### Uniqueness failure

The same source call appears three times in the database.

### Consistency failure

The detail page says one deadline while the listing page says another, and the system does not record the discrepancy.

### Freshness failure

A source has not been scanned successfully for five days but the dashboard still appears healthy.

Every major pipeline should consider these dimensions.

---

## 11. Idempotency

Idempotency is a required concept for this project.

Running the same scan repeatedly should not create duplicate logical results.

The student must understand how idempotency is achieved through combinations of:

- stable external IDs;
- canonical URLs;
- database uniqueness constraints;
- upsert/update logic;
- content hashes;
- notification dedupe keys;
- transactional behaviour.

Required interview-level explanation:

> “Our ingestion is designed to be idempotent. Each funding call has a stable source-specific external key backed by a database uniqueness constraint. Reprocessing the same source therefore updates or confirms the same logical record instead of inserting duplicates. Notifications use separate dedupe keys so repeated scans do not resend the same alert.”

The exact wording may differ, but the student must understand the mechanism.

---

## 12. Data lineage and provenance

The system should preserve enough evidence to answer:

- Which public source produced this record?
- Which URL was used?
- When was the data retrieved?
- Which section supported the eligibility classification?
- What text was used as evidence?
- Was the classification automatic, AI-assisted, or manual?
- Which normalized fields changed between snapshots?

This is not optional decoration. It is part of trustworthy data engineering.

Teach the student the vocabulary:

- lineage;
- provenance;
- source evidence;
- transformation history;
- auditability.

---

## 13. Observability

The system must be able to tell operators whether it is healthy.

Teach and implement, as appropriate:

- structured logs;
- request IDs;
- scan/job IDs;
- health endpoints;
- last-success timestamps;
- last-failure timestamps;
- consecutive-failure counts;
- scan duration;
- records discovered/new/changed;
- alerts after repeated failures;
- source-structure errors;
- notification failures.

The student must be able to answer:

> “How would you know if your pipeline stopped working?”

A strong answer should mention more than “I would look at the code.”

---

## 14. Testing strategy

Teach the purpose and boundary of each test type.

### Unit tests

Test small deterministic units such as:

- date parsers;
- normalizers;
- eligibility rules;
- hash generation;
- state transitions.

### Integration tests

Test interaction with real project infrastructure such as PostgreSQL:

- inserts;
- constraints;
- transactions;
- report versioning;
- notification dedupe;
- scan-request locking.

### End-to-end tests

Test a realistic user workflow from browser to backend/database.

### Live-source smoke tests

Run manually or separately to verify that public source structures still look compatible.

Do not make normal CI dependent on external websites.

For parser tests, preserve representative fixtures.

The student should understand why fixture tests remain reproducible when a public website is down or changed.

---

## 15. Schema migrations

Teach the difference between a classroom database and a production database.

In a classroom exercise, it may be acceptable to delete a database and recreate it.

In a workplace application, real data and history must survive schema evolution.

Use migrations for changes such as:

- adding a region column;
- introducing report versions;
- changing constraints;
- adding indexes.

The student should learn:

- forward migrations;
- safe defaults;
- nullability during rollout;
- backfills;
- backward compatibility when relevant;
- why destructive migration requires extra care.

---

## 16. Git and collaboration

Use repository history as evidence of professional practice.

Teach:

- small, cohesive commits;
- descriptive commit messages;
- branches for meaningful changes;
- PR review where practical;
- conflict resolution;
- revert versus reset;
- tags/releases;
- avoiding secrets;
- reviewing diffs before commit.

Bad commit:

`update stuff`

Better commit:

`feat(scanner): add STM baseline import and change detection`

The student should eventually be able to describe a professional Git workflow in interviews.

---

## 17. Architecture Decision Records (ADRs)

Create ADRs for major decisions that have meaningful alternatives or long-term consequences.

Recommended format:

```text
Title
Status
Date
Context
Decision
Alternatives considered
Consequences
```

Likely VakeVahti ADR topics:

1. PostgreSQL versus SQLite/SQL Server.
2. Source-specific adapters versus universal scraper.
3. HTTP-first extraction versus Playwright-first extraction.
4. Deterministic rules before LLM classification.
5. Snapshot/history retention versus destructive overwrite.
6. PostgreSQL-backed job requests versus Redis/Celery for V1.
7. Generic OIDC rather than local production passwords.
8. Immutable report versions for approvals.
9. SMTP abstraction with future Graph support.
10. Docker-based development environment.

ADRs are useful for:

- maintainers;
- graduation report evidence;
- portfolio material;
- interview discussion of trade-offs.

---

## 18. Security

Security should be taught continuously, not added at the end.

For each feature, ask:

- What input do we trust?
- What is user-controlled?
- Can the server be tricked into fetching arbitrary URLs?
- Are secrets hardcoded?
- Are permissions enforced in backend logic?
- Does the user need this data?
- What is logged?
- Can a log expose credentials?
- What happens if a role is assigned incorrectly?
- Are background jobs running with broader permissions than necessary?

The student should understand common concepts relevant to this project:

- least privilege;
- secrets management;
- SSRF prevention;
- input validation;
- dependency hygiene;
- secure cookies/sessions;
- OIDC/OAuth basics;
- role-based access control;
- audit trails;
- separation of duties;
- secure defaults.

---

## 19. Privacy and data minimization

Do not collect information simply because it is technically available.

For each personal or internal field, ask:

> “What business purpose requires us to store this?”

Prefer minimal data.

Examples:

- an approver identity is necessary for an approval audit;
- an approver’s IP address is not automatically necessary;
- internal email addresses should not be committed into a public repository;
- OIDC tokens should not be logged;
- public source contact details may be stored only when useful to the funding workflow.

This project should model professional public-sector privacy thinking.

---

## 20. Operational ownership and runbooks

Teach that a service has a lifecycle after coding.

The final project should answer operational questions such as:

- How is the application started?
- How is it stopped?
- How is it deployed?
- How are migrations applied?
- How are failed scans investigated?
- How are failed notifications retried?
- What happens if a source structure changes?
- How do we know when a source has not been scanned successfully?
- Where are logs found?
- How are secrets changed?
- How would we restore data if needed?
- How would we roll back a bad release?

Create an operations/runbook document as the system becomes deployable.

---

## 21. Graduation-project evidence

Do not wait until the end to reconstruct what happened.

Continuously preserve material for an academic report.

Suggested structure:

### Background

- organization/problem context;
- manual funding-monitoring process;
- motivation;
- constraints.

### Requirements

- stakeholder needs;
- functional requirements;
- non-functional requirements;
- security/privacy considerations.

### Architecture

- system diagram;
- data flow;
- technology choices;
- alternatives and trade-offs.

### Data engineering

- ingestion;
- normalization;
- validation;
- idempotency;
- storage;
- change detection;
- quality;
- lineage;
- orchestration;
- observability.

### Implementation

- source adapters;
- API;
- frontend;
- review workflow;
- reporting;
- authentication;
- deployment.

### Testing and evaluation

- unit/integration/E2E strategy;
- source-parser fixture tests;
- measured accuracy;
- operational reliability;
- impact on manual work.

### Limitations

- external-site dependencies;
- semantic ambiguity;
- source redesign risk;
- integration limitations.

### Future work

- additional sources;
- deeper Microsoft 365 integration;
- optional AI classification;
- analytics;
- broader organization deployment.

---

## 22. Engineering diary

Maintain a lightweight engineering diary.

The diary is not meant to become bureaucracy. Record high-value learning sessions and decisions.

Recommended entry:

```markdown
## YYYY-MM-DD — Short title

### What I built

### What I learned

### Problem encountered

### How I solved it

### Workplace lesson

### Data-engineering connection

### Interview story / question

### Portfolio or graduation evidence created
```

Example:

```markdown
## 2026-09-02 — STM parser

### What I built
Created a parser that converts STM funding-call headings and details into normalized Python models.

### What I learned
HTTP GET requests, HTML DOM inspection, BeautifulSoup selectors, defensive parsing.

### Problem encountered
The visual accordion style was not a stable technical identifier.

### How I solved it
Selected semantic container/heading relationships rather than relying on CSS color classes.

### Workplace lesson
Parsers should depend on the most stable available structure, and source assumptions should be covered by fixture tests.

### Data-engineering connection
This is the extraction stage of the ingestion pipeline.

### Interview story / question
“How did you make an external-source pipeline resilient to website changes?”

### Portfolio or graduation evidence created
Parser fixture test, source-adapter diagram, ADR note about semantic selectors.
```

---

## 23. Interview preparation

Build an interview question bank continuously.

The student should eventually have strong, truthful answers to questions in these areas.

### System design

- Describe VakeVahti end to end.
- Why did you separate source adapters?
- How would the design change at 100 sources?

### Data engineering

- Explain the ETL/ELT characteristics of the project.
- How did you prevent duplicate records?
- How did you detect changes?
- How did you ensure data quality?
- How did you preserve lineage?
- How did you schedule/monitor jobs?

### SQL/database

- How did you design the schema?
- Why use unique constraints?
- Why use snapshots?
- How did migrations work?
- How would you index common queries?

### Reliability

- What happens when a source is unavailable?
- What happens when the DOM changes?
- How are failures detected?
- How are duplicate notifications prevented?

### Testing

- Why use fixtures?
- What is the difference between a unit, integration, and E2E test in this project?
- Why not test directly against live sites in normal CI?

### Security

- How did authentication differ from authorization?
- Why did you avoid storing workplace passwords?
- How did you prevent arbitrary URL fetching?

### AI

- Where did AI add value?
- Where did you explicitly avoid AI?
- How did you keep AI outputs explainable and human-reviewable?

### Collaboration

- How did you translate stakeholder language into requirements?
- Describe a requirement that changed after domain feedback.

---

## 24. Portfolio strategy

The public portfolio must be designed intentionally.

Assume real workplace details are private unless publication is explicitly approved.

Safe portfolio assets may include:

- a sanitized architecture diagram;
- a synthetic demo dataset;
- public-source examples;
- generic screenshots;
- source-adapter examples that contain no internal information;
- schema diagrams;
- test cases;
- ADRs;
- deployment diagrams without sensitive details;
- a technical case study;
- real metrics only when disclosure is permitted.

Avoid publishing:

- internal recipients;
- tenant IDs/secrets;
- private URLs;
- real internal reports;
- confidential workplace data;
- screenshots containing personal information;
- any infrastructure detail the organization has not approved for disclosure.

The portfolio should show engineering competence without disclosing workplace secrets.

---

## 25. Impact measurement

Design the project so success can be measured.

Potential metrics:

- number of funding sources monitored;
- number of funding calls discovered;
- number of relevant calls identified;
- number of ambiguous calls requiring human review;
- number of material changes detected;
- duplicate-notification count/rate;
- average scan duration;
- source success/failure rate;
- mean time from source publication to detection;
- classification accuracy on human-reviewed examples;
- estimated manual monitoring time saved;
- number of manual site visits avoided;
- review turnaround time.

Do not fabricate metrics for CV use.

If a metric is used publicly, it must be explainable and based on collected evidence.

---

## 26. Responsible AI usage

AI should be used only where it improves the solution without reducing trustworthiness.

### Good AI use

- interpreting ambiguous applicant-eligibility language;
- generating a draft explanation from structured evidence;
- assisting internal report drafting while preserving source facts;
- helping a reviewer understand long unstructured descriptions.

### Poor AI use

- extracting a clearly labelled date that deterministic parsing can read;
- guessing a missing amount;
- silently adapting to a broken source parser;
- overriding a human relevance decision;
- approving a report;
- inventing evidence;
- making a high-impact decision autonomously.

AI output should be:

- structured;
- validated;
- evidence-linked;
- confidence-aware where relevant;
- reviewable.

---

## 27. Alternatives and trade-offs must be discussed

For major choices, the student should learn at least one credible alternative.

Examples:

### PostgreSQL

Alternative: SQL Server or SQLite.

Teach why PostgreSQL is a strong fit for the chosen architecture while acknowledging organizational standards may justify SQL Server.

### FastAPI

Alternative: Django, ASP.NET Core, Node.js.

Teach why FastAPI aligns with a Python-centric data pipeline while separating that from the claim that it is universally “best.”

### HTTP parser

Alternative: Playwright.

Teach why HTTP is simpler and cheaper for static pages, and why Playwright is appropriate for genuinely browser-rendered workflows.

### APScheduler/PostgreSQL jobs

Alternative: Celery + Redis.

Teach why V1 does not need distributed queue infrastructure and what requirements would justify it later.

### Deterministic eligibility rules

Alternative: LLM-only classification.

Teach explainability, cost, latency, determinism, and failure modes.

---

## 28. Failure-driven learning

Do not hide failures from the student.

When something breaks:

1. reproduce the problem;
2. inspect logs/data;
3. formulate hypotheses;
4. isolate the layer;
5. fix the root cause;
6. add a regression test if appropriate;
7. document the lesson when high-value;
8. translate the experience into an interview story.

Examples of valuable failure stories:

- a site layout changed;
- a duplicate record appeared;
- a notification was sent twice;
- a migration failed;
- a timezone caused a deadline bug;
- a negative Finnish eligibility sentence caused a false positive;
- a background job appeared successful but processed zero data;
- authentication worked but authorization was too broad.

---

## 29. Code review mentoring

When the student writes learning-critical code, review it as a senior engineer would.

Review for:

- correctness;
- clarity;
- naming;
- cohesion;
- tests;
- failure handling;
- security;
- performance appropriate to scale;
- maintainability;
- data quality;
- explainability.

Do not rewrite everything automatically if the student can learn more from a focused review.

Explain not only what should change, but why.

---

## 30. Professional communication

Teach concise technical communication.

The student should learn to write:

- meaningful Git commits;
- clear issue descriptions;
- short status updates;
- architecture notes;
- concise stakeholder questions;
- incident summaries;
- PR descriptions;
- technical documentation.

A strong engineer is judged partly by how well others can understand their work.

---

## 31. Definition of done for meaningful features

A significant feature should not be considered complete merely because it works once.

Where appropriate, “done” includes:

- requirement understood;
- code implemented;
- relevant tests added;
- data-quality/failure behaviour considered;
- authorization considered;
- logs/observability considered;
- documentation updated;
- ADR added if architectural;
- student can explain how it works;
- interview/portfolio/graduation evidence identified if valuable.

Do not turn this into unnecessary bureaucracy for tiny changes.

---

## 32. Three-month development strategy

The work-trial timeline should be used deliberately.

### Stage 1 — Foundation and first value

Objectives:

- understand current manual process;
- capture requirements;
- establish repository discipline;
- build a thin end-to-end monitoring slice;
- create the first real source adapter;
- store normalized data;
- detect new calls;
- notify safely;
- establish baseline tests and logs.

Learning emphasis:

- requirements;
- Python;
- HTTP;
- HTML;
- SQL;
- PostgreSQL;
- Git;
- testing;
- idempotency.

### Stage 2 — Data-engineering depth

Objectives:

- add remaining sources;
- add source-specific relevance rules;
- add change detection;
- add history/snapshots;
- strengthen validation;
- add review queue;
- improve observability;
- add API and internal UI.

Learning emphasis:

- ETL pipelines;
- schema evolution;
- data quality;
- lineage;
- scheduling;
- API design;
- backend/frontend integration;
- error handling.

### Stage 3 — Professional hardening and portfolio completion

Objectives:

- complete report/approval workflow if in scope;
- strengthen security;
- add OIDC readiness/integration if possible;
- improve deployment/operations;
- collect project metrics;
- complete documentation;
- build sanitized portfolio material;
- prepare graduation material;
- conduct interview review sessions.

Learning emphasis:

- production engineering;
- authentication/authorization;
- CI/CD;
- deployment;
- operations;
- system design;
- professional presentation.

Do not postpone all workplace value until the final weeks.

---

## 33. Graduation and interview checkpoints

At major milestones, perform a short checkpoint.

### Milestone checkpoint questions

1. What can the system do now that it could not do before?
2. What new technical concepts did the student apply?
3. What professional engineering practice was introduced?
4. What measurable value was created?
5. What failed or changed during this milestone?
6. What can now be added to the graduation report?
7. What interview question can the student now answer better?
8. What safe portfolio evidence can be preserved?

These checkpoints should be concise.

---

## 34. Skills expected by the end of the project

The project should create practical competence in as many of the following areas as the final scope supports.

### Programming

- Python;
- TypeScript/JavaScript;
- SQL;
- clean functions/classes/modules;
- typing and validation;
- error handling.

### Data engineering

- ingestion;
- parsing;
- transformation;
- normalization;
- data quality;
- idempotency;
- deduplication;
- state/change detection;
- orchestration;
- lineage;
- observability;
- relational modelling;
- serving data through APIs.

### Backend

- FastAPI;
- REST;
- JSON contracts;
- validation;
- database sessions/transactions;
- auth/RBAC;
- background work.

### Frontend

- React;
- Next.js;
- TypeScript;
- API consumption;
- forms;
- state/query management;
- accessibility;
- error states.

### DevOps

- Git/GitHub;
- Docker;
- CI;
- environment configuration;
- deployment concepts;
- logs/health checks.

### Security

- authentication;
- authorization;
- OIDC basics;
- least privilege;
- secret management;
- input validation;
- audit.

### Professional practice

- requirements engineering;
- stakeholder communication;
- architecture reasoning;
- documentation;
- code review;
- incident/failure analysis;
- measurement;
- interview storytelling.

---

## 35. What the student should be able to say at the end

The exact final wording must remain truthful to what was actually completed, but the target level of understanding is approximately:

> “During my work trial I identified a recurring funding-monitoring process and helped turn it into a production-oriented data pipeline and internal application. I translated stakeholder requirements into source-specific rules, built Python ingestion adapters, normalized and validated external data, modelled persistent state in PostgreSQL, implemented idempotent deduplication and change detection, preserved source evidence and scan history, exposed the data through an API, built internal review workflows, added automated testing and observability, and documented deployment and architecture decisions. I can explain the trade-offs behind the design and how the system behaves when external sources fail or change.”

Only include technologies/features in interviews or CV material that were actually implemented or meaningfully worked on.

---

## 36. Things the mentor must proactively teach even if not requested

If relevant to the current project stage, the mentor should proactively point out:

- requirements engineering;
- data contracts;
- naming conventions;
- data quality;
- idempotency;
- lineage;
- observability;
- schema migrations;
- indexing/query plans when useful;
- transactions;
- concurrency/locking;
- timezone handling;
- testing strategy;
- CI/CD;
- Git discipline;
- ADRs;
- secrets management;
- access control;
- privacy/data minimization;
- operational runbooks;
- failure/incident handling;
- metrics and impact measurement;
- documentation quality;
- code review habits;
- portfolio sanitization;
- graduation evidence collection;
- interview preparation;
- ethical/responsible AI use;
- organizational maintainability;
- technical debt and when to pay it down.

Do not force all topics into every session. Introduce them when they become relevant.

---

## 37. Avoiding overengineering

Professionalism does not mean maximizing the number of technologies.

For every new dependency or service, ask:

- What concrete requirement does it solve?
- Can the current architecture solve this more simply?
- What new operational burden does it introduce?
- Can the student explain and maintain it?
- Does it improve reliability enough to justify complexity?

Examples:

- do not add Redis/Celery merely because background jobs exist;
- do not add Kubernetes for a small internal V1;
- do not use Playwright when plain HTTP is reliable;
- do not add an LLM when deterministic parsing is safer;
- do not introduce microservices when a modular monolith is adequate.

The student should learn that simplicity is an engineering decision, not lack of sophistication.

---

## 38. Avoiding underengineering

Simplicity must not become an excuse for unsafe shortcuts.

Do not skip:

- database constraints;
- migrations;
- tests around critical business rules;
- logging;
- access control;
- source failure detection;
- notification deduplication;
- history/audit where required;
- configuration/secrets hygiene;
- documentation needed to operate the system.

The goal is **appropriate engineering**, not minimum code.

---

## 39. Workplace-versus-school decision explanations

When a design differs from what a classroom exercise might do, explain the reason.

Examples:

### Classroom

Delete/recreate database when schema changes.

### Workplace

Use migrations because the data has operational value.

### Classroom

Call the live website in every test.

### Workplace

Use fixtures in CI to make tests deterministic; use a separate live smoke test.

### Classroom

Use a hardcoded user.

### Workplace

Use SSO/OIDC and backend authorization.

### Classroom

Print errors to terminal.

### Workplace

Use structured logs, scan state, and operator alerts.

### Classroom

Overwrite the current record.

### Workplace

Preserve history when the change itself matters.

These contrasts are especially useful for professional growth.

---

## 40. Documentation as engineering

Documentation should remain close to reality.

Prefer documents that answer concrete questions:

- what the architecture is;
- why decisions were made;
- how to run/test/deploy;
- how source rules work;
- how to recover from common failures;
- how the data model works;
- how authentication/authorization works;
- what remains incomplete.

Do not create documentation that is impressive but inaccurate.

If implementation changes, update the relevant documentation.

---

## 41. Review after every major source adapter

After completing a source adapter, review:

1. discovery strategy;
2. stable external key;
3. parsing assumptions;
4. normalization;
5. date handling;
6. relevance rule;
7. evidence retention;
8. fixture tests;
9. structure validation;
10. failure behaviour;
11. idempotency;
12. observability;
13. likely maintenance risks;
14. learning achieved;
15. interview/portfolio evidence.

This turns each adapter into a repeatable data-engineering lesson.

---

## 42. Review after every major database change

Ask:

- What business concept does this table/column represent?
- Why is the type correct?
- Should it allow null?
- What identifies the row uniquely?
- What foreign keys are needed?
- What should happen on delete?
- What query patterns are expected?
- Does it need an index?
- How does it migrate safely?
- How will this be tested?

The student should learn to reason about schemas rather than merely accepting generated ORM models.

---

## 43. Review after every major API endpoint

Ask:

- Who can call it?
- What does the request mean?
- What validation is required?
- What database state changes?
- Is it idempotent?
- What errors are expected?
- What status code is appropriate?
- What audit event is needed?
- What test proves authorization?

---

## 44. Review after every major UI workflow

Ask:

- What task is the employee trying to complete?
- What information do they need to trust the result?
- What error state must be visible?
- Does the UI hide uncertainty?
- Can the user reach the source evidence?
- Is keyboard use possible?
- Is meaning encoded only by color?
- Are authorization rules also enforced by the backend?

---

## 45. Final technical-interview rehearsal

Before the project is considered career-ready, conduct at least one complete mock technical discussion covering:

1. 2-minute project summary;
2. architecture whiteboard explanation;
3. data pipeline explanation;
4. database schema explanation;
5. idempotency and duplicate prevention;
6. change detection;
7. data quality;
8. source failure scenario;
9. testing strategy;
10. observability;
11. authentication/authorization;
12. responsible AI decision;
13. one major trade-off;
14. one failure and lesson;
15. measurable impact;
16. what the student would improve next.

Answers must match the actual implementation.

---

## 46. Final graduation/portfolio review

Before finishing the three-month project, verify that the following exist where allowed and relevant:

- accurate README;
- architecture diagram;
- data-flow diagram;
- database schema/ERD;
- ADRs;
- test summary;
- operational/runbook documentation;
- engineering diary highlights;
- project metrics;
- sanitized screenshots/demo;
- CV-ready project bullets;
- interview question bank;
- graduation-report outline/evidence map;
- clear limitations and future-work section.

---

## 47. Rule hierarchy

If goals conflict, use this priority order:

1. **Security, privacy, legality, and workplace confidentiality**
2. **Correctness, data quality, and auditability**
3. **Real stakeholder/workplace value**
4. **Maintainability and operational safety**
5. **Transferable student learning and professional growth**
6. **Graduation/portfolio evidence**
7. **Speed/convenience**

Shortcuts that violate higher priorities must not be taken merely to finish faster.

---

## 48. Final principle

VakeVahti is not only a piece of software.

It is a structured apprenticeship in building a real data-oriented workplace system.

Every important feature should move two things forward:

- the capability of the application; and
- the capability of the developer.

The desired final result is a reliable system and a developer who can explain, maintain, test, extend, defend, and professionally present the engineering behind it.