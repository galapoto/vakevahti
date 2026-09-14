"""Expose backend-owned case automation tasks in the unified workspace."""

_TASK_STYLES = r"""
<style id="vake-case-task-styles">
  .case-task-list { display: grid; gap: 10px; }
  .case-task {
    display: grid;
    grid-template-columns: 30px minmax(0, 1fr) auto;
    gap: 10px;
    align-items: start;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 11px;
    background: var(--surface);
  }
  .case-task-mark {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: color-mix(in srgb, #76CBF3 16%, var(--surface));
    color: #28738A;
    font-size: 13px;
    font-weight: 900;
  }
  .case-task.completed .case-task-mark {
    background: color-mix(in srgb, #1FB578 15%, var(--surface));
    color: #00983A;
  }
  .case-task h4 { margin: 0; color: var(--text); font-size: 11px; line-height: 1.4; }
  .case-task p { margin: 4px 0 0; color: var(--muted); font-size: 10px; line-height: 1.5; }
  .case-task-due {
    white-space: nowrap;
    color: #28738A;
    font-size: 9px;
    font-weight: 800;
  }
  .case-task-state {
    display: inline-block;
    margin-top: 6px;
    border-radius: 999px;
    padding: 3px 7px;
    background: color-mix(in srgb, #76CBF3 12%, var(--surface));
    color: #28738A;
    font-size: 8px;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: .04em;
  }
  .case-task.completed .case-task-state {
    background: color-mix(in srgb, #74B72B 12%, var(--surface));
    color: #00983A;
  }
</style>
"""

_TASK_CARD = r"""
<section class="case-card" id="case-automation-card">
  <div class="case-card-head">
    <strong>Automaattinen tehtävälista</strong>
    <span>VakeTomatti päivittää tilan</span>
  </div>
  <div id="case-task-list" class="case-card-body case-task-list">
    <div class="case-empty">Tehtävät latautuvat, kun avaat rahoituscasen.</div>
  </div>
</section>
"""

_TASK_SCRIPT = r"""
<script id="vake-case-task-script">
(() => {
  const caseLabel = document.getElementById("case-id-label");
  const taskList = document.getElementById("case-task-list");
  const nextAction = document.getElementById("case-next-action");
  if (!caseLabel || !taskList || !nextAction) return;

  let lastCaseId = "";

  function node(tag, value, className) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = String(value ?? "");
    return element;
  }

  function dateLabel(value) {
    if (!value) return "Ei määräpäivää";
    const parts = String(value).split("-");
    if (parts.length === 3) return `${Number(parts[2])}.${Number(parts[1])}.${parts[0]}`;
    return String(value);
  }

  function render(tasks) {
    taskList.replaceChildren();
    if (!tasks.length) {
      taskList.append(node("div", "Automaattisia tehtäviä ei ole vielä muodostettu.", "case-empty"));
      return;
    }
    tasks.forEach((task) => {
      const completed = task.status === "COMPLETED";
      const item = document.createElement("article");
      item.className = `case-task${completed ? " completed" : ""}`;
      item.append(node("div", completed ? "✓" : "→", "case-task-mark"));

      const copy = document.createElement("div");
      copy.append(node("h4", task.title));
      copy.append(node("p", task.detail));
      copy.append(node("span", completed ? "Valmis" : "Avoin", "case-task-state"));
      item.append(copy);
      item.append(node("span", dateLabel(task.due_on), "case-task-due"));
      taskList.append(item);
    });
  }

  async function refresh() {
    const match = caseLabel.textContent.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);
    const caseId = match ? match[0] : "";
    if (!caseId || caseId === lastCaseId) return;
    lastCaseId = caseId;
    taskList.replaceChildren(node("div", "Päivitetään tehtävälistaa…", "case-empty"));
    try {
      const response = await fetch(`/api/cases/${encodeURIComponent(caseId)}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const caseData = await response.json();
      render(caseData.tasks || []);
      if (caseData.next_action) nextAction.textContent = caseData.next_action;
    } catch (error) {
      taskList.replaceChildren(
        node("div", "Automaattista tehtävälistaa ei voitu ladata.", "case-empty")
      );
    }
  }

  const observer = new MutationObserver(refresh);
  observer.observe(caseLabel, { childList: true, characterData: true, subtree: true });
  refresh();
})();
</script>
"""


def render_dashboard_case_tasks(html: str) -> str:
    """Add the automatic checklist to the existing unified case workspace."""

    marker = (
        '<section class="case-card">\n'
        '        <div class="case-card-head"><strong>Caseen liittyvät aineistot</strong>'
    )
    if marker not in html or "</head>" not in html or "</body>" not in html:
        raise ValueError("Dashboard case task sentinels are missing.")

    rendered = html.replace("</head>", f"{_TASK_STYLES}\n</head>", 1)
    rendered = rendered.replace(marker, f"{_TASK_CARD}\n      {marker}", 1)
    return rendered.replace("</body>", f"{_TASK_SCRIPT}\n</body>", 1)
