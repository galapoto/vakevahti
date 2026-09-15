"""Connect the employee report workspace to the report draft API."""

_SAVE_STYLE = r"""
<style id="vake-report-persistence-styles">
  .report-save-state {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: -4px 0 14px;
    color: var(--muted);
    font-size: 10px;
    line-height: 1.45;
  }

  .report-save-state-dot {
    width: 8px;
    height: 8px;
    flex: 0 0 auto;
    border-radius: 50%;
    background: #7f898a;
  }

  .report-save-state.saved .report-save-state-dot { background: #1fb578; }
  .report-save-state.dirty .report-save-state-dot { background: #f4d25a; }
  .report-save-state.waiting .report-save-state-dot { background: #e6007e; }
  .report-save-state.error .report-save-state-dot { background: #d90066; }

  .report-save-state strong {
    color: var(--text);
    font-size: 10px;
  }

  .report-save-id {
    padding: 2px 6px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--surface-soft);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 9px;
  }

  .report-button.save {
    border-color: #00983a;
    color: #006d29;
    background: color-mix(in srgb, #74b72b 12%, var(--surface));
  }

  .report-button.save.saving {
    opacity: .65;
    cursor: wait;
  }

  .report-save-state.approved .report-save-state-dot { background: #1fb578; }
  .report-save-state.rejected .report-save-state-dot { background: #d90066; }

  .report-approval-panel {
    margin: 0 0 18px;
    padding: 16px;
    border: 1px solid color-mix(in srgb, #312783 18%, var(--border));
    border-radius: 14px;
    background: color-mix(in srgb, #312783 4%, var(--surface));
  }

  .report-approval-panel[hidden] { display: none; }

  .report-approval-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    margin-bottom: 13px;
  }

  .report-approval-head strong { color: var(--text); font-size: 13px; }
  .report-approval-head span { color: var(--muted); font-size: 10px; line-height: 1.5; }

  .report-approval-fields {
    display: grid;
    grid-template-columns: minmax(180px, .8fr) minmax(220px, 1fr);
    gap: 10px;
  }

  .report-approval-fields label { color: var(--muted); font-size: 9px; font-weight: 700; }
  .report-approval-fields label:last-child { grid-column: 1 / -1; }
  .report-approval-fields input,
  .report-approval-fields textarea {
    width: 100%;
    margin-top: 5px;
    padding: 9px 10px;
    border: 1px solid var(--border);
    border-radius: 9px;
    color: var(--text);
    background: var(--surface);
    font: inherit;
  }
  .report-approval-fields textarea { min-height: 76px; resize: vertical; }

  .report-approval-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
  .report-button.approve { border-color: #00983a; color: #006d29; }
  .report-button.return { border-color: #b59525; color: #6f5713; }
  .report-button.reject { border-color: #d90066; color: #a0004b; }
  .report-button.revise { border-color: #312783; color: #312783; }

  .report-approval-history {
    display: grid;
    gap: 7px;
    margin: 14px 0 0;
    padding: 0;
    list-style: none;
  }
  .report-approval-history li {
    padding: 9px 10px;
    border-left: 3px solid #76cbf3;
    border-radius: 7px;
    background: var(--surface);
    color: var(--muted);
    font-size: 9px;
    line-height: 1.5;
  }
  .report-approval-history strong { display: block; color: var(--text); font-size: 10px; }

  @media (max-width: 700px) {
    .report-approval-fields { grid-template-columns: 1fr; }
    .report-approval-fields label:last-child { grid-column: auto; }
  }

</style>
"""

_SAVE_STATE = r"""
  <div id="report-save-state" class="report-save-state" aria-live="polite">
    <span class="report-save-state-dot" aria-hidden="true"></span>
    <strong id="report-save-state-label">Ei tallennettu</strong>
    <span id="report-save-id" class="report-save-id" hidden></span>
  </div>
"""

_SAVE_BUTTON = r"""
    <button id="report-save" class="report-button save" type="button">
      Tallenna luonnos
    </button>
"""

_MARK_APPROVAL_BUTTON = r"""    <button id="report-mark-approval" class="report-button approval" type="button">
      Merkitse hyväksyntää varten
    </button>"""


_APPROVAL_PANEL = r"""
  <section id="report-approval-panel" class="report-approval-panel" hidden aria-labelledby="report-approval-heading">
    <div class="report-approval-head">
      <div>
        <strong id="report-approval-heading">Koordinaattorin päätös</strong>
        <span>Hyväksyntä tallennetaan muuttumattomana tapahtumana sekä hyväksytyn raporttisisällön tiivisteenä.</span>
      </div>
      <span id="report-approval-actor-summary">Päätöksen tekijä vahvistetaan palvelimen identiteettirajasta.</span>
    </div>
    <div class="report-approval-fields">
      <label>
        Päätöksen perustelu
        <textarea id="report-approval-comment" maxlength="4000" placeholder="Pakollinen palautettaessa tai hylättäessä; hyväksynnässä valinnainen."></textarea>
      </label>
    </div>
    <div class="report-approval-actions">
      <button id="report-approve" class="report-button approve" type="button">Hyväksy raportti</button>
      <button id="report-return" class="report-button return" type="button">Palauta muokattavaksi</button>
      <button id="report-reject" class="report-button reject" type="button">Hylkää</button>
      <button id="report-revise" class="report-button revise" type="button" hidden>Luo uusi versio</button>
    </div>
    <ol id="report-approval-history" class="report-approval-history" aria-label="Hyväksyntähistoria"></ol>
  </section>
"""

_PREVIEW_GUIDANCE = r"""
          Raporttiluonnos ja hyväksyntätila tallennetaan tässä kehitysesikatselussa
          väliaikaiseen fixture-muistiin. Testidata ei ole tuotantodataa eikä VakeVahti
          lähetä raporttia sähköpostiin tai Teamsiin.
"""

_PERSISTED_GUIDANCE = r"""
          Raporttiluonnos ja hyväksyntätila tallennetaan VakeVahdin tietokantaan.
          Sähköposti- tai Teams-lähetys tehdään vasta erillisen, hyväksytyn VakeTomatti-
          integraation kautta.
"""

_OLD_GUIDANCE = r"""
          Raportin valinta, muistiinpanot ja hyväksyntätila ovat tässä vaiheessa tämän
          selainistunnon työtilaa. VakeVahti ei lähetä raporttia sähköpostiin tai Teamsiin
          ennen erillistä hyväksyttyä integraatiota.
"""

_SAVE_SCRIPT_TEMPLATE = r"""
<script id="vake-report-persistence-script">
(() => {
  const previewMode = __PREVIEW_MODE__;
  const selectedIds = new Set();
  let reportId = null;
  let dirty = true;
  let saving = false;
  let savedSelectionKey = "";
  let currentReportStatus = "DRAFT";
  let currentReportVersion = 1;

  const saveButton = document.getElementById("report-save");
  const approvalButton = document.getElementById("report-mark-approval");
  const clearButton = document.getElementById("report-clear");
  const selectVisibleButton = document.getElementById("report-select-visible");
  const notes = document.getElementById("report-notes");
  const list = document.getElementById("opportunity-list");
  const feedback = document.getElementById("report-feedback");
  const workflowStatus = document.getElementById("report-status");
  const saveState = document.getElementById("report-save-state");
  const saveStateLabel = document.getElementById("report-save-state-label");
  const saveId = document.getElementById("report-save-id");
  const approvalPanel = document.getElementById("report-approval-panel");
  const approvalActorSummary = document.getElementById("report-approval-actor-summary");
  const approvalComment = document.getElementById("report-approval-comment");
  const approveButton = document.getElementById("report-approve");
  const returnButton = document.getElementById("report-return");
  const rejectButton = document.getElementById("report-reject");
  const reviseButton = document.getElementById("report-revise");
  const approvalHistory = document.getElementById("report-approval-history");

  function setFeedback(message) {
    feedback.textContent = message;
  }

  async function loadSessionIdentity() {
    try {
      const response = await fetch("/api/session");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const session = await response.json();
      const label = session.display_name || session.actor_id || "Kirjautunut käyttäjä";
      approvalActorSummary.textContent = `Päätöksen tekijä: ${label} · ${session.identity_source}`;
    } catch (error) {
      approvalActorSummary.textContent = "Kirjautunutta identiteettiä ei voitu vahvistaa.";
    }
  }


  function selectionKey(ids) {
    return ids.join(",");
  }

  function decisionLabel(value) {
    const labels = {
      APPROVE: "Hyväksytty",
      RETURN_FOR_EDIT: "Palautettu muokattavaksi",
      REJECT: "Hylätty",
    };
    return labels[String(value || "").toUpperCase()] || String(value || "Päätös");
  }

  function renderApprovalHistory(report) {
    approvalHistory.replaceChildren();
    (report.approval_events || []).forEach((event) => {
      const item = document.createElement("li");
      const title = document.createElement("strong");
      title.textContent = `${decisionLabel(event.decision)} · ${event.actor_display_name || event.actor_id}`;
      const decidedAt = new Intl.DateTimeFormat("fi-FI", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(event.decided_at));
      const detail = document.createElement("span");
      const hash = String(event.content_hash || "").slice(0, 12);
      detail.textContent = `${decidedAt} · sisältö ${hash}${event.comment ? ` · ${event.comment}` : ""}`;
      item.append(title, detail);
      approvalHistory.append(item);
    });
  }

  function applyReportState(report) {
    currentReportStatus = String(report.status || "DRAFT").toUpperCase();
    currentReportVersion = Number(report.version_number || 1);
    const waiting = currentReportStatus === "WAITING_APPROVAL";
    const approved = currentReportStatus === "APPROVED";
    const rejected = currentReportStatus === "REJECTED";
    const labels = {
      DRAFT: "Luonnos",
      WAITING_APPROVAL: "Odottaa koordinaattorin hyväksyntää",
      APPROVED: "Hyväksytty",
      REJECTED: "Hylätty",
    };
    workflowStatus.textContent = labels[currentReportStatus] || currentReportStatus;
    workflowStatus.classList.toggle("waiting", waiting);
    workflowStatus.classList.toggle("approved", approved);
    workflowStatus.classList.toggle("rejected", rejected);
    approvalPanel.hidden = !reportId || (!waiting && !(report.approval_events || []).length);
    approveButton.disabled = !waiting;
    returnButton.disabled = !waiting;
    rejectButton.disabled = !waiting;
    reviseButton.hidden = !approved;
    reviseButton.disabled = !approved;
    approvalButton.disabled = waiting || approved;
    notes.disabled = approved;
    saveButton.disabled = approved;
    selectVisibleButton.disabled = approved;
    clearButton.disabled = approved;
    document.querySelectorAll(".report-row-button").forEach((button) => {
      button.disabled = approved;
    });
    renderApprovalHistory(report);
    document.dispatchEvent(
      new CustomEvent("vake:report-status", { detail: { status: currentReportStatus } })
    );
  }


  function visibleRows() {
    return Array.from(list.querySelectorAll(".opportunity[data-call-id]"));
  }

  function syncVisibleSelections() {
    visibleRows().forEach((row) => {
      const id = Number(row.dataset.callId);
      const button = row.querySelector(".report-row-button");
      if (!Number.isInteger(id) || !button) return;
      if (button.classList.contains("selected")) selectedIds.add(id);
      else selectedIds.delete(id);
    });
  }

  function setSaveState(kind, label) {
    saveState.classList.remove("saved", "dirty", "waiting", "approved", "rejected", "error");
    if (kind) saveState.classList.add(kind);
    saveStateLabel.textContent = label;
    if (reportId) {
      saveId.hidden = false;
      saveId.textContent = `v${currentReportVersion} · ID ${String(reportId).slice(0, 8)}`;
    } else {
      saveId.hidden = true;
      saveId.textContent = "";
    }
  }

  function markDirty() {
    if (currentReportStatus === "APPROVED") {
      setFeedback("Hyväksytty raportti on muuttumaton. Luo uusi versio ennen muokkaamista.");
      return;
    }
    dirty = true;
    if (reportId) setSaveState("dirty", "Muutoksia tallentamatta");
    else setSaveState("", "Ei tallennettu");
  }

  function setCurrentRowSelection(id, selected) {
    const row = list.querySelector(`.opportunity[data-call-id="${id}"]`);
    if (!row) return;
    const button = row.querySelector(".report-row-button");
    if (!button) return;
    button.classList.toggle("selected", selected);
    button.textContent = selected ? "Raportissa ✓" : "Lisää raporttiin";
  }

  function markVisibleConfirmedSelected() {
    state.calls.forEach((call) => {
      if (String(call.relevance_status || "").toUpperCase() !== "RELEVANT") return;
      const id = Number(call.id);
      if (!Number.isInteger(id)) return;
      selectedIds.add(id);
      setCurrentRowSelection(id, true);
    });
    markDirty();
  }

  function clearSelections() {
    selectedIds.clear();
    visibleRows().forEach((row) => {
      const id = Number(row.dataset.callId);
      if (Number.isInteger(id)) setCurrentRowSelection(id, false);
    });
    reportId = null;
    savedSelectionKey = "";
    currentReportStatus = "DRAFT";
    currentReportVersion = 1;
    approvalPanel.hidden = true;
    approvalHistory.replaceChildren();
    notes.disabled = false;
    dirty = true;
    setSaveState("", "Ei tallennettu");
  }

  async function saveDraft() {
    syncVisibleSelections();
    const ids = Array.from(selectedIds);
    if (!ids.length) {
      setFeedback("Valitse vähintään yksi rahoitushaku ennen tallentamista.");
      return null;
    }
    if (saving) return null;

    saving = true;
    saveButton.disabled = true;
    saveButton.classList.add("saving");
    saveButton.textContent = "Tallennetaan…";
    setSaveState("dirty", "Tallennetaan luonnosta…");

    try {
      const nextSelectionKey = selectionKey(ids);
      const canPatch = reportId && savedSelectionKey === nextSelectionKey;
      const response = await fetch(
        canPatch ? `/api/reports/${encodeURIComponent(reportId)}` : "/api/reports",
        {
          method: canPatch ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(
            canPatch
              ? { notes: notes.value.trim() || null }
              : {
                  title: "VakeHyvän rahoitusraportti",
                  notes: notes.value.trim() || null,
                  funding_call_ids: ids,
                }
          ),
        }
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const report = await response.json();
      reportId = report.id;
      savedSelectionKey = nextSelectionKey;
      dirty = false;
      applyReportState(report);
      setSaveState("saved", previewMode ? "Testiluonnos tallennettu" : "Luonnos tallennettu");
      setFeedback(
        previewMode
          ? "Raporttiluonnos tallennettiin testiympäristön fixture-muistiin."
          : "Raporttiluonnos tallennettiin VakeVahdin tietokantaan."
      );
      return report;
    } catch (error) {
      setSaveState("error", "Tallennus epäonnistui");
      setFeedback("Raporttiluonnosta ei voitu tallentaa. Yritä uudelleen.");
      return null;
    } finally {
      saving = false;
      saveButton.disabled = false;
      saveButton.classList.remove("saving");
      saveButton.textContent = "Tallenna luonnos";
    }
  }

  async function submitForApproval() {
    syncVisibleSelections();
    if (!selectedIds.size) return;

    let report = null;
    if (!reportId || dirty) {
      report = await saveDraft();
      if (!report) {
        workflowStatus.textContent = "Luonnos";
        workflowStatus.classList.remove("waiting");
        return;
      }
    }

    approvalButton.disabled = true;
    try {
      const response = await fetch(`/api/reports/${encodeURIComponent(reportId)}/submit`, {
        method: "POST",
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      report = await response.json();
      dirty = false;
      applyReportState(report);
      setSaveState("waiting", "Tallennettu · odottaa hyväksyntää");
      setFeedback(
        previewMode
          ? "Testiraportti tallennettiin ja siirrettiin koordinaattorin hyväksyntätilaan. Sitä ei lähetetty."
          : "Raportti tallennettiin ja siirrettiin koordinaattorin hyväksyntätilaan."
      );
    } catch (error) {
      workflowStatus.textContent = "Luonnos";
      workflowStatus.classList.remove("waiting");
      setSaveState("error", "Hyväksyntätilan tallennus epäonnistui");
      setFeedback("Raportin hyväksyntätilaa ei voitu tallentaa. Luonnos säilyy työtilassa.");
    } finally {
      approvalButton.disabled = false;
    }
  }


  async function decideReport(decision) {
    if (!reportId || currentReportStatus !== "WAITING_APPROVAL") return;
    const comment = approvalComment.value.trim();
    if (decision !== "APPROVE" && !comment) {
      setFeedback("Kirjaa perustelu ennen raportin palauttamista tai hylkäämistä.");
      approvalComment.focus();
      return;
    }

    [approveButton, returnButton, rejectButton].forEach((button) => { button.disabled = true; });
    try {
      const response = await fetch(`/api/reports/${encodeURIComponent(reportId)}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decision,
          comment: comment || null,
        }),
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`HTTP ${response.status}: ${detail}`);
      }
      const report = await response.json();
      dirty = false;
      applyReportState(report);
      approvalComment.value = "";
      if (report.status === "APPROVED") {
        setSaveState("approved", "Hyväksytty · päätös auditoitu");
        setFeedback("Raportti hyväksyttiin. Hyväksytty sisältö ja päätös tallennettiin muuttumattomaan auditointihistoriaan.");
      } else if (report.status === "REJECTED") {
        setSaveState("rejected", "Hylätty · päätös auditoitu");
        setFeedback("Raportti hylättiin. Päätös ja perustelu tallennettiin auditointihistoriaan.");
      } else {
        setSaveState("saved", "Palautettu muokattavaksi");
        setFeedback("Raportti palautettiin muokattavaksi. Aiempi päätös säilyy auditointihistoriassa.");
      }
    } catch (error) {
      setSaveState("error", "Päätöksen tallennus epäonnistui");
      setFeedback("Koordinaattorin päätöstä ei voitu tallentaa. Raportin tila säilyi ennallaan.");
      [approveButton, returnButton, rejectButton].forEach((button) => { button.disabled = false; });
    }
  }


  async function reviseApprovedReport() {
    if (!reportId || currentReportStatus !== "APPROVED") return;
    reviseButton.disabled = true;
    try {
      const response = await fetch(`/api/reports/${encodeURIComponent(reportId)}/revise`, {
        method: "POST",
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`HTTP ${response.status}: ${detail}`);
      }
      const report = await response.json();
      reportId = report.id;
      currentReportVersion = Number(report.version_number || currentReportVersion + 1);
      savedSelectionKey = selectionKey(Array.from(selectedIds));
      dirty = false;
      notes.value = report.notes || "";
      applyReportState(report);
      setSaveState("saved", `Versio ${currentReportVersion} · luonnos`);
      setFeedback(
        `Hyväksytty versio säilyi muuttumattomana. Versio ${currentReportVersion} luotiin muokattavaksi.`
      );
    } catch (error) {
      reviseButton.disabled = false;
      setSaveState("error", "Uuden version luonti epäonnistui");
      setFeedback("Hyväksytyn raportin seuraavaa versiota ei voitu luoda.");
    }
  }


  saveButton.addEventListener("click", saveDraft);

  approvalButton.addEventListener("click", () => {
    window.setTimeout(submitForApproval, 0);
  });

  approveButton.addEventListener("click", () => decideReport("APPROVE"));
  returnButton.addEventListener("click", () => decideReport("RETURN_FOR_EDIT"));
  rejectButton.addEventListener("click", () => decideReport("REJECT"));
  reviseButton.addEventListener("click", reviseApprovedReport);

  clearButton.addEventListener("click", () => {
    clearSelections();
  });

  selectVisibleButton.addEventListener("click", () => {
    window.setTimeout(markVisibleConfirmedSelected, 0);
  });

  notes.addEventListener("input", markDirty);

  list.addEventListener("click", (event) => {
    const button = event.target.closest(".report-row-button");
    if (!button) return;
    window.setTimeout(() => {
      syncVisibleSelections();
      markDirty();
    }, 0);
  });

  const observer = new MutationObserver(() => {
    syncVisibleSelections();
  });
  observer.observe(list, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["class", "data-call-id"],
  });

  approveButton.disabled = true;
  returnButton.disabled = true;
  rejectButton.disabled = true;
  reviseButton.disabled = true;
  loadSessionIdentity();
  setSaveState("", "Ei tallennettu");
})();
</script>
"""


def render_dashboard_report_persistence(
    html: str,
    *,
    enabled: bool,
    preview_mode: bool,
) -> str:
    """Enable report draft persistence only where a safe report-write API exists."""

    if not enabled:
        return html

    required = (
        "</head>",
        "</body>",
        '<div class="report-toolbar">',
        '<div class="report-grid">',
        _MARK_APPROVAL_BUTTON,
        _OLD_GUIDANCE,
    )
    missing = [sentinel for sentinel in required if sentinel not in html]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Dashboard report persistence sentinels missing: {joined}")

    guidance = _PREVIEW_GUIDANCE if preview_mode else _PERSISTED_GUIDANCE
    script = _SAVE_SCRIPT_TEMPLATE.replace(
        "__PREVIEW_MODE__",
        "true" if preview_mode else "false",
        1,
    )

    rendered = html.replace("</head>", f"{_SAVE_STYLE}\n</head>", 1)
    rendered = rendered.replace(
        '<div class="report-toolbar">',
        f"{_SAVE_STATE}\n  <div class=\"report-toolbar\">",
        1,
    )
    rendered = rendered.replace(
        _MARK_APPROVAL_BUTTON,
        f"{_SAVE_BUTTON}{_MARK_APPROVAL_BUTTON}",
        1,
    )
    rendered = rendered.replace(
        '<div class="report-grid">',
        f"{_APPROVAL_PANEL}\n  <div class=\"report-grid\">",
        1,
    )
    rendered = rendered.replace(_OLD_GUIDANCE, guidance, 1)
    return rendered.replace("</body>", f"{script}\n</body>", 1)
