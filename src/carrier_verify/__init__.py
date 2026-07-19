"""carrier-verify: open-source carrier identity verification against public FMCSA data."""

from .client import QCMobileClient, QCMobileError
from .models import AuthorityRecord, CarrierSnapshot
from .redflags import Finding, Severity, evaluate, name_similarity, verdict
from .validate import ValidationResult, is_valid_usdot, normalize_docket, normalize_usdot

__version__ = "0.1.0"

__all__ = [
    "QCMobileClient",
    "QCMobileError",
    "CarrierSnapshot",
    "AuthorityRecord",
    "Finding",
    "Severity",
    "evaluate",
    "verdict",
    "name_similarity",
    "ValidationResult",
    "is_valid_usdot",
    "normalize_usdot",
    "normalize_docket",
]
