# Automatic funding reports

VakeVahti composes one report automatically after each successful scan cycle when `AUTOMATIC_REPORT_ENABLED=true` (default).

The report is built only from durable notification events created by the cycle. This means:

- baseline scans do not create reports;
- unchanged calls do not create reports;
- `NOT_RELEVANT` calls do not create reports;
- new, changed and review-required findings become report items.

Each cycle receives a deterministic `automation_key` derived from the scan-run IDs. Reprocessing the same cycle therefore returns the existing report instead of creating a duplicate.

The report title, email subject and email body are composed from the actual findings. A single finding names the source and funding call directly. Multiple findings summarize their actual sources and include each title, deadline, VakeHyvä relevance reason and source link.

Configured recipients come from `REPORT_EMAIL_RECIPIENTS` as a comma- or semicolon-separated list. This setting prepares the report for email delivery; transport credentials and durable delivery are handled by the email-delivery layer.

Generated reports remain editable. `PATCH /api/reports/{report_id}` can change the title, notes, email subject, email body and recipients. Editing a report that was waiting for approval automatically returns it to `DRAFT`, so modified content is never presented as previously approved.
