from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.scanners.academy import parse_academy_html
from app.scanners.common import SourceStructureError

SOURCE_URL = "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/"


def test_parse_academy_html_stops_before_preparation_section() -> None:
    html = """
    <main>
      <h2>Avoimet ja tulossa olevat haut</h2>
      <h2>Tutkimusryhmille</h2>
      <h3><a href="/call/eurohpc">2026 EuroHPC-vastinraha, kutsuhaku</a></h3>
      <p>Haku alkaa 11.2.2026</p>
      <p>Haku päättyy 14.10.2026 klo 23.59 Suomen aikaa</p>

      <h3><a href="/call/upcoming">Hyvinvointialueiden T&amp;K-haku</a></h3>
      <p>Haku alkaa 21.10.2026</p>
      <p>Haku päättyy 18.11.2026 klo 23.59 Suomen aikaa</p>

      <h2>Valmistelussa olevat haut</h2>
      <h3>Should not be ingested</h3>
      <p>Haku alkaa 1.1.2027</p>
      <p>Haku päättyy 2.1.2027 klo 12.00</p>
    </main>
    """

    calls = parse_academy_html(html, SOURCE_URL)

    assert [call.title for call in calls] == [
        "2026 EuroHPC-vastinraha, kutsuhaku",
        "Hyvinvointialueiden T&K-haku",
    ]
    assert calls[0].application_deadline_at == datetime(
        2026,
        10,
        14,
        23,
        59,
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )
    assert calls[1].source_code == "ACADEMY"


def test_academy_bare_deadline_date_is_not_given_invented_time() -> None:
    html = """
    <main>
      <h2>Avoimet ja tulossa olevat haut</h2>
      <h3>International call</h3>
      <p>Haku alkaa tammikuu 2026</p>
      <p>Haku päättyy 3.11.2026 (varsinaiset hakemukset)</p>
      <h2>Valmistelussa olevat haut</h2>
    </main>
    """

    call = parse_academy_html(html, SOURCE_URL)[0]

    assert call.application_deadline_at is None
    assert "3.11.2026" in (call.description_text or "")


def test_academy_missing_open_section_fails_loudly() -> None:
    with pytest.raises(SourceStructureError, match="Akatemia"):
        parse_academy_html("<main><h2>Valmistelussa olevat haut</h2></main>", SOURCE_URL)
