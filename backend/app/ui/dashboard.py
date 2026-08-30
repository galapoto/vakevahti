"""Self-contained operational dashboard served by FastAPI.

The dashboard intentionally stays dependency-light for the current managed workplace
machine. It reads only VakeVahti's persisted API contracts; loading the page never
triggers a funding-source scan.
"""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="fi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VakeVahti | Rahoitushakujen tilannekuva</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --surface: #ffffff;
      --surface-soft: #f8fafb;
      --text: #17212b;
      --muted: #667085;
      --border: #dfe5e8;
      --accent: #0f766e;
      --accent-strong: #0b5d57;
      --accent-soft: #e7f5f2;
      --good: #16794f;
      --good-soft: #eaf7f1;
      --warning: #a15c00;
      --warning-soft: #fff6e5;
      --danger: #b42318;
      --danger-soft: #fff0ee;
      --neutral-soft: #eef2f5;
      --shadow: 0 10px 30px rgba(16, 24, 40, .06);
      --radius-lg: 18px;
      --radius-md: 13px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }

    button, select, a { font: inherit; }

    .shell {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 52px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 28px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo {
      width: 42px;
      height: 42px;
      display: grid;
      place-items: center;
      border-radius: 12px;
      background: var(--accent);
      color: #fff;
      font-size: 13px;
      font-weight: 850;
      letter-spacing: .02em;
      box-shadow: 0 7px 16px rgba(15, 118, 110, .2);
    }

    .brand strong { display: block; font-size: 17px; }
    .brand span { display: block; margin-top: 1px; color: var(--muted); font-size: 12px; }

    .system-chip {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 7px 10px;
      border: 1px solid #cfe8e3;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 750;
    }

    .system-chip::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent);
    }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 28px;
      align-items: end;
      margin-bottom: 22px;
    }

    .eyebrow {
      margin: 0 0 7px;
      color: var(--accent);
      font-size: 12px;
      font-weight: 850;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .hero h1 {
      margin: 0;
      max-width: 760px;
      font-size: clamp(30px, 4vw, 48px);
      line-height: 1.05;
      letter-spacing: -.04em;
    }

    .hero p {
      margin: 12px 0 0;
      max-width: 780px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.65;
    }

    .refresh-button {
      border: 1px solid var(--border);
      border-radius: 11px;
      padding: 10px 14px;
      color: var(--text);
      background: var(--surface);
      font-weight: 750;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(16, 24, 40, .04);
    }

    .refresh-button:hover { border-color: #bac6cc; }
    .refresh-button:disabled { opacity: .55; cursor: wait; }

    .status-banner {
      display: none;
      align-items: flex-start;
      gap: 9px;
      padding: 12px 14px;
      margin-bottom: 18px;
      border: 1px solid #f1c7c2;
      border-radius: 11px;
      background: var(--danger-soft);
      color: var(--danger);
      font-size: 13px;
      line-height: 1.5;
    }

    .status-banner.visible { display: flex; }

    .status-dot {
      width: 8px;
      height: 8px;
      margin-top: 5px;
      flex: 0 0 auto;
      border-radius: 50%;
      background: currentColor;
    }

    .kpis {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }

    .kpi {
      min-height: 118px;
      padding: 17px;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      background: var(--surface);
      box-shadow: var(--shadow);
    }

    .kpi-label {
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .05em;
      text-transform: uppercase;
    }

    .kpi-value {
      display: block;
      margin-top: 11px;
      font-size: 29px;
      font-weight: 850;
      line-height: 1;
      letter-spacing: -.035em;
    }

    .kpi-detail {
      display: block;
      margin-top: 9px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }

    .section { margin-top: 24px; }

    .section-head {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 12px;
    }

    .section-head h2 {
      margin: 0;
      font-size: 20px;
      letter-spacing: -.02em;
    }

    .section-head p {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    .source-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .source-card {
      padding: 17px;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      background: var(--surface);
      box-shadow: var(--shadow);
    }

    .source-card-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 15px;
    }

    .source-name { font-size: 16px; font-weight: 850; }

    .health-badge {
      padding: 5px 8px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 850;
      letter-spacing: .03em;
    }

    .health-healthy { color: var(--good); background: var(--good-soft); }
    .health-failing { color: var(--danger); background: var(--danger-soft); }
    .health-running { color: var(--warning); background: var(--warning-soft); }
    .health-never_scanned { color: #53606b; background: var(--neutral-soft); }

    .source-count {
      font-size: 25px;
      font-weight: 850;
      letter-spacing: -.03em;
    }

    .source-count span {
      margin-left: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
      letter-spacing: 0;
    }

    .fact-list { display: grid; gap: 8px; margin-top: 15px; }

    .fact {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      padding-top: 8px;
      border-top: 1px solid #edf1f3;
      color: var(--muted);
      font-size: 11px;
    }

    .fact strong { color: #344054; font-weight: 750; text-align: right; }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius-md) var(--radius-md) 0 0;
      background: var(--surface);
    }

    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    .toolbar label { color: var(--muted); font-size: 12px; font-weight: 750; }

    .source-select {
      min-width: 170px;
      padding: 8px 32px 8px 10px;
      border: 1px solid #cbd5dc;
      border-radius: 9px;
      color: var(--text);
      background: white;
    }

    .list-count { color: var(--muted); font-size: 12px; }

    .opportunity-panel {
      overflow: hidden;
      border: 1px solid var(--border);
      border-top: 0;
      border-radius: 0 0 var(--radius-lg) var(--radius-lg);
      background: var(--surface);
      box-shadow: var(--shadow);
    }

    .empty-state, .loading-state {
      padding: 42px 22px;
      text-align: center;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    .opportunity-list { display: grid; }
    .opportunity { border-top: 1px solid #edf1f3; }
    .opportunity:first-child { border-top: 0; }

    .opportunity-toggle {
      width: 100%;
      display: grid;
      grid-template-columns: 94px minmax(0, 1fr) 170px 28px;
      gap: 14px;
      align-items: center;
      padding: 15px 17px;
      border: 0;
      color: inherit;
      background: #fff;
      text-align: left;
      cursor: pointer;
    }

    .opportunity-toggle:hover { background: #fbfcfd; }
    .opportunity-toggle:focus-visible { outline: 3px solid rgba(15, 118, 110, .22); outline-offset: -3px; }

    .source-pill {
      justify-self: start;
      padding: 5px 8px;
      border-radius: 999px;
      color: var(--accent-strong);
      background: var(--accent-soft);
      font-size: 10px;
      font-weight: 850;
    }

    .opportunity-title {
      min-width: 0;
      font-size: 13px;
      font-weight: 750;
      line-height: 1.45;
    }

    .deadline-block { text-align: right; }

    .deadline-label {
      display: block;
      margin-bottom: 3px;
      color: var(--muted);
      font-size: 10px;
      font-weight: 750;
      text-transform: uppercase;
      letter-spacing: .04em;
    }

    .deadline-value { display: block; color: #344054; font-size: 12px; font-weight: 750; }
    .deadline-soon .deadline-value { color: var(--warning); }
    .deadline-past .deadline-value { color: var(--danger); }

    .chevron {
      justify-self: end;
      color: #667085;
      font-size: 20px;
      line-height: 1;
      transition: transform .16s ease;
    }

    .opportunity-toggle[aria-expanded="true"] .chevron { transform: rotate(90deg); }

    .opportunity-details {
      padding: 0 17px 18px 125px;
      background: var(--surface-soft);
      border-top: 1px solid #edf1f3;
    }

    .details-loading { padding: 17px 0 0; color: var(--muted); font-size: 12px; }

    .detail-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      padding-top: 16px;
    }

    .detail-box {
      min-width: 0;
      padding: 12px;
      border: 1px solid #e3e8eb;
      border-radius: 10px;
      background: #fff;
    }

    .detail-label {
      display: block;
      margin-bottom: 5px;
      color: var(--muted);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: .05em;
      text-transform: uppercase;
    }

    .detail-value {
      margin: 0;
      color: #344054;
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .description-box {
      margin-top: 12px;
      padding: 13px;
      border: 1px solid #e3e8eb;
      border-radius: 10px;
      background: #fff;
    }

    .source-link {
      display: inline-flex;
      align-items: center;
      margin-top: 12px;
      padding: 8px 10px;
      border: 1px solid #cbd5dc;
      border-radius: 8px;
      color: var(--accent-strong);
      background: #fff;
      font-size: 12px;
      font-weight: 750;
      text-decoration: none;
    }

    .source-link:hover { background: #f3faf8; }

    .footnote {
      margin-top: 18px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.55;
    }

    @media (max-width: 900px) {
      .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .source-grid { grid-template-columns: 1fr; }
      .opportunity-toggle { grid-template-columns: 76px minmax(0, 1fr) 28px; }
      .deadline-block { grid-column: 2; grid-row: 2; text-align: left; }
      .chevron { grid-column: 3; grid-row: 1 / span 2; }
      .opportunity-details { padding-left: 17px; }
      .detail-grid { grid-template-columns: 1fr 1fr; }
    }

    @media (max-width: 640px) {
      .shell { width: min(100% - 20px, 1180px); padding-top: 14px; }
      .topbar { align-items: flex-start; }
      .system-chip { display: none; }
      .hero { grid-template-columns: 1fr; gap: 15px; }
      .refresh-button { justify-self: start; }
      .kpis { grid-template-columns: 1fr; }
      .toolbar { align-items: stretch; flex-direction: column; }
      .toolbar-left { align-items: stretch; flex-direction: column; }
      .source-select { width: 100%; }
      .opportunity-toggle { grid-template-columns: 1fr 28px; gap: 8px 12px; }
      .source-pill { grid-column: 1; }
      .opportunity-title { grid-column: 1; }
      .deadline-block { grid-column: 1; grid-row: auto; }
      .chevron { grid-column: 2; grid-row: 1 / span 3; }
      .detail-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="logo" aria-hidden="true">VV</div>
        <div>
          <strong>VakeVahti</strong>
          <span>Rahoitushakujen seuranta</span>
        </div>
      </div>
      <div class="system-chip">Tallennettu tilannekuva</div>
    </header>

    <section class="hero" aria-labelledby="page-title">
      <div>
        <p class="eyebrow">Operatiivinen näkymä</p>
        <h1 id="page-title">Rahoitushakujen tilannekuva</h1>
        <p>
          Näkymä perustuu VakeVahdin viimeisimpiin onnistuneesti tallennettuihin lähdehavaintoihin.
          Sivun avaaminen ei käynnistä uusia verkkohakuja rahoittajien sivustoille.
        </p>
      </div>
      <button id="refresh-button" class="refresh-button" type="button">Päivitä näkymä</button>
    </section>

    <div id="status-banner" class="status-banner" role="alert">
      <span class="status-dot" aria-hidden="true"></span>
      <span id="status-message"></span>
    </div>

    <section class="kpis" aria-label="Tilannekuvan tunnusluvut">
      <article class="kpi">
        <span class="kpi-label">Nykyiset rahoitushaut</span>
        <strong class="kpi-value" id="total-calls">–</strong>
        <span class="kpi-detail">Viimeisimmistä onnistuneista lähdehavainnoista</span>
      </article>
      <article class="kpi">
        <span class="kpi-label">Terveet lähteet</span>
        <strong class="kpi-value" id="healthy-sources">–</strong>
        <span class="kpi-detail" id="healthy-detail">Lähdetilaa ladataan</span>
      </article>
      <article class="kpi">
        <span class="kpi-label">Huomiota vaativat lähteet</span>
        <strong class="kpi-value" id="attention-sources">–</strong>
        <span class="kpi-detail">FAILED/RUNNING/ei vielä skannattu</span>
      </article>
      <article class="kpi">
        <span class="kpi-label">Viimeisin onnistunut lähdeajo</span>
        <strong class="kpi-value" id="latest-success">–</strong>
        <span class="kpi-detail" id="latest-success-detail">Ei vielä tietoa</span>
      </article>
    </section>

    <section class="section" aria-labelledby="sources-heading">
      <div class="section-head">
        <div>
          <h2 id="sources-heading">Lähteiden tila</h2>
          <p>Operatiivinen tila ja viimeisimmän ajon tallennetut faktat lähteittäin.</p>
        </div>
      </div>
      <div id="source-grid" class="source-grid" aria-live="polite">
        <div class="loading-state">Ladataan lähteiden tilaa…</div>
      </div>
    </section>

    <section class="section" aria-labelledby="calls-heading">
      <div class="section-head">
        <div>
          <h2 id="calls-heading">Nykyiset rahoitushaut</h2>
          <p>Lista näyttää vain kunkin lähteen viimeisimpään onnistuneeseen tilannekuvaan kuuluvat haut.</p>
        </div>
      </div>

      <div class="toolbar">
        <div class="toolbar-left">
          <label for="source-filter">Rajaa lähteen mukaan</label>
          <select id="source-filter" class="source-select">
            <option value="">Kaikki lähteet</option>
          </select>
        </div>
        <span id="list-count" class="list-count">Ladataan…</span>
      </div>

      <div class="opportunity-panel">
        <div id="opportunity-list" class="opportunity-list" aria-live="polite">
          <div class="loading-state">Ladataan tallennettuja rahoitushakuja…</div>
        </div>
      </div>

      <p class="footnote">
        Lähteen tila kertoo viimeisimmän tallennetun ajon onnistumisesta. VakeVahti ei tässä vaiheessa
        päättele mielivaltaista vanhentumisrajaa; viimeisimmän onnistuneen ajon aika näytetään erikseen.
      </p>
    </section>
  </main>

  <script>
    const state = { health: [], calls: [], details: new Map(), source: "" };

    const elements = {
      refreshButton: document.getElementById("refresh-button"),
      statusBanner: document.getElementById("status-banner"),
      statusMessage: document.getElementById("status-message"),
      totalCalls: document.getElementById("total-calls"),
      healthySources: document.getElementById("healthy-sources"),
      healthyDetail: document.getElementById("healthy-detail"),
      attentionSources: document.getElementById("attention-sources"),
      latestSuccess: document.getElementById("latest-success"),
      latestSuccessDetail: document.getElementById("latest-success-detail"),
      sourceGrid: document.getElementById("source-grid"),
      sourceFilter: document.getElementById("source-filter"),
      listCount: document.getElementById("list-count"),
      opportunityList: document.getElementById("opportunity-list"),
    };

    function clear(node) {
      while (node.firstChild) node.removeChild(node.firstChild);
    }

    function text(tag, value, className) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      node.textContent = value;
      return node;
    }

    function showError(message) {
      elements.statusMessage.textContent = message;
      elements.statusBanner.classList.add("visible");
    }

    function clearError() {
      elements.statusMessage.textContent = "";
      elements.statusBanner.classList.remove("visible");
    }

    function formatDateTime(value) {
      if (!value) return "Ei tietoa";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "Ei tietoa";
      return new Intl.DateTimeFormat("fi-FI", { dateStyle: "short", timeStyle: "short" }).format(date);
    }

    function formatDeadline(value) {
      if (!value) return { label: "Ei ilmoitettu", className: "" };
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return { label: "Ei ilmoitettu", className: "" };

      const now = new Date();
      const days = Math.ceil((date.getTime() - now.getTime()) / 86400000);
      const label = new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium", timeStyle: "short" }).format(date);

      if (days < 0) return { label, className: "deadline-past" };
      if (days <= 7) return { label, className: "deadline-soon" };
      return { label, className: "" };
    }

    function healthLabel(value) {
      const labels = { HEALTHY: "Toimii", FAILING: "Virhe", RUNNING: "Käynnissä", NEVER_SCANNED: "Ei vielä ajoa" };
      return labels[value] || value;
    }

    function sourceDisplayName(code) {
      const names = { STM: "STM", SITRA: "Sitra", ACADEMY: "Suomen Akatemia" };
      return names[code] || code;
    }

    function addFact(container, label, value) {
      const row = document.createElement("div");
      row.className = "fact";
      row.append(text("span", label));
      row.append(text("strong", value));
      container.append(row);
    }

    function renderHealth() {
      clear(elements.sourceGrid);

      if (!state.health.length) {
        elements.sourceGrid.append(text("div", "Yhtään määritettyä lähdettä ei löytynyt.", "empty-state"));
        elements.healthySources.textContent = "0";
        elements.attentionSources.textContent = "0";
        elements.healthyDetail.textContent = "0 määritettyä lähdettä";
        return;
      }

      const healthy = state.health.filter((item) => item.health === "HEALTHY").length;
      const attention = state.health.length - healthy;
      elements.healthySources.textContent = String(healthy);
      elements.attentionSources.textContent = String(attention);
      elements.healthyDetail.textContent = `${healthy}/${state.health.length} lähdettä toimii`;

      const successfulTimes = state.health
        .map((item) => item.last_successful_scan_at)
        .filter(Boolean)
        .map((value) => new Date(value))
        .filter((value) => !Number.isNaN(value.getTime()));

      if (successfulTimes.length) {
        const latest = new Date(Math.max(...successfulTimes.map((value) => value.getTime())));
        elements.latestSuccess.textContent = new Intl.DateTimeFormat("fi-FI", { hour: "2-digit", minute: "2-digit" }).format(latest);
        elements.latestSuccessDetail.textContent = new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium" }).format(latest);
      } else {
        elements.latestSuccess.textContent = "–";
        elements.latestSuccessDetail.textContent = "Ei onnistuneita ajoja";
      }

      const existingOptions = new Set(Array.from(elements.sourceFilter.options).map((option) => option.value));

      for (const item of state.health) {
        if (!existingOptions.has(item.source_code)) {
          const option = document.createElement("option");
          option.value = item.source_code;
          option.textContent = sourceDisplayName(item.source_code);
          elements.sourceFilter.append(option);
        }

        const card = document.createElement("article");
        card.className = "source-card";

        const head = document.createElement("div");
        head.className = "source-card-head";
        head.append(text("div", sourceDisplayName(item.source_code), "source-name"));

        const badge = text("span", healthLabel(item.health), "health-badge");
        badge.classList.add(`health-${String(item.health).toLowerCase()}`);
        head.append(badge);
        card.append(head);

        const count = document.createElement("div");
        count.className = "source-count";
        count.append(document.createTextNode(String(item.current_call_count)));
        count.append(text("span", "nykyistä hakua"));
        card.append(count);

        const facts = document.createElement("div");
        facts.className = "fact-list";
        addFact(facts, "Viimeisin onnistunut ajo", formatDateTime(item.last_successful_scan_at));
        addFact(facts, "Viimeisin ajotila", item.latest_scan_status || "Ei tietoa");
        addFact(facts, "Uusia / muuttuneita", `${item.latest_new_count ?? "–"} / ${item.latest_changed_count ?? "–"}`);
        if (item.latest_error_type) addFact(facts, "Virheluokka", item.latest_error_type);
        card.append(facts);

        elements.sourceGrid.append(card);
      }
    }

    function detailBox(label, value) {
      const box = document.createElement("div");
      box.className = "detail-box";
      box.append(text("span", label, "detail-label"));
      box.append(text("p", value, "detail-value"));
      return box;
    }

    function renderDetail(container, detail) {
      clear(container);

      const grid = document.createElement("div");
      grid.className = "detail-grid";
      grid.append(detailBox("Haku avautuu", formatDateTime(detail.application_opens_at)));
      grid.append(detailBox("Ensimmäinen havainto", formatDateTime(detail.first_seen_at)));
      grid.append(detailBox("Viimeisin havainto", formatDateTime(detail.last_seen_at)));
      grid.append(detailBox("Relevanssi", detail.relevance_status || "Ei tietoa"));
      grid.append(detailBox("Perustelu", detail.relevance_reason || "Ei tietoa"));
      grid.append(detailBox("Versio", String(detail.current_version)));
      container.append(grid);

      const description = document.createElement("div");
      description.className = "description-box";
      description.append(text("span", "Kuvaus", "detail-label"));
      description.append(text("p", detail.description_text || "Lähteestä ei ole tallennettu kuvaustekstiä.", "detail-value"));
      container.append(description);

      const link = document.createElement("a");
      link.className = "source-link";
      link.href = detail.source_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Avaa alkuperäinen lähde";
      container.append(link);
    }

    async function loadDetail(id, container) {
      if (state.details.has(id)) {
        renderDetail(container, state.details.get(id));
        return;
      }

      clear(container);
      container.append(text("div", "Ladataan tarkempia tietoja…", "details-loading"));

      try {
        const response = await fetch(`/api/funding-calls/${encodeURIComponent(id)}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const detail = await response.json();
        state.details.set(id, detail);
        renderDetail(container, detail);
      } catch (error) {
        clear(container);
        container.append(text("div", "Tarkempia tietoja ei saatu ladattua.", "details-loading"));
      }
    }

    function renderCalls() {
      clear(elements.opportunityList);
      elements.totalCalls.textContent = String(state.calls.length);
      elements.listCount.textContent = `${state.calls.length} hakua`;

      if (!state.calls.length) {
        elements.opportunityList.append(text("div", "Valitussa viimeisimmässä onnistuneessa tilannekuvassa ei ole nykyisiä rahoitushakuja.", "empty-state"));
        return;
      }

      state.calls.forEach((call) => {
        const row = document.createElement("article");
        row.className = "opportunity";

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "opportunity-toggle";
        toggle.setAttribute("aria-expanded", "false");
        toggle.append(text("span", sourceDisplayName(call.source_code), "source-pill"));
        toggle.append(text("span", call.title, "opportunity-title"));

        const deadline = formatDeadline(call.application_deadline_at);
        const deadlineBlock = document.createElement("span");
        deadlineBlock.className = "deadline-block";
        if (deadline.className) deadlineBlock.classList.add(deadline.className);
        deadlineBlock.append(text("span", "Hakuaika päättyy", "deadline-label"));
        deadlineBlock.append(text("span", deadline.label, "deadline-value"));
        toggle.append(deadlineBlock);
        toggle.append(text("span", "›", "chevron"));

        const details = document.createElement("div");
        details.className = "opportunity-details";
        details.hidden = true;

        toggle.addEventListener("click", async () => {
          const expanded = toggle.getAttribute("aria-expanded") === "true";
          toggle.setAttribute("aria-expanded", String(!expanded));
          details.hidden = expanded;
          if (!expanded) await loadDetail(call.id, details);
        });

        row.append(toggle, details);
        elements.opportunityList.append(row);
      });
    }

    async function fetchHealth() {
      const response = await fetch("/api/sources/health");
      if (!response.ok) throw new Error(`Health HTTP ${response.status}`);
      const payload = await response.json();
      state.health = payload.sources || [];
      renderHealth();
    }

    async function fetchCalls() {
      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (state.source) params.set("source_code", state.source);
      const response = await fetch(`/api/funding-calls?${params.toString()}`);
      if (!response.ok) throw new Error(`Funding HTTP ${response.status}`);
      const payload = await response.json();
      state.calls = payload.items || [];
      renderCalls();
    }

    async function loadDashboard() {
      clearError();
      elements.refreshButton.disabled = true;
      try {
        await Promise.all([fetchHealth(), fetchCalls()]);
      } catch (error) {
        showError("Tallennettua tilannekuvaa ei saatu ladattua. Tarkista API:n ja tietokannan tila.");
      } finally {
        elements.refreshButton.disabled = false;
      }
    }

    elements.sourceFilter.addEventListener("change", async (event) => {
      state.source = event.target.value;
      state.calls = [];
      state.details.clear();
      elements.opportunityList.replaceChildren(text("div", "Ladataan…", "loading-state"));
      try {
        await fetchCalls();
      } catch (error) {
        showError("Rahoitushakuja ei saatu ladattua valitulle lähteelle.");
      }
    });

    elements.refreshButton.addEventListener("click", () => {
      state.details.clear();
      loadDashboard();
    });

    loadDashboard();
  </script>
</body>
</html>
"""
