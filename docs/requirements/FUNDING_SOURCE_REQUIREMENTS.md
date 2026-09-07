# VakeVahti funding-source requirements

Status: authoritative stakeholder requirements baseline

Date captured: 2026-09-07

## Purpose

VakeVahti / the Vaketomate Funding module exists so the wellbeing area does not need to manually inspect funding websites every week. The system must monitor the required public sources and surface or notify when a new relevant funding opportunity appears.

The authoritative source set contains five source families:

1. STM
2. Haeavustuksia.fi
3. EURA 2021
4. Sitra
5. Suomen Akatemia

The production target is complete coverage of all five. A source is not considered covered merely because it is displayed in the UI; it must have a tested ingestion/relevance path and operational source-health evidence.

## 1. STM

Source:

`https://stm.fi/vuoden-2026-valtionavustushaut`

Business rule:

- every new funding call published on this page is relevant;
- one funding call corresponds to one blue-background heading/call entity on the page;
- no additional eligibility filtering is required before the opportunity is considered relevant.

Engineering rule:

- semantic entity identity must be based on the funding-call heading/entity, not visual color alone;
- preserve source URL/evidence;
- fail loudly if the expected call structure changes.

## 2. Haeavustuksia.fi

Source:

`https://www.haeavustuksia.fi/fi/?isAdditionalSearchOpen=true`

Business rule:

The site contains many grants unrelated to the wellbeing area. A call is relevant only when the wellbeing area is an eligible applicant.

The eligibility evidence is found by opening the call, then inspecting `Myöntöperusteet`, especially the section:

`Kenelle/mille avustusta voidaan myöntää`

Positive applicant terms supplied by the stakeholder include:

- `hyvinvointialue`
- `Julkisoikeudellinen yhteisö`
- `Julkinen toimija`
- `Julkinen organisaatio`
- `Julkisyhteisö`
- `Julkinen oikeushenkilö`
- `Valtionavustuskelpoinen julkisoikeudellinen toimija`

Engineering rule:

- discover current/upcoming grant notices from Haeavustuksia;
- use a stable source-specific call identifier from the canonical `/fi/haku/<id>` URL when available;
- fetch the individual call/detail content;
- isolate eligibility evidence from the correct Myöntöperusteet section rather than searching unrelated page text blindly;
- normalize case/whitespace and evaluate the positive applicant vocabulary deterministically;
- retain the matched text as provenance/evidence;
- calls with clear positive evidence are `RELEVANT`;
- calls with clear exclusionary applicant evidence may be `NOT_RELEVANT` only when the rule is defensible from evidence;
- structurally valid but ambiguous eligibility must be `NEEDS_REVIEW`, not silently discarded;
- source-structure drift must fail loudly rather than becoming an empty successful scan.

## 3. EURA 2021

Source:

`https://eura2021.fi/hakuilmoitukset`

Business rule:

First apply region scope. Only these calls enter the wellbeing-area eligibility evaluation:

- `Valtakunnallinen`
- `Etelä-Suomi`

The site also contains many calls for unrelated sectors. A regional match is not sufficient: the wellbeing area must be able to participate/apply.

Applicant eligibility can appear in different parts of the notice, including:

- the call description (`Hankehaun kuvaus`);
- additional information (`Lisätiedot`);
- other call text where the applicant rule is stated.

Engineering rule:

- discover individual notice URLs under `/hakuilmoitukset/hakuilmoitus/<uuid>`;
- use the notice UUID / stable notice identity as the external key when available;
- parse `Haun kohdealue` deterministically;
- reject out-of-scope regions before expensive eligibility evaluation;
- preserve the region text as evidence;
- extract applicant-eligibility evidence from the relevant descriptive/additional-information sections;
- deterministic positive wellbeing-area/public-entity evidence may classify the call as `RELEVANT`;
- ambiguous regional calls must become `NEEDS_REVIEW` rather than being dropped;
- do not use an LLM to invent applicant eligibility that is not supported by the notice;
- if an LLM/semantic classifier is introduced later, it must operate as evidence-backed enrichment with explicit confidence/review behavior, not as the only source of truth.

## 4. Sitra

Source:

`https://www.sitra.fi/hae-rahoitusta/`

Business rule:

- every new funding announcement on the funding page is relevant;
- notify when a new announcement is published.

Engineering rule:

- all current/open Sitra funding entities are relevant;
- retain lifecycle status and source evidence;
- HTTP-first acquisition, rendered-browser fallback only when the public Power Pages/app surface requires it;
- a page heading/section label must never be persisted as a funding opportunity.

## 5. Suomen Akatemia

Source:

`https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/`

Business rule:

- every new call appearing on the page is relevant.

Engineering rule:

- all open/upcoming calls are relevant;
- do not invent a clock time for a date-only deadline;
- preserve whether a call is open/upcoming/preparation where the source exposes that distinction;
- structure changes must fail loudly.

## 6. Notification outcome

The stakeholder objective is that weekly manual monitoring is no longer necessary.

Target behavior:

`scheduled scan -> discover -> normalize -> validate -> classify -> persist -> detect NEW -> notification outbox -> approved transport/email`

Important rules:

- first baseline must not create a flood of historical "new" notifications;
- repeated scans must be idempotent;
- a previously seen call must not generate duplicate new-call notifications;
- a disappeared/reappeared call must follow explicit lifecycle semantics;
- notification delivery failures must not lose the underlying discovered event;
- notification transport belongs behind a Vaketomate/platform contract when integrated.

## 7. Data-engineering model

Primary operational grains:

- `funding_calls`: one row per logical source-specific funding opportunity;
- `funding_call_versions`: one row per immutable material content version of a funding opportunity;
- `source_states`: one row per configured funding source;
- `source_scan_runs`: one row per ingestion attempt;
- future eligibility/review facts may require their own explicit grain rather than being hidden in free text if review workflow becomes first-class;
- future notification outbox: one row per intended deduplicated notification event/delivery target according to the final outbox model.

Identity:

- `(source_code, external_key)` is the logical source identity boundary;
- Haeavustuksia should prefer the stable call identifier from the canonical call URL;
- EURA should prefer the notice UUID/stable notice identifier;
- title text alone must not be the primary identity when a stronger stable identifier exists.

Lineage:

Every relevance decision must retain enough evidence to answer:

- which source produced this call?;
- which URL/section supplied applicant eligibility?;
- which regional rule matched?;
- which positive eligibility phrase matched?;
- when was it observed?;
- was the decision deterministic, manual or later AI-assisted?;
- can an operator reproduce the decision from the public source?

## 8. Definition of complete source coverage

A source is complete only when all are true:

- adapter registered and configurable;
- discovery implemented;
- detail extraction implemented where required;
- stable external identity defined;
- relevance/eligibility rule implemented;
- evidence/provenance stored;
- parser fixtures exist;
- unit tests cover positive, negative, ambiguous and structure-drift cases as applicable;
- PostgreSQL integration path works;
- repeated scan is idempotent;
- successful empty snapshot semantics are correct;
- source health is visible;
- live smoke validation has been performed and documented;
- notification semantics are compatible with NEW detection/outbox behavior.

## 9. Vaketomate product status

VakeVahti is the Funding domain/module inside Vaketomate, not an unrelated side application.

The user experience may be one Vaketomate product shell, while Funding retains explicit domain ownership over:

- funding sources;
- normalized opportunities;
- eligibility/relevance evidence;
- source scan state/history;
- funding-call versions;
- future funding application/review lifecycle.

Cross-domain integration must happen through published APIs/events/contracts, never by another Vaketomate module directly editing Funding tables.
