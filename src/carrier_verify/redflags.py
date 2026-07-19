"""Red-flag rules engine for carrier verification at pickup.

Rules are informed by FBI IC3 guidance on cyber-enabled cargo theft
(https://www.ic3.gov/PSA/2026/PSA260430), FMCSA public data semantics, and
industry loss-prevention practice. Each rule yields a Finding with a severity:

- RED    -> hold the load; human decision required
- YELLOW -> verify before release (one extra check)
- INFO   -> contextual note, no action required

Design rule: RED must be rare and nearly always right. Ambiguity is YELLOW.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .models import AuthorityRecord, CarrierSnapshot

# National average out-of-service rates (FMCSA/CVSA commonly cited baselines).
# Sources vary by year; treat as tunable thresholds, not gospel.
NATIONAL_DRIVER_OOS_RATE = 0.059
NATIONAL_VEHICLE_OOS_RATE = 0.207
MIN_INSPECTIONS_FOR_RATE = 10


class Severity(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    INFO = "INFO"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str


def _norm_name(name: str) -> str:
    s = re.sub(r"[^A-Z0-9 ]", " ", name.upper())
    s = re.sub(
        r"\b(INC|LLC|LTD|CORP|CO|COMPANY|TRUCKING|TRANSPORT|TRANSPORTATION|"
        r"LOGISTICS|EXPRESS|CARRIER|CARRIERS|FREIGHT|LINES|GROUP)\b",
        " ",
        s,
    )
    return re.sub(r"\s+", " ", s).strip()


def name_similarity(a: str, b: str) -> float:
    """Similarity in [0,1] between two carrier names, ignoring entity suffixes."""
    na, nb = _norm_name(a), _norm_name(b)
    if not na or not nb:
        return 0.0
    if na == nb or na in nb or nb in na:
        return 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def evaluate(
    carrier: CarrierSnapshot,
    authority: Optional[AuthorityRecord] = None,
    expected_name: Optional[str] = None,
    name_match_threshold: float = 0.75,
) -> List[Finding]:
    """Evaluate a carrier snapshot against the rule set."""
    findings: List[Finding] = []

    # --- hard stops -------------------------------------------------------
    if carrier.allowed_to_operate == "N":
        findings.append(
            Finding(
                Severity.RED,
                "NOT_ALLOWED_TO_OPERATE",
                "FMCSA lists this carrier as NOT allowed to operate.",
            )
        )
    if carrier.oos_date:
        findings.append(
            Finding(
                Severity.RED,
                "OOS_ORDER",
                f"Carrier has an out-of-service order dated {carrier.oos_date}.",
            )
        )
    if carrier.status_code and carrier.status_code != "A":
        findings.append(
            Finding(
                Severity.RED,
                "STATUS_INACTIVE",
                f"Carrier record status is {carrier.status_code!r} (not active).",
            )
        )
    if carrier.safety_rating == "U":
        findings.append(
            Finding(
                Severity.RED,
                "UNSATISFACTORY_RATING",
                "Safety rating is Unsatisfactory.",
            )
        )
    if authority is not None and authority.common_authority in ("I", "N"):
        if authority.contract_authority not in ("A",):
            findings.append(
                Finding(
                    Severity.RED,
                    "NO_ACTIVE_AUTHORITY",
                    "No active common or contract operating authority on file.",
                )
            )

    # --- identity match (the gate use case) -------------------------------
    if expected_name:
        candidates = [n for n in (carrier.legal_name, carrier.dba_name) if n]
        best = max((name_similarity(expected_name, n) for n in candidates), default=0.0)
        if best < name_match_threshold:
            findings.append(
                Finding(
                    Severity.RED,
                    "NAME_MISMATCH",
                    f"Booked carrier {expected_name!r} does not match FMCSA record "
                    f"{carrier.display_name!r} (similarity {best:.2f}). "
                    "Possible deceptive pickup / identity misuse.",
                )
            )
        elif best < 0.95:
            findings.append(
                Finding(
                    Severity.INFO,
                    "NAME_PARTIAL_MATCH",
                    f"Name matches with similarity {best:.2f}; confirm docket/plate.",
                )
            )

    # --- soft signals -----------------------------------------------------
    if carrier.safety_rating == "C":
        findings.append(
            Finding(Severity.YELLOW, "CONDITIONAL_RATING", "Safety rating is Conditional.")
        )
    if carrier.mcs150_outdated == "Y":
        findings.append(
            Finding(
                Severity.YELLOW,
                "MCS150_OUTDATED",
                "MCS-150 registration data is outdated (stale filings correlate "
                "with shell/reincarnated carriers).",
            )
        )
    if carrier.total_power_units is not None and carrier.total_power_units == 0:
        findings.append(
            Finding(
                Severity.YELLOW,
                "ZERO_POWER_UNITS",
                "Carrier reports zero power units — verify it actually operates trucks.",
            )
        )

    for kind, baseline in (("driver", NATIONAL_DRIVER_OOS_RATE), ("vehicle", NATIONAL_VEHICLE_OOS_RATE)):
        insp = carrier.driver_insp if kind == "driver" else carrier.vehicle_insp
        rate = carrier.oos_rate(kind)
        if rate is not None and insp and insp >= MIN_INSPECTIONS_FOR_RATE and rate > 2 * baseline:
            findings.append(
                Finding(
                    Severity.YELLOW,
                    f"HIGH_{kind.upper()}_OOS_RATE",
                    f"{kind.capitalize()} out-of-service rate {rate:.0%} exceeds 2x "
                    f"national average ({baseline:.0%}) over {insp} inspections.",
                )
            )

    if carrier.fatal_crash:
        findings.append(
            Finding(
                Severity.INFO,
                "FATAL_CRASH_HISTORY",
                f"{carrier.fatal_crash} fatal crash(es) in FMCSA's recent window.",
            )
        )

    return findings


def verdict(findings: List[Finding]) -> Severity:
    """Overall verdict: worst severity present, defaulting to green-equivalent INFO."""
    sevs = {f.severity for f in findings}
    if Severity.RED in sevs:
        return Severity.RED
    if Severity.YELLOW in sevs:
        return Severity.YELLOW
    return Severity.INFO
