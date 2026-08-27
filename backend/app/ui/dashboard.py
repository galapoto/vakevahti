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
      --bg: #f5f7f8;
      --surface: #ffffff;
      --text: #17212b;
      --muted: #667085;
      --border: #dfe5e8;
      --accent: #0f766e;
      --accent-soft: #e8f5f3;
      --good: #16845b;
      --good-soft: #eaf7f1;
      --danger: #b42318;
      --shadow: 0 8px 24px rgba(16, 24, 40, .06);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }

    .shell {
      width: min(980px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 34px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 11px;
    }

    .logo {
      width: 38px;
      height: 38px;
      display: grid;
      place-items: center;
      border-radius: 10px;
      background: var(--accent);
      color: white;
      font-weight: 800;
      font-size: 13px;
    }

    .brand strong { display: block; font-size: 17px; }
    .brand span { color: var(--muted); font-size: 12px; }

    .demo-tag {
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
    }

    .intro {
      text-align: center;
      margin: 0 auto 28px;
      max-width: 680px;
    }

    .intro h1 {
      margin: 0 0 10px;
      font-size: clamp(28px, 5vw, 42px);
      letter-spacing: -.035em;
      line-height: 1.08;
    }

    .intro p {
      margin: 0;
      color: var(--muted);
      line-height: 1.6;
      font-size: 15px;
    }

    .flow {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }

    .step {
      position: relative;
      padding: 18px;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: var(--surface);
      box-shadow: var(--shadow);
      min-height: 122px;
    }

    .step-number {
      width: 27px;
      height: 27px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 800;
      font-size: 12px;
      margin-bottom: 12px;
    }

    .step h2 {
      margin: 0 0 6px;
      font-size: 16px;
    }

    .step p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }

    .count {
      color: var(--accent);
      font-weight: 800;
      font-size: 24px;
      line-height: 1;
    }

    .action-card,
    .results-card {
      border: 1px solid var(--border);
      border-radius: 16px;
      background: var(--surface);
      box-shadow: var(--shadow);
    }

    .action-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      padding: 20px;
      margin-bottom: 18px;
    }

    .action-card h2 {
      margin: 0 0 5px;
      font-size: 18px;
    }

    .action-card p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }

    button {
      appearance: none;
      border: 0;
      border-radius: 10px;
      padding: 12px 18px;
      font: inherit;
      font-weight: 750;
      color: white;
      background: var(--accent);
      cursor: pointer;
      white-space: nowrap;
    }

    button:hover { filter: brightness(.96); }
    button:disabled { opacity: .55; cursor: wait; }

    .status {
      display: none;
      align-items: center;
      gap: 8px;
      padding: 11px 13px;
      margin-bottom: 16px;
      border-radius: 10px;
      background: var(--good-soft);
      color: var(--good);
      font-size: 13px;
      font-weight: 650;
    }

    .status.visible { display: flex; }
    .status.error { background: #fff0ee; color: var(--danger); }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
      flex: 0 0 auto;
    }

    .results-card { padding: 22px; }

    .results-head {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }

    .results-head h2 { margin: 0 0 4px; font-size: 19px; }
    .results-head p { margin: 0; color: var(--muted); font-size: 13px; }

    .empty {
      padding: 34px 20px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed var(--border);
      border-radius: 12px;
      font-size: 14px;
    }

    .calls { display: grid; gap: 8px; }

    .call {
      display: grid;
      grid-template-columns: 30px 1fr auto;
      align-items: center;
      gap: 11px;
      padding: 12px 13px;
      border: 1px solid var(--border);
      border-radius: 11px;
    }

    .call-index {
      width: 28px;
      height: 28px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      background: #f0f3f5;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
    }

    .call-title {
      font-size: 13px;
      font-weight: 650;
      line-height: 1.4;
    }

    .badge {
      padding: 5px 8px;
      border-radius: 999px;
      background: var(--good-soft);
      color: var(--good);
      font-size: 10px;
      font-weight: 800;
      white-space: nowrap;
    }

    .more-button {
      display: none;
      margin: 14px auto 0;
      color: var(--accent);
      background: transparent;
      border: 1px solid var(--border);
    }

    .more-button.visible { display: block; }

    details {
      margin-top: 16px;
      border-top: 1px solid var(--border);
      padding-top: 14px;
      color: var(--muted);
      font-size: 12px;
    }

    summary {
      color: var(--text);
      cursor: pointer;
      font-weight: 650;
    }

    .technical {
      margin-top: 10px;
      line-height: 1.7;
    }

    code {
      padding: 2px 5px;
      border-radius: 5px;
      background: #f0f3f5;
      color: #344054;
    }

    @media (max-width: 720px) {
      .flow { grid-template-columns: 1fr; }
      .action-card { align-items: stretch; flex-direction: column; }
      .call { grid-template-columns: 30px 1fr; }
      .badge { grid-column: 2; justify-self: start; }
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
          <strong>VakeVahti</strong>
          <span>Rahoitushakujen seuranta</span>
        </div>
      </div>
      <div class="demo-tag">Kehitysdemo</div>
    </header>

    <section class="intro">
      <h1>Näin VakeVahti toimii</h1>
      <p>
        Järjestelmä tarkistaa julkisen rahoituslähteen, poimii rahoitushaut ja muuttaa ne
        yhtenäiseen, tarkistettavaan muotoon.
      </p>
    </section>

    <section class="flow" aria-label="VakeVahdin toimintavaiheet">
      <article class="step">
        <div class="step-number">1</div>
        <h2>Lähde</h2>
        <p><strong>STM</strong><br>stm.fi:n valtionavustushaut</p>
      </article>
      <article class="step">
        <div class="step-number">2</div>
        <h2>Haku ja käsittely</h2>
        <p>VakeVahti hakee sivun, tunnistaa haut ja validoi tiedot.</p>
      </article>
      <article class="step">
        <div class="step-number">3</div>
        <h2>Tulos</h2>
        <p><span class="count" id="call-count">–</span><br><span id="count-label">rahoitushakua löydetty</span></p>
      </article>
    </section>

    <section class="action-card">
      <div>
        <h2>Kokeile live-hakua</h2>
        <p>Painike hakee tiedot oikeasti STM:n verkkosivulta juuri nyt.</p>
      </div>
      <button id="scan-button" type="button">Hae STM:n rahoitushaut</button>
    </section>

    <div class="status" id="scan-status" role="status">
      <span class="status-dot"></span>
      <span id="scan-message"></span>
    </div>

    <section class="results-card">
      <div class="results-head">
        <div>
          <h2>Löydetyt rahoitushaut</h2>
          <p id="results-subtitle">Käynnistä haku nähdäksesi nykyiset tulokset.</p>
        </div>
      </div>

      <div id="calls" class="calls">
        <div class="empty">Ei tuloksia vielä.</div>
      </div>
      <button id="more-button" class="more-button" type="button">Näytä kaikki</button>

      <details>
        <summary>Näytä tekninen toteutus</summary>
        <div class="technical">
          Live-polku: <code>STM → HTTP → HTML-parsinta → FundingCallCandidate → validointi → API → UI</code>.<br>
          PostgreSQL-, muutostunnistus- ja historiakerros on toteutettu, mutta paikallinen tietokanta
          odottaa työaseman hyväksyttyä PostgreSQL-runtimea.
        </div>
      </details>
    </section>
  </main>

  <script>
    const scanButton = document.getElementById('scan-button');
    const callsNode = document.getElementById('calls');
    const countNode = document.getElementById('call-count');
    const countLabel = document.getElementById('count-label');
    const statusNode = document.getElementById('scan-status');
    const messageNode = document.getElementById('scan-message');
    const subtitleNode = document.getElementById('results-subtitle');
    const moreButton = document.getElementById('more-button');

    let allCalls = [];
    let expanded = false;

    function setStatus(message, isError = false) {
      messageNode.textContent = message;
      statusNode.classList.add('visible');
      statusNode.classList.toggle('error', isError);
    }

    function createCallRow(call, index) {
      const row = document.createElement('div');
      row.className = 'call';

      const number = document.createElement('div');
      number.className = 'call-index';
      number.textContent = String(index + 1).padStart(2, '0');

      const title = document.createElement('div');
      title.className = 'call-title';
      title.textContent = call.title;

      const badge = document.createElement('div');
      badge.className = 'badge';
      badge.textContent = call.relevance_status === 'RELEVANT' ? 'Relevantti' : call.relevance_status;

      row.append(number, title, badge);
      return row;
    }

    function renderCalls() {
      callsNode.replaceChildren();

      if (!allCalls.length) {
        const empty = document.createElement('div');
        empty.className = 'empty';
        empty.textContent = 'Rahoitushakuja ei löytynyt.';
        callsNode.appendChild(empty);
        moreButton.classList.remove('visible');
        return;
      }

      const visibleCalls = expanded ? allCalls : allCalls.slice(0, 5);
      visibleCalls.forEach((call, index) => callsNode.appendChild(createCallRow(call, index)));

      if (allCalls.length > 5) {
        moreButton.classList.add('visible');
        moreButton.textContent = expanded ? 'Näytä vähemmän' : `Näytä kaikki (${allCalls.length})`;
      } else {
        moreButton.classList.remove('visible');
      }
    }

    async function runScan() {
      scanButton.disabled = true;
      scanButton.textContent = 'Haetaan…';
      statusNode.classList.remove('error');
      setStatus('Haetaan STM:n rahoitushakuja…');
      subtitleNode.textContent = 'Live-haku on käynnissä.';

      try {
        const response = await fetch('/api/demo/stm-calls', { cache: 'no-store' });
        if (!response.ok) {
          const errorPayload = await response.json().catch(() => ({}));
          throw new Error(errorPayload.detail || `HTTP ${response.status}`);
        }

        const payload = await response.json();
        allCalls = payload.calls || [];
        expanded = false;
        countNode.textContent = String(payload.count);
        countLabel.textContent = payload.count === 1 ? 'rahoitushaku löydetty' : 'rahoitushakua löydetty';
        subtitleNode.textContent = `STM:stä löytyi ${payload.count} rahoitushakua.`;
        setStatus(`Valmis. ${payload.count} rahoitushakua löydetty ja validoitu.`);
        renderCalls();
      } catch (error) {
        allCalls = [];
        countNode.textContent = '–';
        subtitleNode.textContent = 'Hakua ei voitu suorittaa.';
        callsNode.innerHTML = '<div class="empty">Tuloksia ei voitu ladata.</div>';
        moreButton.classList.remove('visible');
        setStatus(`Haku epäonnistui: ${error.message}`, true);
      } finally {
        scanButton.disabled = false;
        scanButton.textContent = 'Hae STM:n rahoitushaut';
      }
    }

    scanButton.addEventListener('click', runScan);
    moreButton.addEventListener('click', () => {
      expanded = !expanded;
      renderCalls();
    });
  </script>
</body>
</html>
"""
