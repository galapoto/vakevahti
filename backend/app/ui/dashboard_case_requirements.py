"""Expose source-grounded funding requirements in the unified case workspace."""

_REQUIREMENT_STYLES = r"""
<style id="vake-case-requirement-styles">
  .case-requirement-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin-bottom: 12px;
  }
  .case-requirement-count {
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 5px 8px;
    background: var(--surface);
    color: var(--muted);
    font-size: 9px;
    font-weight: 850;
  }
  .case-requirement-list { display: grid; gap: 10px; }
  .case-requirement {
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 11px;
    background: var(--surface);
  }
  .case-requirement-head {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    align-items: flex-start;
  }
  .case-requirement h4 {
    margin: 0;
    color: var(--text);
    font-size: 11px;
    line-height: 1.4;
  }
  .case-requirement p {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 10px;
    line-height: 1.55;
  }
  .case-requirement-badge {
    flex: 0 0 auto;
    border-radius: 999px;
    padding: 4px 7px;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: .035em;
    text-transform: uppercase;
  }
  .case-requirement-badge.confirmed {
    color: #00983A;
    background: color-mix(in srgb, #1FB578 13%, var(--surface));
  }
  .case-requirement-badge.evidence {
    color: #28738A;
    background: color-mix(in srgb, #76CBF3 16%, var(--surface));
  }
  .case-requirement-badge.review {
    color: #7a6113;
    background: color-mix(in srgb, #F4D25A 23%, var(--surface));
  }
  .case-requirement details { margin-top: 8px; }
  .case-requirement summary {
    color: #312783;
    cursor: pointer;
    font-size: 9px;
    font-weight: 850;
  }
  .case-requirement-evidence {
    margin: 7px 0 0;
    padding-left: 16px;
    color: var(--muted);
    font-size: 9px;
    line-height: 1.5;
  }
  .case-requirement-source {
    display: inline-block;
    margin-top: 8px;
    color: #312783;
    font-size: 9px;
    font-weight: 850;
    text-decoration: none;
  }
</style>
"""

_REQUIREMENT_CARD = r"""
<section class="case-card" id="case-requirements-card">
  <div class="case-card-head">
    <strong>Rahoitusvaatimukset</strong>
    <span>Varmuus ja lähdenäyttö erikseen</span>
  </div>
  <div class="case-card-body">
    <div id="case-requirement-summary" class="case-requirement-summary"></div>
    <div id="case-requirement-list" class="case-requirement-list">
      <div class="case-empty">Vaatimukset latautuvat, kun avaat rahoituscasen.</div>
    </div>
  </div>
</section>
"""

_REQUIREMENT_SCRIPT = r"""
<script id="vake-case-requirement-script">
(() => {
  const caseLabel = document.getElementById("case-id-label");
  const list = document.getElementById("case-requirement-list");
  const summary = document.getElementById("case-requirement-summary");
  if (!caseLabel || !list || !summary) return;

  let lastCaseId = "";

  function node(tag, value, className) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = String(value ?? "");
    return element;
  }

  function certainty(value) {
    if (value === "CONFIRMED") return ["Vahvistettu", "confirmed"];
    if (value === "EVIDENCE_FOUND") return ["Lähdenäyttö", "evidence"];
    return ["Tarkistettava", "review"];
  }

  function renderSummary(requirements) {
    const counts = { CONFIRMED: 0, EVIDENCE_FOUND: 0, REVIEW_REQUIRED: 0 };
    requirements.forEach((item) => {
      if (Object.hasOwn(counts, item.certainty)) counts[item.certainty] += 1;
    });
    summary.replaceChildren(
      node("span", `Vahvistettu ${counts.CONFIRMED}`, "case-requirement-count"),
      node("span", `Lähdenäyttö ${counts.EVIDENCE_FOUND}`, "case-requirement-count"),
      node("span", `Tarkistettava ${counts.REVIEW_REQUIRED}`, "case-requirement-count")
    );
  }

  function render(requirements) {
    list.replaceChildren();
    renderSummary(requirements);
    if (!requirements.length) {
      list.append(node("div", "Rakenteisia rahoitusvaatimuksia ei ole vielä muodostettu.", "case-empty"));
      return;
    }

    requirements.forEach((requirement) => {
      const item = document.createElement("article");
      item.className = "case-requirement";
      const head = document.createElement("div");
      head.className = "case-requirement-head";
      head.append(node("h4", requirement.title));
      const [label, badgeClass] = certainty(requirement.certainty);
      head.append(node("span", label, `case-requirement-badge ${badgeClass}`));
      item.append(head, node("p", requirement.statement));

      const evidence = Array.isArray(requirement.evidence) ? requirement.evidence : [];
      if (evidence.length) {
        const details = document.createElement("details");
        const detailsSummary = node("summary", `Näyttö lähteestä (${evidence.length})`);
        const evidenceList = document.createElement("ul");
        evidenceList.className = "case-requirement-evidence";
        evidence.slice(0, 4).forEach((entry) => {
          const text = entry.text || entry.section || "Lähdenäyttö";
          evidenceList.append(node("li", text));
        });
        details.append(detailsSummary, evidenceList);
        item.append(details);
      }

      if (requirement.source_url) {
        const link = document.createElement("a");
        link.className = "case-requirement-source";
        link.href = requirement.source_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Avaa alkuperäinen lähde ↗";
        item.append(link);
      }
      list.append(item);
    });
  }

  async function refresh() {
    const match = caseLabel.textContent.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);
    const caseId = match ? match[0] : "";
    if (!caseId || caseId === lastCaseId) return;
    lastCaseId = caseId;
    summary.replaceChildren();
    list.replaceChildren(node("div", "Päivitetään rahoitusvaatimuksia…", "case-empty"));
    try {
      const response = await fetch(`/api/cases/${encodeURIComponent(caseId)}/requirements`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      render(await response.json());
    } catch (error) {
      list.replaceChildren(
        node("div", "Rahoitusvaatimuksia ei voitu ladata.", "case-empty")
      );
    }
  }

  const observer = new MutationObserver(refresh);
  observer.observe(caseLabel, { childList: true, characterData: true, subtree: true });
  refresh();
})();
</script>
"""


def render_dashboard_case_requirements(html: str) -> str:
    """Add the requirement intelligence card to the unified case workspace."""

    marker = '<section class="case-card" id="case-automation-card">'
    if marker not in html or "</head>" not in html or "</body>" not in html:
        raise ValueError("Dashboard case requirement sentinels are missing.")

    rendered = html.replace("</head>", f"{_REQUIREMENT_STYLES}\n</head>", 1)
    rendered = rendered.replace(marker, f"{_REQUIREMENT_CARD}\n      {marker}", 1)
    return rendered.replace("</body>", f"{_REQUIREMENT_SCRIPT}\n</body>", 1)
