"""Validation and normalization of carrier identifiers (USDOT, MC/docket numbers).

Designed with OCR pipelines in mind: `normalize_usdot` accepts raw strings as
they come off a truck-door read (e.g. "USDOT 1234567", "US DOT# I23456O") and
applies conservative confusable-character correction before validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Characters OCR engines commonly confuse for digits on painted/vinyl truck lettering.
_CONFUSABLE_TO_DIGIT = str.maketrans(
    {
        "O": "0",
        "o": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "l": "1",
        "|": "1",
        "Z": "2",
        "S": "5",
        "s": "5",
        "B": "8",
        "G": "6",
    }
)

_USDOT_PREFIX_RE = re.compile(r"(?:USDOT|US\s*DOT|DOT)\s*[#:.-]?\s*", re.IGNORECASE)
_DOCKET_RE = re.compile(r"^(MC|FF|MX)\s*[#:.-]?\s*0*(\d{1,8})$", re.IGNORECASE)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    value: Optional[str] = None
    reason: Optional[str] = None


def is_valid_usdot(number: str) -> bool:
    """A USDOT number is 1-8 digits with no leading zero."""
    return bool(re.fullmatch(r"[1-9]\d{0,7}", number))


def normalize_usdot(raw: str, correct_confusables: bool = True) -> ValidationResult:
    """Normalize a raw (possibly OCR-derived) string to a USDOT number.

    >>> normalize_usdot("USDOT 1234567").value
    '1234567'
    >>> normalize_usdot("US DOT# I23456O").value
    '1234560'
    """
    if raw is None:
        return ValidationResult(False, reason="empty input")
    s = _USDOT_PREFIX_RE.sub("", raw.strip())
    s = re.sub(r"[\s,._-]", "", s)
    if correct_confusables:
        s = s.translate(_CONFUSABLE_TO_DIGIT)
    if not s:
        return ValidationResult(False, reason="empty after normalization")
    if not s.isdigit():
        return ValidationResult(False, reason=f"non-digit characters remain: {s!r}")
    s = s.lstrip("0") or "0"
    if not is_valid_usdot(s):
        return ValidationResult(False, reason=f"invalid USDOT format: {s!r}")
    return ValidationResult(True, value=s)


def normalize_docket(raw: str) -> ValidationResult:
    """Normalize an MC/FF/MX docket number, e.g. 'MC-123456' -> 'MC123456'."""
    if raw is None:
        return ValidationResult(False, reason="empty input")
    m = _DOCKET_RE.match(raw.strip())
    if not m:
        return ValidationResult(False, reason=f"unrecognized docket format: {raw!r}")
    prefix, digits = m.group(1).upper(), m.group(2)
    return ValidationResult(True, value=f"{prefix}{digits}")
