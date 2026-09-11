LIVE_SOURCE_TEST_HTML = r"""<!doctype html>
<html lang="fi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VakeVahti · Live-lähdetesti</title>
  <style>
    :root {
      --vake-purple: #312783;
      --vake-purple-soft: #6E67A8;
      --vake-blue: #76CBF3;
      --vake-green: #00983A;
      --vake-good: #1FB578;
      --vake-pink: #E6007E;
      --vake-pink-soft: #EA5297;
      --ink: #1C2325;
      --muted: #5F6B6D;
      --panel: #ffffff;
      --page: #f6f7fb;
      --line: #e4e7ef;
      --review: #B59525;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--page);
      color: var(--ink);
      font: 15px/1.5 Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      background: linear-gradient(120deg, var(--vake-purple), #28738A);
      color: white;
      padding: 34px 24px 30px;
    }
    header .wrap, main { max-width: 1180px; margin: 0 auto; }
    h1 { margin: 0 0 8px; font-size: clamp(28px, 4vw, 44px); line-height: 1.05; }
    header p { margin: 0; max-width: 780px; color: #eef8ff; }
    main { padding: 24px; }
    .notice {
      border-left: 5px solid var(--vake-blue);
      background: #eef9fe;
      border-radius: 14px;
      padding: 16px 18px;
      margin-bottom: 20px;
    }
    .notice strong { color: var(--vake-purple); }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px;
      box-shadow: 0 8px 28px rgba(49, 39, 131, 0.06);
    }
    .controls {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      gap: 12px;
      align-items: end;
    }
    label { display: block; font-weight: 700; margin-bottom: 6px; }
    select, button {
      min-height: 46px;
      border-radius: 12px;
      font: inherit;
    }
    select {
      width: 100%;
      border: 1px solid #cadce0;
      background: white;
      padding: 0 12px;
    }
    button {
      border: 0;
      padding: 0 20px;
      background: var(--vake-purple);
      color: white;
      font-weight: 800;
      cursor: pointer;
    }
    button:hover { filter: brightness(1.08); }
    button:disabled { cursor: wait; opacity: .65; }
    #status { min-height: 24px; margin: 14px 0 0; color: var(--muted); }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 20px;
    }
    .metric {
      background: white;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
    }
    .metric span { display: block; color: var(--muted); font-size: 13px; }
    .metric strong { display: block; margin-top: 5px; font-size: 28px; color: var(--vake-purple); }
    .metric.good strong { color: var(--vake-good); }
    .metric.review strong { color: var(--review); }
    .metric.excluded strong { color: var(--vake-pink); }
    .results { margin-top: 20px; }
    .results-head {
      display: flex;
      gap: 16px;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 10px;
    }
    .results-head h2 { margin: 0; font-size: 21px; }
    .results-head small { color: var(--muted); }
    .table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 16px; }
    table { width: 100%; border-collapse: collapse; min-width: 880px; background: white; }
    th, td { text-align: left; padding: 13px 14px; vertical-align: top; border-bottom: 1px solid var(--line); }
    th { background: #f2f0fa; color: var(--vake-purple); font-size: 13px; }
    tr:last-child td { border-bottom: 0; }
    .title { font-weight: 800; color: var(--ink); }
    .reason { max-width: 460px; color: #475052; }
    .badge {
      display: inline-block;
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
      background: #eef0f4;
    }
    .badge.RELEVANT { background: #e7f8f1; color: #0c7650; }
    .badge.NEEDS_REVIEW { background: #fff7d6; color: #806612; }
    .badge.NOT_RELEVANT { background: #fdebf5; color: #9b0054; }
    a { color: var(--vake-purple); font-weight: 700; }
    .error {
      margin-top: 16px;
      border-radius: 14px;
      background: #fdebf5;
      border: 1px solid #f3bfdc;
      color: #7d164d;
      padding: 14px 16px;
      white-space: pre-wrap;
    }
    [hidden] { display: none !important; }
    @media (max-width: 760px) {
      main { padding: 16px; }
      .controls { grid-template-columns: 1fr; }
      .summary { grid-template-columns: 1fr 1fr; }
      button { width: 100%; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>VakeVahti · Live-lähdetesti</h1>
      <p>
        Tarkista yksi rahoituslähde suoraan verkosta ja näe, miten VakeVahti
        luokittelee tämänhetkiset haut.
      </p>
    </div>
  </header>

  <main>
    <div class="notice">
      <strong>Turvallinen testinäkymä:</strong>
      tämä sivu ei tallenna tuloksia tietokantaan eikä muuta työntekijän dashboardia.
      Se käyttää samoja lähdeadaptereita, joita varsinainen ajastus käyttää.
    </div>

    <section class="panel">
      <div class="controls">
        <div>
          <label for="source">Rahoituslähde</label>
          <select id="source" aria-label="Rahoituslähde"></select>
        </div>
        <button id="run" type="button">Testaa lähde nyt</button>
      </div>
      <p id="status">Ladataan testattavia lähteitä…</p>
    </section>

    <section id="summary" class="summary" hidden>
      <div class="metric"><span>Yhteensä</span><strong id="total">0</strong></div>
      <div class="metric good"><span>Varmistetut</span><strong id="relevant">0</strong></div>
      <div class="metric review"><span>Tarkistettavat</span><strong id="review">0</strong></div>
      <div class="metric excluded"><span>Ei sovellu</span><strong id="excluded">0</strong></div>
    </section>

    <section id="results" class="results" hidden>
      <div class="results-head">
        <h2 id="result-title">Tulokset</h2>
        <small id="duration"></small>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Haku</th>
              <th>Luokitus</th>
              <th>Miksi</th>
              <th>Määräaika</th>
              <th>Lähde</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </section>

    <div id="error" class="error" hidden></div>
  </main>

  <script>
    const sourceSelect = document.querySelector('#source');
    const runButton = document.querySelector('#run');
    const statusText = document.querySelector('#status');
    const summary = document.querySelector('#summary');
    const results = document.querySelector('#results');
    const errorBox = document.querySelector('#error');
    const rows = document.querySelector('#rows');

    const statusNames = {
      RELEVANT: 'Varmistettu',
      NEEDS_REVIEW: 'Tarkistettava',
      NOT_RELEVANT: 'Ei sovellu',
    };

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function formatDateFact(exactValue, dateOnlyValue) {
      if (exactValue) {
        const parsed = new Date(exactValue);
        if (!Number.isNaN(parsed.getTime())) {
          return new Intl.DateTimeFormat('fi-FI', {
            dateStyle: 'medium',
            timeStyle: 'short',
          }).format(parsed);
        }
      }
      if (dateOnlyValue) {
        const parts = dateOnlyValue.split('-').map(Number);
        if (parts.length === 3 && parts.every(Number.isFinite)) {
          const localDate = new Date(parts[0], parts[1] - 1, parts[2]);
          return new Intl.DateTimeFormat('fi-FI', { dateStyle: 'medium' }).format(localDate);
        }
      }
      return '—';
    }

    function renderRows(items) {
      if (!items.length) {
        rows.innerHTML = '<tr><td colspan="5">Lähde ei palauttanut yhtään hakua.</td></tr>';
        return;
      }
      rows.innerHTML = items.map((item) => {
        const status = escapeHtml(item.relevance_status);
        const title = escapeHtml(item.title);
        const reason = escapeHtml(item.relevance_reason);
        const sourceUrl = escapeHtml(item.source_url);
        const deadline = escapeHtml(
          formatDateFact(item.application_deadline_at, item.application_deadline_on)
        );
        return `
          <tr>
            <td><div class="title">${title}</div><small>${escapeHtml(item.external_key)}</small></td>
            <td><span class="badge ${status}">${escapeHtml(statusNames[item.relevance_status] || status)}</span></td>
            <td class="reason">${reason}</td>
            <td>${deadline}</td>
            <td><a href="${sourceUrl}" target="_blank" rel="noopener noreferrer">Avaa lähde</a></td>
          </tr>`;
      }).join('');
    }

    async function loadCatalog() {
      const response = await fetch('/api/test/live-sources');
      if (!response.ok) throw new Error(`Lähdeluettelo epäonnistui (${response.status}).`);
      const payload = await response.json();
      sourceSelect.innerHTML = payload.sources.map((source) =>
        `<option value="${escapeHtml(source.code)}">${escapeHtml(source.label)}</option>`
      ).join('');
      statusText.textContent = 'Valitse lähde ja käynnistä live-testi.';
    }

    async function runScan() {
      const code = sourceSelect.value;
      if (!code) return;

      runButton.disabled = true;
      runButton.textContent = 'Testataan…';
      errorBox.hidden = true;
      summary.hidden = true;
      results.hidden = true;
      statusText.textContent = `${sourceSelect.options[sourceSelect.selectedIndex].text} haetaan suoraan lähteestä…`;

      try {
        const response = await fetch(`/api/test/live-sources/${encodeURIComponent(code)}`, {
          method: 'POST',
        });
        const payload = await response.json();
        if (!response.ok) {
          const detail = typeof payload.detail === 'string'
            ? payload.detail
            : JSON.stringify(payload.detail, null, 2);
          throw new Error(detail || `Live-testi epäonnistui (${response.status}).`);
        }

        document.querySelector('#total').textContent = payload.total;
        document.querySelector('#relevant').textContent = payload.distribution.relevant;
        document.querySelector('#review').textContent = payload.distribution.needs_review;
        document.querySelector('#excluded').textContent = payload.distribution.not_relevant;
        document.querySelector('#result-title').textContent = `${payload.source_label} · live-tulos`;
        document.querySelector('#duration').textContent = `${(payload.duration_ms / 1000).toFixed(1)} s`;
        renderRows(payload.items);
        summary.hidden = false;
        results.hidden = false;
        statusText.textContent = 'Live-testi valmis. Mitään ei tallennettu tietokantaan.';
      } catch (error) {
        errorBox.textContent = `Testi epäonnistui:\n${error.message}`;
        errorBox.hidden = false;
        statusText.textContent = 'Lähdettä ei voitu testata.';
      } finally {
        runButton.disabled = false;
        runButton.textContent = 'Testaa lähde nyt';
      }
    }

    runButton.addEventListener('click', runScan);
    loadCatalog().catch((error) => {
      statusText.textContent = 'Testikonsolia ei voitu alustaa.';
      errorBox.textContent = error.message;
      errorBox.hidden = false;
      runButton.disabled = true;
    });
  </script>
</body>
</html>
"""
