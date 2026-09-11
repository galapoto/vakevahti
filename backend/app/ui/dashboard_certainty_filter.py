"""Add an operator-facing certainty filter to the persisted funding dashboard."""

_STYLE = r"""
<style id="vake-certainty-filter">
  .filter-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .certainty-select {
    min-width: 165px;
    min-height: 40px;
    padding: 8px 32px 8px 10px;
    border: 1px solid #cbd5dc;
    border-radius: 9px;
    color: var(--text);
    background: white;
  }

  .certainty-select:focus-visible {
    outline: 3px solid rgba(49, 39, 131, .20);
    outline-offset: 2px;
  }

  @media (max-width: 700px) {
    .filter-group {
      align-items: stretch;
      flex-direction: column;
      gap: 5px;
    }
    .certainty-select { width: 100%; }
  }
</style>
"""

_TOOLBAR_OLD = r'''        <div class="toolbar-left">
          <label for="source-filter">Rajaa lähteen mukaan</label>
          <select id="source-filter" class="source-select">
            <option value="">Kaikki lähteet</option>
          </select>
        </div>'''

_TOOLBAR_NEW = r'''        <div class="toolbar-left">
          <div class="filter-group">
            <label for="source-filter">Lähde</label>
            <select id="source-filter" class="source-select">
              <option value="">Kaikki lähteet</option>
            </select>
          </div>
          <div class="filter-group">
            <label for="relevance-filter">Varmuus</label>
            <select id="relevance-filter" class="certainty-select">
              <option value="">Kaikki</option>
              <option value="RELEVANT">Varmistetut</option>
              <option value="NEEDS_REVIEW">Tarkistettavat</option>
            </select>
          </div>
        </div>'''

_STATE_OLD = (
    '    const state = { health: [], calls: [], details: new Map(), source: "", '
    'latestSource: null };'
)
_STATE_NEW = (
    '    const state = { health: [], calls: [], details: new Map(), source: "", '
    'relevance: "", latestSource: null };'
)

_ELEMENTS_OLD = '''      sourceGrid: document.getElementById("source-grid"),
      sourceFilter: document.getElementById("source-filter"),
      listCount: document.getElementById("list-count"),'''
_ELEMENTS_NEW = '''      sourceGrid: document.getElementById("source-grid"),
      sourceFilter: document.getElementById("source-filter"),
      relevanceFilter: document.getElementById("relevance-filter"),
      listCount: document.getElementById("list-count"),'''

_FETCH_FILTER_OLD = '''      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (state.source) params.set("source_code", state.source);
      const response = await fetch(`/api/funding-calls?${params.toString()}`);'''
_FETCH_FILTER_NEW = '''      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (state.source) params.set("source_code", state.source);
      if (state.relevance) params.set("relevance_status", state.relevance);
      const response = await fetch(`/api/funding-calls?${params.toString()}`);'''

_LISTENERS_OLD = '''    elements.sourceFilter.addEventListener("change", (event) => applySourceFilter(event.target.value, false));
    elements.refreshButton.addEventListener("click", () => { state.details.clear(); loadDashboard(); });
    elements.kpiCurrent.addEventListener("click", () => applySourceFilter(""));'''
_LISTENERS_NEW = '''    elements.sourceFilter.addEventListener("change", (event) => applySourceFilter(event.target.value, false));
    elements.relevanceFilter.addEventListener("change", (event) => {
      state.relevance = event.target.value;
      applySourceFilter(state.source, false);
    });
    elements.refreshButton.addEventListener("click", () => { state.details.clear(); loadDashboard(); });
    elements.kpiCurrent.addEventListener("click", () => {
      state.relevance = "RELEVANT";
      elements.relevanceFilter.value = "RELEVANT";
      applySourceFilter("");
    });'''


def _replace_once(html: str, old: str, new: str, *, label: str) -> str:
    if old not in html:
        raise RuntimeError(f"Dashboard certainty-filter sentinel missing: {label}")
    return html.replace(old, new, 1)


def render_dashboard_certainty_filter(html: str) -> str:
    """Add source-independent RELEVANT/NEEDS_REVIEW filtering to the dashboard."""

    html = _replace_once(html, "</head>", f"{_STYLE}\n</head>", label="head")
    replacements = (
        (_TOOLBAR_OLD, _TOOLBAR_NEW, "toolbar"),
        (_STATE_OLD, _STATE_NEW, "state"),
        (_ELEMENTS_OLD, _ELEMENTS_NEW, "elements"),
        (_FETCH_FILTER_OLD, _FETCH_FILTER_NEW, "fetch-filter"),
        (_LISTENERS_OLD, _LISTENERS_NEW, "listeners"),
    )
    for old, new, label in replacements:
        html = _replace_once(html, old, new, label=label)
    return html
