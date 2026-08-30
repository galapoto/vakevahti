# Milestone 4 lesson: configurable source registry

## Engineering lesson

Orchestration should depend on an adapter contract, not concrete source classes.

The worker no longer needs to be permanently hard-coded to `STMScanner`. A source registry maps configured source codes to factories that return the shared `FundingSourceAdapter` protocol. `ENABLED_SOURCES` is normalized and de-duplicated before adapters are created.

This keeps source-specific parsing inside each adapter while letting the worker and ingestion service remain source-independent. It also prevents accidentally scheduling the same source twice because configuration used duplicate or differently cased source codes.

## Interview questions and strong answers

### Why use a source registry instead of importing every scanner directly in the worker?

> A registry makes orchestration depend on a stable adapter contract rather than concrete implementations. The worker asks for configured funding-source adapters and treats them uniformly. Adding Sitra or Suomen Akatemia therefore changes registration and source-specific extraction, not the downstream ingestion, persistence or audit pipeline.

### Why normalize and de-duplicate configured source codes?

> Configuration is external input and should be validated before it affects execution. Normalizing case avoids accidental mismatches, while de-duplication prevents the same logical source from being scanned twice in one interval, which would create unnecessary load and confusing operational audit records.

### If one source fails, should all other scheduled sources stop?

> No. Source failures should be isolated where possible. The multi-source worker attempts each configured source independently so one broken website does not prevent healthy sources from being monitored. In one-shot mode it still returns an unhealthy process result after all sources are attempted, allowing an external scheduler to detect partial failure while preserving successful source transactions and audit records.
