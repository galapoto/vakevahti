# Linux PostgreSQL, test isolation and environment safety

## Context

On the Linux development machine, Docker 29.3.1 was available and PostgreSQL 16 was started in a container. Alembic migrations applied successfully and all 18 tests passed against PostgreSQL.

A subsequent real STM worker run unexpectedly reported `baseline=False`, found 9 new calls, and the development database contained 10 funding rows. The cause was not the live scanner. `DATABASE_URL` and `TEST_DATABASE_URL` had been pointed at the same local database, while integration tests intentionally truncate and repopulate the funding tables. The final integration test left test state behind, so the later production-style worker inherited test-created `source_states` and funding data.

## Engineering lesson

Test isolation is a data-safety requirement, not only a test-quality preference. Destructive integration tests must never silently target a developer or production runtime database.

VakeVahti now uses three protections:

1. local development and integration tests use separate PostgreSQL databases (`vakevahti` and `vakevahti_test`)
2. pytest refuses to start when `TEST_DATABASE_URL == DATABASE_URL`, unless an explicit ephemeral-database override is supplied
3. integration fixtures clean their tables after each test as well as before execution

CI is intentionally ephemeral and sets `ALLOW_TEST_DATABASE_REUSE=true`, so its one disposable PostgreSQL database can safely serve both migration and test execution.

## Technical question: Why did the first real worker run show `baseline=False` on a fresh container?

Strong answer:

> The container itself was fresh, but I had configured the runtime and integration-test URLs to the same database. The PostgreSQL integration tests create source state and funding rows after truncating the database. Because the test fixtures only cleaned before execution, the final test left state behind. The worker therefore correctly observed an already-established source baseline. The bug was environment isolation, not the baseline algorithm.

## Technical question: Why is `TEST_DATABASE_URL` separation important if tests clean their data?

Strong answer:

> Cleanup is defense in depth, not the primary safety boundary. A test can crash, be interrupted, or contain a bug before teardown executes. A separate test database constrains the blast radius. I additionally use a pytest startup guard so destructive integration tests fail closed if the configured test and runtime databases are the same.

## Technical question: Why allow database reuse in CI at all?

Strong answer:

> The CI PostgreSQL service is created for one workflow run and destroyed afterward, so it is explicitly ephemeral. Reusing that database reduces setup complexity without risking persistent data. The exception is explicit through `ALLOW_TEST_DATABASE_REUSE=true`; local environments do not get that behavior by default.

## Technical question: What is the difference between migration testing and application integration testing?

Strong answer:

> Migration testing proves that the schema can be created or upgraded using the same migration path expected in deployment. Application integration testing then exercises SQLAlchemy, PostgreSQL constraints, transactions, locks and domain behavior against that schema. Both are necessary: application tests against an unmanaged schema can hide migration failures, while migrations alone do not prove application behavior.

## Interview question: Describe a defect you discovered through end-to-end testing rather than a failing unit test.

Strong answer:

> After all 18 tests passed, I ran the real scheduled ingestion path against local PostgreSQL. The first run unexpectedly reported that the source baseline already existed. I traced the discrepancy to environment configuration: the integration-test database URL and runtime database URL were identical, so passing tests had contaminated the runtime state. I treated that as a system-design defect, added separate development/test databases, a fail-closed pytest guard, fixture teardown cleanup and an explicit CI-only override. The incident reinforced that green tests do not prove environment safety.

## Interview question: What does defense in depth mean in test-data safety?

Strong answer:

> I avoid relying on a single safeguard. Here, the main boundary is a separate test database. A pytest startup guard prevents accidental URL reuse, fixtures clean before and after tests, CI reuse is explicitly opted into only for an ephemeral database, and runtime data remains outside the destructive test path. If one protection fails, the others still reduce the risk of data damage.

## Portfolio evidence

This incident demonstrates PostgreSQL operations, Alembic migrations, Docker-based local infrastructure, integration testing, environment configuration, root-cause analysis, fail-safe design and data-safety engineering using a real monitoring pipeline.
