"""Canonical VAKE brand tokens and typography for employee-facing surfaces."""

VAKE_FONT_FAMILY = '"Poppins", Calibri, Arial, sans-serif'
VAKE_COLORS = {
    "purple": "#312783",
    "light_blue": "#76CBF3",
    "green": "#00983A",
    "light_green": "#74B72B",
    "fuchsia": "#E6007E",
    "light_fuchsia": "#EA5297",
    "black": "#000000",
    "white": "#FFFFFF",
}

_POPPINS_LINKS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap"
>
"""

_BRAND_STYLES = f"""
<style id="vake-brand-typography">
  :root {{
    --vake-font: {VAKE_FONT_FAMILY};
    --vake-purple: #312783;
    --vake-light-blue: #76CBF3;
    --vake-green: #00983A;
    --vake-light-green: #74B72B;
    --vake-fuchsia: #E6007E;
    --vake-light-fuchsia: #EA5297;
  }}

  html,
  body,
  button,
  input,
  select,
  textarea {{
    font-family: var(--vake-font);
  }}

  body {{
    font-weight: 400;
    letter-spacing: -.006em;
  }}

  h1,
  .hero h1,
  .brand strong {{
    font-family: var(--vake-font);
    font-weight: 700;
    letter-spacing: -.028em;
  }}

  h2,
  h3,
  .section-head h2,
  .report-panel-head strong,
  .report-item h3 {{
    font-family: var(--vake-font);
    font-weight: 600;
    letter-spacing: -.018em;
  }}

  .hero p,
  .section-head p,
  .report-guidance,
  .description-box,
  .detail-label {{
    font-family: var(--vake-font);
    font-weight: 300;
  }}

  button,
  .system-chip,
  .status-pill,
  .certainty-pill,
  .health-pill,
  .source-card-status {{
    font-weight: 600;
  }}

  .refresh-button,
  .report-button.primary {{
    background: #312783;
    border-color: #312783;
    color: #fff;
  }}

  .report-button.approval {{
    border-color: #E6007E;
    color: #E6007E;
  }}

  .report-button.save {{
    border-color: #00983A;
    color: #006d29;
  }}

  ::selection {{
    color: #000;
    background: #76CBF3;
  }}
</style>
"""


def apply_vake_brand_typography(html: str) -> str:
    """Apply the official VAKE Poppins typography and canonical brand tokens."""

    if "</head>" not in html:
        raise ValueError("VAKE brand typography requires a closing head element.")
    assets = f"{_POPPINS_LINKS}\n{_BRAND_STYLES}"
    return html.replace("</head>", f"{assets}\n</head>", 1)
