"""Vake-aligned presentation layer for the operational dashboard."""

_LOGO_DATA = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA3MCA3MCI+CjxyZWN0"
    "IHg9IjE1IiB5PSI1IiB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHJ4PSIxLjUiIGZpbGw9IiMzMTI3ODMiLz4KPHJl"
    "Y3QgeD0iNDUiIHk9IjUiIHdpZHRoPSIxMCIgaGVpZ2h0PSIxMCIgcng9IjEuNSIgZmlsbD0iI0U2MDA3RSIvPgo8"
    "cmVjdCB4PSI1IiB5PSIyMCIgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiByeD0iMS41IiBmaWxsPSIjNzZDQkYzIi8+"
    "CjxyZWN0IHg9IjIwIiB5PSIyMCIgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiByeD0iMS41IiBmaWxsPSIjMzEyNzgz"
    "Ii8+CjxyZWN0IHg9IjM1IiB5PSIyMCIgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiByeD0iMS41IiBmaWxsPSIjRUE1"
    "Mjk3Ii8+CjxyZWN0IHg9IjUwIiB5PSIyMCIgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiByeD0iMS41IiBmaWxsPSIj"
    "RTYwMDdFIi8+CjxyZWN0IHg9IjUiIHk9IjM1IiB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHJ4PSIxLjUiIGZpbGw9"
    "IiMwMDk4M0EiLz4KPHJlY3QgeD0iMjAiIHk9IjM1IiB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHJ4PSIxLjUiIGZp"
    "bGw9IiM3NEI3MkIiLz4KPHJlY3QgeD0iMzUiIHk9IjM1IiB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHJ4PSIxLjUi"
    "IGZpbGw9IiM3NkNCRjMiLz4KPHJlY3QgeD0iNTAiIHk9IjM1IiB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHJ4PSIx"
    "LjUiIGZpbGw9IiNFQTUyOTciLz4KPHJlY3QgeD0iMjAiIHk9IjUwIiB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHJ4"
    "PSIxLjUiIGZpbGw9IiMwMDk4M0EiLz4KPHJlY3QgeD0iMzUiIHk9IjUwIiB3aWR0aD0iMTAiIGhlaWdodD0iMTAi"
    "IHJ4PSIxLjUiIGZpbGw9IiM3NEI3MkIiLz4KPHJlY3QgeD0iNTAiIHk9IjUwIiB3aWR0aD0iMTAiIGhlaWdodD0i"
    "MTAiIHJ4PSIxLjUiIGZpbGw9IiNFNjAwN0UiLz4KPHJlY3QgeD0iMzUiIHk9IjY1IiB3aWR0aD0iMTAiIGhlaWdo"
    "dD0iNCIgcng9IjEuNSIgZmlsbD0iIzMxMjc4MyIvPgo8L3N2Zz4="
)

_THEME_BOOTSTRAP = """
<script>
(() => {
  const saved = localStorage.getItem("vakevahti-theme");
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved === "light" || saved === "dark"
    ? saved
    : (systemDark ? "dark" : "light");
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
})();
</script>
"""

_THEME_STYLES = f"""
<style id="vake-theme-styles">
  :root {{
    --brand: #312783;
    --brand-strong: #312783;
    --brand-soft: #eeecfb;
    --brand-faint: #f8f7fd;
    --blue: #312783;
    --blue-soft: #eeecfb;
    --purple: #e6007e;
    --purple-soft: #fdebf5;
    --amber: #00983a;
    --amber-soft: #eaf7ee;
    --good: #00983a;
    --good-soft: #eaf7ee;
    --warning: #e6007e;
    --warning-soft: #fdebf5;
    --bg: #f5f7fa;
    --surface: #ffffff;
    --surface-soft: #fafbfc;
    --text: #1b2030;
    --muted: #667085;
    --border: #dfe4ec;
  }}

  html[data-theme="dark"] {{
    color-scheme: dark;
    --bg: #10131b;
    --surface: #181c26;
    --surface-soft: #202530;
    --text: #f4f6fa;
    --muted: #aeb6c5;
    --border: #303746;
    --brand: #76cbf3;
    --brand-strong: #9bddfb;
    --brand-soft: #1b2a3b;
    --brand-faint: #161d29;
    --blue: #76cbf3;
    --blue-soft: #1b2a3b;
    --purple: #ea5297;
    --purple-soft: #382333;
    --amber: #74b72b;
    --amber-soft: #24331d;
    --good: #74b72b;
    --good-soft: #24331d;
    --warning: #ea5297;
    --warning-soft: #382333;
    --danger: #ff8f96;
    --danger-soft: #3a2428;
    --shadow-xs: 0 2px 8px rgba(0, 0, 0, .22);
    --shadow: 0 12px 30px rgba(0, 0, 0, .28);
    --shadow-hover: 0 18px 40px rgba(0, 0, 0, .38);
  }}

  body {{
    background:
      radial-gradient(circle at 12% 0%, rgba(118, 203, 243, .12), transparent 30rem),
      radial-gradient(circle at 92% 6%, rgba(230, 0, 126, .07), transparent 27rem),
      var(--bg);
    transition: background-color .2s ease, color .2s ease;
  }}

  html[data-theme="dark"] body {{
    background:
      radial-gradient(circle at 12% 0%, rgba(118, 203, 243, .08), transparent 30rem),
      radial-gradient(circle at 92% 6%, rgba(234, 82, 151, .07), transparent 27rem),
      var(--bg);
  }}

  .top-actions {{
    display: flex;
    align-items: center;
    gap: 9px;
  }}

  .theme-toggle {{
    min-height: 36px;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text);
    background: var(--surface);
    box-shadow: var(--shadow-xs);
    cursor: pointer;
    font-size: 11px;
    font-weight: 800;
    transition: transform .16s ease, border-color .16s ease, background .16s ease;
  }}

  .theme-toggle:hover {{
    transform: translateY(-1px);
    border-color: var(--brand);
  }}

  .theme-toggle:focus-visible {{
    outline: 3px solid color-mix(in srgb, var(--brand) 25%, transparent);
    outline-offset: 2px;
  }}

  .theme-toggle-icon {{
    width: 20px;
    height: 20px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    color: var(--brand-strong);
    background: var(--brand-soft);
  }}

  .logo {{
    display: grid;
    place-items: center;
    overflow: visible;
    border: 1px solid var(--border);
    border-radius: 15px;
    background: var(--surface);
    box-shadow: var(--shadow-xs);
  }}

  .logo svg {{ display: none; }}

  .logo::before {{
    content: "";
    width: 42px;
    height: 42px;
    background: url("{_LOGO_DATA}") center / contain no-repeat;
  }}

  .system-chip {{
    border-color: color-mix(in srgb, var(--brand) 22%, var(--border));
    color: var(--brand-strong);
    background: var(--brand-faint);
  }}

  .system-chip::before {{
    background: #00983a;
    box-shadow: 0 0 0 4px color-mix(in srgb, #00983a 12%, transparent);
  }}

  .hero {{
    border-color: color-mix(in srgb, var(--brand) 15%, var(--border));
    background: linear-gradient(115deg, var(--surface), var(--brand-faint));
  }}

  .hero::after {{
    background: radial-gradient(
      circle,
      color-mix(in srgb, var(--brand) 14%, transparent),
      transparent 68%
    );
  }}

  .hero h1 .vakehyva {{ color: var(--brand-strong); }}

  .refresh-button {{
    border-color: #312783;
    background: linear-gradient(180deg, #3f34a0, #312783);
    box-shadow: 0 8px 18px rgba(49, 39, 131, .19);
  }}

  .refresh-button:hover {{
    box-shadow: 0 12px 24px rgba(49, 39, 131, .24);
  }}

  .kpi,
  .source-card {{
    background: linear-gradient(145deg, var(--surface) 46%, var(--kpi-soft, var(--source-soft)));
  }}

  .source-card {{
    background: linear-gradient(155deg, var(--surface) 50%, var(--source-soft));
  }}

  .kpi-icon {{
    background: color-mix(in srgb, var(--kpi-color) 10%, var(--surface));
  }}

  .toolbar,
  .opportunity-panel,
  .opportunity,
  .detail-box,
  .description-box,
  .source-home-link,
  .row-source-link,
  .source-link,
  .source-select {{
    background-color: var(--surface);
    color: var(--text);
    border-color: var(--border);
  }}

  .opportunity {{
    margin: 8px 10px;
    border: 1px solid var(--border);
    border-radius: 13px;
    overflow: hidden;
    box-shadow: 0 2px 7px rgba(16, 24, 40, .035);
  }}

  .opportunity:first-child {{ margin-top: 10px; }}
  .opportunity:last-child {{ margin-bottom: 10px; }}

  .opportunity:hover {{
    background: color-mix(in srgb, var(--row-soft) 30%, var(--surface));
  }}

  .opportunity-details {{
    border-top-color: var(--border);
    background: color-mix(in srgb, var(--row-soft) 35%, var(--surface-soft));
  }}

  .fact,
  .source-card-footer {{
    border-color: color-mix(in srgb, var(--source-color) 12%, var(--border));
  }}

  .fact strong,
  .detail-value,
  .deadline-value {{ color: var(--text); }}

  .section-head h2,
  .brand strong {{ color: var(--text); }}

  .source-card[data-source="STM"] {{
    --source-color: #312783;
    --source-soft: #eeecfb;
  }}

  .source-card[data-source="SITRA"] {{
    --source-color: #e6007e;
    --source-soft: #fdebf5;
  }}

  .source-card[data-source="ACADEMY"] {{
    --source-color: #00983a;
    --source-soft: #eaf7ee;
  }}

  html[data-theme="dark"] .source-card[data-source="STM"] {{
    --source-color: #76cbf3;
    --source-soft: #1b2a3b;
  }}

  html[data-theme="dark"] .source-card[data-source="SITRA"] {{
    --source-color: #ea5297;
    --source-soft: #382333;
  }}

  html[data-theme="dark"] .source-card[data-source="ACADEMY"] {{
    --source-color: #74b72b;
    --source-soft: #24331d;
  }}

  html[data-theme="dark"] .opportunity[data-source="STM"] {{
    --row-color: #76cbf3;
    --row-soft: #1b2a3b;
  }}

  html[data-theme="dark"] .opportunity[data-source="SITRA"] {{
    --row-color: #ea5297;
    --row-soft: #382333;
  }}

  html[data-theme="dark"] .opportunity[data-source="ACADEMY"] {{
    --row-color: #74b72b;
    --row-soft: #24331d;
  }}

  html[data-theme="dark"] .health-never_scanned {{
    color: #d6dbe4;
    background: #2b313d;
  }}

  @media (max-width: 700px) {{
    .top-actions {{ gap: 6px; }}
    .theme-toggle-label {{ display: none; }}
    .theme-toggle {{ width: 36px; padding: 7px; justify-content: center; }}
    .logo::before {{ width: 36px; height: 36px; }}
  }}
</style>
"""

_THEME_TOGGLE = """
      <div class="top-actions">
        <div class="system-chip">Tallennettu tilannekuva</div>
        <button
          id="theme-toggle"
          class="theme-toggle"
          type="button"
          aria-label="Vaihda tumma tai vaalea tila"
          aria-pressed="false"
        >
          <span id="theme-toggle-icon" class="theme-toggle-icon" aria-hidden="true">☾</span>
          <span id="theme-toggle-label" class="theme-toggle-label">Tumma tila</span>
        </button>
      </div>
"""

_THEME_SCRIPT = """
<script id="vake-theme-script">
(() => {
  const root = document.documentElement;
  const button = document.getElementById("theme-toggle");
  const icon = document.getElementById("theme-toggle-icon");
  const label = document.getElementById("theme-toggle-label");
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function currentTheme() {
    return root.dataset.theme === "dark" ? "dark" : "light";
  }

  function renderToggle() {
    const dark = currentTheme() === "dark";
    button.setAttribute("aria-pressed", String(dark));
    icon.textContent = dark ? "☀" : "☾";
    label.textContent = dark ? "Vaalea tila" : "Tumma tila";
  }

  function applyTheme(theme, persist) {
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    if (persist) localStorage.setItem("vakevahti-theme", theme);
    renderToggle();
  }

  button.addEventListener("click", () => {
    applyTheme(currentTheme() === "dark" ? "light" : "dark", true);
  });

  media.addEventListener("change", (event) => {
    if (!localStorage.getItem("vakevahti-theme")) {
      applyTheme(event.matches ? "dark" : "light", false);
    }
  });

  renderToggle();
})();
</script>
"""


def apply_dashboard_theme(html: str) -> str:
    """Inject brand-aligned theming without changing dashboard data behavior."""

    html = html.replace("<style>", f"{_THEME_BOOTSTRAP}\n<style>", 1)
    html = html.replace("</style>", f"</style>\n{_THEME_STYLES}", 1)
    html = html.replace(
        '<div class="system-chip">Tallennettu tilannekuva</div>',
        _THEME_TOGGLE.strip(),
        1,
    )
    return html.replace("</body>", f"{_THEME_SCRIPT}\n</body>", 1)
