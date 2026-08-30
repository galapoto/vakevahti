# 2026-08-30: Milestone 4 source-registry foundation

## Changes

- added configurable funding-source registry
- added `ENABLED_SOURCES` runtime configuration
- normalized and de-duplicated configured source codes
- refactored worker to execute configured adapters through the shared ingestion service
- preserved per-source failure isolation in loop mode
- one-shot mode attempts all configured sources, then reports partial failure through `ExceptionGroup`
- added unit coverage for registry configuration and unknown source handling

## Next

Implement Sitra and Suomen Akatemia adapters with fixture-based parser tests, then register them without changing downstream persistence/audit code.
