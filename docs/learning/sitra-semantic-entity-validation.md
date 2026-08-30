# Sitra semantic entity validation: idempotent wrong data is still wrong

Date: 2026-08-30

Status: regression fix implemented; live revalidation required before PR #8 can be merged.

## What the live test revealed

After the Power Pages browser fallback was introduced, two consecutive live Sitra scans succeeded operationally:

- first run: `baseline=True`, `new=1`
- second run: `baseline=False`, `unchanged=1`

The multi-source worker then repeated STM, Sitra and Suomen Akatemia twice without duplication, and the full local quality suite passed with 27 tests.

However, inspecting the persisted Sitra row exposed a semantic defect:

- stored title: `Rahoitushaut`
- stored URL: `https://asiointi.sitra.fi/`
- stored deadline: the deadline of one nested call

`Rahoitushaut` is the section heading, not an individual funding opportunity. The rendered public page contains individual `h3` funding-card headings beneath that section.

This means the pipeline was transport-correct and idempotent, but entity extraction was wrong.

## Root cause

The parser originally iterated headings and collected following sibling text. In the rendered Power Pages DOM, the broad `h2 Rahoitushaut` section could see the text of all nested cards, including lifecycle markers such as `Haku käynnissä`.

At the same time, an individual call heading can be wrapped inside an anchor while its lifecycle marker lives in a sibling element. Looking only at direct siblings of the heading therefore failed to associate the individual `h3` with its status.

The result was a false semantic match:

`section heading -> nested card statuses -> emitted as one funding call`

## Fix

The Sitra parser now works in the opposite direction:

1. locate lifecycle text such as `Haku käynnissä` or `Haku sulkeutunut`
2. walk upward from that lifecycle marker
3. select the nearest container that contains exactly one individual funding-card heading (`h3`-`h6`)
4. use that heading as the call title
5. prefer a link that owns/wraps that heading for source identity
6. fall back to the source root plus title identity only when no call-specific link is available
7. recognize closed calls but emit only open calls

A regression fixture contains an `h2 Rahoitushaut` around multiple nested cards and proves that the section heading is never emitted.

## Data Engineering lesson: idempotency is necessary but not sufficient

Idempotency answers: "If I process the same logical input again, do I avoid creating a second copy or an unintended new version?"

It does not answer: "Did I identify the correct logical entity in the first place?"

The first live Sitra implementation was perfectly repeatable but repeatably wrong. Data quality gates therefore need multiple independent dimensions:

- acquisition correctness
- entity identification
- field-level semantic correctness
- provenance
- identity stability
- idempotency
- persistence invariants
- operational auditability

### Data Engineering interview question

**The pipeline was idempotent. Why was it still incorrect?**

> Idempotency only guarantees convergence when the same logical record is processed repeatedly. In the Sitra incident, the extractor chose the wrong logical record: a section heading instead of an individual funding call. The pipeline then persisted that wrong entity consistently. I learned to validate semantic identity separately from duplicate prevention by inspecting titles, canonical URLs, counts and source evidence against the authoritative source.

## Backend Engineering lesson: parse from the strongest semantic anchor

The lifecycle marker is closer to the business meaning of an individual Sitra card than a broad ancestor heading. Starting from the lifecycle marker and finding its nearest single-card heading reduces accidental scope expansion.

### Backend interview question

**Why did you reverse the parser from heading-first to lifecycle-first?**

> The heading-first traversal allowed a broad section heading to absorb text from multiple nested cards. The lifecycle label belongs to one call, so I use it as the semantic anchor and walk to the nearest container with one call heading. This narrows the extraction scope and makes the DOM relationship match the business relationship.

### Technical question

**Why require exactly one call heading in the selected container?**

> It is a structural guard against selecting a parent container that represents a list of calls. If an ancestor contains several candidate headings, it is too broad to represent one logical funding record. Requiring one heading makes ambiguous containers ineligible rather than guessing.

## Testing lesson: assertions must validate meaning, not only counts

The first live validation checked:

- worker success
- baseline behavior
- repeat `UNCHANGED`
- no duplicates
- audit rows

Those checks all passed. The persisted-row inspection caught what they could not.

The regression suite now explicitly asserts:

- the section heading `Rahoitushaut` is not emitted
- nested individual cards are emitted separately
- closed cards are recognized but excluded
- card-specific links are associated with their own titles

### QA interview question

**What test would have prevented this defect earlier?**

> A representative nested-card fixture containing the real semantic hierarchy: a section-level `h2`, multiple anchor-wrapped `h3` call titles, and lifecycle status in sibling descendants. The earlier fixtures were too flat, so they verified the algorithm we expected rather than the structure the source actually rendered.

## System Design lesson: operational success is not business success

A source run can be technically `SUCCEEDED` because retrieval, parsing and persistence completed without exceptions, yet still produce semantically invalid data.

Future source-health work should distinguish at least:

- transport health
- parser/structure health
- semantic/data-quality health
- persistence health

Not every semantic validation should become a hardcoded rule, but high-value invariants should be checked where they are stable and source-owned.

### System Design interview question

**Would you change `source_scan_runs` from SUCCEEDED to FAILED for this historical run?**

> I would not rewrite historical audit facts after the fact. At execution time the software completed according to its then-current contract, so the audit row accurately records what the system believed. I would record the defect and correction, improve semantic validation, and if needed introduce a future quality status or incident linkage rather than mutating operational history.

## Data correction consideration

The incorrect baseline row already exists in the developer runtime database. The next live validation must not simply accept that row as legitimate history.

Because this is a development database and the record was created by a known parser defect, the validation procedure should remove only the affected Sitra test/runtime state in a controlled way before establishing the corrected Sitra baseline. Do not delete STM or Academy state, and do not use ad hoc schema recreation.

Production data correction would require an explicit audited repair/migration procedure rather than casual deletion.

### Database interview question

**Why not just let the corrected scan turn the old `Rahoitushaut` row into CHANGED?**

> The old row and the real funding cards are not different versions of the same logical entity. Treating them as versions would preserve a false identity relationship. In a development environment I prefer a narrowly scoped cleanup of the known-invalid Sitra state, then rebuild the baseline from the corrected parser. In production I would use an explicit audited data-repair process.

## Current merge gate

PR #8 remains draft until all of the following are true:

1. CI passes the lifecycle-to-card parser regression.
2. The known-invalid Sitra developer data is cleaned in a source-scoped manner.
3. A fresh live Sitra baseline emits individual call titles, not `Rahoitushaut`.
4. The emitted count and lifecycle state are checked against the rendered official page.
5. A second Sitra run is `UNCHANGED` for those same logical calls.
6. `STM,SITRA,ACADEMY` is run twice successfully.
7. Ruff, strict mypy and full PostgreSQL pytest remain green.
8. The PR description is updated with the final live evidence before marking it ready.
