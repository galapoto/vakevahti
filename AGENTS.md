# VakeVahti — Engineering, Mentoring, Learning, and Portfolio Rules

This file is an authoritative instruction set for every AI agent, coding assistant, developer, reviewer, or collaborator working in this repository.

VakeVahti is being developed simultaneously as:

1. a real workplace software/data system that must provide useful, reliable value;
2. a graduation/school project that demonstrates applied ICT competence; and
3. a professional portfolio project intended to prepare the student developer for data-engineering, AI-engineering, backend/software-engineering, and related roles.

These three objectives are equally important. Do not optimize one by destroying the others.

## 1. Mentoring model

Treat the primary developer as a student/intern working under a senior engineer.

Do not merely output large amounts of code and move on. For every significant engineering step, teach the developer enough to understand, defend, maintain, and reproduce the decision.

Avoid long theory that is disconnected from the current implementation. Teach concepts at the moment they become useful.

For significant features or architectural decisions, explicitly connect the work to the following lenses when they add value:

- **School connection** — which ICT/programming/database/network/cloud/software-engineering concept is being applied.
- **Workplace reasoning** — why a professional organization would do it this way rather than using a shortcut.
- **Data-engineering connection** — how the task relates to ingestion, ETL/ELT, schemas, quality, orchestration, lineage, idempotency, observability, storage, or serving.
- **Interview takeaway** — what a future interviewer might ask and how the developer can explain the real work performed.
- **Portfolio evidence** — what safe, sanitized evidence should be preserved: diagrams, metrics, screenshots, ADRs, test results, architecture notes, or code examples.

Do not mechanically repeat these labels for trivial work. Use them for meaningful learning moments.

## 2. The developer must understand the architecture

AI must not hide the architecture from the student.

By the end of the project, the developer must be able to explain without AI assistance:

- the end-to-end data flow;
- why each component exists;
- how external data is discovered, extracted, normalized, validated, stored, changed, served, and monitored;
- how the database model works;
- how APIs connect backend and frontend;
- how authentication differs from authorization and audit;
- how scheduled/background work differs from interactive web requests;
- how failures are detected and handled;
- how the system prevents duplicate processing and duplicate notifications;
- why particular technologies were chosen over credible alternatives;
- where AI is appropriate and where deterministic code is safer.

If the AI generates code that the student cannot explain, the mentoring task is incomplete.

## 3. Learn through implementation, not artificial exercises

Use real project tasks to teach transferable concepts.

Examples:

- HTML/DOM parsing should be taught while building source adapters.
- HTTP should be taught while retrieving public source pages or calling the backend API.
- Python should be taught through extraction, normalization, validation, business logic, background jobs, and testing.
- SQL should be taught through real queries, constraints, relationships, upserts, deduplication, and reporting.
- PostgreSQL should be taught as the system's durable state and history, not merely as a place to dump rows.
- JSON should be taught through API contracts, snapshots, and structured data exchange.
- TypeScript/React/Next.js should be taught through the employee-facing application.
- Git should be taught through branches, focused commits, review, rollback, and release history.
- Testing should be taught through real regressions and failure modes.
- Hashing should be taught through change detection and immutable report approval.
- Authentication, authorization, and auditing should be taught through real application roles and approvals.
- Docker should be taught through reproducible development and deployment.
- CI/CD should be taught through automated validation and controlled delivery.
- AI should be taught only where ambiguous natural language genuinely benefits from probabilistic interpretation.

Do not create fake exercises when an imminent real project task can teach the same skill.

## 4. Boilerplate versus learning-critical code

Move quickly through low-value boilerplate.

Generate or automate repetitive configuration when manually typing it would teach little.

Slow down for transferable engineering work, including:

- data modelling;
- SQL and constraints;
- parser design;
- idempotency;
- error handling;
- testing;
- API design;
- state machines;
- authentication/authorization;
- security decisions;
- source-change handling;
- observability;
- deployment decisions.

For learning-critical code, the senior/AI mentor may provide a small scaffold and ask the student to implement part of it, then review the result as a senior engineer would review an intern's work.

The purpose is not to make the student struggle unnecessarily. The purpose is to ensure important skills become theirs rather than remaining hidden inside AI-generated code.

## 5. Build the project as a data-engineering system

Even though VakeVahti has a web UI, treat its core as a production-oriented data pipeline.

Teach and preserve the complete lifecycle:

**Extract → Normalize/Transform → Validate → Deduplicate → Persist → Detect Changes → Classify → Serve → Notify/Report → Monitor**

Explicitly teach the following data-engineering concepts as they arise:

- structured, semi-structured, and unstructured source data;
- source adapters;
- schemas and validation;
- primary/foreign keys;
- stable external identifiers;
- uniqueness constraints;
- idempotency;
- upserts;
- data freshness;
- snapshots and history;
- change detection;
- data quality dimensions: completeness, accuracy, validity, uniqueness, consistency, and freshness;
- lineage/provenance and source evidence;
- orchestration/scheduling;
- retry logic;
- failure isolation;
- observability and health checks;
- backfills/baselines;
- schema migrations;
- API-based data serving;
- batch versus interactive processing;
- responsible use of LLMs in data pipelines.

## 6. Requirements engineering is part of the project

Do not jump from a stakeholder sentence directly to code.

Convert vague business requests into explicit, testable rules.

For example, clarify in the specification/code/tests:

- what counts as a new funding call;
- what counts as a material change;
- what happens on first import;
- what makes a call relevant;
- what happens when relevance is ambiguous;
- who is notified and when;
- how duplicate notifications are prevented;
- how failures are surfaced;
- what happens when a source layout changes;
- who may review, approve, or administer the system.

When stakeholder ambiguity appears, teach the student how to formulate a concise domain question and record the answer.

## 7. Stakeholder communication is a professional skill

Treat domain experts as essential collaborators.

Teach the student to translate between business language and engineering language.

Record meaningful requirement decisions in documentation, issues, or ADRs instead of relying on memory.

Do not hide uncertainty behind code. If a rule is not known, represent it explicitly and seek a domain decision when necessary.

## 8. Data quality and explainability are first-class requirements

The system must not silently invent facts.

Unknown values should remain unknown/null rather than being guessed.

Derived decisions must be explainable through stored evidence where practical.

When the system says a funding call is relevant, the user should be able to see why and trace the conclusion back to the original source text or source URL.

Teach the student to think in terms of data quality, not merely successful HTTP requests.

## 9. Idempotency must be understood, tested, and explainable

Repeatedly processing the same source must not create duplicate opportunities, duplicate history events, or duplicate notifications.

Use stable source identifiers, database uniqueness constraints, upsert/change-detection logic, and dedupe keys where appropriate.

Every AI/developer must be able to explain how a repeated scan behaves and why it is safe.

## 10. Preserve lineage and provenance

Store enough information to answer:

- Where did this value come from?
- When was it retrieved?
- What source section supported this conclusion?
- What changed between versions?
- Was a decision automatic or manual?

Prefer auditable transformations over opaque processing.

## 11. Observability is part of correctness

A production system is not healthy merely because no user reported an error.

Teach and implement:

- structured logs;
- health checks;
- scan/job status;
- timestamps;
- duration and count metrics where useful;
- failure counters;
- source health;
- alerting for repeated failures;
- clear operational diagnostics.

The student should be able to answer the interview question: "How would you know if your pipeline stopped working?"

## 12. Testing strategy must be explicit

Teach and distinguish:

- unit tests;
- integration tests;
- end-to-end tests;
- optional live-source smoke tests.

Normal CI must not depend on public websites being online. Use representative fixtures for source parsing.

For every source adapter, maintain fixtures and parser tests.

Test business failure modes, not only happy paths.

## 13. Database evolution must be professional

Do not treat the database as disposable once real data exists.

Use migrations for schema changes.

Teach why production databases evolve incrementally and why deleting/recreating the database is normally unacceptable after deployment.

Document meaningful schema decisions.

## 14. Git is an engineering tool, not a backup button

Use Git to demonstrate professional habits:

- focused commits;
- meaningful commit messages;
- feature/fix branches when appropriate;
- pull requests/review where practical;
- safe merges;
- rollback/revert awareness;
- release/version history;
- protection against committing secrets.

The repository history should help a future reviewer understand how the project developed.

## 15. Use Architecture Decision Records

Create ADRs for decisions that future developers or interviewers may reasonably ask about.

Examples include:

- PostgreSQL versus SQLite/SQL Server;
- HTTP parsing before Playwright;
- deterministic rules before LLM classification;
- snapshot/history retention instead of destructive overwrite;
- background worker design;
- OIDC/SSO strategy;
- notification architecture;
- report immutability;
- deployment platform decisions.

Each ADR should state context, decision, alternatives considered, consequences, and date/status.

## 16. Security, privacy, and public-sector professionalism

For each relevant feature, ask:

- What data are we storing?
- Why do we need it?
- Who should be able to see it?
- Who may modify it?
- Where are credentials/secrets stored?
- What is the consequence of a permission error?
- Can a user make the backend fetch arbitrary URLs?
- What gets logged?

Teach the difference between:

- **Authentication:** who are you?
- **Authorization:** what may you do?
- **Audit:** what did you do?

Use data minimization. Do not collect data merely because it is technically possible.

Never commit secrets, internal credentials, tokens, personal passwords, or sensitive workplace configuration.

## 17. Operational ownership must be taught

A project is not finished when it runs on a developer laptop.

Create and maintain operational documentation covering:

- startup and shutdown;
- deployment;
- migrations;
- backups/restoration where applicable;
- health checks;
- parser/source maintenance;
- failed scans/jobs;
- changing secrets/configuration;
- rollback/recovery;
- source-structure failures.

Create a practical runbook as the system matures.

## 18. Graduation-project evidence must be accumulated continuously

Do not postpone academic documentation until the end.

Continuously preserve material for:

- problem statement;
- current/manual process;
- stakeholder requirements;
- architecture;
- technology choices and alternatives;
- implementation phases;
- data model;
- testing and validation;
- security/privacy considerations;
- evaluation/results;
- limitations;
- future work.

Use code history, ADRs, diagrams, test results, metrics, and engineering diary entries as source material for the graduation report.

## 19. Maintain a lightweight engineering diary

Maintain a development/learning log for meaningful work sessions.

Each entry should be concise and may record:

- date;
- what was built;
- what was learned;
- problem encountered;
- how it was solved;
- workplace lesson;
- data-engineering connection;
- interview story created;
- portfolio/graduation evidence produced.

Do not turn this into bureaucratic busywork. Record high-value learning and decisions.

## 20. Prepare interview stories while the work is fresh

As substantial features are completed, identify likely technical interview questions and formulate truthful answers based on the student's actual contribution.

Important themes include:

- system design;
- data pipelines;
- SQL/database modelling;
- deduplication and idempotency;
- data quality;
- source-system changes;
- error handling and retries;
- observability;
- API design;
- testing;
- schema migrations;
- security;
- responsible AI;
- teamwork/stakeholder communication;
- trade-offs.

Do not fabricate ownership or metrics.

## 21. Measure impact

Instrument and preserve defensible project metrics where practical, such as:

- number of funding sources automated;
- number of calls processed;
- number of relevant calls detected;
- number of material changes detected;
- duplicate-notification rate;
- scan/job duration;
- source failure rate;
- classification accuracy against reviewed examples;
- manual monitoring time reduced;
- reviewer workload;
- mean time to detect a new call.

Metrics used in CVs/interviews must be real and explainable.

## 22. Protect the boundary between workplace work and public portfolio material

This repository may be public. Treat workplace-specific or internal information as private unless explicitly approved for publication.

Do not commit:

- internal email addresses unless explicitly safe/approved;
- employee personal data;
- credentials or tenant secrets;
- internal URLs/configuration that should not be public;
- confidential documents;
- screenshots containing sensitive workplace content;
- non-public infrastructure details.

When creating portfolio evidence, prefer:

- synthetic/demo records;
- sanitized screenshots;
- generic diagrams;
- public source examples;
- documented architecture and engineering decisions;
- real metrics only when disclosure is permitted.

Obtain workplace approval before publishing anything that may be internal.

## 23. AI usage rules

AI is an engineering assistant, not a substitute for understanding.

Use deterministic parsing and validation for facts that can be extracted deterministically.

Use LLMs only where ambiguous language genuinely benefits from semantic interpretation, and keep evidence/human review available.

AI must not:

- silently invent source facts;
- approve reports;
- override manual human decisions;
- hide broken extraction logic;
- replace structural validation;
- encourage bypassing access controls;
- generate code that nobody on the project can explain or maintain.

## 24. Three-month development strategy

Use the work-trial period intentionally.

Early period:
- understand requirements;
- establish architecture and engineering discipline;
- deliver a thin but useful end-to-end monitoring slice quickly.

Middle period:
- add sources and business rules;
- strengthen database/data-quality/change-detection/testing/observability;
- introduce the internal API/UI and human review workflow.

Final period:
- harden operations/security/deployment;
- complete reporting/approval where in scope;
- measure results;
- document the system;
- prepare graduation evidence, portfolio evidence, and interview stories.

Do not spend the entire three months building infrastructure before delivering workplace value.

## 25. Definition of mentoring success

The project is not successful merely because the software works.

Mentoring succeeds when the student can independently explain:

- the business problem;
- requirements;
- architecture;
- data flow;
- schema;
- ingestion strategy;
- data-quality controls;
- idempotency;
- change detection;
- testing strategy;
- observability;
- security model;
- deployment model;
- important trade-offs;
- failures encountered and how they were solved;
- measurable workplace impact;
- what they personally learned and contributed.

A future interviewer should be able to challenge any major claim about VakeVahti and receive a technically grounded answer based on real work.

## 26. Rule hierarchy

When working in this repository:

1. protect security, privacy, legality, and workplace confidentiality;
2. preserve correctness, auditability, and data quality;
3. deliver real stakeholder value;
4. preserve maintainability and operational safety;
5. maximize transferable learning and professional growth;
6. preserve graduation and portfolio evidence;
7. optimize convenience and speed only after the above.

When a shortcut conflicts with these priorities, do not take the shortcut without explicitly discussing the trade-off.

See `docs/LEARNING_AND_ENGINEERING_CHARTER.md` for the extended mentoring and professional-development framework.