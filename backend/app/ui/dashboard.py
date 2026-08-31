"""Self-contained operational dashboard served by FastAPI.

The dashboard intentionally stays dependency-light for the current managed workplace
machine. It reads only VakeVahti's persisted API contracts; loading the page never
triggers a funding-source scan.
"""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="fi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VakeVahti | VakeHyvälle sopivat rahoitushaut</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7f9;
      --surface: #ffffff;
      --surface-soft: #f9fafb;
      --text: #16202a;
      --muted: #667085;
      --border: #dfe5ea;
      --brand: #e20b17;
      --brand-strong: #b70710;
      --brand-soft: #fff0f1;
      --brand-faint: #fff8f8;
      --good: #16805a;
      --good-soft: #eaf8f2;
      --warning: #b26200;
      --warning-soft: #fff6e3;
      --danger: #b42318;
      --danger-soft: #fff0ee;
      --blue: #2563eb;
      --blue-soft: #eef5ff;
      --purple: #7c3aed;
      --purple-soft: #f5f1ff;
      --amber: #c15f08;
      --amber-soft: #fff7e8;
      --shadow-xs: 0 2px 8px rgba(16, 24, 40, .05);
      --shadow: 0 10px 28px rgba(16, 24, 40, .07);
      --shadow-hover: 0 18px 36px rgba(16, 24, 40, .12);
      --radius-xl: 22px;
      --radius-lg: 17px;
      --radius-md: 13px;
    }

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 14% 0%, rgba(226, 11, 23, .055), transparent 28rem),
        radial-gradient(circle at 92% 8%, rgba(37, 99, 235, .045), transparent 26rem),
        var(--bg);
    }

    button, select, a { font: inherit; }
    button { color: inherit; }

    .shell {
      width: min(1220px, calc(100% - 36px));
      margin: 0 auto;
      padding: 22px 0 58px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 24px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .logo {
      width: 56px;
      height: 56px;
      flex: 0 0 auto;
      overflow: hidden;
      border-radius: 16px;
      box-shadow: 0 10px 24px rgba(183, 7, 16, .24);
    }

    .logo svg { display: block; width: 100%; height: 100%; }
    .brand strong { display: block; font-size: 18px; letter-spacing: -.02em; }
    .brand span { display: block; margin-top: 2px; color: var(--muted); font-size: 12px; }

    .system-chip {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 8px 11px;
      border: 1px solid #f0cfd2;
      border-radius: 999px;
      background: var(--brand-faint);
      color: var(--brand-strong);
      font-size: 11px;
      font-weight: 800;
      box-shadow: var(--shadow-xs);
    }

    .system-chip::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--brand);
      box-shadow: 0 0 0 4px rgba(226, 11, 23, .08);
    }

    .hero {
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 28px;
      align-items: end;
      overflow: hidden;
      margin-bottom: 18px;
      padding: 28px 30px;
      border: 1px solid #eadfe0;
      border-radius: var(--radius-xl);
      background:
        linear-gradient(115deg, rgba(255,255,255,.97), rgba(255,248,248,.96)),
        var(--surface);
      box-shadow: var(--shadow);
    }

    .hero::after {
      content: "";
      position: absolute;
      width: 240px;
      height: 240px;
      right: -80px;
      top: -120px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(226, 11, 23, .12), rgba(226, 11, 23, 0) 68%);
      pointer-events: none;
    }

    .eyebrow {
      margin: 0 0 8px;
      color: var(--brand-strong);
      font-size: 11px;
      font-weight: 850;
      letter-spacing: .09em;
      text-transform: uppercase;
    }

    .hero h1 {
      margin: 0;
      max-width: 820px;
      font-size: clamp(31px, 4vw, 50px);
      line-height: 1.03;
      letter-spacing: -.045em;
    }

    .hero h1 .vakehyva { color: var(--brand); }

    .hero p {
      margin: 13px 0 0;
      max-width: 820px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.68;
    }

    .refresh-button {
      position: relative;
      z-index: 1;
      min-height: 44px;
      border: 1px solid var(--brand);
      border-radius: 11px;
      padding: 10px 15px;
      color: #fff;
      background: linear-gradient(180deg, #ef1b26, var(--brand));
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 8px 18px rgba(226, 11, 23, .18);
      transition: transform .16s ease, box-shadow .16s ease;
    }

    .refresh-button:hover { transform: translateY(-1px); box-shadow: 0 12px 24px rgba(226, 11, 23, .23); }
    .refresh-button:focus-visible { outline: 3px solid rgba(226, 11, 23, .23); outline-offset: 3px; }
    .refresh-button:disabled { opacity: .55; cursor: wait; transform: none; }

    .status-banner {
      display: none;
      align-items: flex-start;
      gap: 9px;
      padding: 12px 14px;
      margin-bottom: 18px;
      border: 1px solid #f1c7c2;
      border-radius: 11px;
      background: var(--danger-soft);
      color: var(--danger);
      font-size: 13px;
      line-height: 1.5;
    }

    .status-banner.visible { display: flex; }
    .status-dot { width: 8px; height: 8px; margin-top: 5px; flex: 0 0 auto; border-radius: 50%; background: currentColor; }

    .kpis {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 28px;
    }

    .kpi {
      --kpi-color: var(--brand);
      --kpi-soft: var(--brand-soft);
      position: relative;
      min-height: 136px;
      padding: 18px 18px 17px;
      overflow: hidden;
      border: 1px solid color-mix(in srgb, var(--kpi-color) 25%, var(--border));
      border-radius: var(--radius-lg);
      background: linear-gradient(145deg, #fff 44%, var(--kpi-soft));
      box-shadow: var(--shadow-xs);
      text-align: left;
      cursor: pointer;
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }

    .kpi::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--kpi-color); }
    .kpi::after { content: ""; position: absolute; width: 90px; height: 90px; right: -38px; bottom: -45px; border-radius: 50%; background: color-mix(in srgb, var(--kpi-color) 7%, transparent); }
    .kpi:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); border-color: var(--kpi-color); }
    .kpi:focus-visible { outline: 3px solid color-mix(in srgb, var(--kpi-color) 26%, transparent); outline-offset: 2px; }
    .kpi-blue { --kpi-color: var(--blue); --kpi-soft: var(--blue-soft); }
    .kpi-green { --kpi-color: var(--good); --kpi-soft: var(--good-soft); }
    .kpi-amber { --kpi-color: var(--amber); --kpi-soft: var(--amber-soft); }
    .kpi-purple { --kpi-color: var(--purple); --kpi-soft: var(--purple-soft); }

    .kpi-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .kpi-icon { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 9px; color: var(--kpi-color); background: color-mix(in srgb, var(--kpi-color) 10%, white); font-size: 14px; font-weight: 900; }
    .kpi-label { color: var(--muted); font-size: 10px; font-weight: 850; letter-spacing: .055em; text-transform: uppercase; }
    .kpi-value { display: block; margin-top: 10px; color: var(--kpi-color); font-size: 31px; font-weight: 880; line-height: 1; letter-spacing: -.04em; }
    .kpi-detail { display: block; margin-top: 8px; color: var(--muted); font-size: 11px; line-height: 1.42; }
    .kpi-action { display: inline-flex; margin-top: 9px; color: var(--kpi-color); font-size: 10px; font-weight: 850; }

    .section { margin-top: 28px; scroll-margin-top: 18px; }
    .section-head { display: flex; align-items: end; justify-content: space-between; gap: 16px; margin-bottom: 13px; }
    .section-head h2 { margin: 0; font-size: 22px; letter-spacing: -.028em; }
    .section-head p { margin: 6px 0 0; max-width: 820px; color: var(--muted); font-size: 13px; line-height: 1.52; }

    .section-kicker {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 6px;
      color: var(--brand-strong);
      font-size: 10px;
      font-weight: 850;
      letter-spacing: .07em;
      text-transform: uppercase;
    }

    .section-kicker::before { content: ""; width: 18px; height: 3px; border-radius: 999px; background: var(--brand); }

    .source-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 13px; }

    .source-card {
      --source-color: var(--brand);
      --source-soft: var(--brand-soft);
      position: relative;
      overflow: hidden;
      border: 1px solid color-mix(in srgb, var(--source-color) 25%, var(--border));
      border-radius: var(--radius-lg);
      background: linear-gradient(155deg, #fff 48%, var(--source-soft));
      box-shadow: var(--shadow-xs);
      transition: box-shadow .16s ease, transform .16s ease, border-color .16s ease;
    }

    .source-card::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 5px; background: linear-gradient(90deg, var(--source-color), color-mix(in srgb, var(--source-color) 45%, white)); }
    .source-card[data-source="STM"] { --source-color: var(--blue); --source-soft: var(--blue-soft); }
    .source-card[data-source="SITRA"] { --source-color: var(--purple); --source-soft: var(--purple-soft); }
    .source-card[data-source="ACADEMY"] { --source-color: var(--amber); --source-soft: var(--amber-soft); }
    .source-card:hover { transform: translateY(-3px); border-color: var(--source-color); box-shadow: var(--shadow-hover); }
    .source-card.flash { animation: card-flash .85s ease; }

    @keyframes card-flash {
      0%, 100% { box-shadow: var(--shadow-xs); }
      45% { box-shadow: 0 0 0 4px color-mix(in srgb, var(--source-color) 20%, transparent), var(--shadow-hover); }
    }

    .source-card-main { width: 100%; padding: 20px 19px 13px; border: 0; background: transparent; text-align: left; cursor: pointer; }
    .source-card-main:focus-visible { outline: 3px solid color-mix(in srgb, var(--source-color) 26%, transparent); outline-offset: -3px; }
    .source-card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
    .source-name { color: var(--source-color); font-size: 16px; font-weight: 880; letter-spacing: -.015em; }

    .health-badge { padding: 5px 8px; border-radius: 999px; font-size: 9px; font-weight: 880; letter-spacing: .03em; }
    .health-healthy { color: var(--good); background: var(--good-soft); }
    .health-failing { color: var(--danger); background: var(--danger-soft); }
    .health-running { color: var(--warning); background: var(--warning-soft); }
    .health-never_scanned { color: #53606b; background: #eef2f5; }

    .source-count { color: var(--source-color); font-size: 29px; font-weight: 880; letter-spacing: -.04em; }
    .source-count span { margin-left: 5px; color: var(--muted); font-size: 11px; font-weight: 700; letter-spacing: 0; }
    .fact-list { display: grid; gap: 8px; margin-top: 15px; }
    .fact { display: grid; grid-template-columns: 1fr auto; gap: 10px; padding-top: 8px; border-top: 1px solid color-mix(in srgb, var(--source-color) 11%, #edf1f3); color: var(--muted); font-size: 10px; }
    .fact strong { color: #344054; font-weight: 800; text-align: right; }

    .source-card-footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 18px 14px; border-top: 1px solid color-mix(in srgb, var(--source-color) 12%, #edf1f3); }
    .source-filter-hint { color: var(--source-color); font-size: 10px; font-weight: 850; }

    .source-home-link, .row-source-link, .source-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      border: 1px solid currentColor;
      border-radius: 9px;
      background: #fff;
      font-size: 10px;
      font-weight: 850;
      text-decoration: none;
      transition: transform .14s ease, box-shadow .14s ease;
    }

    .source-home-link { min-height: 34px; padding: 7px 10px; color: var(--source-color); }
    .source-home-link:hover, .row-source-link:hover, .source-link:hover { transform: translateY(-1px); box-shadow: var(--shadow-xs); }
    .source-home-link:focus-visible, .row-source-link:focus-visible, .source-link:focus-visible { outline: 3px solid rgba(226, 11, 23, .18); outline-offset: 2px; }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 14px 16px;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      background: var(--surface);
      box-shadow: var(--shadow-xs);
    }

    .toolbar-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
    .toolbar label { color: var(--muted); font-size: 11px; font-weight: 800; }
    .source-select { min-width: 190px; min-height: 40px; padding: 8px 32px 8px 10px; border: 1px solid #cbd5dc; border-radius: 9px; color: var(--text); background: white; }
    .source-select:focus-visible { outline: 3px solid rgba(226, 11, 23, .16); outline-offset: 2px; }
    .list-count { color: var(--muted); font-size: 11px; font-weight: 700; }

    .opportunity-panel { margin-top: 12px; }
    .empty-state, .loading-state { padding: 44px 22px; border: 1px solid var(--border); border-radius: var(--radius-lg); background: var(--surface); text-align: center; color: var(--muted); font-size: 13px; line-height: 1.6; box-shadow: var(--shadow-xs); }
    .opportunity-list { display: grid; gap: 10px; }

    .opportunity {
      --row-color: var(--brand);
      --row-soft: var(--brand-soft);
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      overflow: hidden;
      border: 1px solid color-mix(in srgb, var(--row-color) 16%, var(--border));
      border-radius: 14px;
      background: #fff;
      box-shadow: var(--shadow-xs);
      transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    }

    .opportunity[data-source="STM"] { --row-color: var(--blue); --row-soft: var(--blue-soft); }
    .opportunity[data-source="SITRA"] { --row-color: var(--purple); --row-soft: var(--purple-soft); }
    .opportunity[data-source="ACADEMY"] { --row-color: var(--amber); --row-soft: var(--amber-soft); }
    .opportunity:hover { transform: translateY(-1px); border-color: color-mix(in srgb, var(--row-color) 45%, var(--border)); box-shadow: var(--shadow); }
    .opportunity::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--row-color); }

    .opportunity-toggle {
      min-width: 0;
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr) 178px 28px;
      gap: 14px;
      align-items: center;
      padding: 16px 12px 16px 20px;
      border: 0;
      background: transparent;
      text-align: left;
      cursor: pointer;
    }

    .opportunity-toggle:focus-visible { outline: 3px solid color-mix(in srgb, var(--row-color) 22%, transparent); outline-offset: -3px; }
    .source-pill { justify-self: start; padding: 6px 9px; border-radius: 999px; color: var(--row-color); background: var(--row-soft); font-size: 9px; font-weight: 880; }
    .title-stack { min-width: 0; }
    .opportunity-title { display: block; min-width: 0; font-size: 13px; font-weight: 820; line-height: 1.42; transition: color .14s ease; }
    .opportunity-toggle:hover .opportunity-title { color: var(--row-color); }

    .why-line {
      display: -webkit-box;
      margin-top: 5px;
      overflow: hidden;
      color: #667085;
      font-size: 10px;
      line-height: 1.45;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
    }

    .why-line strong { color: var(--brand-strong); font-weight: 850; }
    .deadline-block { text-align: right; }
    .deadline-label { display: block; margin-bottom: 4px; color: var(--muted); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; }
    .deadline-value { display: inline-block; padding: 5px 8px; border-radius: 8px; color: #344054; background: #f4f6f8; font-size: 10px; font-weight: 800; }
    .deadline-soon .deadline-value { color: var(--warning); background: var(--warning-soft); }
    .deadline-past .deadline-value { color: var(--danger); background: var(--danger-soft); }
    .chevron { justify-self: end; color: var(--row-color); font-size: 21px; line-height: 1; transition: transform .16s ease; }
    .opportunity-toggle[aria-expanded="true"] .chevron { transform: rotate(90deg); }

    .row-action { display: flex; align-items: center; padding: 10px 14px 10px 4px; }
    .row-source-link { min-height: 36px; padding: 7px 10px; color: var(--row-color); white-space: nowrap; }

    .opportunity-details {
      grid-column: 1 / -1;
      padding: 0 18px 18px 124px;
      border-top: 1px solid color-mix(in srgb, var(--row-color) 12%, #edf1f3);
      background: linear-gradient(180deg, color-mix(in srgb, var(--row-soft) 48%, #fff), #fff);
    }

    .details-loading { padding: 17px 0 0; color: var(--muted); font-size: 11px; }
    .fit-box { margin-top: 16px; padding: 14px 15px; border: 1px solid #f0cfd2; border-radius: 12px; background: linear-gradient(135deg, #fff, var(--brand-faint)); }
    .fit-box .detail-label { color: var(--brand-strong); }
    .fit-box .detail-value { color: #3a2426; font-size: 12px; font-weight: 650; }

    .detail-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 11px; padding-top: 12px; }
    .detail-box { min-width: 0; padding: 12px; border: 1px solid #e3e8eb; border-radius: 10px; background: #fff; }
    .detail-label { display: block; margin-bottom: 5px; color: var(--muted); font-size: 9px; font-weight: 850; letter-spacing: .055em; text-transform: uppercase; }
    .detail-value { margin: 0; color: #344054; font-size: 11px; line-height: 1.55; white-space: pre-wrap; overflow-wrap: anywhere; }
    .description-box { margin-top: 11px; padding: 13px; border: 1px solid #e3e8eb; border-radius: 10px; background: #fff; }
    .source-link { margin-top: 12px; min-height: 36px; padding: 8px 11px; color: var(--brand-strong); }
    .footnote { margin-top: 18px; color: var(--muted); font-size: 10px; line-height: 1.6; }

    @media (max-width: 1000px) {
      .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .source-grid { grid-template-columns: 1fr; }
      .opportunity-toggle { grid-template-columns: 76px minmax(0, 1fr) 28px; }
      .deadline-block { grid-column: 2; grid-row: 2; text-align: left; }
      .chevron { grid-column: 3; grid-row: 1 / span 2; }
      .opportunity-details { padding-left: 18px; }
      .detail-grid { grid-template-columns: 1fr 1fr; }
    }

    @media (max-width: 700px) {
      .shell { width: min(100% - 20px, 1220px); padding-top: 14px; }
      .topbar { align-items: flex-start; }
      .logo { width: 48px; height: 48px; border-radius: 14px; }
      .system-chip { display: none; }
      .hero { grid-template-columns: 1fr; gap: 16px; padding: 22px 20px; }
      .refresh-button { justify-self: start; }
      .kpis { grid-template-columns: 1fr; }
      .toolbar { align-items: stretch; flex-direction: column; }
      .toolbar-left { align-items: stretch; flex-direction: column; }
      .source-select { width: 100%; }
      .opportunity { grid-template-columns: minmax(0, 1fr); }
      .opportunity-toggle { grid-template-columns: minmax(0, 1fr) 28px; gap: 8px 12px; padding-right: 18px; }
      .source-pill, .title-stack, .deadline-block { grid-column: 1; }
      .deadline-block { grid-row: auto; }
      .chevron { grid-column: 2; grid-row: 1 / span 3; }
      .row-action { padding: 0 18px 14px; }
      .row-source-link { width: 100%; min-height: 44px; }
      .detail-grid { grid-template-columns: 1fr; }
    }

    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="logo" aria-label="VakeHyvä">
          <svg viewBox="0 0 100 90" role="img" aria-label="VakeHyvän kuutiosydän">
            <defs>
              <linearGradient id="vake-red" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#ff2631"/>
                <stop offset="1" stop-color="#d8000c"/>
              </linearGradient>
              <filter id="cube-shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="1" stdDeviation="1.2" flood-color="#8c0008" flood-opacity=".22"/>
              </filter>
            </defs>
            <rect width="100" height="90" rx="18" fill="url(#vake-red)"/>
            <g fill="#fff" filter="url(#cube-shadow)">
              <rect x="28" y="10" width="10" height="10" rx="1.5"/><rect x="41" y="10" width="10" height="10" rx="1.5"/>
              <rect x="62" y="10" width="10" height="10" rx="1.5"/><rect x="75" y="10" width="10" height="10" rx="1.5"/>
              <rect x="15" y="23" width="10" height="10" rx="1.5"/><rect x="28" y="23" width="10" height="10" rx="1.5"/>
              <rect x="41" y="23" width="10" height="10" rx="1.5"/><rect x="54" y="23" width="10" height="10" rx="1.5"/>
              <rect x="67" y="23" width="10" height="10" rx="1.5"/><rect x="80" y="23" width="10" height="10" rx="1.5"/>
              <rect x="15" y="36" width="10" height="10" rx="1.5"/><rect x="28" y="36" width="10" height="10" rx="1.5"/>
              <rect x="41" y="36" width="10" height="10" rx="1.5"/><rect x="54" y="36" width="10" height="10" rx="1.5"/>
              <rect x="67" y="36" width="10" height="10" rx="1.5"/><rect x="80" y="36" width="10" height="10" rx="1.5"/>
              <rect x="28" y="49" width="10" height="10" rx="1.5"/><rect x="41" y="49" width="10" height="10" rx="1.5"/>
              <rect x="54" y="49" width="10" height="10" rx="1.5"/><rect x="67" y="49" width="10" height="10" rx="1.5"/>
              <rect x="41" y="62" width="10" height="10" rx="1.5"/><rect x="54" y="62" width="10" height="10" rx="1.5"/>
              <rect x="54" y="75" width="10" height="10" rx="1.5"/>
            </g>
          </svg>
        </div>
        <div>
          <strong>VakeVahti</strong>
          <span>VakeHyvän rahoitusmahdollisuuksien seuranta</span>
        </div>
      </div>
      <div class="system-chip">Tallennettu tilannekuva</div>
    </header>

    <section class="hero" aria-labelledby="page-title">
      <div>
        <p class="eyebrow">Rahoitushakujen tilannekuva</p>
        <h1 id="page-title"><span class="vakehyva">VakeHyvälle</span> sopivat rahoitushaut</h1>
        <p>
          VakeVahti kokoaa rahoitushaut yhteen ja näyttää, miksi kukin mahdollisuus on arvioitu
          VakeHyvälle relevantiksi. Näkymä perustuu viimeisimpään onnistuneesti tallennettuun
          tilannekuvaan, eikä sivun avaaminen käynnistä uusia verkkohakuja.
        </p>
      </div>
      <button id="refresh-button" class="refresh-button" type="button">Päivitä näkymä</button>
    </section>

    <div id="status-banner" class="status-banner" role="alert">
      <span class="status-dot" aria-hidden="true"></span>
      <span id="status-message"></span>
    </div>

    <section class="kpis" aria-label="Tilannekuvan tunnusluvut">
      <button id="kpi-current" class="kpi kpi-blue" type="button">
        <span class="kpi-top"><span class="kpi-label">VakeHyvälle sopivat haut</span><span class="kpi-icon">↗</span></span>
        <strong class="kpi-value" id="total-calls">–</strong>
        <span class="kpi-detail">Kaikkien seurattujen lähteiden nykyiset relevantit haut</span>
        <span class="kpi-action">Näytä kaikki haut →</span>
      </button>
      <button id="kpi-healthy" class="kpi kpi-green" type="button">
        <span class="kpi-top"><span class="kpi-label">Toimivat lähteet</span><span class="kpi-icon">✓</span></span>
        <strong class="kpi-value" id="healthy-sources">–</strong>
        <span class="kpi-detail" id="healthy-detail">Lähdetilaa ladataan</span>
        <span class="kpi-action">Näytä lähteet →</span>
      </button>
      <button id="kpi-attention" class="kpi kpi-amber" type="button">
        <span class="kpi-top"><span class="kpi-label">Huomiota vaativat</span><span class="kpi-icon">!</span></span>
        <strong class="kpi-value" id="attention-sources">–</strong>
        <span class="kpi-detail">Epäonnistuneet, käynnissä olevat tai vielä ajamattomat lähteet</span>
        <span class="kpi-action">Tarkista tila →</span>
      </button>
      <button id="kpi-latest" class="kpi kpi-purple" type="button">
        <span class="kpi-top"><span class="kpi-label">Viimeisin onnistunut lähdeajo</span><span class="kpi-icon">◷</span></span>
        <strong class="kpi-value" id="latest-success">–</strong>
        <span class="kpi-detail" id="latest-success-detail">Ei vielä tietoa</span>
        <span class="kpi-action">Näytä viimeisin lähde →</span>
      </button>
    </section>

    <section id="sources-section" class="section" aria-labelledby="sources-heading">
      <div class="section-head">
        <div>
          <span class="section-kicker">Seurannan tila</span>
          <h2 id="sources-heading">Rahoituslähteet</h2>
          <p>Klikkaa lähdekorttia rajataksesi näkymän. Avaa lähde -painike vie alkuperäiselle julkiselle rahoitussivulle.</p>
        </div>
      </div>
      <div id="source-grid" class="source-grid" aria-live="polite">
        <div class="loading-state">Ladataan lähteiden tilaa…</div>
      </div>
    </section>

    <section id="calls-section" class="section" aria-labelledby="calls-heading">
      <div class="section-head">
        <div>
          <span class="section-kicker">VakeHyvä-relevanssi</span>
          <h2 id="calls-heading">VakeHyvälle tunnistetut rahoitusmahdollisuudet</h2>
          <p>Jokaisen haun alla näkyy suoraan tallennettu perustelu sille, miksi haku on arvioitu VakeHyvälle relevantiksi.</p>
        </div>
      </div>

      <div class="toolbar">
        <div class="toolbar-left">
          <label for="source-filter">Rajaa lähteen mukaan</label>
          <select id="source-filter" class="source-select">
            <option value="">Kaikki lähteet</option>
          </select>
        </div>
        <span id="list-count" class="list-count">Ladataan…</span>
      </div>

      <div class="opportunity-panel">
        <div id="opportunity-list" class="opportunity-list" aria-live="polite">
          <div class="loading-state">Ladataan VakeHyvälle sopivia rahoitushakuja…</div>
        </div>
      </div>

      <p class="footnote">
        Lähteen tila kertoo viimeisimmän tallennetun ajon onnistumisesta. VakeVahti ei tässä vaiheessa
        päättele mielivaltaista vanhentumisrajaa; viimeisimmän onnistuneen ajon aika näytetään erikseen.
      </p>
    </section>
  </main>

  <script>
    const state = { health: [], calls: [], details: new Map(), source: "", latestSource: null };

    const SOURCE_META = {
      STM: { name: "STM", home: "https://stm.fi/vuoden-2026-valtionavustushaut" },
      SITRA: { name: "Sitra", home: "https://asiointi.sitra.fi/" },
      ACADEMY: { name: "Suomen Akatemia", home: "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/" },
    };

    const elements = {
      refreshButton: document.getElementById("refresh-button"),
      statusBanner: document.getElementById("status-banner"),
      statusMessage: document.getElementById("status-message"),
      totalCalls: document.getElementById("total-calls"),
      healthySources: document.getElementById("healthy-sources"),
      healthyDetail: document.getElementById("healthy-detail"),
      attentionSources: document.getElementById("attention-sources"),
      latestSuccess: document.getElementById("latest-success"),
      latestSuccessDetail: document.getElementById("latest-success-detail"),
      sourceGrid: document.getElementById("source-grid"),
      sourceFilter: document.getElementById("source-filter"),
      listCount: document.getElementById("list-count"),
      opportunityList: document.getElementById("opportunity-list"),
      sourcesSection: document.getElementById("sources-section"),
      callsSection: document.getElementById("calls-section"),
      kpiCurrent: document.getElementById("kpi-current"),
      kpiHealthy: document.getElementById("kpi-healthy"),
      kpiAttention: document.getElementById("kpi-attention"),
      kpiLatest: document.getElementById("kpi-latest"),
    };

    function clear(node) {
      while (node.firstChild) node.removeChild(node.firstChild);
    }

    function text(tag, value, className) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      node.textContent = value;
      return node;
    }

    function sourceMeta(code) {
      return SOURCE_META[code] || { name: code, home: null };
    }

    function showError(message) {
      elements.statusMessage.textContent = message;
      elements.statusBanner.classList.add("visible");
    }

    function clearError() {
      elements.statusMessage.textContent = "";
      elements.statusBanner.classList.remove("visible");
    }

    function formatDateTime(value) {
      if (!value) return "Ei tietoa";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "Ei tietoa";
      return new Intl.DateTimeFormat("fi-FI", { dateStyle: "short", timeStyle: "short" }).format(date);
    }

    function formatDeadline(value) {
      if (!value) return { label: "Ei ilmoitettu", className: "" };
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return { label: "Ei ilmoitettu", className: "" };
      const days = Math.ceil((date.getTime() - Date.now()) / 86400000);
      const label = new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium", timeStyle: "short" }).format(date);
      if (days < 0) return { label, className: "deadline-past" };
      if (days <= 7) return { label, className: "deadline-soon" };
      return { label, className: "" };
    }

    function healthLabel(value) {
      const labels = { HEALTHY: "Toimii", FAILING: "Virhe", RUNNING: "Käynnissä", NEVER_SCANNED: "Ei vielä ajoa" };
      return labels[value] || value || "Ei tietoa";
    }

    function scanStatusLabel(value) {
      const labels = {
        SUCCEEDED: "Onnistunut",
        FAILED: "Epäonnistunut",
        RUNNING: "Käynnissä",
        CANCELLED: "Keskeytetty",
      };
      return labels[value] || value || "Ei tietoa";
    }

    function relevanceLabel(value) {
      const labels = { RELEVANT: "Relevantti", NOT_RELEVANT: "Ei relevantti", REVIEW: "Tarkistettava" };
      return labels[value] || value || "Ei tietoa";
    }

    function relevanceReason(call) {
      const reason = String(call.relevance_reason || "").trim();
      if (reason) return reason;
      return "VakeVahti on luokitellut haun VakeHyvälle relevantiksi tallennettujen tietojen perusteella.";
    }

    function addFact(container, label, value) {
      const row = document.createElement("div");
      row.className = "fact";
      row.append(text("span", label));
      row.append(text("strong", value));
      container.append(row);
    }

    function flashCards(predicate) {
      document.querySelectorAll(".source-card").forEach((card) => {
        card.classList.remove("flash");
        if (predicate(card)) {
          void card.offsetWidth;
          card.classList.add("flash");
        }
      });
    }

    async function applySourceFilter(sourceCode, scroll = true) {
      state.source = sourceCode;
      elements.sourceFilter.value = sourceCode;
      state.calls = [];
      state.details.clear();
      elements.opportunityList.replaceChildren(text("div", "Ladataan…", "loading-state"));
      try {
        await fetchCalls();
        clearError();
        if (scroll) elements.callsSection.scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (error) {
        showError("Rahoitushakuja ei saatu ladattua valitulle lähteelle.");
      }
    }

    function renderHealth() {
      clear(elements.sourceGrid);
      const totalCurrent = state.health.reduce((sum, item) => sum + Number(item.current_call_count || 0), 0);
      elements.totalCalls.textContent = String(totalCurrent);

      if (!state.health.length) {
        elements.sourceGrid.append(text("div", "Yhtään määritettyä lähdettä ei löytynyt.", "empty-state"));
        elements.healthySources.textContent = "0";
        elements.attentionSources.textContent = "0";
        elements.healthyDetail.textContent = "0 määritettyä lähdettä";
        state.latestSource = null;
        return;
      }

      const healthy = state.health.filter((item) => item.health === "HEALTHY").length;
      const attention = state.health.length - healthy;
      elements.healthySources.textContent = String(healthy);
      elements.attentionSources.textContent = String(attention);
      elements.healthyDetail.textContent = `${healthy}/${state.health.length} lähdettä toimii`;

      const successful = state.health
        .filter((item) => item.last_successful_scan_at)
        .map((item) => ({ item, date: new Date(item.last_successful_scan_at) }))
        .filter(({ date }) => !Number.isNaN(date.getTime()))
        .sort((a, b) => b.date.getTime() - a.date.getTime());

      if (successful.length) {
        const latest = successful[0];
        state.latestSource = latest.item.source_code;
        elements.latestSuccess.textContent = new Intl.DateTimeFormat("fi-FI", { hour: "2-digit", minute: "2-digit" }).format(latest.date);
        elements.latestSuccessDetail.textContent = `${sourceMeta(latest.item.source_code).name} · ${new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium" }).format(latest.date)}`;
      } else {
        state.latestSource = null;
        elements.latestSuccess.textContent = "–";
        elements.latestSuccessDetail.textContent = "Ei onnistuneita ajoja";
      }

      const existingOptions = new Set(Array.from(elements.sourceFilter.options).map((option) => option.value));

      for (const item of state.health) {
        const meta = sourceMeta(item.source_code);
        if (!existingOptions.has(item.source_code)) {
          const option = document.createElement("option");
          option.value = item.source_code;
          option.textContent = meta.name;
          elements.sourceFilter.append(option);
        }

        const card = document.createElement("article");
        card.className = "source-card";
        card.dataset.source = item.source_code;
        card.dataset.health = item.health;

        const main = document.createElement("button");
        main.type = "button";
        main.className = "source-card-main";
        main.setAttribute("aria-label", `Näytä lähteen ${meta.name} nykyiset rahoitushaut`);
        main.addEventListener("click", () => applySourceFilter(item.source_code));

        const head = document.createElement("div");
        head.className = "source-card-head";
        head.append(text("div", meta.name, "source-name"));
        const badge = text("span", healthLabel(item.health), "health-badge");
        badge.classList.add(`health-${String(item.health).toLowerCase()}`);
        head.append(badge);
        main.append(head);

        const count = document.createElement("div");
        count.className = "source-count";
        count.append(document.createTextNode(String(item.current_call_count)));
        count.append(text("span", "VakeHyvälle sopivaa hakua"));
        main.append(count);

        const facts = document.createElement("div");
        facts.className = "fact-list";
        addFact(facts, "Viimeisin onnistunut ajo", formatDateTime(item.last_successful_scan_at));
        addFact(facts, "Viimeisen ajon tila", scanStatusLabel(item.latest_scan_status));
        addFact(facts, "Uusia / muuttuneita", `${item.latest_new_count ?? "–"} / ${item.latest_changed_count ?? "–"}`);
        if (item.latest_error_type) addFact(facts, "Virheluokka", item.latest_error_type);
        main.append(facts);
        card.append(main);

        const footer = document.createElement("div");
        footer.className = "source-card-footer";
        footer.append(text("span", "Näytä tämän lähteen haut →", "source-filter-hint"));

        if (meta.home) {
          const sourceHome = document.createElement("a");
          sourceHome.className = "source-home-link";
          sourceHome.href = meta.home;
          sourceHome.target = "_blank";
          sourceHome.rel = "noopener noreferrer";
          sourceHome.textContent = "Avaa lähde ↗";
          footer.append(sourceHome);
        }

        card.append(footer);
        elements.sourceGrid.append(card);
      }
    }

    function detailBox(label, value) {
      const box = document.createElement("div");
      box.className = "detail-box";
      box.append(text("span", label, "detail-label"));
      box.append(text("p", value, "detail-value"));
      return box;
    }

    function renderDetail(container, detail) {
      clear(container);

      const fit = document.createElement("div");
      fit.className = "fit-box";
      fit.append(text("span", "Miksi tämä sopii VakeHyvälle", "detail-label"));
      fit.append(text("p", relevanceReason(detail), "detail-value"));
      container.append(fit);

      const grid = document.createElement("div");
      grid.className = "detail-grid";
      grid.append(detailBox("Haku avautuu", formatDateTime(detail.application_opens_at)));
      grid.append(detailBox("Ensimmäinen havainto", formatDateTime(detail.first_seen_at)));
      grid.append(detailBox("Viimeisin havainto", formatDateTime(detail.last_seen_at)));
      grid.append(detailBox("Relevanssi", relevanceLabel(detail.relevance_status)));
      grid.append(detailBox("Versio", String(detail.current_version)));
      grid.append(detailBox("Lähde", sourceMeta(detail.source_code).name));
      container.append(grid);

      const description = document.createElement("div");
      description.className = "description-box";
      description.append(text("span", "Rahoitushaun kuvaus", "detail-label"));
      description.append(text("p", detail.description_text || "Lähteestä ei ole tallennettu kuvaustekstiä.", "detail-value"));
      container.append(description);

      const link = document.createElement("a");
      link.className = "source-link";
      link.href = detail.source_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Avaa alkuperäinen rahoitushaku ↗";
      container.append(link);
    }

    async function loadDetail(id, container) {
      if (state.details.has(id)) {
        renderDetail(container, state.details.get(id));
        return;
      }

      clear(container);
      container.append(text("div", "Ladataan tarkempia tietoja…", "details-loading"));
      try {
        const response = await fetch(`/api/funding-calls/${encodeURIComponent(id)}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const detail = await response.json();
        state.details.set(id, detail);
        renderDetail(container, detail);
      } catch (error) {
        clear(container);
        container.append(text("div", "Tarkempia tietoja ei saatu ladattua.", "details-loading"));
      }
    }

    function renderCalls() {
      clear(elements.opportunityList);
      elements.listCount.textContent = state.source
        ? `${state.calls.length} hakua · ${sourceMeta(state.source).name}`
        : `${state.calls.length} hakua · kaikki lähteet`;

      if (!state.calls.length) {
        elements.opportunityList.append(text("div", "Valitussa viimeisimmässä onnistuneessa tilannekuvassa ei ole nykyisiä VakeHyvälle sopivia rahoitushakuja.", "empty-state"));
        return;
      }

      state.calls.forEach((call) => {
        const row = document.createElement("article");
        row.className = "opportunity";
        row.dataset.source = call.source_code;

        const detailsId = `funding-call-${call.id}-details`;
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "opportunity-toggle";
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-controls", detailsId);
        toggle.append(text("span", sourceMeta(call.source_code).name, "source-pill"));

        const titleStack = document.createElement("span");
        titleStack.className = "title-stack";
        titleStack.append(text("span", call.title, "opportunity-title"));
        const why = document.createElement("span");
        why.className = "why-line";
        const whyLabel = document.createElement("strong");
        whyLabel.textContent = "Miksi VakeHyvälle: ";
        why.append(whyLabel, document.createTextNode(relevanceReason(call)));
        titleStack.append(why);
        toggle.append(titleStack);

        const deadline = formatDeadline(call.application_deadline_at);
        const deadlineBlock = document.createElement("span");
        deadlineBlock.className = "deadline-block";
        if (deadline.className) deadlineBlock.classList.add(deadline.className);
        deadlineBlock.append(text("span", "Hakuaika päättyy", "deadline-label"));
        deadlineBlock.append(text("span", deadline.label, "deadline-value"));
        toggle.append(deadlineBlock);
        toggle.append(text("span", "›", "chevron"));

        const rowAction = document.createElement("div");
        rowAction.className = "row-action";
        const directLink = document.createElement("a");
        directLink.className = "row-source-link";
        directLink.href = call.source_url;
        directLink.target = "_blank";
        directLink.rel = "noopener noreferrer";
        directLink.textContent = "Avaa lähde ↗";
        directLink.setAttribute("aria-label", `Avaa alkuperäinen lähde: ${call.title}`);
        rowAction.append(directLink);

        const details = document.createElement("div");
        details.id = detailsId;
        details.className = "opportunity-details";
        details.hidden = true;

        toggle.addEventListener("click", async () => {
          const expanded = toggle.getAttribute("aria-expanded") === "true";
          toggle.setAttribute("aria-expanded", String(!expanded));
          details.hidden = expanded;
          if (!expanded) await loadDetail(call.id, details);
        });

        row.append(toggle, rowAction, details);
        elements.opportunityList.append(row);
      });
    }

    async function fetchHealth() {
      const response = await fetch("/api/sources/health");
      if (!response.ok) throw new Error(`Health HTTP ${response.status}`);
      const payload = await response.json();
      state.health = payload.sources || [];
      renderHealth();
    }

    async function fetchCalls() {
      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (state.source) params.set("source_code", state.source);
      const response = await fetch(`/api/funding-calls?${params.toString()}`);
      if (!response.ok) throw new Error(`Funding HTTP ${response.status}`);
      const payload = await response.json();
      state.calls = payload.items || [];
      renderCalls();
    }

    async function loadDashboard() {
      clearError();
      elements.refreshButton.disabled = true;
      try {
        await Promise.all([fetchHealth(), fetchCalls()]);
      } catch (error) {
        showError("Tilannekuvaa ei saatu ladattua. Tarkista VakeVahdin API:n ja tietolähteen tila.");
      } finally {
        elements.refreshButton.disabled = false;
      }
    }

    elements.sourceFilter.addEventListener("change", (event) => applySourceFilter(event.target.value, false));
    elements.refreshButton.addEventListener("click", () => { state.details.clear(); loadDashboard(); });
    elements.kpiCurrent.addEventListener("click", () => applySourceFilter(""));
    elements.kpiHealthy.addEventListener("click", () => {
      elements.sourcesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      flashCards((card) => card.dataset.health === "HEALTHY");
    });
    elements.kpiAttention.addEventListener("click", () => {
      elements.sourcesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      flashCards((card) => card.dataset.health !== "HEALTHY");
    });
    elements.kpiLatest.addEventListener("click", () => {
      elements.sourcesSection.scrollIntoView({ behavior: "smooth", block: "start" });
      if (state.latestSource) flashCards((card) => card.dataset.source === state.latestSource);
    });

    loadDashboard();
  </script>
</body>
</html>
"""
