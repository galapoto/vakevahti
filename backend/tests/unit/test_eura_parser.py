from datetime import date

import pytest

from app.domain.funding_call import RelevanceStatus
from app.scanners.common import SourceStructureError
from app.scanners.eura import (
    EuraListingStructureError,
    parse_eura_detail_html,
    parse_eura_listing_html,
)


def test_listing_discovers_uuid_notice_links() -> None:
    html = """
    <main>
      <a href="/hakuilmoitukset/hakuilmoitus/74ae7bec-e403-4bdc-ba0b-db96a29a3673">First</a>
      <a href="/hakuilmoitukset/hakuilmoitus/6fe99522-a31c-4b16-9ceb-6bdaa865f7e1/">Second</a>
    </main>
    """

    urls = parse_eura_listing_html(html, "https://eura2021.fi/hakuilmoitukset")

    assert urls == [
        "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/74ae7bec-e403-4bdc-ba0b-db96a29a3673",
        "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/6fe99522-a31c-4b16-9ceb-6bdaa865f7e1",
    ]


def test_target_region_plus_wellbeing_evidence_is_relevant() -> None:
    html = """
    <main>
      <h1>Etelä-Suomen hyvinvoinnin kehittämishaku</h1>
      <p>Hakuilmoituksen tunnus TEST-1</p>
      <div>Alkaa</div>
      <div>1.9.2026</div>
      <div>Päättyy</div>
      <div>30.9.2026</div>
      <div>Haun kohdealue</div>
      <div>Etelä-Suomi</div>
      <div>Maakunnat</div>
      <div>Uusimaa</div>
      <div>Hankehaun kuvaus</div>
      <p>Hakijoina voivat toimia hyvinvointialueet ja muut julkiset toimijat.</p>
      <div>Hakeminen</div>
      <p>Hakemus jätetään EURA-järjestelmässä.</p>
      <div>Lisätiedot</div>
      <p>Yhteistyö on sallittua.</p>
      <div>Lainsäädäntö</div>
    </main>
    """

    call = parse_eura_detail_html(
        html,
        "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/74ae7bec-e403-4bdc-ba0b-db96a29a3673",
    )

    assert call.source_code == "EURA"
    assert call.relevance_status is RelevanceStatus.RELEVANT
    assert "hyvinvointialue" in call.relevance_reason.casefold()
    assert call.application_opens_on == date(2026, 9, 1)
    assert call.application_opens_at is None
    assert call.application_deadline_on == date(2026, 9, 30)
    assert call.application_deadline_at is None
    assert any(item.section == "Haun kohdealue" for item in call.evidence)
    assert any(item.section == "Hakuaika" for item in call.evidence)


def test_out_of_scope_region_is_not_relevant_even_if_text_mentions_public_actor() -> None:
    html = """
    <main>
      <h1>Pohjois-Suomen haku</h1>
      <div>Haun kohdealue</div>
      <div>Pohjois-Suomi</div>
      <div>Maakunnat</div>
      <div>Lappi</div>
      <div>Hankehaun kuvaus</div>
      <p>Julkinen organisaatio voi osallistua.</p>
      <div>Hakeminen</div>
    </main>
    """

    call = parse_eura_detail_html(
        html,
        "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/74ae7bec-e403-4bdc-ba0b-db96a29a3673",
    )

    assert call.relevance_status is RelevanceStatus.NOT_RELEVANT


def test_target_region_without_explicit_eligibility_is_needs_review() -> None:
    html = """
    <main>
      <h1>Valtakunnallinen kehittämishaku</h1>
      <div>Haun kohdealue</div>
      <div>Valtakunnallinen</div>
      <div>Maakunnat</div>
      <div>-</div>
      <div>Hankehaun kuvaus</div>
      <p>Hankkeilla kehitetään uusia palvelumalleja.</p>
      <div>Lisätiedot</div>
      <p>Katso tarkemmat ehdot hakuilmoituksesta.</p>
      <div>Lainsäädäntö</div>
    </main>
    """

    call = parse_eura_detail_html(
        html,
        "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/74ae7bec-e403-4bdc-ba0b-db96a29a3673",
    )

    assert call.relevance_status is RelevanceStatus.NEEDS_REVIEW


def test_missing_region_block_is_structure_error() -> None:
    html = """
    <main>
      <h1>Broken notice</h1>
      <div>Hankehaun kuvaus</div><p>Text</p>
    </main>
    """

    with pytest.raises(SourceStructureError, match="Haun kohdealue"):
        parse_eura_detail_html(
            html,
            "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/74ae7bec-e403-4bdc-ba0b-db96a29a3673",
        )


def test_listing_structure_change_fails_loudly() -> None:
    with pytest.raises(EuraListingStructureError):
        parse_eura_listing_html(
            "<main><h1>Hakuilmoitukset</h1></main>",
            "https://eura2021.fi/hakuilmoitukset",
        )
