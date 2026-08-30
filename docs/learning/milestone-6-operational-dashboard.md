# Milestone 6: PostgreSQL-driven operational dashboard

Date: 2026-08-30

Status: first implementation slice complete; CI green; live Linux/browser validation pending.

## Why this milestone comes after the persisted read API

The first VakeVahti landing page was intentionally a development demo. Its main interaction manually ran the STM adapter against the public website. That was useful when only one source adapter existed, but it is the wrong normal workflow once PostgreSQL contains durable multi-source state.

Milestone 5 created the stable serving contracts:

- `GET /api/funding-calls`
- `GET /api/funding-calls/{id}`
- `GET /api/sources/health`

Milestone 6 makes those persisted contracts the primary employee/operator experience.

Opening or refreshing the dashboard must not trigger a scraper. External acquisition remains background/worker responsibility.

## Architecture

The first operational dashboard remains a self-contained FastAPI-served HTML document with browser JavaScript.

Current flow:

`PostgreSQL -> read/query service -> FastAPI persisted API -> browser dashboard`

External funding websites are not part of the dashboard request path.

The page reads:

- source health and current counts from `/api/sources/health`
- current opportunities from `/api/funding-calls`
- expanded opportunity detail from `/api/funding-calls/{id}` on demand

The old `/api/demo/stm-calls` live-source endpoint remains an engineering diagnostic boundary but is absent from the normal dashboard UI.

## Frontend/tooling decision: no React/Next.js yet

A separate frontend toolchain was deliberately not introduced in this slice.

The current product need is a small internal operational surface with:

- three configured sources
- summary KPIs
- source health cards
- one source filter
- a bounded opportunity list
- expandable detail

FastAPI can already serve the page in the managed development environment. Adding Node.js, bundling, frontend dependency management and a second development server would create deployment and operational complexity before the dashboard needs capabilities that justify it.

This is not a permanent ban on a frontend framework. The decision should be revisited if the product gains substantial client-side state, approval workflows, role-aware navigation, complex tables/forms, cross-application composition, or a design system that materially benefits from component tooling.

### System Design interview question: Why did you not use React immediately?

> I chose the smallest architecture that met the current operator requirements. The backend already exposes typed APIs and serves HTML, while the dashboard currently has limited client-side state. A separate React build would add a package ecosystem, build pipeline and deployment surface without solving a current requirement. Because the API boundary is already separated, we can introduce a richer frontend later without coupling it to the database.

## Data Engineering lesson: serving state is not source acquisition

The dashboard's refresh button reloads persisted API state. It does not rescan the public funding websites.

This preserves the separation between:

- source-facing extraction, which is slower and failure-prone
- database persistence/change detection, which establishes accepted state
- application serving, which should be predictable and repeatable

### Data Engineering interview question: What does “refresh” mean in your dashboard?

> It means re-read the application's current persisted snapshot from its API. It does not mean run the extract pipeline again. Source acquisition is scheduled/background work. Keeping those operations separate prevents every user interaction from becoming a scrape and lets the UI continue serving the last successful snapshot even if an external source is temporarily failing.

## Current snapshot semantics are visible in the UI

The opportunity list explicitly represents the latest successful source snapshots established in Milestone 5.

A funding-call row may remain in PostgreSQL historically while no longer appearing in the dashboard because its `last_seen_at` no longer matches that source's latest successful snapshot watermark.

This is a practical example of a read model over retained history.

### Database interview question: Does hiding a disappeared call mean you deleted it?

> No. Historical identity and versions remain stored. Current membership is a projection over the latest successful source snapshot. That lets the operator UI show the current set without destroying evidence needed for audit, reappearance handling or later analysis.

## Health versus freshness

The dashboard displays source operational health and the last successful scan timestamp separately.

It does not invent a `STALE` threshold.

A source can be HEALTHY because its latest persisted run succeeded, while a future source-specific cadence policy may still determine that its data is older than expected. Those are different concepts.

### Observability interview question: Why does the dashboard not turn a source red after N hours?

> We have not yet defined source-specific expected scan intervals or freshness SLAs. Using an arbitrary number would present policy as fact. The dashboard therefore shows the latest successful scan timestamp and the actual latest-run health. Once cadence requirements are agreed, freshness can be added as a separate derived state.

## Security lesson: public source text is still untrusted text

Descriptions and titles originate on external public websites. Public does not mean safe to execute.

The dashboard creates DOM nodes and assigns source-controlled strings with `textContent`. It does not interpolate those values into `innerHTML`.

External source links are opened with `target="_blank"` and `rel="noopener noreferrer"`.

### Security interview question: Why care about XSS when the data comes from public funding websites?

> The application is ingesting text from systems outside our trust boundary. If I later insert that text as HTML, a compromised or malformed source could become executable content in an internal application. Treating source values as text by default prevents that class of stored/second-order XSS without needing to assume public upstream content is benign.

## Deadline presentation and unknown values

The UI formats stored deadline timestamps for Finnish users but does not invent values when the source did not provide them.

A null deadline is displayed as `Ei ilmoitettu` rather than being assigned an estimated date/time.

The UI may visually emphasize deadlines that are already past or within seven days. That visual comparison is based on a stored deadline fact; it is not a new source fact and is not persisted as business truth.

### Data-quality interview question: What do you display when a source has no deadline?

> I preserve the null and render an explicit unknown/not-provided state. Guessing a deadline would violate provenance and could mislead an employee about an application window.

## UI state and failure handling

The dashboard has explicit states for:

- initial loading
- empty configured-source/current-call results
- persisted API failure
- detail-load failure

It does not silently replace an API failure with an empty-success display.

### Frontend interview question: Why distinguish empty from error?

> Zero current opportunities can be a valid successful source snapshot. An API/database failure means we do not know the current result. Showing both as an empty list would hide an operational incident and give the user false confidence.

## Accessibility decisions in the first slice

The page uses semantic sections/headings, real buttons and a labelled source select. Expandable opportunity rows expose `aria-expanded`, and loading/list regions use `aria-live` where appropriate.

The responsive layout keeps the same content hierarchy on narrower displays instead of dropping operational facts.

A final browser/accessibility review is still required before Milestone 6 is merged.

## Testing boundary

The dashboard contract test asserts that the page:

- contains the operational dashboard language
- references the persisted source-health and funding APIs
- does not reference `/api/demo/stm-calls`
- no longer presents `Kehitysdemo` as the normal UI

The read APIs themselves remain covered by PostgreSQL integration tests from Milestone 5.

Normal CI does not call public funding websites.

### QA interview question: Why test that a URL is *absent* from the HTML?

> The architecture has a negative requirement: page load must not return to live scraping. The old demo endpoint still exists for engineering diagnostics, so simply testing that the page loads is insufficient. An explicit regression assertion makes that boundary executable.

## First CI evidence

Backend CI #80 on the initial Milestone 6 branch passed the substantive pipeline gates:

- dependency installation
- Ruff
- strict mypy
- Alembic migrations
- PostgreSQL pytest

The existing Starlette/httpx deprecation warning remains tracked separately and is not a Milestone 6 regression.

## Portfolio/interview narrative

> After building a durable multi-source ingestion pipeline and persisted read APIs, I replaced the original scraper-driven development page with an operator dashboard over the database serving layer. The dashboard shows current snapshot counts, source health, latest scan facts, filtered funding opportunities and on-demand details without triggering external scans. I intentionally kept the first frontend dependency-light because the current interaction complexity did not justify another build/deployment stack. I also treated upstream public text as untrusted by inserting it with `textContent`, preserved null source facts instead of guessing them, and made the no-live-scraping UI boundary a regression-tested requirement.

## Remaining validation before merge

- pull the Milestone 6 branch on the Linux development machine
- run Ruff, strict mypy and the full PostgreSQL pytest suite
- start the FastAPI application against the populated development database
- visually verify the operational dashboard renders the expected 17-call / 9-1-7 source state
- exercise source filtering and one detail expansion
- verify no dashboard action triggers `/api/demo/stm-calls`
- review responsive/accessibility behavior
- record evidence and complete final PR review
