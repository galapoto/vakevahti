# 2026-09-15 — VAKE dashboard branding and roadmap refresh

## Context

The repository `main` branch had advanced through automatic funding-case starter drafts, while the dashboard still contained an older pure-red base theme and a hand-built logo under newer VAKE theme overrides. The README roadmap also still listed several milestones that had already been merged.

## Implementation

- Replaced the hand-built dashboard logo treatment with the official public VAKE pixel-heart asset from the VAKE/STT media bank. The embedded crop is 3x the displayed size so it remains crisp on high-DPI screens.
- Removed the legacy pure-red base brand colors and aligned the base layer with the canonical VAKE palette.
- Promoted the relevance explanation into the visible funding section heading: `Miksi nämä rahoitushaut sopivat VakeHyvälle`.
- Strengthened each funding card's `Miksi tämä sopii VakeHyvälle` / `Miksi tämä vaatii tarkistuksen` explanation.
- Preserved case-insensitive source-run localization and added a regression fixture using lowercase `succeeded`, matching the observed operator-UI defect.
- Refreshed the README so completed source/read/outbox/case work is no longer described as future work.

## Verification evidence

- Focused dashboard/brand regression suite: 14 tests passed before the high-DPI asset swap; 6 focused brand/theme tests passed after the asset swap.
- Repository quality gate: Ruff passed; strict mypy passed across 64 source files; Alembic upgraded the separate test database; full PostgreSQL-backed pytest passed with 120 tests.
- Browser acceptance check against preview mode:
  - preview API returned lowercase `succeeded`;
  - zero raw `succeeded` strings were visible;
  - all five source cards showed `Viimeisen ajon tila Onnistunut`;
  - computed `--brand` was `#312783`;
  - the logo pseudo-element used an embedded PNG data URI; and
  - the funding list exposed the new `Miksi nämä rahoitushaut sopivat VakeHyvälle` heading.

The only test warning observed was the existing Starlette/httpx TestClient deprecation warning; it is unrelated to this change.

## Why this matters professionally

The important engineering lesson is that visual regressions often come from layered ownership rather than one wrong CSS value. The base dashboard, customization layer and theme layer were all styling the same brand elements. Removing obsolete base assumptions reduces the chance that a later injection order exposes an old color or logo.

For interviews, this change is a small example of regression-driven frontend maintenance: reproduce the exact bad input (`succeeded`), make the normalization behavior observable in a browser, add anti-regression tests, and keep the change isolated from the funding-domain logic.

## Next implementation slice

The next domain feature should be the real coordinator approval decision/audit flow. `FundingReportStatus` currently stops at `DRAFT` and `WAITING_APPROVAL`; the production workflow still needs explicit approve/reject/return-for-edit decisions tied to authenticated actor context before approval can be considered complete.
