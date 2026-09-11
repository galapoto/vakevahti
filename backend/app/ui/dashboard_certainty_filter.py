"""Add operator certainty filtering and complete pagination to the funding dashboard."""

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

_FETCH_CALLS_OLD = r'''    async function fetchCalls() {
      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (state.source) params.set("source_code", state.source);
      const response = await fetch(`/api/funding-calls?${params.toString()}`);
      if (!response.ok) throw new Error(`Funding HTTP ${response.status}`);
      const payload = await response.json();
      state.calls = payload.items || [];
      renderCalls();
    }'''

_FETCH_CALLS_NEW = r'''    async function fetchCalls() {
      const pageSize = 100;
      let offset = 0;
      let expectedTotal = null;
      const calls = [];

      while (expectedTotal === null || offset < expectedTotal) {
        const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
        if (state.source) params.set("source_code", state.source);
        if (state.relevance) params.set("relevance_status", state.relevance);

        const response = await fetch(`/api/funding-calls?${params.toString()}`);
        if (!response.ok) throw new Error(`Funding HTTP ${response.status}`);
        const payload = await response.json();
        const pageItems = Array.isArray(payload.items) ? payload.items : [];
        const total = Number(payload.total);
        if (!Number.isFinite(total) || total < 0) {
          throw new Error("Funding API returned an invalid total.");
        }
        expectedTotal = total;
        calls.push(...pageItems);
        offset += pageItems.length;

        if (!pageItems.length && offset < expectedTotal) {
          throw new Error("Funding API pagination stopped before the advertised total.");
        }
      }

      state.calls = calls;
      renderCalls();
    }'''

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
    """Add certainty filtering and load every page from the persisted read API."""

    html = _replace_once(html, "</head>", f"{_STYLE}\n</head>", label="head")
    replacements = (
        (_TOOLBAR_OLD, _TOOLBAR_NEW, "toolbar"),
        (_STATE_OLD, _STATE_NEW, "state"),
        (_ELEMENTS_OLD, _ELEMENTS_NEW, "elements"),
        (_FETCH_CALLS_OLD, _FETCH_CALLS_NEW, "fetch-calls"),
        (_LISTENERS_OLD, _LISTENERS_NEW, "listeners"),
    )
    for old, new, label in replacements:
        html = _replace_once(html, old, new, label=label)
    return html
