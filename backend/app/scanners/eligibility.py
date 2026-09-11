"""Deterministic Finnish applicant-eligibility phrase matching.

Funding sources inflect the same public-entity concepts in many grammatical cases
(e.g. ``julkisoikeudelliset yhteisöt`` and ``julkisoikeudelliselle yhteisölle``).
Keep that morphology handling in one small, auditable helper instead of duplicating
literal phrase lists across source adapters.
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


def match_public_entity_eligibility_term(text: str) -> str | None:
    """Return the first VakeHyvä-relevant public-entity phrase found in ``text``.

    The matcher is intentionally narrow: it recognizes only stakeholder-approved
    public-entity concepts, while allowing normal Finnish suffix inflection. It does
    not infer eligibility from generic words such as ``yhteisö`` or ``organisaatio``.
    Source adapters remain responsible for supplying text from an eligibility-bearing
    section before calling this helper.
    """

    normalized = normalize_text(text)
    for pattern in _PUBLIC_ENTITY_PATTERNS:
        match = pattern.search(normalized)
        if match is not None:
            return normalize_text(match.group(0))
    return None
