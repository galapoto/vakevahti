# ADR 0003: Keep VakeVahti standalone but Vaketomate-extraction-ready

- Status: Accepted
- Date: 2026-08-30

## Context

The work trial will produce several automation products that will later live under the Vaketomate umbrella. At the same time, an individual product such as VakeVahti may grow into a large funding/application/project-lifecycle system and may eventually need independent deployment, scaling or ownership.

Prematurely merging every product's internals into one shared code/data model would make later extraction expensive. Premature microservices would add deployment and operational complexity that the current team and scale do not justify.

## Decision

Continue building VakeVahti as an independently runnable bounded product.

When VakeVahti joins Vaketomate:

- Vaketomate may provide the application shell and shared platform capabilities.
- VakeVahti retains ownership of funding-domain rules and funding-owned data.
- Cross-product capabilities are consumed through published contracts.
- No product may directly update another product's internal database tables.
- API/event contracts are versioned and remain stable across deployment changes.
- Identity, audit aggregation, notifications, scheduling and generic project management may move to shared Vaketomate services without moving funding business logic out of VakeVahti.

## Consequences

- VakeVahti can move under Vaketomate without a funding-domain rewrite.
- A future large Funding platform can be extracted into its own deployment/database while preserving contracts.
- Some interface/ownership discipline is required even while everything is deployed together.
- Shared code is not created merely because two modules have similar implementation details; it must represent a genuinely shared capability.
- Integration tests and documentation must preserve boundary behavior, not only internal implementation.
