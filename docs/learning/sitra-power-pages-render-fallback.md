# Sitra Power Pages transport fallback

Date: 2026-08-30

Status: implementation and deterministic CI validation complete; live Sitra idempotency validation still required before PR #8 is ready.

## Incident

The Sitra fixture parser passed, but the real worker failed against `https://asiointi.sitra.fi/` with `SourceStructureError`.

The public endpoint returned HTTP 200, yet the HTTP body available to `httpx` contained only the Power Pages application shell and not the lifecycle blocks used by the parser. A rendered browser representation exposes the funding cards and lifecycle labels such as `Haku käynnissä` and `Haku sulkeutunut`.

The correct diagnosis was therefore a transport/rendering mismatch, not permission to weaken parser validation or invent an empty successful result.

## What changed

- retained normal HTTP as the first retrieval strategy
- added Sitra-specific headless Chromium rendering only when the HTTP representation has no visible lifecycle status
- retained the same semantic parser after rendering
- broadened recognized HTML heading levels from a narrow `h3`/`h4` assumption to semantic `h2`-`h6` headings
- kept lifecycle recognition mandatory
- kept closed calls recognized but not emitted
- injected the renderer behind a callable boundary so ordinary unit tests do not need a real browser or live website
- added deterministic regression tests for the Power Pages shell and for fail-loud behavior
- added Playwright as a backend dependency while keeping the Chromium binary an explicit worker-runtime requirement
- kept PR #8 in draft until live Sitra validation proves the complete path

GitHub Actions run #54 passed dependency installation, Ruff, strict mypy, Alembic and PostgreSQL pytest after this implementation.

## Lesson: separate transport from semantic extraction

A scanner has at least two different responsibilities that should not be conflated:

1. obtaining an authoritative representation of the source
2. interpreting that representation into domain data

The Sitra bug occurred in the first responsibility. Rewriting relevance rules or persistence would have addressed the wrong layer.

### Interview question: Why did you not replace the parser with Playwright selectors?

> The semantic parser was already the tested contract for interpreting Sitra lifecycle state. The defect was that normal HTTP did not expose the client-rendered content. I kept extraction semantics independent of retrieval: HTTP first, browser rendering only when needed, then the same parser. That minimizes duplicated logic and keeps source-structure failures explicit.

## Lesson: HTTP-first is an operational optimization, not dogma

HTTP retrieval is cheaper, faster and easier to operate than a browser. It should remain the default where it can retrieve the required public content. A browser is justified when the authoritative public page genuinely renders the required information client-side.

### Interview question: Why not use Playwright for every source?

> Browser automation has a larger runtime, more dependencies, more failure modes and higher resource cost than normal HTTP. STM and Suomen Akatemia do not need it. I introduced Chromium only inside the Sitra adapter after live evidence showed that the required Power Pages content was absent from the HTTP representation.

### Technical question: Why not use a search-engine cache as the Sitra data source?

> Search results are not the authoritative application surface and can be stale. During diagnosis, cached results still showed lifecycle state that had already crossed a deadline. I used search only as evidence that the public page renders the cards, never as production ingestion data.

## Lesson: a fallback must not hide structural failures

The adapter checks whether lifecycle text is already visible in the HTTP representation. If lifecycle labels are visible but the parser cannot associate them with funding cards, the parser error is re-raised instead of invoking a browser to mask the defect.

Rendered HTML must also pass the same parser. If it does not, the scan remains failed.

### Interview question: How did you preserve fail-loud semantics after adding a fallback?

> I made the fallback conditional on missing client-rendered content, not on any arbitrary parser exception. If the raw page already exposes lifecycle markers but the parser cannot understand the structure, that is a parser/source-contract problem and fails immediately. The rendered result is also parsed through the same strict rules, so browser automation cannot turn an unknown structure into guessed data.

## Lesson: dependency injection improves deterministic testing

The Sitra scanner can receive an HTML-renderer callable. Production uses Playwright; unit tests provide a tiny deterministic async renderer that returns representative HTML.

### Technical question: Why inject the renderer instead of launching Chromium in unit tests?

> The behavior I need to test is the decision boundary: raw HTTP shell should trigger rendering, while visible-but-unrecognized lifecycle markup should fail. Injecting the renderer tests that behavior deterministically without network access, browser downloads or timing variability. Live browser validation remains an operational gate.

## Lesson: code dependency and runtime dependency are different

Installing the Python `playwright` package is not the same as installing Chromium and its operating-system libraries. CI can type-check and unit-test the code without launching the browser, while a worker that enables `SITRA` must have the Chromium runtime provisioned.

### DevOps interview question: What would you put in a production container for this source?

> I would build the application image with the pinned Python dependencies plus the approved Playwright Chromium runtime and required OS libraries. I would not download a browser ad hoc during each scheduled run. The image should be reproducible, scanned and promoted through the normal deployment pipeline.

## Security interview question: Is headless-browser retrieval bypassing a security control?

> No. The scanner renders the same unauthenticated public Sitra page a normal user browser can access. It does not log in, evade bot protections, manipulate challenges or access private APIs. If the source later requires authentication or blocks automated access, that becomes a governance/integration decision rather than something the scanner should bypass.

## Data Engineering interview question: Why does a web-rendering bug matter to data engineering?

> Data pipelines start at source acquisition. If acquisition returns an incomplete representation, downstream normalization and persistence can be perfectly coded yet still produce wrong data. I treat source retrieval, semantic extraction, normalization, provenance, change detection and persistence as separate quality boundaries with explicit failure behavior.

## Remaining proof before merge

1. install the Chromium runtime on the Linux development environment
2. run Sitra live once and inspect emitted records
3. run Sitra immediately again and prove `UNCHANGED`
4. run `STM,SITRA,ACADEMY` twice
5. inspect `funding_calls`, versions, source baselines and `source_scan_runs`
6. rerun local Ruff, strict mypy and full PostgreSQL pytest
7. keep GitHub CI green
8. only then update PR #8 to ready-for-review
