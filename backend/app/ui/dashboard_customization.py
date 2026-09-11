"""VAKE-specific presentation refinements for the employee funding dashboard.

The operational dashboard is shared from the Milestone 6 branch. This module keeps
Milestone 7 source integration and VAKE visual refinements explicit and fail-loudly:
if the shared dashboard structure changes, a missing sentinel raises instead of
silently serving a partially customized page.
"""

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
  .opportunity[data-relevance="NEEDS_REVIEW"],
  .opportunity[data-relevance="REVIEW"] {
    --row-color: #B59525;
    --row-soft: #fbf7e9;
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

_REASON_OLD = r'''    function relevanceReason(call) {
      const reason = String(call.relevance_reason || "").trim();
      if (reason) return reason;
      return "VakeVahti on luokitellut haun VakeHyvälle relevantiksi tallennettujen tietojen perusteella.";
    }'''

_REASON_NEW = r'''    function needsReview(value) {
      const normalized = String(value || "").trim().toUpperCase();
      return normalized === "NEEDS_REVIEW" || normalized === "REVIEW";
    }

    function relevanceReason(call) {
      const reason = String(call.relevance_reason || "").trim();
      if (reason) return reason;
      if (needsReview(call.relevance_status)) {
        return "VakeVahti ei pystynyt varmistamaan hakukelpoisuutta automaattisesti. Haku vaatii henkilön tarkistuksen.";
      }
      return "VakeVahti on luokitellut haun VakeHyvälle relevantiksi tallennettujen tietojen perusteella.";
    }'''

_DEADLINE_CALL_OLD = '        const deadline = formatDeadline(call.application_deadline_at);'
_DEADLINE_CALL_NEW = (
    '        const deadline = formatDeadline('
    'call.application_deadline_at || call.application_deadline_on);'
)

_HERO_TITLE_OLD = '<h1 id="page-title"><span class="vakehyva">VakeHyvälle</span> sopivat rahoitushaut</h1>'
_HERO_TITLE_NEW = '<h1 id="page-title"><span class="vakehyva">VakeHyvälle</span> varmistetut ja tarkistettavat rahoitushaut</h1>'

_HERO_COPY_OLD = '''          VakeVahti kokoaa rahoitushaut yhteen ja näyttää, miksi kukin mahdollisuus on arvioitu
          VakeHyvälle relevantiksi.'''
_HERO_COPY_NEW = '''          VakeVahti kokoaa rahoitushaut yhteen ja erottaa varmistetusti relevantit haut niistä,
          joiden hakukelpoisuus vaatii vielä henkilön tarkistuksen.'''

_KPI_LABEL_OLD = '<span class="kpi-top"><span class="kpi-label">VakeHyvälle sopivat haut</span><span class="kpi-icon">↗</span></span>'
_KPI_LABEL_NEW = '<span class="kpi-top"><span class="kpi-label">Varmistetusti sopivat haut</span><span class="kpi-icon">↗</span></span>'
_KPI_DETAIL_OLD = '<span class="kpi-detail">Kaikkien seurattujen lähteiden nykyiset relevantit haut</span>'
_KPI_DETAIL_NEW = '<span class="kpi-detail">Vain vahvistetut relevantit haut; tarkistettavat näkyvät listassa erikseen</span>'

_CALLS_HEADING_OLD = '<h2 id="calls-heading">VakeHyvälle tunnistetut rahoitusmahdollisuudet</h2>'
_CALLS_HEADING_NEW = '<h2 id="calls-heading">Varmistetut ja tarkistettavat rahoitusmahdollisuudet</h2>'
_CALLS_COPY_OLD = '<p>Jokaisen haun alla näkyy suoraan tallennettu perustelu sille, miksi haku on arvioitu VakeHyvälle relevantiksi.</p>'
_CALLS_COPY_NEW = '<p>Jokaisen haun alla näkyy tallennettu perustelu sekä selkeä tieto siitä, onko sopivuus varmistettu vai vaatiiko haku tarkistuksen.</p>'
_LOADING_OLD = '<div class="loading-state">Ladataan VakeHyvälle sopivia rahoitushakuja…</div>'
_LOADING_NEW = '<div class="loading-state">Ladataan varmistettuja ja tarkistettavia rahoitushakuja…</div>'
_EMPTY_OLD = '        elements.opportunityList.append(text("div", "Valitussa viimeisimmässä onnistuneessa tilannekuvassa ei ole nykyisiä VakeHyvälle sopivia rahoitushakuja.", "empty-state"));'
_EMPTY_NEW = '        elements.opportunityList.append(text("div", "Valitussa viimeisimmässä onnistuneessa tilannekuvassa ei ole varmistettuja tai tarkistettavia rahoitushakuja.", "empty-state"));'

_HEALTH_TOTAL_OLD = '''      const totalCurrent = state.health.reduce((sum, item) => sum + Number(item.current_call_count || 0), 0);
      elements.totalCalls.textContent = String(totalCurrent);'''
_HEALTH_TOTAL_NEW = '''      const totalRelevant = state.health.reduce((sum, item) => sum + Number(item.relevant_call_count || 0), 0);
      elements.totalCalls.textContent = String(totalRelevant);'''

_SOURCE_COUNT_OLD = '''        const count = document.createElement("div");
        count.className = "source-count";
        count.append(document.createTextNode(String(item.current_call_count)));
        count.append(text("span", "VakeHyvälle sopivaa hakua"));
        main.append(count);

        const facts = document.createElement("div");
        facts.className = "fact-list";
        addFact(facts, "Viimeisin onnistunut ajo", formatDateTime(item.last_successful_scan_at));'''
_SOURCE_COUNT_NEW = '''        const count = document.createElement("div");
        count.className = "source-count";
        count.append(document.createTextNode(String(item.relevant_call_count || 0)));
        count.append(text("span", "varmistetusti sopivaa hakua"));
        main.append(count);

        const facts = document.createElement("div");
        facts.className = "fact-list";
        addFact(facts, "Tarkistettavat", String(item.review_call_count || 0));
        addFact(facts, "Viimeisin onnistunut ajo", formatDateTime(item.last_successful_scan_at));'''

_DETAIL_FIT_OLD = '      fit.append(text("span", "Miksi tämä sopii VakeHyvälle", "detail-label"));'
_DETAIL_FIT_NEW = '''      const fitLabel = needsReview(detail.relevance_status)
        ? "Miksi tämä on tarkistettava"
        : "Miksi tämä sopii VakeHyvälle";
      fit.append(text("span", fitLabel, "detail-label"));'''

_LIST_COUNT_OLD = '''      elements.listCount.textContent = state.source
        ? `${state.calls.length} hakua · ${sourceMeta(state.source).name}`
        : `${state.calls.length} hakua · kaikki lähteet`;'''
_LIST_COUNT_NEW = '''      const confirmedCount = state.calls.filter((call) => String(call.relevance_status || "").trim().toUpperCase() === "RELEVANT").length;
      const reviewCount = state.calls.filter((call) => needsReview(call.relevance_status)).length;
      const scope = state.source ? sourceMeta(state.source).name : "kaikki lähteet";
      elements.listCount.textContent = `${confirmedCount} vahvistettua · ${reviewCount} tarkistettavaa · ${scope}`;'''

_ROW_DATA_OLD = '        row.dataset.source = call.source_code;'
_ROW_DATA_NEW = '''        row.dataset.source = call.source_code;
        row.dataset.relevance = String(call.relevance_status || "").trim().toUpperCase();'''

_WHY_LABEL_OLD = '        whyLabel.textContent = "Miksi VakeHyvälle: ";'
_WHY_LABEL_NEW = '        whyLabel.textContent = needsReview(call.relevance_status) ? "Miksi tarkistettava: " : "Miksi VakeHyvälle: ";'


def _replace_once(html: str, old: str, new: str, *, label: str) -> str:
    if old not in html:
        raise RuntimeError(f"Dashboard customization sentinel missing: {label}")
    return html.replace(old, new, 1)


def render_dashboard_html(base_html: str) -> str:
    """Return the employee dashboard with VAKE styling and certainty-aware wording."""

    html = _replace_once(
        base_html,
        "</head>",
        f"{_STYLE_OVERRIDES}\n</head>",
        label="head",
    )
    replacements = (
        (_SOURCE_META_OLD, _SOURCE_META_NEW, "source-meta"),
        (_SCAN_STATUS_OLD, _SCAN_STATUS_NEW, "scan-status"),
        (_RELEVANCE_OLD, _RELEVANCE_NEW, "relevance-status"),
        (_REASON_OLD, _REASON_NEW, "relevance-reason"),
        (_DEADLINE_CALL_OLD, _DEADLINE_CALL_NEW, "deadline"),
        (_HERO_TITLE_OLD, _HERO_TITLE_NEW, "hero-title"),
        (_HERO_COPY_OLD, _HERO_COPY_NEW, "hero-copy"),
        (_KPI_LABEL_OLD, _KPI_LABEL_NEW, "kpi-label"),
        (_KPI_DETAIL_OLD, _KPI_DETAIL_NEW, "kpi-detail"),
        (_CALLS_HEADING_OLD, _CALLS_HEADING_NEW, "calls-heading"),
        (_CALLS_COPY_OLD, _CALLS_COPY_NEW, "calls-copy"),
        (_LOADING_OLD, _LOADING_NEW, "loading-copy"),
        (_EMPTY_OLD, _EMPTY_NEW, "empty-copy"),
        (_HEALTH_TOTAL_OLD, _HEALTH_TOTAL_NEW, "health-total"),
        (_SOURCE_COUNT_OLD, _SOURCE_COUNT_NEW, "source-count"),
        (_DETAIL_FIT_OLD, _DETAIL_FIT_NEW, "detail-fit"),
        (_LIST_COUNT_OLD, _LIST_COUNT_NEW, "list-count"),
        (_ROW_DATA_OLD, _ROW_DATA_NEW, "row-relevance"),
        (_WHY_LABEL_OLD, _WHY_LABEL_NEW, "why-label"),
    )
    for old, new, label in replacements:
        html = _replace_once(html, old, new, label=label)
    return html
