from datetime import date

from app.domain.funding_call import RelevanceStatus
from app.scanners.eligibility import match_public_entity_eligibility_term
from app.scanners.eura import parse_eura_detail_html
from app.scanners.haeavustuksia import parse_haeavustuksia_detail_html


def test_public_entity_matcher_handles_finnish_inflection_without_generic_overmatch() -> None:
    assert (
        match_public_entity_eligibility_term(
            "Rahoitusta voivat hakea julkisoikeudelliset yhteisöt ja järjestöt."
        )
        == "julkisoikeudelliset yhteisöt"
    )
    assert (
        match_public_entity_eligibility_term(
            "Tukea voidaan myöntää julkisoikeudelliselle yhteisölle."
        )
        == "julkisoikeudelliselle yhteisölle"
    )
    assert (
        match_public_entity_eligibility_term(
            "Hakijoina voivat olla kunnat ja muut julkiset organisaatiot."
        )
        == "julkiset organisaatiot"
    )
    assert match_public_entity_eligibility_term("Oikeuskelpoiset yhteisöt voivat hakea.") is None


def test_public_entity_matcher_rejects_negated_and_incidental_mentions() -> None:
    assert (
        match_public_entity_eligibility_term(
            "Avustusta ei voida myöntää hyvinvointialueille eikä kunnille."
        )
        is None
    )
    assert (
        match_public_entity_eligibility_term(
            "Hanke toteutetaan yhteistyössä hyvinvointialueiden kanssa."
        )
        is None
    )
    assert (
        match_public_entity_eligibility_term(
            "Avustusta ei voida myöntää yksityishenkilöille, mutta "
            "hyvinvointialueet voivat hakea avustusta."
        )
        == "hyvinvointialueet"
    )


def test_eura_current_2026_etela_suomi_shape_with_inflected_public_entity_is_relevant() -> None:
    # Regression shape observed from a live EURA 2021 Etelä-Suomi notice in September 2026.
    html = """
    <main>
      <h1>EAKR alueellisten ympäristöhankkeiden haku Etelä-Karjalassa</h1>
      <div>Alkaa</div>
      <div>1.4.2026</div>
      <div>Päättyy</div>
      <div>3.6.2026</div>
      <div>Haun kohdealue</div>
      <div>Etelä-Suomi</div>
      <div>Maakunnat</div>
      <div>Etelä-Karjala</div>
      <div>Hankehaun kuvaus:</div>
      <p>
        Tukea voidaan myöntää julkisoikeudelliselle yhteisölle ja
        yksityisoikeudelliselle oikeushenkilölle, kuten kunnille ja korkeakouluille.
      </p>
      <div>Hakeminen</div>
    </main>
    """

    call = parse_eura_detail_html(
        html,
        "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/54727044-9922-4095-af2d-66c54adf8f63",
    )

    assert call.relevance_status is RelevanceStatus.RELEVANT
    assert "julkisoikeudelliselle yhteisölle" in call.relevance_reason
    assert call.application_opens_on == date(2026, 4, 1)
    assert call.application_deadline_on == date(2026, 6, 3)


def test_eura_incidental_wellbeing_mention_is_not_applicant_evidence() -> None:
    html = """
    <main>
      <h1>Etelä-Suomen yhteistyöhanke</h1>
      <div>Haun kohdealue</div>
      <div>Etelä-Suomi</div>
      <div>Maakunnat</div>
      <div>Uusimaa</div>
      <div>Hankehaun kuvaus</div>
      <p>Hanke toteutetaan yhteistyössä hyvinvointialueiden kanssa.</p>
      <div>Hakeminen</div>
    </main>
    """

    call = parse_eura_detail_html(
        html,
        "https://eura2021.fi/hakuilmoitukset/hakuilmoitus/11111111-2222-3333-4444-555555555555",
    )

    assert call.relevance_status is RelevanceStatus.NEEDS_REVIEW


def test_haeavustuksia_current_2026_generic_legal_entity_shape_stays_reviewable() -> None:
    # Regression shape observed from a live Haeavustuksia.fi Myöntöperusteet page.
    html = """
    <main>
      <h1>Hankeavustukset yleisiin taidetta ja kulttuuria edistäviin hankkeisiin 2026</h1>
      <p>Hakuaika alkoi 12.3.2026 klo 10.00 ja päättyi 9.4.2026 klo 16.15</p>
      <h2>Myöntöperusteet</h2>
      <h3>Kenelle/mille avustusta voidaan myöntää</h3>
      <p>
        Avustusta voivat hakea oikeuskelpoiset yhteisöt ja säätiöt.
        Avustusta ei voida myöntää yksityishenkilöille tai työryhmille.
      </p>
      <h3>Mihin käyttötarkoituksiin avustusta voidaan myöntää</h3>
    </main>
    """

    call = parse_haeavustuksia_detail_html(
        html,
        "https://www.haeavustuksia.fi/fi/haku/va-okm-2026-15",
    )

    assert call.relevance_status is RelevanceStatus.NEEDS_REVIEW
    assert call.application_opens_on == date(2026, 3, 12)
    assert call.application_deadline_on == date(2026, 4, 9)


def test_haeavustuksia_inflected_public_entity_wording_is_relevant() -> None:
    html = """
    <main>
      <h1>Julkisen toiminnan kehittämisavustus</h1>
      <h2>Kenelle/mille avustusta voidaan myöntää</h2>
      <p>Avustusta voidaan myöntää julkisoikeudelliselle yhteisölle.</p>
      <h2>Mihin käyttötarkoituksiin avustusta voidaan myöntää</h2>
    </main>
    """

    call = parse_haeavustuksia_detail_html(
        html,
        "https://www.haeavustuksia.fi/fi/haku/va-test-2026-inflection",
    )

    assert call.relevance_status is RelevanceStatus.RELEVANT
    assert "julkisoikeudelliselle yhteisölle" in call.relevance_reason


def test_haeavustuksia_negated_wellbeing_term_does_not_false_positive() -> None:
    html = """
    <main>
      <h1>Rajattu avustus</h1>
      <h2>Kenelle/mille avustusta voidaan myöntää</h2>
      <p>Avustusta ei voida myöntää hyvinvointialueille.</p>
      <h2>Mihin käyttötarkoituksiin avustusta voidaan myöntää</h2>
    </main>
    """

    call = parse_haeavustuksia_detail_html(
        html,
        "https://www.haeavustuksia.fi/fi/haku/va-test-2026-negated",
    )

    assert call.relevance_status is not RelevanceStatus.RELEVANT
