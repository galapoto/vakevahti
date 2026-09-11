from datetime import date

import pytest

from app.domain.funding_call import RelevanceStatus
from app.scanners.haeavustuksia import (
    HaeavustuksiaListingStructureError,
    parse_haeavustuksia_detail_html,
    parse_haeavustuksia_listing_html,
)


def test_listing_deduplicates_section_links_to_same_call_root() -> None:
    html = """
    <main>
      <a href="/fi/haku/va-stm-2026-4">Call</a>
      <a href="/fi/haku/va-stm-2026-4/hakuilmoitus/myontoperusteet">Criteria</a>
      <a href="/fi/haku/va-thl-2026-1">Second</a>
    </main>
    """

    urls = parse_haeavustuksia_listing_html(
        html,
        "https://www.haeavustuksia.fi/fi/?isAdditionalSearchOpen=true",
    )

    assert urls == [
        "https://www.haeavustuksia.fi/fi/haku/va-stm-2026-4",
        "https://www.haeavustuksia.fi/fi/haku/va-thl-2026-1",
    ]


def test_positive_public_entity_term_is_relevant_and_evidenced() -> None:
    html = """
    <main>
      <h1>Hyvinvoinnin kehittämisavustus</h1>
      <p>Hakuaika on alkanut 1.9.2026 klo 08.00 ja päättyy 30.9.2026 klo 16.15</p>
      <h2>Myöntöperusteet</h2>
      <h3>Kenelle/mille avustusta voidaan myöntää</h3>
      <p>
        Avustusta voidaan myöntää hyvinvointialueelle tai muulle
        julkisoikeudelliselle yhteisölle.
      </p>
      <h3>Mihin käyttötarkoituksiin avustusta voidaan myöntää</h3>
      <p>Kehittämiseen.</p>
    </main>
    """

    call = parse_haeavustuksia_detail_html(
        html,
        "https://www.haeavustuksia.fi/fi/haku/va-stm-2026-99",
    )

    assert call.source_code == "HAEAVUSTUKSIA"
    assert call.relevance_status is RelevanceStatus.RELEVANT
    assert "hyvinvointialue" in call.relevance_reason.casefold()
    assert call.application_opens_on == date(2026, 9, 1)
    assert call.application_opens_at is not None
    assert call.application_deadline_on == date(2026, 9, 30)
    assert call.application_deadline_at is not None
    assert any(
        item.section == "Kenelle/mille avustusta voidaan myöntää"
        for item in call.evidence
    )


def test_date_only_window_is_preserved_without_invented_time() -> None:
    html = """
    <main>
      <h1>Päivämäärätarkkuuden testihaku</h1>
      <p>Hakuaika alkaa 2.10.2026 ja päättyy 30.10.2026</p>
      <h2>Kenelle/mille avustusta voidaan myöntää</h2>
      <p>Avustusta voidaan myöntää julkiselle organisaatiolle.</p>
      <h2>Mihin avustusta voidaan käyttää</h2>
    </main>
    """

    call = parse_haeavustuksia_detail_html(
        html,
        "https://www.haeavustuksia.fi/fi/haku/va-test-2026-date",
    )

    assert call.application_opens_on == date(2026, 10, 2)
    assert call.application_opens_at is None
    assert call.application_deadline_on == date(2026, 10, 30)
    assert call.application_deadline_at is None


def test_explicit_only_rule_without_positive_term_is_not_relevant() -> None:
    html = """
    <main>
      <h1>Kuntien erityisavustus</h1>
      <h2>Kenelle/mille avustusta voidaan myöntää</h2>
      <p>Avustusta voivat hakea ainoastaan Manner-Suomen kunnat.</p>
      <h2>Mihin käyttötarkoituksiin avustusta voidaan myöntää</h2>
      <p>Kuntien toimintaan.</p>
    </main>
    """

    call = parse_haeavustuksia_detail_html(
        html,
        "https://www.haeavustuksia.fi/fi/haku/va-test-2026-1",
    )

    assert call.relevance_status is RelevanceStatus.NOT_RELEVANT


def test_ambiguous_eligibility_is_needs_review_not_silently_excluded() -> None:
    html = """
    <main>
      <h1>Monialainen kehittämisavustus</h1>
      <h2>Kenelle/mille avustusta voidaan myöntää</h2>
      <p>Hakijoiden tulee täyttää hakuilmoituksessa kuvatut yleiset ehdot.</p>
      <h2>Arviointiperusteet</h2>
      <p>Vaikuttavuus.</p>
    </main>
    """

    call = parse_haeavustuksia_detail_html(
        html,
        "https://www.haeavustuksia.fi/fi/haku/va-test-2026-2",
    )

    assert call.relevance_status is RelevanceStatus.NEEDS_REVIEW


def test_listing_structure_change_fails_loudly() -> None:
    with pytest.raises(HaeavustuksiaListingStructureError):
        parse_haeavustuksia_listing_html(
            "<main><h1>Haut</h1></main>",
            "https://www.haeavustuksia.fi/fi/",
        )
