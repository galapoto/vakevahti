# Milestone 6 technical assignment workbook

Date: 2026-08-31

Status: active learning workbook; solutions are included so the implementation can be studied after attempting each task.

## Learning contract for this project

From this point, every meaningful VakeVahti implementation slice follows this sequence:

`implement -> test -> document -> explain -> technical assignment -> worked solution -> interview/code questions -> continue`

The goal is not only to finish VakeVahti. The same work must also train the developer to explain, debug and reproduce the engineering decisions without AI hiding the architecture.

For each slice, the learning record should cover:

- what changed in the code and data flow
- why the change was needed
- alternatives and trade-offs
- school/course relevance
- Data Engineering / Software Engineering relevance
- security/privacy implications
- tests and failure modes
- a hands-on technical assignment
- a fully worked solution
- conceptual interview questions
- code/debugging questions
- a concise portfolio story

---

# Part 1 — The Docker/PostgreSQL/Windows switch

## What actually changed

The production architecture did **not** switch away from PostgreSQL.

On the Linux development machine, PostgreSQL is run in Docker. PostgreSQL listens on port `5432` inside the container and Docker maps it to host port `55432`:

`Linux application -> 127.0.0.1:55432 -> Docker port mapping -> PostgreSQL:5432`

The Windows work machine is different:

- Docker is not available.
- Native PostgreSQL is not installed.
- `psql` is not installed.
- port `5432` is closed.
- the user is not in the local Administrators group, so installing infrastructure software should not be assumed.

Therefore the Windows workstation cannot run the PostgreSQL integration path locally.

Instead of weakening the real architecture, Milestone 6 introduced an explicit **development preview provider**:

`Windows browser -> same dashboard -> same /api/funding-calls and /api/sources/health contracts -> synthetic preview provider`

while Linux/CI/production remain:

`browser -> same dashboard -> persisted API -> read service -> PostgreSQL`

The feature flag is:

```text
DASHBOARD_PREVIEW_MODE=true
```

Preview mode is opt-in and clearly labelled `Kehitysesikatselu · fixture-data` so synthetic data is not mistaken for production data.

This is a practical example of separating an interface/contract from a concrete infrastructure provider.

---

# Assignment 1 — Explain the port difference

## Task

Explain why this Linux connection string used port `55432`:

```text
postgresql+asyncpg://vakevahti:vakevahti@127.0.0.1:55432/vakevahti
```

while a normal native PostgreSQL installation would commonly use `5432`.

Then draw the request path.

## Worked solution

PostgreSQL itself normally listens on `5432`. In the Linux development setup, the database runs inside a Docker container. Docker publishes the container's `5432` port as `55432` on the host to avoid clashes and make the local environment explicit.

So the application connects to the **host-side published port**, not directly to the container port.

```text
Python / FastAPI
      |
      | TCP 127.0.0.1:55432
      v
Docker host-port mapping
      |
      | container:5432
      v
PostgreSQL
```

A native Windows PostgreSQL installation would usually expose PostgreSQL directly on host port `5432`, so no Docker translation would exist.

## Interview answer

> Port 5432 is PostgreSQL's default service port. Our Linux development environment containerizes PostgreSQL and publishes container port 5432 as host port 55432. The application therefore connects to 55432 on the host. This is infrastructure configuration, not a different database protocol.

---

# Assignment 2 — Diagnose `ConnectionRefusedError`

## Task

You receive:

```text
ConnectionRefusedError: [WinError 10061]
```

for `127.0.0.1:55432` on Windows.

Write a debugging sequence that proves whether the error is credentials, schema, DNS, firewall or simply "nothing is listening".

## Worked solution

Start at the TCP layer before debugging SQLAlchemy or credentials.

PowerShell:

```powershell
Test-NetConnection 127.0.0.1 -Port 55432
Test-NetConnection 127.0.0.1 -Port 5432
Get-Service *postgres* -ErrorAction SilentlyContinue
Get-Command psql.exe -ErrorAction SilentlyContinue
```

Interpretation:

- `TcpTestSucceeded : False` means a TCP connection could not be established.
- If both ports fail and no PostgreSQL service exists, credentials and database names are irrelevant because authentication was never reached.
- An authentication error would occur **after** a TCP connection reaches PostgreSQL.
- A missing database would normally produce a PostgreSQL error such as `database ... does not exist`, again proving the network/service layer already worked.

This is layered debugging: network/service availability first, then authentication, then schema/application logic.

## Interview answer

> I avoid debugging ORM configuration before proving the database process is reachable. Connection refused means no listener accepted the TCP connection, so I check the port and service first. Authentication and migrations cannot be the root cause until the connection reaches PostgreSQL.

---

# Assignment 3 — Explain why preview mode is not replacing PostgreSQL

## Task

A reviewer says: "You switched from PostgreSQL to fixture data because Windows could not run Docker. Isn't that an architectural regression?"

Give a senior-level answer.

## Worked solution

No. PostgreSQL remains the source of truth for the real application. The preview provider exists only for a constrained development workstation.

The important architectural boundary is the API contract:

```text
GET /api/funding-calls
GET /api/funding-calls/{id}
GET /api/sources/health
```

Both providers satisfy those same contracts. The dashboard does not know whether its data came from PostgreSQL or the preview fixture provider.

The normal application path creates the SQLAlchemy engine/session factory and includes the persisted API router. Preview mode deliberately does not create the database engine and instead includes the preview router.

This allows frontend work on a machine without local database infrastructure while CI and Linux still validate PostgreSQL behavior.

The correct mental model is:

```text
                  +---------------------+
                  |     Dashboard       |
                  +----------+----------+
                             |
                       same HTTP API
                             |
             +---------------+---------------+
             |                               |
      normal/runtime                     preview/dev
             |                               |
      persisted router                    fixture router
             |                               |
       read service                       in-memory data
             |
        PostgreSQL
```

## Interview answer

> I did not replace PostgreSQL. I separated the consumer contract from its provider. Normal runtime and CI still use PostgreSQL; the restricted Windows workstation uses an explicitly labelled fixture provider behind the same API contract. This preserves architecture while improving development portability.

---

# Assignment 4 — Implement explicit router selection

## Task

Write Python logic that selects the preview API router only when `dashboard_preview_mode` is true. Avoid duplicating `include_router` calls.

## Worked solution

```python
selected_router = (
    preview_api_router
    if settings.dashboard_preview_mode
    else api_router
)
application.include_router(selected_router)
```

Why this is preferable to hidden global mutation:

- the decision is explicit at application construction time
- tests can construct an app with known settings
- preview mode does not need to monkey-patch dependencies
- production behavior remains the default

A compact one-line variant is valid, but readability matters more than minimizing lines.

---

# Assignment 5 — Prevent environment-sensitive tests

## Task

Why was this test design fragile?

```python
from app.main import app

client = TestClient(app)
```

when `app = create_app()` reads environment settings at import time?

Refactor it so a shell variable such as `DASHBOARD_PREVIEW_MODE=true` cannot silently change what a "normal dashboard" test means.

## Worked solution

The imported module-level `app` is constructed from ambient process environment. Therefore the test's behavior depends on whatever variables happen to exist in the developer's shell.

Use explicit configuration:

```python
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _normal_client() -> TestClient:
    app = create_app(Settings(dashboard_preview_mode=False))
    return TestClient(app)


def _preview_client() -> TestClient:
    app = create_app(
        Settings(
            dashboard_preview_mode=True,
            enabled_sources="STM,SITRA,ACADEMY",
        )
    )
    return TestClient(app)
```

Now the test itself declares its runtime mode.

## Core concept

Environment variables are **ambient global state**. Deterministic tests should make important configuration explicit whenever practical.

## Interview answer

> A module-level app constructed from environment settings can make tests machine-dependent. I fixed that by testing the application factory directly with explicit settings, so each test states which mode it exercises.

---

# Assignment 6 — Verify provider contract equivalence

## Task

Write a test proving preview mode exposes the same high-level list and health endpoints needed by the frontend.

## Worked solution

```python
def test_preview_mode_exposes_dashboard_contracts() -> None:
    client = _preview_client()

    response = client.get("/api/funding-calls")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 17

    sitra = client.get(
        "/api/funding-calls",
        params={"source_code": "sitra"},
    )
    assert sitra.status_code == 200
    assert sitra.json()["total"] == 1

    health = client.get("/api/sources/health")
    assert health.status_code == 200
    sources = {
        item["source_code"]: item
        for item in health.json()["sources"]
    }
    assert sources["STM"]["current_call_count"] == 9
    assert sources["SITRA"]["current_call_count"] == 1
    assert sources["ACADEMY"]["current_call_count"] == 7
```

The test should not claim the fixture values are production truth. It only validates that the preview provider can drive the UI contract.

---

# Assignment 7 — Current-state SQL over retained history

## Task

VakeVahti retains historical funding-call rows, but the dashboard must show only calls belonging to the latest successful source snapshot.

The invariant is:

```text
funding_calls.last_seen_at == source_states.last_successful_scan_at
```

Write SQL that returns current calls and excludes disappeared historical rows.

## Worked solution

```sql
SELECT fc.*
FROM funding_calls AS fc
JOIN source_states AS ss
  ON ss.source_code = fc.source_code
WHERE fc.last_seen_at = ss.last_successful_scan_at
ORDER BY fc.application_deadline_at ASC NULLS LAST,
         fc.id ASC;
```

Why the join matters:

- `funding_calls` contains retained history/current entities
- `source_states` contains the authoritative latest-success watermark per source
- membership in the current snapshot is derived, not represented by deleting history

If a successful scan returns zero calls, `last_successful_scan_at` advances but no funding call receives that timestamp, so the current result is legitimately empty.

If a scan fails, the watermark does not advance, so the last successful current snapshot remains served while source health becomes failing.

## Interview answer

> I model current membership as a projection over retained history. A call is current when its last-seen watermark matches the source's latest successful snapshot watermark. Failed scans do not move the watermark, while a successful empty scan does.

---

# Assignment 8 — Why `SUCCEEDED` should not reach the UI

## Task

The backend stores scan state as machine-oriented strings such as `SUCCEEDED` and `FAILED`. Implement a Finnish presentation mapping without changing the stored audit value.

## Worked solution

```javascript
function scanStatusLabel(value) {
  const labels = {
    SUCCEEDED: "Onnistunut",
    FAILED: "Epäonnistunut",
    RUNNING: "Käynnissä",
    CANCELLED: "Keskeytetty",
  };
  return labels[value] || "Ei tietoa";
}
```

Then:

```javascript
addFact(
  facts,
  "Viimeisen ajon tila",
  scanStatusLabel(item.latest_scan_status),
);
```

Do **not** rewrite the database status to Finnish. Storage/audit contracts should remain stable and language-neutral; localization belongs to the presentation layer.

## Interview answer

> I keep persisted state machine values stable and machine-oriented, then translate them at the presentation boundary. That avoids coupling database contracts to one UI language.

---

# Assignment 9 — Implement persistent light/dark mode

## Task

Implement a theme system with these requirements:

- default to the operating-system preference
- allow manual light/dark toggle
- remember manual choice across reloads
- avoid waiting until the entire page is rendered before selecting the theme

## Worked solution

Run an early bootstrap script in `<head>`:

```javascript
(() => {
  const saved = localStorage.getItem("vakevahti-theme");
  const systemDark = window.matchMedia(
    "(prefers-color-scheme: dark)"
  ).matches;

  const theme = saved === "light" || saved === "dark"
    ? saved
    : (systemDark ? "dark" : "light");

  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
})();
```

Toggle logic:

```javascript
const button = document.getElementById("theme-toggle");

button.addEventListener("click", () => {
  const current = document.documentElement.dataset.theme;
  const next = current === "dark" ? "light" : "dark";

  document.documentElement.dataset.theme = next;
  document.documentElement.style.colorScheme = next;
  localStorage.setItem("vakevahti-theme", next);
});
```

CSS can then override tokens:

```css
:root {
  --bg: #f5f7fa;
  --surface: #ffffff;
  --text: #1b2030;
}

html[data-theme="dark"] {
  --bg: #10131b;
  --surface: #181c26;
  --text: #f4f6fa;
}
```

Why run the bootstrap early? It reduces a flash where the browser first paints light mode and immediately flips to dark mode.

---

# Assignment 10 — Stored XSS reasoning

## Task

A public funding source returns this title:

```html
<img src=x onerror=alert('xss')>
```

Explain the difference between these two implementations:

```javascript
node.innerHTML = title;
```

and:

```javascript
node.textContent = title;
```

## Worked solution

`innerHTML` asks the browser to parse the string as markup. If untrusted content contains executable HTML/event handlers, it can become DOM content and potentially execute.

`textContent` treats the value as text. The angle brackets are displayed as characters instead of being parsed as an element.

Because funding text originates outside VakeVahti's trust boundary, the dashboard defaults to `textContent`.

This is especially important for stored/second-order XSS: unsafe upstream text can be persisted today and executed much later when another employee opens the dashboard.

## Interview answer

> Public does not mean trusted. I render upstream values as text by default and use `noopener noreferrer` for external new-tab links. This reduces stored XSS and reverse-tabnabbing risk.

---

# Assignment 11 — Windows versus CI test strategy

## Task

The Windows work machine has no PostgreSQL. Design a test strategy that does not pretend database integration tests passed locally.

## Worked solution

Windows workstation:

```powershell
python -m ruff check .
python -m mypy app
python -m pytest tests/unit -q
```

This validates static analysis, UI/application-factory logic and preview-mode unit behavior.

Linux development / GitHub CI:

```text
PostgreSQL service available
-> Alembic migrations
-> full pytest suite
-> integration tests against isolated test DB
```

The important rule is evidence labeling. Do not say "all tests passed on Windows" if PostgreSQL integration tests were skipped. Say "Windows unit/static gates passed; PostgreSQL integration gates passed in CI/Linux."

## Interview answer

> I adapt local developer feedback to the workstation's capabilities without weakening the release gate. The constrained Windows machine runs deterministic unit/static checks, while CI remains authoritative for PostgreSQL migrations and integration tests.

---

# Assignment 12 — Coding exercise: provider interface

## Task

Refactor the conceptual design so both persisted and preview data providers could satisfy a Python protocol. You do not need to use this exact abstraction in production; the purpose is to demonstrate dependency inversion.

## Worked solution

```python
from typing import Protocol

from app.api.schemas import (
    FundingCallDetail,
    FundingCallListResponse,
    SourceHealthResponse,
)


class DashboardReadProvider(Protocol):
    async def list_calls(
        self,
        *,
        source_code: str | None,
        limit: int,
        offset: int,
    ) -> FundingCallListResponse: ...

    async def get_call(self, call_id: int) -> FundingCallDetail | None: ...

    async def source_health(self) -> SourceHealthResponse: ...
```

A PostgreSQL-backed implementation could delegate to the read service. A preview implementation could read in-memory fixtures.

Why this exercise matters: it reveals that the browser's true dependency is not PostgreSQL; it is the **read contract**.

---

# Assignment 13 — Debugging exercise: environment leakage

## Scenario

A test expects the production badge `Tallennettu tilannekuva`, but on one Windows machine it receives `Kehitysesikatselu · fixture-data`. CI passes.

## Questions

What is the likely root cause? Why can CI pass? What change makes the test deterministic?

## Worked solution

Likely root cause: the Windows shell contains `DASHBOARD_PREVIEW_MODE=true`, and the imported module-level `app` resolved configuration at import time.

CI may pass because its environment does not set that variable.

The deterministic fix is to construct the application explicitly with `Settings(dashboard_preview_mode=False)` in the normal test and `True` in the preview test.

This is not a Windows-specific Python bug. Windows merely exposed hidden ambient configuration dependence.

---

# Assignment 14 — Mini take-home assignment

## Brief

You are given four hours. Extend VakeVahti with a third dashboard provider called `demo-file` that reads a checked-in JSON fixture while preserving the same read contracts.

Requirements:

- mode must be explicit and disabled by default
- malformed fixture must fail loudly, not become an empty successful result
- list filtering and pagination must match existing semantics
- detail endpoint must return 404 for missing IDs
- source health must use the same response schema
- no database engine should be created in file-preview mode
- add tests for mode selection, malformed JSON, filtering, pagination and 404
- document why this mode must never be confused with production state

## Reference solution architecture

```text
Settings
  |
  +-- normal ------> persisted router -> read service -> PostgreSQL
  |
  +-- preview -----> in-memory fixture router
  |
  +-- demo-file ---> JSON provider -> validated Pydantic models
```

A strong implementation should parse JSON once at startup or provider initialization, validate it with the same Pydantic response/item models, and expose errors clearly.

Do not add provider-specific conditions throughout the browser code. Provider selection belongs at the backend composition boundary.

---

# Interview question bank — recent Milestone 6 work

## Backend / API

### Q: Why use an application factory instead of only a module-level FastAPI app?

**Answer:** An application factory allows runtime dependencies and settings to be injected explicitly. That improves tests, makes resource ownership visible and enables preview/normal composition without mutating global state.

### Q: Why should preview and persisted modes expose the same response schemas?

**Answer:** The frontend should depend on stable application contracts, not infrastructure. Shared schemas catch provider drift and make switching development providers transparent to the consumer.

### Q: Why not put `if preview_mode` checks inside every route?

**Answer:** That spreads infrastructure selection across request logic. Selecting a provider/router at composition time keeps mode choice centralized and routes simpler.

## Data Engineering / Databases

### Q: Why did VakeVahti keep PostgreSQL when the Windows machine could not run it?

**Answer:** Workstation limitations should not redefine system-of-record architecture. PostgreSQL is still required for durable state, history, concurrency and audit behavior. The Windows preview is only a development substitute behind the read contract.

### Q: What is the difference between entity history and current snapshot membership?

**Answer:** Entity history records what has existed and changed. Snapshot membership answers which entities belong to the latest successful source observation. A disappeared call can remain historically stored while no longer being current.

### Q: Why is a successful zero-result scan different from a failed scan?

**Answer:** A successful zero-result scan is authoritative evidence that the current set is empty, so the source snapshot watermark advances. A failed scan provides no authoritative membership result, so the last successful snapshot remains current.

## DevOps / Platform

### Q: What did Docker provide on Linux?

**Answer:** Reproducible PostgreSQL version/configuration, isolation from host software, easy lifecycle commands and a predictable port mapping. It was a development infrastructure choice, not an application requirement.

### Q: Why not bypass workplace restrictions and install a portable database?

**Answer:** Managed workstations have security and governance boundaries. Development convenience does not justify bypassing organizational controls. We instead created a safe preview mode and retained authoritative integration validation in CI/Linux.

## Testing / QA

### Q: What is test pyramid relevance here?

**Answer:** Fast unit tests cover parsers, presentation logic, application configuration and preview behavior. PostgreSQL integration tests cover migrations, persistence semantics and HTTP-to-database behavior. Live source checks are rarer because they are external and less deterministic.

### Q: Why test negative requirements?

**Answer:** Some architectural rules state what must *not* happen, such as the dashboard never invoking `/api/demo/stm-calls`. An explicit absence/regression assertion protects that boundary.

## Frontend

### Q: Why is theme state stored in `localStorage` rather than the database?

**Answer:** Theme is a per-browser presentation preference with no business/audit meaning. Persisting it in the operational database would add unnecessary backend state and coupling.

### Q: Why keep source colors different from the general VAKE brand color?

**Answer:** Brand colors establish product identity while source colors encode information categories. The design system can use VAKE's official palette to do both without turning every component into one undifferentiated color.

## Security

### Q: What is reverse tabnabbing and how is it mitigated?

**Answer:** A page opened with `target="_blank"` can potentially access the opener in some contexts. Using `rel="noopener noreferrer"` prevents the new page from controlling the original window and avoids leaking referrer information where appropriate.

### Q: Why does fixture data need an explicit preview label?

**Answer:** Synthetic data can create an operational integrity risk if employees mistake it for real state. The label makes the trust/status boundary visible in the UI.

---

# Code interview drill

## Question 1

What does this expression do?

```python
normalized_source = source_code.strip().upper() if source_code else None
```

**Answer:** It normalizes a supplied source filter by removing surrounding whitespace and converting it to uppercase; missing input stays `None`. This lets `sitra`, ` SITRA ` and `SITRA` match the same configured source code.

## Question 2

Why is this ordering deterministic?

```python
ORDER BY application_deadline_at ASC NULLS LAST, id ASC
```

**Answer:** Deadline alone can contain duplicates, so pagination could otherwise return unstable ordering among ties. Adding unique `id` as a final tie-breaker produces deterministic page boundaries.

## Question 3

What is wrong with this frontend code for upstream descriptions?

```javascript
container.innerHTML = detail.description_text;
```

**Answer:** It parses external source content as HTML, creating stored-XSS risk. Use `textContent` unless trusted/sanitized HTML is explicitly required.

## Question 4

Why can a SQLAlchemy `SELECT` affect transaction state?

**Answer:** SQLAlchemy sessions use autobegin. A read operation can start a transaction, so attempting a nested explicit `session.begin()` without ending the current transaction can raise an error.

## Question 5

Why use `async_sessionmaker` injection in tests?

**Answer:** It lets the application use an isolated test database/session lifecycle without replacing global engine state. Resource ownership and test boundaries remain explicit.

---

# Portfolio story from this switch

> The workplace Windows machine could not run Docker or a native PostgreSQL service, while the Linux environment and CI used PostgreSQL as the durable source of truth. Instead of changing the production architecture, I introduced an opt-in database-free preview provider behind the same typed read contracts. I made application composition explicit through settings, prevented environment-dependent tests by using the FastAPI application factory with explicit configuration, and kept PostgreSQL migrations/integration tests mandatory in CI. This let frontend work continue safely on a restricted workstation without confusing fixture data with production state.

---

# Self-assessment checklist

Before claiming mastery of this slice, be able to do all of the following without copying the solution:

- explain host port `55432` versus PostgreSQL port `5432`
- distinguish connection refusal from authentication/schema failure
- draw normal and preview request paths
- explain why PostgreSQL remains the source of truth
- write an application-factory test with explicit settings
- write current-snapshot SQL using source watermarks
- explain failed scan versus successful empty scan
- implement and test `scanStatusLabel`
- implement persistent light/dark mode
- explain `textContent` versus `innerHTML`
- explain which tests can run on the restricted Windows machine and which require PostgreSQL
- give the portfolio story in under 90 seconds
