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
      --blue: #2563eb;
      --blue-soft: #eff6ff;
      --purple: #7c3aed;
      --purple-soft: #f5f3ff;
      --amber: #b45309;
      --amber-soft: #fffbeb;
      --shadow: 0 10px 30px rgba(16, 24, 40, .06);
      --shadow-hover: 0 14px 30px rgba(16, 24, 40, .11);
      --radius-lg: 18px;
      --radius-md: 13px;
    }

    * { box-sizing: border-box; }

    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }

    button, select, a { font: inherit; }
    button { color: inherit; }

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

    .brand { display: flex; align-items: center; gap: 12px; }

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
      min-height: 44px;
      border: 1px solid var(--border);
      border-radius: 11px;
      padding: 10px 14px;
      color: var(--text);
      background: var(--surface);
      font-weight: 750;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(16, 24, 40, .04);
    }

    .refresh-button:hover { border-color: #bac6cc; box-shadow: var(--shadow); }
    .refresh-button:focus-visible { outline: 3px solid rgba(15, 118, 110, .24); outline-offset: 2px; }
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
      --kpi-color: var(--accent);
      --kpi-soft: var(--accent-soft);
      position: relative;
      min-height: 126px;
      padding: 18px;
      overflow: hidden;
      border: 1px solid color-mix(in srgb, var(--kpi-color) 25%, var(--border));
      border-radius: var(--radius-md);
      background: linear-gradient(145deg, var(--surface) 45%, var(--kpi-soft));
      box-shadow: var(--shadow);
      text-align: left;
      cursor: pointer;
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }

    .kpi::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: var(--kpi-color);
    }

    .kpi:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); border-color: var(--kpi-color); }
    .kpi:focus-visible { outline: 3px solid color-mix(in srgb, var(--kpi-color) 28%, transparent); outline-offset: 2px; }
    .kpi-blue { --kpi-color: var(--blue); --kpi-soft: var(--blue-soft); }
    .kpi-green { --kpi-color: var(--good); --kpi-soft: var(--good-soft); }
    .kpi-amber { --kpi-color: var(--amber); --kpi-soft: var(--amber-soft); }
    .kpi-purple { --kpi-color: var(--purple); --kpi-soft: var(--purple-soft); }

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
      color: var(--kpi-color);
      font-size: 31px;
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

    .kpi-action {
      display: inline-flex;
      margin-top: 10px;
      color: var(--kpi-color);
      font-size: 11px;
      font-weight: 800;
    }

    .section { margin-top: 24px; scroll-margin-top: 18px; }

    .section-head {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 12px;
    }

    .section-head h2 { margin: 0; font-size: 20px; letter-spacing: -.02em; }
    .section-head p { margin: 5px 0 0; color: var(--muted); font-size: 13px; line-height: 1.45; }

    .source-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .source-card {
      --source-color: var(--accent);
      --source-soft: var(--accent-soft);
      position: relative;
      overflow: hidden;
      border: 1px solid color-mix(in srgb, var(--source-color) 24%, var(--border));
      border-radius: var(--radius-md);
      background: linear-gradient(155deg, #fff 52%, var(--source-soft));
      box-shadow: var(--shadow);
      transition: box-shadow .16s ease, transform .16s ease, border-color .16s ease;
    }

    .source-card::before {
      content: "";
      position: absolute;
      inset: 0 0 auto 0;
      height: 4px;
      background: var(--source-color);
    }

    .source-card[data-source="STM"] { --source-color: var(--blue); --source-soft: var(--blue-soft); }
    .source-card[data-source="SITRA"] { --source-color: var(--purple); --source-soft: var(--purple-soft); }
    .source-card[data-source="ACADEMY"] { --source-color: var(--amber); --source-soft: var(--amber-soft); }
    .source-card:hover { transform: translateY(-2px); border-color: var(--source-color); box-shadow: var(--shadow-hover); }
    .source-card.flash { animation: card-flash .85s ease; }

    @keyframes card-flash {
      0%, 100% { box-shadow: var(--shadow); }
      45% { box-shadow: 0 0 0 4px color-mix(in srgb, var(--source-color) 22%, transparent), var(--shadow-hover); }
    }

    .source-card-main {
      width: 100%;
      padding: 18px 18px 12px;
      border: 0;
      background: transparent;
      text-align: left;
      cursor: pointer;
    }

    .source-card-main:focus-visible { outline: 3px solid color-mix(in srgb, var(--source-color) 28%, transparent); outline-offset: -3px; }

    .source-card-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 15px;
    }

    .source-name { color: var(--source-color); font-size: 16px; font-weight: 850; }

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
    .health-never_scanned { color: #53606b; background: #eef2f5; }

    .source-count { color: var(--source-color); font-size: 27px; font-weight: 850; letter-spacing: -.03em; }
    .source-count span { margin-left: 5px; color: var(--muted); font-size: 12px; font-weight: 650; letter-spacing: 0; }
    .fact-list { display: grid; gap: 8px; margin-top: 15px; }

    .fact {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      padding-top: 8px;
      border-top: 1px solid color-mix(in srgb, var(--source-color) 11%, #edf1f3);
      color: var(--muted);
      font-size: 11px;
    }

    .fact strong { color: #344054; font-weight: 750; text-align: right; }

    .source-card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 18px 14px;
      border-top: 1px solid color-mix(in srgb, var(--source-color) 12%, #edf1f3);
    }

    .source-filter-hint { color: var(--source-color); font-size: 11px; font-weight: 800; }

    .source-home-link,
    .row-source-link,
    .source-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      border: 1px solid currentColor;
      border-radius: 8px;
      color: var(--accent-strong);
      background: #fff;
      font-size: 11px;
      font-weight: 800;
      text-decoration: none;
    }

    .source-home-link { min-height: 34px; padding: 7px 9px; color: var(--source-color); }
    .source-home-link:hover, .row-source-link:hover, .source-link:hover { filter: brightness(.97); }
    .source-home-link:focus-visible, .row-source-link:focus-visible, .source-link:focus-visible { outline: 3px solid rgba(15, 118, 110, .2); outline-offset: 2px; }

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

    .toolbar-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
    .toolbar label { color: var(--muted); font-size: 12px; font-weight: 750; }

    .source-select {
      min-width: 185px;
      min-height: 40px;
      padding: 8px 32px 8px 10px;
      border: 1px solid #cbd5dc;
      border-radius: 9px;
      color: var(--text);
      background: white;
    }

    .source-select:focus-visible { outline: 3px solid rgba(15, 118, 110, .2); outline-offset: 2px; }
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

    .opportunity {
      --row-color: var(--accent);
      --row-soft: var(--accent-soft);
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      border-top: 1px solid #edf1f3;
      background: #fff;
    }

    .opportunity:first-child { border-top: 0; }
    .opportunity[data-source="STM"] { --row-color: var(--blue); --row-soft: var(--blue-soft); }
    .opportunity[data-source="SITRA"] { --row-color: var(--purple); --row-soft: var(--purple-soft); }
    .opportunity[data-source="ACADEMY"] { --row-color: var(--amber); --row-soft: var(--amber-soft); }
    .opportunity:hover { background: color-mix(in srgb, var(--row-soft) 45%, #fff); }

    .opportunity::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 3px;
      background: var(--row-color);
      opacity: .65;
    }

    .opportunity-toggle {
      min-width: 0;
      display: grid;
      grid-template-columns: 94px minmax(0, 1fr) 170px 28px;
      gap: 14px;
      align-items: center;
      padding: 15px 12px 15px 18px;
      border: 0;
      background: transparent;
      text-align: left;
      cursor: pointer;
    }

    .opportunity-toggle:hover .opportunity-title { color: var(--row-color); }
    .opportunity-toggle:focus-visible { outline: 3px solid color-mix(in srgb, var(--row-color) 24%, transparent); outline-offset: -3px; }

    .source-pill {
      justify-self: start;
      padding: 5px 8px;
      border-radius: 999px;
      color: var(--row-color);
      background: var(--row-soft);
      font-size: 10px;
      font-weight: 850;
    }

    .opportunity-title { min-width: 0; font-size: 13px; font-weight: 750; line-height: 1.45; transition: color .14s ease; }
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

    .chevron { justify-self: end; color: var(--row-color); font-size: 20px; line-height: 1; transition: transform .16s ease; }
    .opportunity-toggle[aria-expanded="true"] .chevron { transform: rotate(90deg); }

    .row-action {
      display: flex;
      align-items: center;
      padding: 10px 14px 10px 4px;
    }

    .row-source-link {
      min-height: 36px;
      padding: 7px 9px;
      color: var(--row-color);
      white-space: nowrap;
    }

    .opportunity-details {
      grid-column: 1 / -1;
      padding: 0 17px 18px 125px;
      border-top: 1px solid #edf1f3;
      background: color-mix(in srgb, var(--row-soft) 52%, var(--surface-soft));
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

    .source-link { margin-top: 12px; min-height: 36px; padding: 8px 10px; }

    .footnote { margin-top: 18px; color: var(--muted); font-size: 11px; line-height: 1.55; }

    @media (max-width: 1000px) {
      .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .source-grid { grid-template-columns: 1fr; }
      .opportunity-toggle { grid-template-columns: 76px minmax(0, 1fr) 28px; }
      .deadline-block { grid-column: 2; grid-row: 2; text-align: left; }
      .chevron { grid-column: 3; grid-row: 1 / span 2; }
      .opportunity-details { padding-left: 18px; }
      .detail-grid { grid-template-columns: 1fr 1fr; }
    }

    @media (max-width: 700px) {
      .shell { width: min(100% - 20px, 1180px); padding-top: 14px; }
      .topbar { align-items: flex-start; }
      .system-chip { display: none; }
      .hero { grid-template-columns: 1fr; gap: 15px; }
      .refresh-button { justify-self: start; }
      .kpis { grid-template-columns: 1fr; }
      .toolbar { align-items: stretch; flex-direction: column; }
      .toolbar-left { align-items: stretch; flex-direction: column; }
      .source-select { width: 100%; }
      .opportunity { grid-template-columns: minmax(0, 1fr); }
      .opportunity-toggle { grid-template-columns: minmax(0, 1fr) 28px; gap: 8px 12px; padding-right: 18px; }
      .source-pill { grid-column: 1; }
      .opportunity-title { grid-column: 1; }
      .deadline-block { grid-column: 1; grid-row: auto; }
      .chevron { grid-column: 2; grid-row: 1 / span 3; }
      .row-action { padding: 0 18px 14px; }
      .row-source-link { width: 100%; min-height: 44px; }
      .detail-grid { grid-template-columns: 1fr; }
    }

    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
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
      <button id="kpi-current" class="kpi kpi-blue" type="button">
        <span class="kpi-label">Nykyiset rahoitushaut</span>
        <strong class="kpi-value" id="total-calls">–</strong>
        <span class="kpi-detail">Kaikkien lähteiden viimeisin onnistunut tilannekuva</span>
        <span class="kpi-action">Näytä kaikki haut →</span>
      </button>
      <button id="kpi-healthy" class="kpi kpi-green" type="button">
        <span class="kpi-label">Terveet lähteet</span>
        <strong class="kpi-value" id="healthy-sources">–</strong>
        <span class="kpi-detail" id="healthy-detail">Lähdetilaa ladataan</span>
        <span class="kpi-action">Näytä lähteet →</span>
      </button>
      <button id="kpi-attention" class="kpi kpi-amber" type="button">
        <span class="kpi-label">Huomiota vaativat lähteet</span>
        <strong class="kpi-value" id="attention-sources">–</strong>
        <span class="kpi-detail">FAILED / RUNNING / ei vielä skannattu</span>
        <span class="kpi-action">Tarkista tila →</span>
      </button>
      <button id="kpi-latest" class="kpi kpi-purple" type="button">
        <span class="kpi-label">Viimeisin onnistunut lähdeajo</span>
        <strong class="kpi-value" id="latest-success">–</strong>
        <span class="kpi-detail" id="latest-success-detail">Ei vielä tietoa</span>
        <span class="kpi-action">Näytä viimeisin lähde →</span>
      </button>
    </section>

    <section id="sources-section" class="section" aria-labelledby="sources-heading">
      <div class="section-head">
        <div>
          <h2 id="sources-heading">Lähteiden tila</h2>
          <p>Klikkaa lähdekorttia rajataksesi rahoitushaut. Avaa lähde -painike vie alkuperäiselle julkiselle seurantasivulle.</p>
        </div>
      </div>
      <div id="source-grid" class="source-grid" aria-live="polite">
        <div class="loading-state">Ladataan lähteiden tilaa…</div>
      </div>
    </section>

    <section id="calls-section" class="section" aria-labelledby="calls-heading">
      <div class="section-head">
        <div>
          <h2 id="calls-heading">Nykyiset rahoitushaut</h2>
          <p>Avaa rivi tarkempia tallennettuja tietoja varten tai siirry suoraan alkuperäiseen lähteeseen.</p>
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
    const state = { health: [], calls: [], details: new Map(), source: "", latestSource: null };

    const SOURCE_META = {
      STM: {
        name: "STM",
        home: "https://stm.fi/vuoden-2026-valtionavustushaut",
      },
      SITRA: {
        name: "Sitra",
        home: "https://asiointi.sitra.fi/",
      },
      ACADEMY: {
        name: "Suomen Akatemia",
        home: "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/",
      },
    };

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
      sourcesSection: document.getElementById("sources-section"),
      callsSection: document.getElementById("calls-section"),
      kpiCurrent: document.getElementById("kpi-current"),
      kpiHealthy: document.getElementById("kpi-healthy"),
      kpiAttention: document.getElementById("kpi-attention"),
      kpiLatest: document.getElementById("kpi-latest"),
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

    function sourceMeta(code) {
      return SOURCE_META[code] || { name: code, home: null };
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

      const days = Math.ceil((date.getTime() - Date.now()) / 86400000);
      const label = new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium", timeStyle: "short" }).format(date);

      if (days < 0) return { label, className: "deadline-past" };
      if (days <= 7) return { label, className: "deadline-soon" };
      return { label, className: "" };
    }

    function healthLabel(value) {
      const labels = { HEALTHY: "Toimii", FAILING: "Virhe", RUNNING: "Käynnissä", NEVER_SCANNED: "Ei vielä ajoa" };
      return labels[value] || value;
    }

    function addFact(container, label, value) {
      const row = document.createElement("div");
      row.className = "fact";
      row.append(text("span", label));
      row.append(text("strong", value));
      container.append(row);
    }

    function flashCards(predicate) {
      document.querySelectorAll(".source-card").forEach((card) => {
        card.classList.remove("flash");
        if (predicate(card)) {
          void card.offsetWidth;
          card.classList.add("flash");
        }
      });
    }

    async function applySourceFilter(sourceCode, scroll = true) {
      state.source = sourceCode;
      elements.sourceFilter.value = sourceCode;
      state.calls = [];
      state.details.clear();
      elements.opportunityList.replaceChildren(text("div", "Ladataan…", "loading-state"));
      try {
        await fetchCalls();
        clearError();
        if (scroll) elements.callsSection.scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (error) {
        showError("Rahoitushakuja ei saatu ladattua valitulle lähteelle.");
      }
    }

    function renderHealth() {
      clear(elements.sourceGrid);

      const totalCurrent = state.health.reduce((sum, item) => sum + Number(item.current_call_count || 0), 0);
      elements.totalCalls.textContent = String(totalCurrent);

      if (!state.health.length) {
        elements.sourceGrid.append(text("div", "Yhtään määritettyä lähdettä ei löytynyt.", "empty-state"));
        elements.healthySources.textContent = "0";
        elements.attentionSources.textContent = "0";
        elements.healthyDetail.textContent = "0 määritettyä lähdettä";
        state.latestSource = null;
        return;
      }

      const healthy = state.health.filter((item) => item.health === "HEALTHY").length;
      const attention = state.health.length - healthy;
      elements.healthySources.textContent = String(healthy);
      elements.attentionSources.textContent = String(attention);
      elements.healthyDetail.textContent = `${healthy}/${state.health.length} lähdettä toimii`;

      const successful = state.health
        .filter((item) => item.last_successful_scan_at)
        .map((item) => ({ item, date: new Date(item.last_successful_scan_at) }))
        .filter(({ date }) => !Number.isNaN(date.getTime()))
        .sort((a, b) => b.date.getTime() - a.date.getTime());

      if (successful.length) {
        const latest = successful[0];
        state.latestSource = latest.item.source_code;
        elements.latestSuccess.textContent = new Intl.DateTimeFormat("fi-FI", { hour: "2-digit", minute: "2-digit" }).format(latest.date);
        elements.latestSuccessDetail.textContent = `${sourceMeta(latest.item.source_code).name} · ${new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium" }).format(latest.date)}`;
      } else {
        state.latestSource = null;
        elements.latestSuccess.textContent = "–";
        elements.latestSuccessDetail.textContent = "Ei onnistuneita ajoja";
      }

      const existingOptions = new Set(Array.from(elements.sourceFilter.options).map((option) => option.value));

      for (const item of state.health) {
        const meta = sourceMeta(item.source_code);

        if (!existingOptions.has(item.source_code)) {
          const option = document.createElement("option");
          option.value = item.source_code;
          option.textContent = meta.name;
          elements.sourceFilter.append(option);
        }

        const card = document.createElement("article");
        card.className = "source-card";
        card.dataset.source = item.source_code;
        card.dataset.health = item.health;

        const main = document.createElement("button");
        main.type = "button";
        main.className = "source-card-main";
        main.setAttribute("aria-label", `Näytä lähteen ${meta.name} nykyiset rahoitushaut`);
        main.addEventListener("click", () => applySourceFilter(item.source_code));

        const head = document.createElement("div");
        head.className = "source-card-head";
        head.append(text("div", meta.name, "source-name"));

        const badge = text("span", healthLabel(item.health), "health-badge");
        badge.classList.add(`health-${String(item.health).toLowerCase()}`);
        head.append(badge);
        main.append(head);

        const count = document.createElement("div");
        count.className = "source-count";
        count.append(document.createTextNode(String(item.current_call_count)));
        count.append(text("span", "nykyistä hakua"));
        main.append(count);

        const facts = document.createElement("div");
        facts.className = "fact-list";
        addFact(facts, "Viimeisin onnistunut ajo", formatDateTime(item.last_successful_scan_at));
        addFact(facts, "Viimeisin ajotila", item.latest_scan_status || "Ei tietoa");
        addFact(facts, "Uusia / muuttuneita", `${item.latest_new_count ?? "–"} / ${item.latest_changed_count ?? "–"}`);
        if (item.latest_error_type) addFact(facts, "Virheluokka", item.latest_error_type);
        main.append(facts);
        card.append(main);

        const footer = document.createElement("div");
        footer.className = "source-card-footer";
        footer.append(text("span", "Näytä tämän lähteen haut →", "source-filter-hint"));

        if (meta.home) {
          const sourceHome = document.createElement("a");
          sourceHome.className = "source-home-link";
          sourceHome.href = meta.home;
          sourceHome.target = "_blank";
          sourceHome.rel = "noopener noreferrer";
          sourceHome.textContent = "Avaa lähde ↗";
          footer.append(sourceHome);
        }

        card.append(footer);
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
      link.textContent = "Avaa alkuperäinen lähde ↗";
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
      elements.listCount.textContent = state.source
        ? `${state.calls.length} hakua · ${sourceMeta(state.source).name}`
        : `${state.calls.length} hakua · kaikki lähteet`;

      if (!state.calls.length) {
        elements.opportunityList.append(text("div", "Valitussa viimeisimmässä onnistuneessa tilannekuvassa ei ole nykyisiä rahoitushakuja.", "empty-state"));
        return;
      }

      state.calls.forEach((call) => {
        const row = document.createElement("article");
        row.className = "opportunity";
        row.dataset.source = call.source_code;

        const detailsId = `funding-call-${call.id}-details`;
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "opportunity-toggle";
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-controls", detailsId);
        toggle.append(text("span", sourceMeta(call.source_code).name, "source-pill"));
        toggle.append(text("span", call.title, "opportunity-title"));

        const deadline = formatDeadline(call.application_deadline_at);
        const deadlineBlock = document.createElement("span");
        deadlineBlock.className = "deadline-block";
        if (deadline.className) deadlineBlock.classList.add(deadline.className);
        deadlineBlock.append(text("span", "Hakuaika päättyy", "deadline-label"));
        deadlineBlock.append(text("span", deadline.label, "deadline-value"));
        toggle.append(deadlineBlock);
        toggle.append(text("span", "›", "chevron"));

        const rowAction = document.createElement("div");
        rowAction.className = "row-action";
        const directLink = document.createElement("a");
        directLink.className = "row-source-link";
        directLink.href = call.source_url;
        directLink.target = "_blank";
        directLink.rel = "noopener noreferrer";
        directLink.textContent = "Avaa lähde ↗";
        directLink.setAttribute("aria-label", `Avaa alkuperäinen lähde: ${call.title}`);
        rowAction.append(directLink);

        const details = document.createElement("div");
        details.id = detailsId;
        details.className = "opportunity-details";
        details.hidden = true;

        toggle.addEventListener("click", async () => {
          const expanded = toggle.getAttribute("aria-expanded") === "true";
          toggle.setAttribute("aria-expanded", String(!expanded));
          details.hidden = expanded;
          if (!expanded) await loadDetail(call.id, details);
        });

        row.append(toggle, rowAction, details);
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

    elements.sourceFilter.addEventListener("change", (event) => {
      applySourceFilter(event.target.value, false);
    });

    elements.refreshButton.addEventListener("click", () => {
      state.details.clear();
      loadDashboard();
    });

    elements.kpiCurrent.addEventListener("click", () => applySourceFilter(""));

    elements.kpiHealthy.addEventListener("click", () => {
      elements.sourcesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      flashCards((card) => card.dataset.health === "HEALTHY");
    });

    elements.kpiAttention.addEventListener("click", () => {
      elements.sourcesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      flashCards((card) => card.dataset.health !== "HEALTHY");
    });

    elements.kpiLatest.addEventListener("click", () => {
      elements.sourcesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      if (state.latestSource) flashCards((card) => card.dataset.source === state.latestSource);
    });

    loadDashboard();
  </script>
</body>
</html>
"""
