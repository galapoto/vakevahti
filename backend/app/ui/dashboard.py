"""Self-contained development dashboard served by FastAPI.

This is intentionally dependency-light so it can run on the managed workplace
machine without Node.js or a separate frontend toolchain. It is a mentor/demo
surface, not the final employee-facing UI.
"""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="fi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VakeVahti | Kehitysdemo</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111f;
      --panel: #0d1a2b;
      --panel-2: #102238;
      --border: #203a55;
      --text: #edf5ff;
      --muted: #9eb1c5;
      --accent: #5bd4c7;
      --accent-2: #8aa7ff;
      --good: #72dfa7;
      --warn: #f0c66f;
      --danger: #ff8f9b;
      --shadow: 0 20px 55px rgba(0, 0, 0, .25);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 10% 0%, rgba(91, 212, 199, .13), transparent 30%),
        radial-gradient(circle at 90% 10%, rgba(138, 167, 255, .12), transparent 28%),
        var(--bg);
    }

    a { color: inherit; }

    .shell {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 56px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 26px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 13px;
    }

    .logo {
      width: 46px;
      height: 46px;
      display: grid;
      place-items: center;
      border-radius: 14px;
      font-weight: 800;
      letter-spacing: -.04em;
      color: #06131c;
      background: linear-gradient(135deg, var(--accent), #9af1e8);
      box-shadow: var(--shadow);
    }

    .brand h1 {
      margin: 0;
      font-size: 20px;
      letter-spacing: -.02em;
    }

    .brand p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .dev-pill {
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(13, 26, 43, .7);
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.5fr .8fr;
      gap: 18px;
      margin-bottom: 18px;
    }

    .panel {
      border: 1px solid var(--border);
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(16, 34, 56, .96), rgba(11, 25, 42, .96));
      box-shadow: var(--shadow);
    }

    .hero-main { padding: 34px; }

    .eyebrow {
      margin: 0 0 12px;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: .14em;
      font-size: 11px;
      font-weight: 800;
    }

    .hero h2 {
      max-width: 760px;
      margin: 0;
      font-size: clamp(30px, 5vw, 56px);
      line-height: 1.02;
      letter-spacing: -.045em;
    }

    .hero-copy {
      max-width: 760px;
      margin: 18px 0 0;
      color: var(--muted);
      line-height: 1.65;
      font-size: 15px;
    }

    .pipeline {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 24px;
    }

    .pipeline span {
      padding: 8px 10px;
      border-radius: 10px;
      border: 1px solid rgba(91, 212, 199, .22);
      background: rgba(91, 212, 199, .08);
      color: #c8fbf6;
      font-size: 12px;
    }

    .hero-side {
      padding: 24px;
      display: grid;
      align-content: center;
      gap: 12px;
    }

    .metric {
      padding: 17px;
      border-radius: 16px;
      background: rgba(5, 17, 31, .48);
      border: 1px solid rgba(255,255,255,.06);
    }

    .metric-label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 7px;
    }

    .metric-value {
      display: flex;
      align-items: baseline;
      gap: 7px;
      font-size: 22px;
      font-weight: 750;
    }

    .metric-value small {
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }

    .status-card { padding: 18px; }

    .status-line {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .status-title {
      font-weight: 700;
      font-size: 14px;
    }

    .status-card p {
      margin: 9px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      box-shadow: 0 0 0 4px rgba(114, 223, 167, .08);
      background: var(--good);
    }

    .dot.warn {
      background: var(--warn);
      box-shadow: 0 0 0 4px rgba(240, 198, 111, .08);
    }

    .section { padding: 24px; }

    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    .section h3 {
      margin: 0;
      font-size: 20px;
      letter-spacing: -.02em;
    }

    .section-subtitle {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    button {
      appearance: none;
      border: 0;
      border-radius: 12px;
      padding: 11px 15px;
      font: inherit;
      font-weight: 750;
      color: #07151b;
      background: linear-gradient(135deg, var(--accent), #8be9df);
      cursor: pointer;
      transition: transform .14s ease, opacity .14s ease;
    }

    button:hover { transform: translateY(-1px); }
    button:disabled { cursor: wait; opacity: .58; transform: none; }

    .scan-state {
      display: flex;
      align-items: center;
      gap: 9px;
      padding: 11px 13px;
      margin-bottom: 14px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(5, 17, 31, .45);
      color: var(--muted);
      font-size: 13px;
    }

    .scan-state strong { color: var(--text); }

    .calls {
      display: grid;
      gap: 10px;
    }

    .call {
      display: grid;
      grid-template-columns: 42px 1fr auto;
      gap: 14px;
      align-items: start;
      padding: 16px;
      border: 1px solid rgba(255,255,255,.07);
      border-radius: 16px;
      background: rgba(5, 17, 31, .38);
    }

    .call-index {
      width: 36px;
      height: 36px;
      display: grid;
      place-items: center;
      border-radius: 11px;
      background: rgba(138, 167, 255, .10);
      color: #cfd8ff;
      font-weight: 800;
      font-size: 12px;
    }

    .call-title {
      margin: 0 0 6px;
      font-size: 14px;
      line-height: 1.45;
    }

    .call-reason {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 7px 9px;
      border-radius: 999px;
      border: 1px solid rgba(114, 223, 167, .2);
      background: rgba(114, 223, 167, .08);
      color: #bdf7d5;
      font-size: 11px;
      font-weight: 750;
      text-decoration: none;
      white-space: nowrap;
    }

    .empty {
      padding: 30px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed var(--border);
      border-radius: 16px;
    }

    .error { color: var(--danger); }

    .footer {
      margin-top: 16px;
      color: #6f8398;
      font-size: 11px;
      text-align: center;
      line-height: 1.5;
    }

    @media (max-width: 820px) {
      .hero, .grid { grid-template-columns: 1fr; }
      .call { grid-template-columns: 38px 1fr; }
      .call .badge { grid-column: 2; justify-self: start; }
      .section-head { align-items: flex-start; flex-direction: column; }
      .topbar { align-items: flex-start; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="logo">VV</div>
        <div>
          <h1>VakeVahti</h1>
          <p>Rahoitusmahdollisuuksien seuranta ja datan käsittely</p>
        </div>
      </div>
      <div class="dev-pill">Kehitysdemo · Milestone 2</div>
    </header>

    <section class="hero">
      <div class="panel hero-main">
        <p class="eyebrow">Työpaikan tarpeesta rakennettu dataputki</p>
        <h2>Julkisista rahoituslähteistä jäljitettävää ja käsiteltävää tietoa.</h2>
        <p class="hero-copy">
          Nykyinen toteutus hakee STM:n rahoitushaut HTTP:n kautta, parsii ne lähderakenteesta,
          normalisoi ne yhteiseen FundingCallCandidate-malliin ja validoi tuloksen. PostgreSQL-
          persistenssikerros, muutosten tunnistus ja historiaversiointi on nyt rakennettu seuraavaa
          käyttöönottovaihetta varten.
        </p>
        <div class="pipeline" aria-label="Dataputki">
          <span>Extract</span><span>Parse</span><span>Normalize</span><span>Validate</span>
          <span>Deduplicate</span><span>Persist</span><span>Detect changes</span>
        </div>
      </div>

      <aside class="panel hero-side">
        <div class="metric">
          <div class="metric-label">Live-lähde</div>
          <div class="metric-value">STM <small>stm.fi</small></div>
        </div>
        <div class="metric">
          <div class="metric-label">Tällä hetkellä löydetty</div>
          <div class="metric-value"><span id="call-count">—</span> <small>rahoitushakua</small></div>
        </div>
        <div class="metric">
          <div class="metric-label">Koodin laatukerrokset</div>
          <div class="metric-value">Ruff · mypy · pytest</div>
        </div>
      </aside>
    </section>

    <section class="grid" aria-label="Järjestelmän tila">
      <article class="panel status-card">
        <div class="status-line"><span class="status-title">FastAPI-palvelu</span><span class="dot"></span></div>
        <p>Käynnissä paikallisesti. Terveystarkistus: <code>/health/live</code>.</p>
      </article>
      <article class="panel status-card">
        <div class="status-line"><span class="status-title">STM-ingestointi</span><span class="dot"></span></div>
        <p>Live HTTP -haku, semanttinen HTML-parsinta, vakaa lähdeavain ja fail-loudly-rakennetarkistus.</p>
      </article>
      <article class="panel status-card">
        <div class="status-line"><span class="status-title">PostgreSQL-kerros</span><span class="dot warn"></span></div>
        <p>Toteutettu SQLAlchemy + Alembic -tasolla. Työasemalla ei vielä ole hyväksyttyä paikallista PostgreSQL-runtimea.</p>
      </article>
    </section>

    <section class="panel section">
      <div class="section-head">
        <div>
          <h3>STM:n rahoitushaut</h3>
          <p class="section-subtitle">Painike käynnistää oikean live-skannauksen nykyisellä adapterilla.</p>
        </div>
        <button id="scan-button" type="button">Hae STM:n haut nyt</button>
      </div>

      <div class="scan-state" id="scan-state">
        <span class="dot warn" id="scan-dot"></span>
        <span id="scan-message">Valmiina live-skannaukseen.</span>
      </div>
      <div class="calls" id="calls"><div class="empty">Rahoitushaut ladataan tähän.</div></div>
    </section>

    <p class="footer">
      Tämä näkymä on kehitysvaiheen mentoridemo. Se näyttää oikeasti toteutetut ominaisuudet eikä esitä
      vielä keskeneräisiä työnkulkuja valmiina tuotantotoimintoina.
    </p>
  </main>

  <script>
    const button = document.getElementById("scan-button");
    const count = document.getElementById("call-count");
    const callsRoot = document.getElementById("calls");
    const scanMessage = document.getElementById("scan-message");
    const scanDot = document.getElementById("scan-dot");

    function make(tag, className, text) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    }

    function renderCalls(calls) {
      callsRoot.replaceChildren();
      if (!calls.length) {
        callsRoot.appendChild(make("div", "empty", "Lähteestä ei löytynyt rahoitushakuja."));
        return;
      }

      calls.forEach((call, index) => {
        const row = make("article", "call");
        row.appendChild(make("div", "call-index", String(index + 1).padStart(2, "0")));

        const content = make("div", "call-content");
        content.appendChild(make("h4", "call-title", call.title));
        content.appendChild(make("p", "call-reason", call.relevance_reason));
        row.appendChild(content);

        const link = make("a", "badge", "RELEVANT · avaa lähde");
        link.href = call.source_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        row.appendChild(link);
        callsRoot.appendChild(row);
      });
    }

    async function scanSTM() {
      button.disabled = true;
      button.textContent = "Haetaan...";
      scanDot.className = "dot warn";
      scanMessage.className = "";
      scanMessage.textContent = "VakeVahti hakee ja jäsentää STM:n live-sivua...";

      try {
        const response = await fetch("/api/demo/stm-calls", { cache: "no-store" });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "Live-skannaus epäonnistui.");

        count.textContent = String(payload.count);
        renderCalls(payload.calls);
        scanDot.className = "dot";
        scanMessage.textContent = `Onnistui: ${payload.count} rahoitushakua löydetty ja validoitu.`;
      } catch (error) {
        count.textContent = "—";
        scanDot.className = "dot warn";
        scanMessage.className = "error";
        scanMessage.textContent = `Skannaus epäonnistui: ${error.message}`;
        callsRoot.replaceChildren(make("div", "empty error", "Lähdettä ei voitu lukea tällä hetkellä."));
      } finally {
        button.disabled = false;
        button.textContent = "Hae STM:n haut nyt";
      }
    }

    button.addEventListener("click", scanSTM);
    window.addEventListener("DOMContentLoaded", scanSTM);
  </script>
</body>
</html>
"""
