from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.scanners.common import SourceStructureError
from app.scanners.sitra import (
    _parse_sitra_with_render_fallback,
    parse_sitra_html,
)

SOURCE_URL = "https://asiointi.sitra.fi/"


def test_parse_sitra_html_returns_only_open_calls() -> None:
    html = """
    <main>
      <section>
        <h3><a href="/rahoitushaku/open-call">Open public-sector call</a></h3>
        <p>Haku käynnissä 22.6.2026 - 15.9.2026 09.00</p>
      </section>
      <section>
        <h3><a href="/rahoitushaku/closed-call">Closed call</a></h3>
        <p>Haku sulkeutunut Päättyi 11.8.2026 09.00</p>
      </section>
    </main>
    """

    calls = parse_sitra_html(html, SOURCE_URL)

    assert len(calls) == 1
    assert calls[0].source_code == "SITRA"
    assert calls[0].title == "Open public-sector call"
    assert str(calls[0].source_url) == "https://asiointi.sitra.fi/rahoitushaku/open-call"
    assert calls[0].application_deadline_at == datetime(
        2026,
        9,
        15,
        9,
        0,
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )


def test_sitra_external_key_is_stable_for_canonical_link() -> None:
    html = """
    <main>
      <section>
        <h3><a href="/rahoitushaku/stable-call#details">Stable title</a></h3>
        <p>Haku käynnissä 1.6.2026 - 28.8.2026 09.00</p>
      </section>
    </main>
    """

    first = parse_sitra_html(html, SOURCE_URL)[0]
    second = parse_sitra_html(html.replace("Stable title", "Renamed title"), SOURCE_URL)[0]

    assert first.external_key == second.external_key


def test_sitra_accepts_semantic_heading_levels_without_css_assumptions() -> None:
    html = """
    <main>
      <article>
        <h5><a href="/funding/open-call">Open semantic card</a></h5>
        <p>Haku käynnissä 22.6.2026 - 15.9.2026 09.00</p>
      </article>
    </main>
    """

    calls = parse_sitra_html(html, SOURCE_URL)

    assert [call.title for call in calls] == ["Open semantic card"]


@pytest.mark.asyncio
async def test_sitra_power_pages_shell_uses_rendered_html_fallback() -> None:
    shell_html = """
    <html>
      <body>
        <main><h1>Rahoituksen Asiointipalvelu</h1></main>
        <script>window.portalBootstrap = true;</script>
      </body>
    </html>
    """
    rendered_html = """
    <main>
      <section>
        <h3><a href="/funding/open-call">Rendered open call</a></h3>
        <p>Haku käynnissä 22.6.2026 - 15.9.2026 09.00</p>
      </section>
    </main>
    """
    render_calls = 0

    async def render_html() -> str:
        nonlocal render_calls
        render_calls += 1
        return rendered_html

    calls = await _parse_sitra_with_render_fallback(
        shell_html,
        SOURCE_URL,
        timezone="Europe/Helsinki",
        render_html=render_html,
    )

    assert render_calls == 1
    assert [call.title for call in calls] == ["Rendered open call"]


@pytest.mark.asyncio
async def test_sitra_visible_status_structure_change_does_not_hide_behind_browser() -> None:
    html = """
    <main>
      <div>Haku käynnissä 22.6.2026 - 15.9.2026 09.00</div>
    </main>
    """
    render_calls = 0

    async def render_html() -> str:
        nonlocal render_calls
        render_calls += 1
        return "<main></main>"

    with pytest.raises(SourceStructureError, match="Sitra"):
        await _parse_sitra_with_render_fallback(
            html,
            SOURCE_URL,
            timezone="Europe/Helsinki",
            render_html=render_html,
        )

    assert render_calls == 0


def test_sitra_structure_change_fails_loudly() -> None:
    with pytest.raises(SourceStructureError, match="Sitra"):
        parse_sitra_html("<main><h2>No funding cards here</h2></main>", SOURCE_URL)
