from pathlib import Path

import pytest

from app.domain.funding_call import RelevanceStatus
from app.scanners.stm import SourceStructureError, parse_stm_html

FIXTURE = Path(__file__).parents[1] / "fixtures" / "stm" / "listing.html"
SOURCE_URL = "https://stm.fi/vuoden-2026-valtionavustushaut"


def test_parse_stm_html_discovers_funding_calls() -> None:
    calls = parse_stm_html(FIXTURE.read_text(encoding="utf-8"), SOURCE_URL)

    assert len(calls) == 2
    assert calls[0].title.startswith("Valtionavustus kliinisten")
    assert calls[0].source_code == "STM"
    assert calls[0].relevance_status is RelevanceStatus.RELEVANT
    assert calls[0].evidence[0].text == calls[0].title


def test_parse_stm_html_captures_accordion_details() -> None:
    calls = parse_stm_html(FIXTURE.read_text(encoding="utf-8"), SOURCE_URL)

    assert calls[0].description_text == "Avustuksen hakuaika on 29.6.2026 - 31.8.2026."
    assert calls[0].evidence[1].section == "STM funding call details"
    assert calls[1].description_text == (
        "Haettavana on valtionavustusta yksilöllisen lääketieteen edistämiseen."
    )


def test_external_key_is_stable_for_same_title() -> None:
    html = FIXTURE.read_text(encoding="utf-8")

    first = parse_stm_html(html, SOURCE_URL)
    second = parse_stm_html(html, SOURCE_URL)

    assert first[0].external_key == second[0].external_key


def test_duplicate_heading_is_not_ingested_twice() -> None:
    html = """
    <main>
      <button>Valtionavustus erittäin tärkeään julkisen sektorin kehittämishankkeeseen</button>
      <button>Valtionavustus erittäin tärkeään julkisen sektorin kehittämishankkeeseen</button>
    </main>
    """

    calls = parse_stm_html(html, SOURCE_URL)

    assert len(calls) == 1


def test_missing_expected_structure_fails_loudly() -> None:
    html = "<main><h1>Vuoden 2026 valtionavustushaut</h1><p>Ei painikkeita.</p></main>"

    with pytest.raises(SourceStructureError):
        parse_stm_html(html, SOURCE_URL)
