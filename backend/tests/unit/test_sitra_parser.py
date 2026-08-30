from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.scanners.common import SourceStructureError
from app.scanners.sitra import parse_sitra_html

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


def test_sitra_structure_change_fails_loudly() -> None:
    with pytest.raises(SourceStructureError, match="Sitra"):
        parse_sitra_html("<main><h2>No funding cards here</h2></main>", SOURCE_URL)
