"""Inject the employee report-drafting workspace into the funding dashboard."""

_REPORT_STYLES = r"""
<style id="vake-report-workspace-styles">
  .report-workspace {
    margin-top: 34px;
    padding: 24px;
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    background: var(--surface);
    box-shadow: var(--shadow);
  }

  .report-workspace-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 18px;
  }

  .report-workspace h2 {
    margin: 0;
    color: var(--text);
    font-size: 24px;
    letter-spacing: -.03em;
  }

  .report-workspace-copy {
    max-width: 780px;
    margin: 7px 0 0;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.6;
  }

  .report-status {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 11px;
    border: 1px solid color-mix(in srgb, #B59525 35%, var(--border));
    border-radius: 999px;
    color: #7d641b;
    background: color-mix(in srgb, #F4D25A 18%, var(--surface));
    font-size: 10px;
    font-weight: 850;
    white-space: nowrap;
  }

  .report-status::before {
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #B59525;
  }

  .report-status.waiting {
    border-color: color-mix(in srgb, #E6007E 28%, var(--border));
    color: #A00058;
    background: color-mix(in srgb, #EA5297 12%, var(--surface));
  }

  .report-status.waiting::before { background: #E6007E; }

  .report-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-bottom: 16px;
  }

  .report-metric {
    padding: 14px 15px;
    border: 1px solid var(--border);
    border-radius: 13px;
    background: var(--surface-soft);
  }

  .report-metric span {
    display: block;
    color: var(--muted);
    font-size: 9px;
    font-weight: 800;
    letter-spacing: .05em;
    text-transform: uppercase;
  }

  .report-metric strong {
    display: block;
    margin-top: 5px;
    color: var(--brand-strong);
    font-size: 24px;
  }

  .report-toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    margin-bottom: 18px;
  }

  .report-button,
  .report-row-button {
    min-height: 38px;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 12px;
    color: var(--text);
    background: var(--surface);
    font: inherit;
    font-size: 11px;
    font-weight: 800;
    cursor: pointer;
    transition: transform .14s ease, border-color .14s ease;
  }

  .report-button:hover,
  .report-row-button:hover {
    transform: translateY(-1px);
    border-color: var(--brand);
  }

  .report-button.primary {
    border-color: #312783;
    color: #fff;
    background: #312783;
  }

  .report-button.approval {
    border-color: #E6007E;
    color: #fff;
    background: #E6007E;
  }

  .report-button:disabled {
    opacity: .45;
    cursor: not-allowed;
    transform: none;
  }

  .report-row-button {
    min-height: 36px;
    color: var(--row-color, var(--brand-strong));
    white-space: nowrap;
  }

  .report-row-button.selected {
    border-color: #00983A;
    color: #006f2a;
    background: color-mix(in srgb, #74B72B 13%, var(--surface));
  }

  .report-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.3fr) minmax(300px, .7fr);
    gap: 16px;
  }

  .report-panel {
    min-width: 0;
    border: 1px solid var(--border);
    border-radius: 15px;
    background: var(--surface-soft);
    overflow: hidden;
  }

  .report-panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }

  .report-panel-head strong {
    color: var(--text);
    font-size: 12px;
  }

  .report-panel-head span {
    color: var(--muted);
    font-size: 10px;
  }

  .report-preview {
    max-height: 620px;
    overflow: auto;
    padding: 14px;
  }

  .report-empty {
    padding: 26px 18px;
    color: var(--muted);
    text-align: center;
    font-size: 12px;
    line-height: 1.6;
  }

  .report-item {
    padding: 15px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--surface);
  }

  .report-item + .report-item { margin-top: 10px; }

  .report-item-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  .report-item-source {
    display: inline-flex;
    margin-bottom: 5px;
    color: var(--brand-strong);
    font-size: 9px;
    font-weight: 850;
    text-transform: uppercase;
  }

  .report-item h3 {
    margin: 0;
    color: var(--text);
    font-size: 13px;
    line-height: 1.4;
  }

  .report-certainty {
    flex: 0 0 auto;
    padding: 5px 7px;
    border-radius: 999px;
    color: #006f2a;
    background: color-mix(in srgb, #74B72B 14%, var(--surface));
    font-size: 9px;
    font-weight: 850;
  }

  .report-certainty.review {
    color: #7d641b;
    background: color-mix(in srgb, #F4D25A 22%, var(--surface));
  }

  .report-item dl {
    display: grid;
    grid-template-columns: 120px minmax(0, 1fr);
    gap: 8px 11px;
    margin: 13px 0 0;
    font-size: 10px;
    line-height: 1.5;
  }

  .report-item dt { color: var(--muted); font-weight: 800; }
  .report-item dd { margin: 0; color: var(--text); }

  .report-item a {
    color: var(--brand-strong);
    font-weight: 800;
    text-decoration: none;
  }

  .report-notes-wrap { padding: 14px; }

  .report-notes-wrap label {
    display: block;
    margin-bottom: 7px;
    color: var(--text);
    font-size: 11px;
    font-weight: 800;
  }

  .report-notes {
    width: 100%;
    min-height: 180px;
    resize: vertical;
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 11px 12px;
    color: var(--text);
    background: var(--surface);
    font: inherit;
    font-size: 12px;
    line-height: 1.55;
  }

  .report-guidance {
    margin: 12px 0 0;
    padding: 11px 12px;
    border-left: 4px solid #76CBF3;
    border-radius: 8px;
    color: var(--muted);
    background: color-mix(in srgb, #76CBF3 10%, var(--surface));
    font-size: 10px;
    line-height: 1.55;
  }

  .report-feedback {
    min-height: 20px;
    margin-top: 12px;
    color: var(--muted);
    font-size: 10px;
  }

  @media (max-width: 900px) {
    .report-grid { grid-template-columns: 1fr; }
    .report-workspace-head { flex-direction: column; }
    .report-metrics { grid-template-columns: 1fr; }
  }

  @media print {
    .topbar,
    .hero,
    .kpis,
    #sources-section,
    #calls-section,
    .report-toolbar,
    .report-notes-wrap,
    .report-guidance,
    .report-feedback,
    .theme-toggle { display: none !important; }
    .report-workspace { box-shadow: none; border: 0; margin: 0; padding: 0; }
    .report-grid { display: block; }
    .report-panel { border: 0; }
    .report-preview { max-height: none; overflow: visible; padding: 0; }
  }
</style>
"""

_REPORT_SECTION = r"""
<section id="report-workspace" class="report-workspace" aria-labelledby="report-heading">
  <div class="report-workspace-head">
    <div>
      <span class="section-kicker">Koordinaattorin työtila</span>
      <h2 id="report-heading">VakeHyvän rahoitusraportti</h2>
      <p class="report-workspace-copy">
        Valitse olennaiset rahoitushaut, muodosta koottu raporttiluonnos ja valmistele se
        koordinaattorin hyväksyntää varten. Jokaisessa kohdassa näkyy perustelu sille,
        miksi haku sopii VakeHyvälle tai miksi se vaatii vielä tarkistuksen.
      </p>
    </div>
    <span id="report-status" class="report-status">Luonnos</span>
  </div>

  <div class="report-metrics" aria-label="Raportin tunnusluvut">
    <div class="report-metric">
      <span>Valittu raporttiin</span>
      <strong id="report-selected-count">0</strong>
    </div>
    <div class="report-metric">
      <span>Varmistettu</span>
      <strong id="report-confirmed-count">0</strong>
    </div>
    <div class="report-metric">
      <span>Tarkistettava</span>
      <strong id="report-review-count">0</strong>
    </div>
  </div>

  <div class="report-toolbar">
    <button id="report-select-visible" class="report-button" type="button">
      Valitse näkyvät varmistetut
    </button>
    <button id="report-clear" class="report-button" type="button">Tyhjennä</button>
    <button id="report-build" class="report-button primary" type="button">
      Muodosta raporttiluonnos
    </button>
    <button id="report-mark-approval" class="report-button approval" type="button">
      Merkitse hyväksyntää varten
    </button>
    <button id="report-copy" class="report-button" type="button">Kopioi raportti</button>
    <button id="report-print" class="report-button" type="button">Tulosta / PDF</button>
  </div>

  <div class="report-grid">
    <div class="report-panel">
      <div class="report-panel-head">
        <strong>Raporttiluonnos</strong>
        <span id="report-generated-at">Ei vielä muodostettu</span>
      </div>
      <div id="report-preview" class="report-preview">
        <div class="report-empty">
          Lisää rahoitushakuja raporttiin hakulistasta tai valitse näkyvät varmistetut haut.
        </div>
      </div>
    </div>

    <aside class="report-panel" aria-label="Raportin muistiinpanot">
      <div class="report-panel-head">
        <strong>Koordinaattorin muistiinpanot</strong>
        <span>Luonnos</span>
      </div>
      <div class="report-notes-wrap">
        <label for="report-notes">Yhteenveto, vastuut ja seuraavat toimet</label>
        <textarea
          id="report-notes"
          class="report-notes"
          placeholder="Kirjaa tähän esimerkiksi vastuuhenkilö, arvioitu seuraava vaihe tai tarkistettava asia."
        ></textarea>
        <p class="report-guidance">
          Raportin valinta, muistiinpanot ja hyväksyntätila ovat tässä vaiheessa tämän
          selainistunnon työtilaa. VakeVahti ei lähetä raporttia sähköpostiin tai Teamsiin
          ennen erillistä hyväksyttyä integraatiota.
        </p>
        <div id="report-feedback" class="report-feedback" aria-live="polite"></div>
      </div>
    </aside>
  </div>
</section>
"""

_REPORT_SCRIPT_TEMPLATE = r"""
<script id="vake-report-workspace-script">
(() => {
  const previewMode = __PREVIEW_MODE__;
  const selected = new Map();
  let reportText = "";
  let status = "DRAFT";

  const ui = {
    workspace: document.getElementById("report-workspace"),
    preview: document.getElementById("report-preview"),
    notes: document.getElementById("report-notes"),
    status: document.getElementById("report-status"),
    selected: document.getElementById("report-selected-count"),
    confirmed: document.getElementById("report-confirmed-count"),
    review: document.getElementById("report-review-count"),
    generatedAt: document.getElementById("report-generated-at"),
    feedback: document.getElementById("report-feedback"),
    selectVisible: document.getElementById("report-select-visible"),
    clear: document.getElementById("report-clear"),
    build: document.getElementById("report-build"),
    markApproval: document.getElementById("report-mark-approval"),
    copy: document.getElementById("report-copy"),
    print: document.getElementById("report-print"),
    list: document.getElementById("opportunity-list"),
  };

  function isReview(call) {
    const value = String(call.relevance_status || "").trim().toUpperCase();
    return value === "NEEDS_REVIEW" || value === "REVIEW";
  }

  function isConfirmed(call) {
    return String(call.relevance_status || "").trim().toUpperCase() === "RELEVANT";
  }

  function statusLabel(call) {
    return isReview(call) ? "Tarkistettava" : "Varmistettu";
  }

  function nextAction(call) {
    if (isReview(call)) {
      return "Tarkista hakukelpoisuus ja hakijarajaus ennen etenemispäätöstä.";
    }
    return "Arvioi vastuuhenkilö, aikataulu ja valmistelun käynnistäminen.";
  }

  function deadlineLabel(call) {
    const value = call.application_deadline_at || call.application_deadline_on;
    return formatDeadline(value).label;
  }

  function updateStatus(nextStatus) {
    status = nextStatus;
    const waiting = status === "WAITING_APPROVAL";
    ui.status.textContent = waiting ? "Odottaa koordinaattorin hyväksyntää" : "Luonnos";
    ui.status.classList.toggle("waiting", waiting);
  }

  function updateMetrics() {
    const calls = Array.from(selected.values());
    ui.selected.textContent = String(calls.length);
    ui.confirmed.textContent = String(calls.filter(isConfirmed).length);
    ui.review.textContent = String(calls.filter(isReview).length);
    ui.markApproval.disabled = calls.length === 0;
    ui.copy.disabled = calls.length === 0;
    ui.print.disabled = calls.length === 0;
  }

  function setFeedback(message) {
    ui.feedback.textContent = message;
  }

  function reportItem(call) {
    const article = document.createElement("article");
    article.className = "report-item";

    const top = document.createElement("div");
    top.className = "report-item-top";
    const heading = document.createElement("div");
    heading.append(text("span", sourceMeta(call.source_code).name, "report-item-source"));
    heading.append(text("h3", call.title));
    top.append(heading);

    const certainty = text("span", statusLabel(call), "report-certainty");
    if (isReview(call)) certainty.classList.add("review");
    top.append(certainty);
    article.append(top);

    const facts = document.createElement("dl");
    const entries = [
      ["Hakuaika päättyy", deadlineLabel(call)],
      ["Miksi VakeHyvälle", relevanceReason(call)],
      ["Seuraava vaihe", nextAction(call)],
    ];
    entries.forEach(([label, value]) => {
      facts.append(text("dt", label));
      facts.append(text("dd", value));
    });

    facts.append(text("dt", "Alkuperäinen lähde"));
    const sourceValue = document.createElement("dd");
    const link = document.createElement("a");
    link.href = call.source_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "Avaa rahoitushaku ↗";
    sourceValue.append(link);
    facts.append(sourceValue);
    article.append(facts);
    return article;
  }

  function buildPlainText() {
    const calls = Array.from(selected.values());
    const lines = [
      "VAKEHYVÄN RAHOITUSRAPORTTI",
      "",
      `Valittuja hakuja: ${calls.length}`,
      `Varmistettuja: ${calls.filter(isConfirmed).length}`,
      `Tarkistettavia: ${calls.filter(isReview).length}`,
      "",
    ];

    calls.forEach((call, index) => {
      lines.push(`${index + 1}. ${call.title}`);
      lines.push(`Lähde: ${sourceMeta(call.source_code).name}`);
      lines.push(`Tila: ${statusLabel(call)}`);
      lines.push(`Hakuaika päättyy: ${deadlineLabel(call)}`);
      lines.push(`Miksi VakeHyvälle: ${relevanceReason(call)}`);
      lines.push(`Seuraava vaihe: ${nextAction(call)}`);
      lines.push(`Linkki: ${call.source_url}`);
      lines.push("");
    });

    const notes = ui.notes.value.trim();
    if (notes) {
      lines.push("KOORDINAATTORIN MUISTIINPANOT");
      lines.push(notes);
      lines.push("");
    }
    lines.push(
      status === "WAITING_APPROVAL"
        ? "Tila: Odottaa koordinaattorin hyväksyntää"
        : "Tila: Luonnos"
    );
    if (previewMode) lines.push("Kehitysesikatselu: fixture-dataa, ei lähetetty.");
    return lines.join("\n");
  }

  function renderDraft() {
    const calls = Array.from(selected.values());
    ui.preview.replaceChildren();
    if (!calls.length) {
      ui.preview.append(
        text(
          "div",
          "Raportissa ei ole vielä rahoitushakuja. Lisää hakuja hakulistasta.",
          "report-empty"
        )
      );
      reportText = "";
      updateMetrics();
      return;
    }

    calls.forEach((call) => ui.preview.append(reportItem(call)));
    reportText = buildPlainText();
    const now = new Intl.DateTimeFormat("fi-FI", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date());
    ui.generatedAt.textContent = `Muodostettu ${now}`;
    updateMetrics();
  }

  async function loadFullCall(call) {
    if (call.description_text !== undefined) return call;
    const response = await fetch(`/api/funding-calls/${encodeURIComponent(call.id)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async function toggleSelection(call, button) {
    if (selected.has(call.id)) {
      selected.delete(call.id);
      button.classList.remove("selected");
      button.textContent = "Lisää raporttiin";
      updateStatus("DRAFT");
      renderDraft();
      return;
    }

    button.disabled = true;
    try {
      const full = await loadFullCall(call);
      selected.set(call.id, full);
      button.classList.add("selected");
      button.textContent = "Raportissa ✓";
      updateStatus("DRAFT");
      renderDraft();
      setFeedback(`Lisättiin raporttiin: ${full.title}`);
    } catch (error) {
      setFeedback("Hakua ei voitu lisätä raporttiin. Yritä uudelleen.");
    } finally {
      button.disabled = false;
    }
  }

  function decorateRows() {
    const rows = Array.from(ui.list.querySelectorAll(".opportunity"));
    rows.forEach((row, index) => {
      const call = state.calls[index];
      if (!call) return;
      row.dataset.callId = String(call.id);
      const action = row.querySelector(".row-action");
      if (!action || action.querySelector(".report-row-button")) return;

      const button = document.createElement("button");
      button.type = "button";
      button.className = "report-row-button";
      button.textContent = selected.has(call.id) ? "Raportissa ✓" : "Lisää raporttiin";
      if (selected.has(call.id)) button.classList.add("selected");
      button.addEventListener("click", () => toggleSelection(call, button));
      action.prepend(button);
    });
  }

  async function selectVisibleConfirmed() {
    const visible = state.calls.filter(isConfirmed);
    if (!visible.length) {
      setFeedback("Nykyisessä rajauksessa ei ole varmistettuja hakuja.");
      return;
    }

    ui.selectVisible.disabled = true;
    try {
      const details = await Promise.all(visible.map(loadFullCall));
      details.forEach((call) => selected.set(call.id, call));
      updateStatus("DRAFT");
      renderDraft();
      decorateRows();
      setFeedback(`Raporttiin lisättiin ${details.length} näkyvää varmistettua hakua.`);
    } catch (error) {
      setFeedback("Kaikkia näkyviä hakuja ei voitu lisätä raporttiin.");
    } finally {
      ui.selectVisible.disabled = false;
    }
  }

  ui.selectVisible.addEventListener("click", selectVisibleConfirmed);
  ui.clear.addEventListener("click", () => {
    selected.clear();
    updateStatus("DRAFT");
    renderDraft();
    decorateRows();
    setFeedback("Raportin valinnat tyhjennettiin.");
  });
  ui.build.addEventListener("click", () => {
    updateStatus("DRAFT");
    renderDraft();
    ui.workspace.scrollIntoView({ behavior: "smooth", block: "start" });
    setFeedback("Raporttiluonnos muodostettiin nykyisistä valinnoista.");
  });
  ui.markApproval.addEventListener("click", () => {
    if (!selected.size) return;
    updateStatus("WAITING_APPROVAL");
    renderDraft();
    setFeedback(
      "Raportti on merkitty hyväksyntää varten tässä työtilassa. Sitä ei ole lähetetty."
    );
  });
  ui.copy.addEventListener("click", async () => {
    reportText = buildPlainText();
    try {
      await navigator.clipboard.writeText(reportText);
      setFeedback("Raportti kopioitiin leikepöydälle.");
    } catch (error) {
      setFeedback("Kopiointi ei onnistunut tässä selaimessa.");
    }
  });
  ui.print.addEventListener("click", () => {
    renderDraft();
    window.print();
  });
  ui.notes.addEventListener("input", () => {
    updateStatus("DRAFT");
    reportText = buildPlainText();
  });

  const observer = new MutationObserver(decorateRows);
  observer.observe(ui.list, { childList: true, subtree: true });
  decorateRows();
  updateMetrics();
})();
</script>
"""


def render_dashboard_report_workspace(html: str, *, preview_mode: bool) -> str:
    """Add local report drafting and approval preparation to the employee dashboard."""

    required = ("</head>", "</main>", "</body>", 'id="opportunity-list"')
    missing = [sentinel for sentinel in required if sentinel not in html]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Dashboard report workspace sentinels missing: {joined}")

    script = _REPORT_SCRIPT_TEMPLATE.replace(
        "__PREVIEW_MODE__",
        "true" if preview_mode else "false",
        1,
    )
    rendered = html.replace("</head>", f"{_REPORT_STYLES}\n</head>", 1)
    rendered = rendered.replace("</main>", f"{_REPORT_SECTION}\n</main>", 1)
    return rendered.replace("</body>", f"{script}\n</body>", 1)
