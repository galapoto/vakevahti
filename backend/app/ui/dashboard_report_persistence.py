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

  function setFeedback(message) {
    feedback.textContent = message;
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
    saveState.classList.remove("saved", "dirty", "waiting", "error");
    if (kind) saveState.classList.add(kind);
    saveStateLabel.textContent = label;
    if (reportId) {
      saveId.hidden = false;
      saveId.textContent = `ID ${String(reportId).slice(0, 8)}`;
    } else {
      saveId.hidden = true;
      saveId.textContent = "";
    }
  }

  function markDirty() {
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
      const response = await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: "VakeHyvän rahoitusraportti",
          notes: notes.value.trim() || null,
          funding_call_ids: ids,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const report = await response.json();
      reportId = report.id;
      dirty = false;
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
      workflowStatus.textContent = "Odottaa koordinaattorin hyväksyntää";
      workflowStatus.classList.add("waiting");
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

  saveButton.addEventListener("click", saveDraft);

  approvalButton.addEventListener("click", () => {
    window.setTimeout(submitForApproval, 0);
  });

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
    rendered = rendered.replace(_OLD_GUIDANCE, guidance, 1)
    return rendered.replace("</body>", f"{script}\n</body>", 1)
