"""VAKE-specific presentation refinements for the employee funding dashboard.

The operational dashboard is shared from the Milestone 6 branch. This module keeps
Milestone 7 source integration and VAKE visual refinements explicit and fail-loudly:
if the shared dashboard structure changes, a missing sentinel raises instead of
silently serving a partially customized page.
"""

from __future__ import annotations


_STYLE_OVERRIDES = r"""
<style id="vake-m7-overrides">
  :root {
    --brand: #312783;
    --brand-strong: #312783;
    --brand-soft: #f1f0f8;
    --brand-faint: #faf9fe;
    --good: #1FB578;
    --good-soft: #edf9f4;
    --danger: #D90066;
    --danger-soft: #fff0f7;
    --blue: #28738A;
    --blue-soft: #edf7fa;
    --purple: #6E67A8;
    --purple-soft: #f3f2f9;
    --amber: #B59525;
    --amber-soft: #fbf7e9;
  }

  body {
    background:
      radial-gradient(circle at 14% 0%, rgba(49, 39, 131, .065), transparent 28rem),
      radial-gradient(circle at 92% 8%, rgba(230, 0, 126, .045), transparent 26rem),
      var(--bg);
  }

  .logo {
    border-radius: 15px;
    background: #312783;
    box-shadow: 0 10px 24px rgba(49, 39, 131, .20);
  }

  .logo svg > rect { fill: #312783 !important; }
  .logo svg g { filter: none !important; }
  .logo svg g rect:last-child { fill: #E6007E; }

  .system-chip {
    border-color: #d8d5ea;
    background: #f8f7fc;
    color: #312783;
  }

  .system-chip::before {
    background: #E6007E;
    box-shadow: 0 0 0 4px rgba(230, 0, 126, .08);
  }

  .hero {
    border-color: #dedbea;
    background:
      linear-gradient(115deg, rgba(255,255,255,.98), rgba(248,247,252,.97)),
      var(--surface);
  }

  .hero::after {
    background: radial-gradient(circle, rgba(118, 203, 243, .18), rgba(118, 203, 243, 0) 68%);
  }

  .hero h1 .vakehyva { color: #312783; }
  .refresh-button {
    border-color: #312783;
    background: linear-gradient(180deg, #494091, #312783);
    box-shadow: 0 8px 18px rgba(49, 39, 131, .18);
  }
  .refresh-button:hover { box-shadow: 0 12px 24px rgba(49, 39, 131, .22); }
  .refresh-button:focus-visible { outline-color: rgba(49, 39, 131, .24); }

  .section-kicker::before { background: #E6007E; }
  .source-grid { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }

  .source-card[data-source="HAEAVUSTUKSIA"] {
    --source-color: #00983A;
    --source-soft: #edf8f0;
  }
  .source-card[data-source="EURA"] {
    --source-color: #E6007E;
    --source-soft: #fff0f8;
  }
  .opportunity[data-source="HAEAVUSTUKSIA"] {
    --row-color: #00983A;
    --row-soft: #edf8f0;
  }
  .opportunity[data-source="EURA"] {
    --row-color: #E6007E;
    --row-soft: #fff0f8;
  }

  .why-line strong,
  .fit-box .detail-label,
  .source-link { color: #312783; }
  .fit-box {
    border-color: #d8d5ea;
    background: linear-gradient(135deg, #fff, #f8f7fc);
  }

  .source-home-link:focus-visible,
  .row-source-link:focus-visible,
  .source-link:focus-visible,
  .source-select:focus-visible {
    outline-color: rgba(49, 39, 131, .20);
  }
</style>
"""

_SOURCE_META_OLD = r'''    const SOURCE_META = {
      STM: { name: "STM", home: "https://stm.fi/vuoden-2026-valtionavustushaut" },
      SITRA: { name: "Sitra", home: "https://asiointi.sitra.fi/" },
      ACADEMY: { name: "Suomen Akatemia", home: "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/" },
    };'''

_SOURCE_META_NEW = r'''    const SOURCE_META = {
      STM: { name: "STM", home: "https://stm.fi/vuoden-2026-valtionavustushaut" },
      HAEAVUSTUKSIA: { name: "Haeavustuksia.fi", home: "https://www.haeavustuksia.fi/fi/?isAdditionalSearchOpen=true" },
      EURA: { name: "EURA 2021", home: "https://eura2021.fi/hakuilmoitukset" },
      SITRA: { name: "Sitra", home: "https://asiointi.sitra.fi/" },
      ACADEMY: { name: "Suomen Akatemia", home: "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/" },
    };'''

_SCAN_STATUS_OLD = r'''    function scanStatusLabel(value) {
      const labels = {
        SUCCEEDED: "Onnistunut",
        FAILED: "Epäonnistunut",
        RUNNING: "Käynnissä",
        CANCELLED: "Keskeytetty",
      };
      return labels[value] || value || "Ei tietoa";
    }'''

_SCAN_STATUS_NEW = r'''    function scanStatusLabel(value) {
      const normalized = String(value || "").trim().toUpperCase();
      const labels = {
        SUCCEEDED: "Onnistunut",
        SUCCESS: "Onnistunut",
        FAILED: "Epäonnistunut",
        FAILURE: "Epäonnistunut",
        RUNNING: "Käynnissä",
        CANCELLED: "Keskeytetty",
        CANCELED: "Keskeytetty",
      };
      return labels[normalized] || normalized || "Ei tietoa";
    }'''

_RELEVANCE_OLD = r'''    function relevanceLabel(value) {
      const labels = { RELEVANT: "Relevantti", NOT_RELEVANT: "Ei relevantti", REVIEW: "Tarkistettava" };
      return labels[value] || value || "Ei tietoa";
    }'''

_RELEVANCE_NEW = r'''    function relevanceLabel(value) {
      const normalized = String(value || "").trim().toUpperCase();
      const labels = {
        RELEVANT: "Relevantti",
        NOT_RELEVANT: "Ei relevantti",
        REVIEW: "Tarkistettava",
        NEEDS_REVIEW: "Tarkistettava",
      };
      return labels[normalized] || normalized || "Ei tietoa";
    }'''

_DEADLINE_CALL_OLD = '        const deadline = formatDeadline(call.application_deadline_at);'
_DEADLINE_CALL_NEW = (
    '        const deadline = formatDeadline('
    'call.application_deadline_at || call.application_deadline_on);'
)


def _replace_once(html: str, old: str, new: str, *, label: str) -> str:
    if old not in html:
        raise RuntimeError(f"Dashboard customization sentinel missing: {label}")
    return html.replace(old, new, 1)


def render_dashboard_html(base_html: str) -> str:
    """Return the Milestone 7 employee dashboard with VAKE styling and five-source metadata."""

    html = _replace_once(
        base_html,
        "</head>",
        f"{_STYLE_OVERRIDES}\n</head>",
        label="head",
    )
    html = _replace_once(html, _SOURCE_META_OLD, _SOURCE_META_NEW, label="source-meta")
    html = _replace_once(html, _SCAN_STATUS_OLD, _SCAN_STATUS_NEW, label="scan-status")
    html = _replace_once(html, _RELEVANCE_OLD, _RELEVANCE_NEW, label="relevance-status")
    html = _replace_once(html, _DEADLINE_CALL_OLD, _DEADLINE_CALL_NEW, label="deadline")
    return html
