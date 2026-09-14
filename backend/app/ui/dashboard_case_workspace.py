"""Inject one cross-app funding case workspace into the employee dashboard."""

_CASE_STYLES = r"""
<style id="vake-case-workspace-styles">
  .case-workspace {
    margin-top: 34px;
    padding: 24px;
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    background: var(--surface);
    box-shadow: var(--shadow);
  }
  .case-workspace[hidden] { display: none; }
  .case-head {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: flex-start;
    margin-bottom: 18px;
  }
  .case-kicker {
    color: #E6007E;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: .09em;
    text-transform: uppercase;
  }
  .case-title {
    margin: 6px 0 0;
    color: var(--text);
    font-size: clamp(24px, 3vw, 34px);
    line-height: 1.15;
    letter-spacing: -.035em;
  }
  .case-subtitle {
    max-width: 820px;
    margin: 8px 0 0;
    color: var(--muted);
    font-size: 12px;
    line-height: 1.65;
  }
  .case-close,
  .case-open-button,
  .case-action {
    border: 1px solid var(--border);
    border-radius: 10px;
    min-height: 38px;
    padding: 8px 12px;
    font: inherit;
    font-size: 11px;
    font-weight: 800;
    cursor: pointer;
    background: var(--surface);
    color: var(--text);
  }
  .case-open-button {
    color: #312783;
    white-space: nowrap;
  }
  .case-open-button:hover,
  .case-action:hover,
  .case-close:hover { border-color: #312783; }
  .case-action.primary {
    border-color: #312783;
    background: #312783;
    color: #fff;
  }
  .case-action.send {
    border-color: #E6007E;
    background: #E6007E;
    color: #fff;
  }
  .case-action:disabled { opacity: .48; cursor: not-allowed; }
  .case-status-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 18px;
  }
  .case-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 7px 10px;
    background: var(--surface-soft);
    color: var(--text);
    font-size: 10px;
    font-weight: 800;
  }
  .case-pill.good {
    color: #006f2a;
    border-color: color-mix(in srgb, #00983A 28%, var(--border));
    background: color-mix(in srgb, #74B72B 12%, var(--surface));
  }
  .case-pill.review {
    color: #7d641b;
    border-color: color-mix(in srgb, #B59525 35%, var(--border));
    background: color-mix(in srgb, #F4D25A 18%, var(--surface));
  }
  .case-next {
    margin-bottom: 18px;
    padding: 14px 16px;
    border-left: 5px solid #76CBF3;
    border-radius: 10px;
    background: color-mix(in srgb, #76CBF3 11%, var(--surface));
  }
  .case-next span {
    display: block;
    color: #28738A;
    font-size: 9px;
    font-weight: 850;
    letter-spacing: .06em;
    text-transform: uppercase;
  }
  .case-next strong {
    display: block;
    margin-top: 5px;
    color: var(--text);
    font-size: 13px;
    line-height: 1.5;
  }
  .case-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(320px, .85fr);
    gap: 16px;
  }
  .case-column { display: grid; gap: 16px; align-content: start; }
  .case-card {
    border: 1px solid var(--border);
    border-radius: 15px;
    overflow: hidden;
    background: var(--surface-soft);
  }
  .case-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 13px 15px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }
  .case-card-head strong { color: var(--text); font-size: 12px; }
  .case-card-head span { color: var(--muted); font-size: 9px; }
  .case-card-body { padding: 15px; }
  .case-facts {
    display: grid;
    grid-template-columns: 130px minmax(0, 1fr);
    gap: 9px 12px;
    margin: 0;
    font-size: 11px;
    line-height: 1.55;
  }
  .case-facts dt { color: var(--muted); font-weight: 800; }
  .case-facts dd { margin: 0; color: var(--text); }
  .case-facts a { color: #312783; font-weight: 800; text-decoration: none; }
  .case-artifacts { display: grid; gap: 10px; }
  .case-artifact {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 10px;
    align-items: start;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 11px;
    background: var(--surface);
  }
  .case-artifact input { margin-top: 4px; accent-color: #312783; }
  .case-artifact h4 { margin: 0; color: var(--text); font-size: 11px; line-height: 1.35; }
  .case-artifact p { margin: 5px 0 0; color: var(--muted); font-size: 10px; line-height: 1.5; }
  .case-artifact-meta { margin-top: 7px; color: #28738A; font-size: 9px; font-weight: 800; }
  .case-artifact a { color: #312783; font-size: 10px; font-weight: 800; text-decoration: none; }
  .case-field { display: block; margin-bottom: 12px; }
  .case-field span { display: block; margin-bottom: 6px; color: var(--text); font-size: 10px; font-weight: 800; }
  .case-input,
  .case-textarea {
    width: 100%;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 11px;
    color: var(--text);
    background: var(--surface);
    font: inherit;
    font-size: 11px;
  }
  .case-textarea { min-height: 210px; resize: vertical; line-height: 1.55; }
  .case-email-actions { display: flex; flex-wrap: wrap; gap: 8px; }
  .case-feedback { min-height: 18px; margin-top: 10px; color: var(--muted); font-size: 10px; line-height: 1.45; }
  .case-timeline { position: relative; display: grid; gap: 0; }
  .case-event {
    position: relative;
    padding: 0 0 16px 24px;
    color: var(--text);
    font-size: 10px;
    line-height: 1.45;
  }
  .case-event:last-child { padding-bottom: 0; }
  .case-event::before {
    content: "";
    position: absolute;
    left: 4px;
    top: 4px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #312783;
  }
  .case-event::after {
    content: "";
    position: absolute;
    left: 7px;
    top: 14px;
    bottom: 0;
    width: 2px;
    background: color-mix(in srgb, #6E67A8 30%, var(--border));
  }
  .case-event:last-child::after { display: none; }
  .case-event strong { display: block; font-size: 10px; }
  .case-event span { display: block; margin-top: 2px; color: var(--muted); }
  .case-empty { padding: 18px; color: var(--muted); font-size: 11px; line-height: 1.6; text-align: center; }
  @media (max-width: 900px) {
    .case-layout { grid-template-columns: 1fr; }
    .case-head { flex-direction: column; }
    .case-facts { grid-template-columns: 1fr; gap: 3px; }
    .case-facts dd { margin-bottom: 8px; }
  }
</style>
"""

_CASE_SECTION = r"""
<section id="funding-case-workspace" class="case-workspace" hidden aria-labelledby="case-title">
  <div class="case-head">
    <div>
      <span class="case-kicker">Rahoituscase · VakeTomatti</span>
      <h2 id="case-title" class="case-title">Valitse rahoitushaku</h2>
      <p class="case-subtitle">
        Sama case yhdistää rahoitushaun, prosessikuvauksen, raportoinnin ja sähköpostin.
        Tavallinen työskentely tapahtuu tässä näkymässä ilman siirtymistä sovelluksesta toiseen.
      </p>
    </div>
    <button id="case-close" class="case-close" type="button">Sulje case</button>
  </div>
  <div id="case-status-row" class="case-status-row"></div>
  <div class="case-next">
    <span>Seuraava toimenpide</span>
    <strong id="case-next-action">Valitse rahoitushaku avataksesi casen.</strong>
  </div>
  <div class="case-layout">
    <div class="case-column">
      <section class="case-card">
        <div class="case-card-head"><strong>Yhteenveto</strong><span id="case-id-label"></span></div>
        <div class="case-card-body"><dl id="case-facts" class="case-facts"></dl></div>
      </section>
      <section class="case-card">
        <div class="case-card-head"><strong>Caseen liittyvät aineistot</strong><span>Valitse sähköpostiin</span></div>
        <div id="case-artifacts" class="case-card-body case-artifacts"></div>
      </section>
      <section class="case-card">
        <div class="case-card-head"><strong>Tapahtumat</strong><span>Case-aikajana</span></div>
        <div id="case-timeline" class="case-card-body case-timeline"></div>
      </section>
    </div>
    <div class="case-column">
      <section class="case-card">
        <div class="case-card-head"><strong>Raportti ja sähköposti</strong><span>Muokattava ennen lähetystä</span></div>
        <div class="case-card-body">
          <label class="case-field">
            <span>Vastaanottajat · oma tai muu sähköposti</span>
            <input id="case-email-recipients" class="case-input" type="text" placeholder="nimi@vakehyva.fi, toinen@vakehyva.fi">
          </label>
          <label class="case-field">
            <span>Aihe</span>
            <input id="case-email-subject" class="case-input" type="text">
          </label>
          <label class="case-field">
            <span>Viestin sisältö</span>
            <textarea id="case-email-body" class="case-textarea"></textarea>
          </label>
          <div class="case-email-actions">
            <button id="case-refresh-package" class="case-action" type="button">Päivitä automaattinen pohja</button>
            <button id="case-send-email" class="case-action send" type="button">Lähetä sähköposti</button>
          </div>
          <div id="case-feedback" class="case-feedback" aria-live="polite"></div>
        </div>
      </section>
    </div>
  </div>
</section>
"""

_CASE_SCRIPT_TEMPLATE = r"""
<script id="vake-case-workspace-script">
(() => {
  const previewMode = __PREVIEW_MODE__;
  const ui = {
    workspace: document.getElementById("funding-case-workspace"),
    title: document.getElementById("case-title"),
    close: document.getElementById("case-close"),
    statuses: document.getElementById("case-status-row"),
    next: document.getElementById("case-next-action"),
    id: document.getElementById("case-id-label"),
    facts: document.getElementById("case-facts"),
    artifacts: document.getElementById("case-artifacts"),
    timeline: document.getElementById("case-timeline"),
    recipients: document.getElementById("case-email-recipients"),
    subject: document.getElementById("case-email-subject"),
    body: document.getElementById("case-email-body"),
    refresh: document.getElementById("case-refresh-package"),
    send: document.getElementById("case-send-email"),
    feedback: document.getElementById("case-feedback"),
    list: document.getElementById("opportunity-list"),
  };
  const caseByCall = new Map();
  let activeCase = null;
  let defaultArtifacts = new Set();

  function node(tag, value, className) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (value !== undefined && value !== null) element.textContent = String(value);
    return element;
  }

  function formatDate(value) {
    if (!value) return "Ei ilmoitettu";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return String(value);
    return new Intl.DateTimeFormat("fi-FI", { dateStyle: "short" }).format(parsed);
  }

  function sourceName(code) {
    const labels = {
      STM: "STM",
      HAEAVUSTUKSIA: "Haeavustuksia.fi",
      EURA: "EURA 2021",
      SITRA: "Sitra",
      ACADEMY: "Suomen Akatemia",
    };
    return labels[code] || code;
  }

  function statusName(value) {
    const normalized = String(value || "").toUpperCase();
    if (normalized === "APPROVED") return "Hyväksytty";
    if (normalized === "DRAFT") return "Luonnos";
    if (normalized === "NEEDS_REVIEW") return "Tarkistettava";
    if (normalized === "RELEVANT") return "Varmistettu";
    if (normalized === "OPEN") return "Avoin";
    return value || "–";
  }

  function artifactLabel(type) {
    const labels = {
      PROCESS_DESCRIPTION: "Prosessikuvaus",
      REPORTING: "Raportointi",
      FUNDING_REPORT: "Rahoitusraportti",
      ATTACHMENT: "Liite",
    };
    return labels[type] || String(type || "Aineisto").replaceAll("_", " ");
  }

  function selectedArtifactIds() {
    return Array.from(ui.artifacts.querySelectorAll('input[type="checkbox"]:checked'))
      .map((checkbox) => checkbox.value);
  }

  function setFeedback(message) {
    ui.feedback.textContent = message;
  }

  function addFact(label, value, href) {
    ui.facts.append(node("dt", label));
    const dd = document.createElement("dd");
    if (href) {
      const link = node("a", value);
      link.href = href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      dd.append(link);
    } else {
      dd.textContent = value;
    }
    ui.facts.append(dd);
  }

  function preferredArtifact(caseData, type) {
    const matches = caseData.artifacts.filter((artifact) => artifact.artifact_type === type);
    if (!matches.length) return null;
    const approved = matches.filter((artifact) => artifact.status === "APPROVED");
    const pool = approved.length ? approved : matches;
    return pool.sort((a, b) => b.version - a.version)[0];
  }

  function nextAction(caseData) {
    const call = caseData.funding_call;
    if (call.relevance_status === "NEEDS_REVIEW") {
      return "Tarkista ensin VakeHyvän hakukelpoisuus ennen valmistelun automatisointia.";
    }
    if (!preferredArtifact(caseData, "PROCESS_DESCRIPTION")) {
      return "Luo rahoitushaulle prosessikuvaus ja nimeä valmistelun omistaja.";
    }
    if (!preferredArtifact(caseData, "REPORTING")) {
      return "Luo raportointisuunnitelma ja tunnista rahoittajan raportointivelvoitteet.";
    }
    const report = preferredArtifact(caseData, "FUNDING_REPORT");
    if (!report || report.status !== "APPROVED") {
      return "Tarkista automaattinen rahoitusraportti, vastaanottajat ja sähköpostin sisältö.";
    }
    return "Case on koottu. Lähetä hyväksytty paketti tai jatka hakemuksen valmisteluun.";
  }

  function renderStatuses(caseData) {
    ui.statuses.replaceChildren();
    const call = caseData.funding_call;
    const certainty = node("span", statusName(call.relevance_status), "case-pill");
    certainty.classList.add(call.relevance_status === "NEEDS_REVIEW" ? "review" : "good");
    ui.statuses.append(certainty);
    ["PROCESS_DESCRIPTION", "REPORTING", "FUNDING_REPORT"].forEach((type) => {
      const artifact = preferredArtifact(caseData, type);
      ui.statuses.append(
        node(
          "span",
          `${artifactLabel(type)}: ${artifact ? statusName(artifact.status) : "Puuttuu"}`,
          "case-pill"
        )
      );
    });
  }

  function renderArtifacts(caseData) {
    ui.artifacts.replaceChildren();
    if (!caseData.artifacts.length) {
      ui.artifacts.append(node("div", "Caseen ei ole vielä liitetty aineistoja.", "case-empty"));
      return;
    }
    const grouped = new Map();
    caseData.artifacts.forEach((artifact) => {
      const key = `${artifact.source_app}:${artifact.artifact_type}:${artifact.external_artifact_id}`;
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key).push(artifact);
    });
    grouped.forEach((versions) => {
      const approved = versions.filter((artifact) => artifact.status === "APPROVED");
      const pool = approved.length ? approved : versions;
      const artifact = pool.sort((a, b) => b.version - a.version)[0];
      const item = document.createElement("label");
      item.className = "case-artifact";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = artifact.id;
      checkbox.checked = defaultArtifacts.has(artifact.id);
      const copy = document.createElement("div");
      copy.append(node("h4", `${artifactLabel(artifact.artifact_type)} · ${artifact.title}`));
      if (artifact.summary) copy.append(node("p", artifact.summary));
      copy.append(
        node(
          "div",
          `${statusName(artifact.status)} · versio ${artifact.version} · ${artifact.source_app}`,
          "case-artifact-meta"
        )
      );
      item.append(checkbox, copy);
      if (artifact.content_url) {
        const link = node("a", "Avaa ↗");
        link.href = artifact.content_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        item.append(link);
      } else {
        item.append(node("span", ""));
      }
      ui.artifacts.append(item);
    });
  }

  function renderTimeline(caseData) {
    ui.timeline.replaceChildren();
    const events = [
      ["Rahoitushaku löydetty", formatDate(caseData.created_at)],
      ["Rahoituscase luotu", formatDate(caseData.created_at)],
    ];
    caseData.artifacts
      .slice()
      .sort((a, b) => String(a.updated_at).localeCompare(String(b.updated_at)))
      .forEach((artifact) => {
        events.push([
          `${artifactLabel(artifact.artifact_type)} · ${statusName(artifact.status)}`,
          `${formatDate(artifact.updated_at)} · versio ${artifact.version}`,
        ]);
      });
    events.forEach(([title, detail]) => {
      const item = document.createElement("div");
      item.className = "case-event";
      item.append(node("strong", title), node("span", detail));
      ui.timeline.append(item);
    });
  }

  async function loadPackage(caseData, preserveEdits = false) {
    const response = await fetch(`/api/cases/${encodeURIComponent(caseData.id)}/email-package`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const packageData = await response.json();
    defaultArtifacts = new Set(packageData.included_artifacts.map((artifact) => artifact.id));
    renderArtifacts(caseData);
    if (!preserveEdits) {
      ui.subject.value = packageData.subject;
      ui.body.value = packageData.body;
    }
  }

  async function openCase(caseData) {
    activeCase = caseData;
    ui.workspace.hidden = false;
    ui.title.textContent = caseData.funding_call.title;
    ui.id.textContent = `Case ${caseData.id}`;
    ui.next.textContent = nextAction(caseData);
    renderStatuses(caseData);
    ui.facts.replaceChildren();
    const call = caseData.funding_call;
    addFact("Lähde", sourceName(call.source_code));
    addFact("Hakuaika päättyy", formatDate(call.application_deadline_at || call.application_deadline_on));
    addFact("Miksi VakeHyvälle", call.relevance_reason);
    addFact("Tila", statusName(call.relevance_status));
    addFact("Alkuperäinen rahoitushaku", "Avaa lähde ↗", call.source_url);
    renderTimeline(caseData);
    setFeedback("Ladataan automaattista sähköpostipohjaa…");
    try {
      await loadPackage(caseData);
      setFeedback(
        previewMode
          ? "Kehitysesikatselu: lähetys simuloidaan eikä sähköpostia lähetetä ulos."
          : "Sähköpostipohja on koottu casen nykyisistä hyväksytyistä aineistoista."
      );
    } catch (error) {
      renderArtifacts(caseData);
      setFeedback("Sähköpostipohjaa ei voitu ladata.");
    }
    ui.workspace.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function decorateRows() {
    const rows = Array.from(ui.list.querySelectorAll(".opportunity"));
    rows.forEach((row, index) => {
      const call = state.calls[index];
      if (!call) return;
      const caseData = caseByCall.get(call.id);
      const action = row.querySelector(".row-action");
      if (!caseData || !action || action.querySelector(".case-open-button")) return;
      const button = node("button", "Avaa case", "case-open-button");
      button.type = "button";
      button.addEventListener("click", () => openCase(caseData));
      action.prepend(button);
    });
  }

  async function loadCases() {
    try {
      const response = await fetch("/api/cases");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const cases = await response.json();
      cases.forEach((caseData) => caseByCall.set(caseData.funding_call.id, caseData));
      decorateRows();
    } catch (error) {
      console.error("Funding cases could not be loaded", error);
    }
  }

  ui.close.addEventListener("click", () => {
    ui.workspace.hidden = true;
    activeCase = null;
  });

  ui.refresh.addEventListener("click", async () => {
    if (!activeCase) return;
    ui.refresh.disabled = true;
    try {
      await loadPackage(activeCase, false);
      setFeedback("Automaattinen sähköpostipohja päivitettiin casen nykyisistä aineistoista.");
    } catch (error) {
      setFeedback("Sähköpostipohjan päivitys ei onnistunut.");
    } finally {
      ui.refresh.disabled = false;
    }
  });

  ui.send.addEventListener("click", async () => {
    if (!activeCase) return;
    const recipients = ui.recipients.value
      .split(/[;,]/)
      .map((value) => value.trim())
      .filter(Boolean);
    if (!recipients.length) {
      setFeedback("Lisää vähintään yksi vastaanottajan sähköpostiosoite.");
      ui.recipients.focus();
      return;
    }
    ui.send.disabled = true;
    setFeedback(previewMode ? "Simuloidaan lähetystä…" : "Jonotetaan sähköpostia…");
    try {
      const response = await fetch(`/api/cases/${encodeURIComponent(activeCase.id)}/email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient_emails: recipients,
          subject: ui.subject.value,
          body: ui.body.value,
          artifact_ids: selectedArtifactIds(),
        }),
      });
      if (!response.ok) {
        if (response.status === 404 && !previewMode) {
          setFeedback("Lähetys odottaa työpaikan luotetun integraation käyttöönottoa.");
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }
      const queued = await response.json();
      const message = previewMode
        ? `Esikatselujono valmis vastaanottajille: ${queued.recipients.join(", ")}. Oikeaa sähköpostia ei lähetetty.`
        : `Sähköposti jonotettiin. Tila: ${queued.delivery_status}.`;
      setFeedback(message);
      const event = document.createElement("div");
      event.className = "case-event";
      event.append(
        node("strong", previewMode ? "Sähköpostilähetys simuloitu" : "Sähköposti jonotettu"),
        node("span", new Intl.DateTimeFormat("fi-FI", { dateStyle: "short", timeStyle: "short" }).format(new Date()))
      );
      ui.timeline.append(event);
    } catch (error) {
      setFeedback("Sähköpostia ei voitu jonottaa. Tarkista osoitteet ja integraation tila.");
    } finally {
      ui.send.disabled = false;
    }
  });

  const observer = new MutationObserver(decorateRows);
  observer.observe(ui.list, { childList: true, subtree: true });
  loadCases();
})();
</script>
"""


def render_dashboard_case_workspace(html: str, *, preview_mode: bool) -> str:
    """Add the unified funding-case workspace before portfolio report tooling."""

    required = ("</head>", "</main>", "</body>", 'id="opportunity-list"')
    missing = [sentinel for sentinel in required if sentinel not in html]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Dashboard case workspace sentinels missing: {joined}")

    script = _CASE_SCRIPT_TEMPLATE.replace(
        "__PREVIEW_MODE__",
        "true" if preview_mode else "false",
        1,
    )
    rendered = html.replace("</head>", f"{_CASE_STYLES}\n</head>", 1)
    rendered = rendered.replace("</main>", f"{_CASE_SECTION}\n</main>", 1)
    return rendered.replace("</body>", f"{script}\n</body>", 1)
