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

    button, a { font: inherit; }

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
      max-width: 700px;
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
      border-radius: 14px;
      box-shadow: var(--shadow);
      min-height: 132px;
      border: 1px solid var(--step-border);
      background: var(--step-bg);
    }

    .step-source {
      --step-color: #1d4ed8;
      --step-bg: #eff6ff;
      --step-border: #bfdbfe;
    }

    .step-process {
      --step-color: #b45309;
      --step-bg: #fffbeb;
      --step-border: #fde68a;
    }

    .step-result {
      --step-color: #047857;
      --step-bg: #ecfdf5;
      --step-border: #a7f3d0;
    }

    .step-number {
      width: 28px;
      height: 28px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      color: white;
      background: var(--step-color);
      font-weight: 800;
      font-size: 12px;
      margin-bottom: 12px;
    }

    .step h2 {
      margin: 0 0 7px;
      color: var(--step-color);
      font-size: 17px;
      font-weight: 800;
    }

    .step p {
      margin: 0;
      color: #475467;
      font-size: 13px;
      line-height: 1.55;
    }

    .step strong { color: var(--step-color); }

    .count {
      color: var(--step-color);
      font-weight: 850;
      font-size: 26px;
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
      max-width: 690px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }

    .primary-button {
      appearance: none;
      border: 0;
      border-radius: 10px;
      padding: 12px 18px;
      font-weight: 750;
      color: white;
      background: var(--accent);
      cursor: pointer;
      white-space: nowrap;
    }

    .primary-button:hover { filter: brightness(.96); }
    .primary-button:disabled { opacity: .55; cursor: wait; }

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
      --row-bg: #ffffff;
      overflow: hidden;
      border: 1px solid var(--border);
      border-radius: 11px;
      background: var(--row-bg);
      transition: border-color .14s ease, box-shadow .14s ease;
    }

    .call:nth-child(even) { --row-bg: #f3f7fb; }

    .call:hover {
      border-color: #b7c8d8;
      box-shadow: 0 4px 14px rgba(16, 24, 40, .05);
    }

    .call-toggle {
      width: 100%;
      display: grid;
      grid-template-columns: 30px 1fr auto auto;
      align-items: center;
      gap: 11px;
      padding: 12px 13px;
      border: 0;
      color: inherit;
      background: var(--row-bg);
      text-align: left;
      cursor: pointer;
    }

    .call-toggle:hover { filter: brightness(.985); }
    .call-toggle:focus-visible { outline: 3px solid rgba(15, 118, 110, .22); outline-offset: -3px; }

    .call-index {
      width: 28px;
      height: 28px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      background: #e8eef3;
      color: #536476;
      font-size: 11px;
      font-weight: 800;
    }

    .call-title {
      min-width: 0;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.45;
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

    .chevron {
      color: #667085;
      font-size: 20px;
      line-height: 1;
      transition: transform .16s ease;
    }

    .call-toggle[aria-expanded="true"] .chevron { transform: rotate(90deg); }

    .call-details {
      padding: 15px 17px 17px 58px;
      border-top: 1px solid var(--border);
      background: rgba(255, 255, 255, .72);
    }

    .detail-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 14px;
      margin-bottom: 13px;
    }

    .detail-label {
      display: block;
      margin-bottom: 4px;
      color: #667085;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: .06em;
      text-transform: uppercase;
    }

    .detail-value {
      margin: 0;
      color: #344054;
      font-size: 13px;
      line-height: 1.55;
    }

    .summary-box {
      padding: 12px 13px;
      border-radius: 10px;
      background: #f8fafc;
      border: 1px solid #e6ebef;
    }

    .source-link {
      display: inline-flex;
      margin-top: 12px;
      padding: 7px 10px;
      border: 1px solid #cbd5dc;
      border-radius: 8px;
      color: var(--accent);
      background: white;
      font-size: 12px;
      font-weight: 700;
      text-decoration: none;
    }

    .source-link:hover { background: #f7fbfa; }

    .more-button {
      display: none;
      margin: 14px auto 0;
      padding: 9px 14px;
      border-radius: 9px;
      color: var(--accent);
      background: transparent;
      border: 1px solid var(--border);
      cursor: pointer;
      font-weight: 700;
    }

    .more-button.visible { display: block; }

    details.technical-details {
      margin-top: 16px;
      border-top: 1px solid var(--border);
      padding-top: 14px;
      color: var(--muted);
      font-size: 12px;
    }

    details.technical-details summary {
      color: var(--text);
      cursor: pointer;
      font-weight: 650;
    }

    .technical { margin-top: 10px; line-height: 1.7; }

    code {
      padding: 2px 5px;
      border-radius: 5px;
      background: #f0f3f5;
      color: #344054;
    }

    @media (max-width: 720px) {
      .flow { grid-template-columns: 1fr; }
      .action-card { align-items: stretch; flex-direction: column; }
      .call-toggle { grid-template-columns: 30px 1fr auto; }
      .badge { grid-column: 2; justify-self: start; }
      .chevron { grid-column: 3; grid-row: 1 / span 2; }
      .call-details { padding-left: 17px; }
      .detail-grid { grid-template-columns: 1fr; }
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
        Valmiissa käytössä VakeVahti tarkistaa rahoituslähteet automaattisesti ajastuksen mukaan.
        Tässä kehitysdemossa nykyinen STM-adapteri voidaan käynnistää käsin.
      </p>
    </section>

    <section class="flow" aria-label="VakeVahdin toimintavaiheet">
      <article class="step step-source">
        <div class="step-number">1</div>
        <h2>Seurattava lähde</h2>
        <p><strong>Nykyinen toteutus: STM</strong><br>stm.fi:n valtionavustushaut</p>
      </article>
      <article class="step step-process">
        <div class="step-number">2</div>
        <h2>Automaattinen käsittely</h2>
        <p>VakeVahti hakee sivun, tunnistaa haut ja validoi tiedot.</p>
      </article>
      <article class="step step-result">
        <div class="step-number">3</div>
        <h2>Tulos</h2>
        <p><span class="count" id="call-count">–</span><br><span id="count-label">rahoitushakua löydetty</span></p>
      </article>
    </section>

    <section class="action-card">
      <div>
        <h2>Manuaalinen testihaku</h2>
        <p>
          Painike on demo- ja ylläpitokäyttöä varten. Varsinainen seuranta rakennetaan
          ajastetuksi, jolloin käyttäjän ei tarvitse käynnistää hakua itse.
        </p>
      </div>
      <button id="scan-button" class="primary-button" type="button">Päivitä STM nyt</button>
    </section>

    <div class="status" id="scan-status" role="status">
      <span class="status-dot"></span>
      <span id="scan-message"></span>
    </div>

    <section class="results-card">
      <div class="results-head">
        <div>
          <h2>Löydetyt rahoitushaut</h2>
          <p id="results-subtitle">Käynnistä testihaku nähdäksesi nykyiset STM-tulokset.</p>
        </div>
      </div>

      <div id="calls" class="calls">
        <div class="empty">Ei tuloksia vielä.</div>
      </div>
      <button id="more-button" class="more-button" type="button">Näytä kaikki</button>

      <details class="technical-details">
        <summary>Näytä tekninen toteutus</summary>
        <div class="technical">
          Nykyinen toimiva live-polku: <code>STM → HTTP → HTML-parsinta → FundingCallCandidate → validointi → API → UI</code>.<br>
          Suunnitellut seurantalähteet: STM, Haeavustuksia.fi, EURA 2021, Sitra ja Suomen Akatemia.<br>
          Seuraavat tuotantovaiheet ovat PostgreSQL-persistenssin käyttöönotto, ajastettu seuranta,
          muutostunnistus ja ilmoitukset. Manuaalinen "Päivitä nyt" säilyy ylläpito- ja testitoimintona.
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
    let openCallKey = null;

    function setStatus(message, isError = false) {
      messageNode.textContent = message;
      statusNode.classList.add('visible');
      statusNode.classList.toggle('error', isError);
    }

    function formatDate(value) {
      if (!value) return null;
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return String(value);
      return new Intl.DateTimeFormat('fi-FI').format(date);
    }

    function deadlineText(call) {
      const structured = formatDate(call.application_deadline_at);
      if (structured) return structured;

      const text = call.description_text || '';
      const range = text.match(/(\d{1,2}\.\d{1,2}\.\d{4})\s*[-–]\s*(\d{1,2}\.\d{1,2}\.\d{4})/);
      if (range) return `${range[1]} - ${range[2]}`;

      const single = text.match(/(?:määräaika|hakuaika|haku)[^0-9]{0,50}(\d{1,2}\.\d{1,2}\.\d{4})/i);
      if (single) return single[1];

      return 'Ei erillistä määräaikatietoa tässä listanäkymässä.';
    }

    function summaryText(call) {
      const raw = (call.description_text || call.relevance_reason || '').trim();
      if (!raw) return 'Tarkempaa sisältökuvausta ei ole vielä saatavilla.';
      return raw.length > 320 ? `${raw.slice(0, 317)}…` : raw;
    }

    function relevanceLabel(status) {
      if (status === 'RELEVANT') return 'Relevantti';
      if (status === 'NEEDS_REVIEW') return 'Tarkistettava';
      if (status === 'NOT_RELEVANT') return 'Ei relevantti';
      return status || 'Tila puuttuu';
    }

    function createDetailBlock(label, value) {
      const block = document.createElement('div');
      const labelNode = document.createElement('span');
      labelNode.className = 'detail-label';
      labelNode.textContent = label;

      const valueNode = document.createElement('p');
      valueNode.className = 'detail-value';
      valueNode.textContent = value;

      block.append(labelNode, valueNode);
      return block;
    }

    function createCallRow(call, index) {
      const key = call.external_key || `${index}-${call.title}`;
      const isOpen = openCallKey === key;

      const row = document.createElement('article');
      row.className = 'call';

      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'call-toggle';
      toggle.setAttribute('aria-expanded', String(isOpen));
      toggle.setAttribute('aria-label', `${call.title}. Näytä tai piilota lisätiedot.`);

      const number = document.createElement('div');
      number.className = 'call-index';
      number.textContent = String(index + 1).padStart(2, '0');

      const title = document.createElement('div');
      title.className = 'call-title';
      title.textContent = call.title;

      const badge = document.createElement('div');
      badge.className = 'badge';
      badge.textContent = relevanceLabel(call.relevance_status);

      const chevron = document.createElement('span');
      chevron.className = 'chevron';
      chevron.setAttribute('aria-hidden', 'true');
      chevron.textContent = '›';

      toggle.append(number, title, badge, chevron);
      toggle.addEventListener('click', () => {
        openCallKey = openCallKey === key ? null : key;
        renderCalls();
      });

      row.appendChild(toggle);

      if (isOpen) {
        const details = document.createElement('div');
        details.className = 'call-details';

        const grid = document.createElement('div');
        grid.className = 'detail-grid';
        grid.append(
          createDetailBlock('Hakuaika / määräaika', deadlineText(call)),
          createDetailBlock('Lähde', call.source_code || 'STM')
        );

        const summary = document.createElement('div');
        summary.className = 'summary-box';
        summary.appendChild(createDetailBlock('Lyhyt sisältö', summaryText(call)));

        details.append(grid, summary);

        if (call.source_url) {
          const sourceLink = document.createElement('a');
          sourceLink.className = 'source-link';
          sourceLink.href = call.source_url;
          sourceLink.target = '_blank';
          sourceLink.rel = 'noreferrer';
          sourceLink.textContent = 'Avaa STM:n lähdesivu';
          details.appendChild(sourceLink);
        }

        row.appendChild(details);
      }

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
      scanButton.textContent = 'Päivitetään…';
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
        openCallKey = null;
        countNode.textContent = String(payload.count);
        countLabel.textContent = payload.count === 1 ? 'rahoitushaku löydetty' : 'rahoitushakua löydetty';
        subtitleNode.textContent = `STM:stä löytyi ${payload.count} rahoitushakua. Klikkaa riviä nähdäksesi lisätiedot.`;
        setStatus(`Valmis. ${payload.count} rahoitushakua löydetty ja validoitu.`);
        renderCalls();
      } catch (error) {
        allCalls = [];
        openCallKey = null;
        countNode.textContent = '–';
        subtitleNode.textContent = 'Hakua ei voitu suorittaa.';
        callsNode.innerHTML = '<div class="empty">Tuloksia ei voitu ladata.</div>';
        moreButton.classList.remove('visible');
        setStatus(`Haku epäonnistui: ${error.message}`, true);
      } finally {
        scanButton.disabled = false;
        scanButton.textContent = 'Päivitä STM nyt';
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
