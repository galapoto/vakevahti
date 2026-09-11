# Report save workflow

The employee dashboard can persist a funding-report draft only when a safe write API is available.

- In `DASHBOARD_PREVIEW_MODE=true`, `/api/reports` uses synthetic in-memory preview storage and can be tested publicly without touching PostgreSQL.
- In persisted mode, report writes require `ENABLE_REPORT_WRITE_ROUTES=true` and the configured PostgreSQL database.
- The dashboard exposes `Tallenna luonnos` only when one of those safe write paths exists.
- `Merkitse hyväksyntää varten` saves dirty changes first and then moves the saved report to `WAITING_APPROVAL` through `/api/reports/{id}/submit`.
- The UI never claims that an email or Teams message was sent. Delivery is a separate platform transport concern.
