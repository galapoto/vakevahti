# Milestone 6: interactive dashboard card design

Date: 2026-08-30

Status: implemented on the Milestone 6 dashboard branch; live visual validation pending.

## Why the first operational dashboard needed another interaction pass

The first PostgreSQL-driven dashboard correctly showed persisted multi-source state, but much of the page still behaved like a static report. The operator could inspect opportunity rows and use the source select, but the KPI and source cards did not themselves help the user move through the information.

The interaction pass turns each visual card into a meaningful navigation or action surface without making every click perform the same kind of action.

## Interaction contract

### KPI cards

Each KPI card is a real button with one dashboard-level action:

- **Nykyiset rahoitushaut** clears the source filter and moves to the complete opportunity list.
- **Terveet lähteet** moves to the source-health area and highlights healthy source cards.
- **Huomiota vaativat lähteet** moves to the source-health area and highlights non-healthy cards.
- **Viimeisin onnistunut lähdeajo** moves to source health and highlights the source with the latest successful scan timestamp.

The global current-call KPI is deliberately independent of the source filter. A filter may reduce the visible list to 9, 1 or 7 rows, but the system-level KPI continues to describe the complete current state. The filtered count is shown in the opportunity toolbar instead.

### Source cards

Each source card has two explicit meanings and therefore two explicit controls:

1. the main card button filters the opportunity list to that source;
2. a separately labelled `Avaa lähde` link opens the source's public funding listing page.

The whole card is not made into a single external link. That would make the primary dashboard interaction unexpectedly navigate away from VakeVahti.

### Funding-call rows

Each current funding-call row has two explicit actions:

1. the main row button expands persisted VakeVahti details;
2. a separately labelled `Avaa lähde` link opens that funding record's persisted `source_url` provenance link.

The browser does not reconstruct call URLs from titles or source codes. The call-level link comes from the persisted API record so the serving layer remains aligned with the ingestion/provenance model.

## Color system

Color now communicates persistent source/category identity and operational meaning instead of being decoration only.

- STM uses a blue source identity.
- Sitra uses a purple source identity.
- Suomen Akatemia uses an amber source identity.
- Healthy operational state uses green.
- Attention/error state uses amber/red semantics.
- The latest-run KPI uses purple as a distinct navigation category.

Color is a secondary cue. Source names, health labels, counts and action labels remain visible so meaning is not dependent on color perception.

## Frontend lesson: card interaction should match information architecture

A card is not automatically a link. The right interaction depends on what the card represents.

A KPI summarizes a system-level fact, so clicking it should navigate to the evidence behind that fact. A source card represents both an internal filterable entity and an external source, so those actions must remain distinct. An opportunity row represents an internal persisted record and external provenance, so expansion and external navigation are separate.

### Frontend interview question: Why not make every card a single clickable `<a>` element?

> Different cards represent different actions. A source card needs both an internal filtering action and an external public-source action. Making the whole card an external link would surprise users and make nested interactive controls invalid or awkward. I used explicit native buttons for in-app actions and explicit anchors for navigation, so the semantics, keyboard behavior and user expectations remain clear.

## Data Engineering lesson: global KPI versus filtered read model

The initial dashboard implementation updated the headline current-call KPI from `state.calls.length`. That meant selecting Sitra could make the system KPI change from 17 to 1 even though the underlying system still contained 17 current calls.

The interaction pass separates:

- global current-state count, derived from persisted per-source health/current counts;
- filtered list count, derived from the active `/api/funding-calls?source_code=...` response.

### Data Engineering interview question: Why separate a KPI from the currently filtered list count?

> They answer different questions. The global KPI describes the complete authoritative current snapshot across configured sources. The list count describes the active user query. If the same number changes meaning when a filter is applied, the dashboard becomes misleading. I therefore keep system state and query-result state as separate UI values.

## Provenance and link ownership

Source summary cards use known canonical public listing pages for their source. Funding-call rows use the `source_url` returned by the persisted API record.

This preserves an important ownership rule:

- source-level navigation may be configured from the source registry/UI metadata;
- entity-level provenance belongs to the ingested/persisted record.

### Backend/Data interview question: Why not rebuild the call URL in JavaScript?

> The ingestion layer is the component that understands source structure and canonical identity. Reconstructing URLs in the frontend would duplicate source-specific logic and could drift from what was actually observed. The UI consumes the persisted provenance URL instead.

## Accessibility lesson: avoid nested and ambiguous interactive controls

The implementation uses native controls:

- KPI: `<button>`
- source filter surface: `<button>`
- external source navigation: `<a>`
- funding detail expansion: `<button aria-expanded aria-controls>`
- funding provenance navigation: `<a>`

The implementation avoids putting an `<a>` inside a `<button>` or making a generic `<div>` keyboard-clickable.

Focus-visible states are present, touch targets are enlarged on narrow screens, and reduced-motion preferences disable nonessential animation.

### Accessibility interview question: Why is a clickable `div` weaker than a native button here?

> A native button already has keyboard activation, focus behavior, accessibility semantics and disabled-state behavior. A clickable div requires recreating those contracts manually and is easy to get wrong. I use native controls whenever the interaction matches a native semantic element.

## Security lesson: direct links are still bounded navigation

External links use `target="_blank"` together with `rel="noopener noreferrer"`.

Source-controlled text continues to be inserted through DOM `textContent`, not HTML interpolation.

The interaction pass does not turn source URLs into browser fetch targets inside VakeVahti; they remain explicit user-initiated navigation.

## Testing lesson

A new dashboard contract test protects the interaction surface in addition to the existing no-live-scrape contract.

The test checks for:

- all four KPI action controls;
- the source-aware interaction functions;
- STM/Sitra/Academy source identities;
- the canonical source listing destinations;
- the direct funding-row source-link contract;
- `aria-controls` detail-expansion semantics.

Normal CI still does not make requests to public funding websites.

### QA interview question: Why test static interaction markers if browser E2E tests do not yet exist?

> It is not a replacement for browser E2E testing, but it protects important architectural and semantic contracts while the frontend remains dependency-light. It catches accidental removal of required actions, source destinations or accessibility attributes. Live browser validation then complements it with actual interaction and visual checks.

## Portfolio story

> I converted a static operational dashboard into an action-oriented interface without coupling the frontend back to live scraping. KPI cards navigate to the evidence behind their values, source cards separately support in-app filtering and external source navigation, and each funding row separates persisted detail expansion from provenance navigation. I also corrected the state model so the global KPI remains global while filtered result counts remain query-specific. The design uses native controls, source-specific color identities, persisted entity URLs and regression tests for the interaction contract.
