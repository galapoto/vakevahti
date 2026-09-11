"""Deterministic Finnish applicant-eligibility phrase matching.

Funding sources inflect the same public-entity concepts in many grammatical cases
(e.g. ``julkisoikeudelliset yhteisöt`` and ``julkisoikeudelliselle yhteisölle``).
Keep morphology and local eligibility context handling in one small, auditable helper
instead of duplicating literal phrase lists across source adapters.
"""

import re

from app.scanners.common import normalize_text

_PUBLIC_ENTITY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bhyvinvointialue\w*\b", re.IGNORECASE),
    re.compile(r"\bjulkisoikeudellis\w*\s+yhteis\w*\b", re.IGNORECASE),
    re.compile(r"\bjulkis\w*\s+toimij\w*\b", re.IGNORECASE),
    re.compile(r"\bjulkis\w*\s+organisaatio\w*\b", re.IGNORECASE),
    re.compile(r"\bjulkisyhteis\w*\b", re.IGNORECASE),
    re.compile(r"\bjulkis\w*\s+oikeushenkil\w*\b", re.IGNORECASE),
)

# These markers mean the clause is describing applicant eligibility rather than merely
# mentioning a wellbeing/public entity as a partner, target group or beneficiary.
_APPLICANT_CONTEXT = re.compile(
    r"\b(?:hakij\w*|hakea|hakevat|haettav\w*|hakukelpoi\w*|"
    r"myönt\w*|myonn\w*|rahoitusta\s+voivat|tukea\s+voidaan)\b",
    re.IGNORECASE,
)

# A positive-looking entity term inside an explicit exclusion must never become proof
# of eligibility. Matching is clause-local so a later positive clause can still win.
_NEGATIVE_ELIGIBILITY = re.compile(
    r"\b(?:ei|eivät|eivat)\b.{0,80}\b(?:"
    r"hakea|hakevat|hakij\w*|hakukelpoi\w*|myönt\w*|myonn\w*|saada|saavat"
    r")\b|\b(?:ei|eivät|eivat)\s+voida\s+myönt\w*\b",
    re.IGNORECASE,
)

_CLAUSE_SPLIT = re.compile(r"(?:[.;!?]\s+|\s*[;]\s*|\s*,?\s+mutta\s+)", re.IGNORECASE)


def _clauses(text: str) -> tuple[str, ...]:
    normalized = normalize_text(text)
    if not normalized:
        return ()
    return tuple(part for raw in _CLAUSE_SPLIT.split(normalized) if (part := raw.strip()))


def match_public_entity_eligibility_term(
    text: str,
    *,
    require_applicant_context: bool = True,
) -> str | None:
    """Return the first affirmative VakeHyvä-relevant applicant phrase in ``text``.

    The matcher is intentionally narrow: it recognizes only stakeholder-approved
    public-entity concepts while allowing normal Finnish suffix inflection. A match in
    an explicit negative clause is ignored. By default applicant language must occur
    in the same clause so incidental mentions such as collaboration with a wellbeing
    area do not become false evidence of eligibility. A source adapter may disable
    that extra guard only when the source section itself is an explicit applicant list.
    """

    for clause in _clauses(text):
        if _NEGATIVE_ELIGIBILITY.search(clause):
            continue
        if require_applicant_context and _APPLICANT_CONTEXT.search(clause) is None:
            continue
        for pattern in _PUBLIC_ENTITY_PATTERNS:
            match = pattern.search(clause)
            if match is not None:
                return normalize_text(match.group(0))
    return None
