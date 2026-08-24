# ADR 0001: Build VakeVahti in thin vertical slices

- Status: Accepted
- Date: 2026-08-24

## Context

VakeVahti has a broad Version 1 scope: five external funding sources, persistence, relevance rules, monitoring, notifications, dashboard, human review, reporting, approval, PDF generation, authentication, and audit history.

Building every layer before proving any one end-to-end path would create significant integration risk and would make the project harder to learn, test, and explain.

## Decision

Build the application in thin, production-oriented vertical slices.

The first slice is:

`STM website -> HTTP -> HTML parsing -> FundingCallCandidate validation -> terminal output`

The following slice will add:

`FundingCallCandidate -> PostgreSQL -> baseline/deduplication -> NEW/UNCHANGED/CHANGED`

Later slices add notifications, additional sources, API/UI, review, and reporting.

## Alternatives considered

### Build database, frontend, authentication, scheduler, and all source adapters first

Rejected because it delays business feedback and creates too many simultaneous failure points.

### Build a throwaway scraper script

Rejected because the first implementation should already use the canonical domain model, tests, configuration, and source-adapter boundary that the production system will keep.

## Consequences

Positive:

- business value arrives earlier;
- failures are isolated;
- each milestone is testable;
- learning is attached to real implementation;
- interview stories map to genuine engineering decisions;
- later infrastructure is built around proven data flows.

Trade-off:

- some architecture is introduced incrementally rather than appearing complete immediately;
- temporary CLI entry points may exist before the final web workflow is available.
