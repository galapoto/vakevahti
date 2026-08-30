# Multi-source funding registry

VakeVahti keeps source-specific extraction behind the `FundingSourceAdapter` contract.

```text
ENABLED_SOURCES
      |
      v
source registry
      |
      +--> STM adapter
      +--> Sitra adapter (next)
      +--> Suomen Akatemia adapter (next)
      |
      v
run_source_ingestion
      |
      +--> scan audit
      +--> PostgreSQL persistence
      +--> NEW / UNCHANGED / CHANGED
```

The worker must not contain source-specific parsing. Adding a source means implementing the adapter contract and registering its factory. Downstream services stay unchanged.
