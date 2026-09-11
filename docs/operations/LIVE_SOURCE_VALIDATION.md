# Live funding-source validation

Status: operational validation gate for Milestone 7

## Purpose

Automated unit/integration tests stay deterministic and must not depend on public-site uptime. Before merging source-adapter changes, an operator should nevertheless run the current public sources end to end and inspect both parser health and relevance distributions.

The generic CLI commands below use the same registered adapters as the worker. `scan-source` performs a dry run and does **not** write PostgreSQL. `scan-source-persist` uses the normal audited ingestion path.

## Dry-run validation

From `backend/` on Windows:

```powershell
.\.venv\Scripts\python.exe -m app.cli scan-source HAEAVUSTUKSIA
.\.venv\Scripts\python.exe -m app.cli scan-source EURA
```

Linux/macOS:

```bash
python -m app.cli scan-source HAEAVUSTUKSIA
python -m app.cli scan-source EURA
```

The output includes:

- discovered-call count
- `RELEVANT`, `NEEDS_REVIEW`, and `NOT_RELEVANT` distribution
- each title and persisted-style relevance reason

Treat these as review gates rather than success-by-count. A sudden all-zero result, a large `NEEDS_REVIEW` spike, or implausibly broad `RELEVANT` output should be investigated before persistence.

## GitHub Actions manual smoke

`.github/workflows/live-source-smoke.yml` provides an **on-demand only** live validation job. It deliberately does not run on every pull request because public-site uptime and rendering must not make deterministic CI flaky.

From GitHub Actions, run **Live Funding Source Smoke** manually. The workflow:

1. installs the backend and Playwright Chromium fallback;
2. executes real dry-run scans for Haeavustuksia.fi and EURA 2021;
3. fails if either adapter fails structurally/network-wise;
4. uploads both CLI outputs as a 14-day workflow artifact for review evidence.

The artifact should be reviewed for relevance distribution and obvious false positives/false negatives before the live-validation checkbox is marked complete.

## Current live-shape observations (2026-09-11)

Haeavustuksia.fi still exposes stable `/fi/haku/<id>` call roots and semantic `Myöntöperusteet` pages. A current page uses the heading `Kenelle/mille avustusta voidaan myöntää` and generic wording such as `oikeuskelpoiset yhteisöt ja säätiöt`; generic legal-entity wording intentionally remains `NEEDS_REVIEW` unless a VakeHyvä-approved public-entity expression is present.

Example source:

- https://www.haeavustuksia.fi/fi/haku/va-okm-2026-15/hakuilmoitus/myontoperusteet

EURA 2021 still exposes stable `/hakuilmoitukset/hakuilmoitus/<uuid>` notices with `Alkaa`, `Päättyy`, `Haun kohdealue`, `Maakunnat`, and `Hankehaun kuvaus` semantics. Current notices use normal Finnish inflection such as `julkisoikeudelliset yhteisöt` and `julkisoikeudelliselle yhteisölle`; the shared eligibility matcher therefore matches approved public-entity concepts by bounded Finnish stems instead of one literal grammatical form.

The matcher also requires applicant context and rejects explicit negative clauses. A phrase such as `yhteistyössä hyvinvointialueiden kanssa` is not enough to prove applicant eligibility, and `ei voida myöntää hyvinvointialueille` cannot become a positive match.

Example sources:

- https://eura2021.fi/hakuilmoitukset/hakuilmoitus/54727044-9922-4095-af2d-66c54adf8f63
- https://eura2021.fi/hakuilmoitukset/hakuilmoitus/4b943b71-c613-4571-a26c-547e1e3157ba/

## Persisted repeat-scan proof

After a dry run looks credible and PostgreSQL migrations are applied:

```powershell
.\.venv\Scripts\python.exe -m app.cli scan-source-persist HAEAVUSTUKSIA
.\.venv\Scripts\python.exe -m app.cli scan-source-persist HAEAVUSTUKSIA
.\.venv\Scripts\python.exe -m app.cli scan-source-persist EURA
.\.venv\Scripts\python.exe -m app.cli scan-source-persist EURA
```

On an unchanged source, the second run should report `new=0` and `changed=0`; previously persisted calls should be `UNCHANGED` internally and no extra funding-call version or notification intent should be created. Every attempt still gets its own `source_scan_runs` audit row.

The PostgreSQL integration suite contains a deterministic repeated-ingestion proof for this invariant. The live repetition is still required before merge because it additionally validates stable source identity and current public-site structure.

## Browser fallback

Both Haeavustuksia.fi and EURA use HTTP-first discovery. If the normal representation does not expose call links, the adapters can fall back to Playwright Chromium. Install Chromium in environments that need that fallback:

```powershell
.\.venv\Scripts\playwright.exe install chromium
```

or:

```bash
./.venv/bin/playwright install chromium
```

Ordinary CI intentionally does not contact the public funding sites or launch Chromium; live availability must not make the deterministic quality gate flaky.
