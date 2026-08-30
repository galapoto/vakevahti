# ADR 0005: Configurable funding-source registry

- Status: Accepted
- Date: 2026-08-30

## Context

VakeVahti began with one STM adapter. Milestone 4 adds more funding sources while the existing ingestion, persistence, audit and scheduling path should remain source-independent.

## Decision

Introduce a small source registry that maps configured source codes to factories returning the `FundingSourceAdapter` contract. Runtime configuration supplies `ENABLED_SOURCES`; codes are normalized and de-duplicated before scanners are instantiated.

The worker iterates registered adapters and invokes the same `run_source_ingestion` application service for every source. Source-specific parsing stays inside source adapters.

## Consequences

- adding a new source does not require duplicating orchestration or persistence logic
- configuration can enable or disable adapters without changing worker code
- unknown source codes fail at startup instead of being silently ignored
- one unhealthy source can be isolated from healthy sources
- the registry remains deliberately small; if source discovery becomes dynamic later it can evolve without changing the adapter contract
