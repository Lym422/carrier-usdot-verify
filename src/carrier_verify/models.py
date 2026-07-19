"""Typed views over FMCSA QCMobile API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _to_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


@dataclass
class CarrierSnapshot:
    """Normalized subset of the QCMobile `carrier` object used for verification."""

    dot_number: Optional[int] = None
    legal_name: Optional[str] = None
    dba_name: Optional[str] = None
    allowed_to_operate: Optional[str] = None  # 'Y' / 'N'
    status_code: Optional[str] = None  # 'A' active
    oos_date: Optional[str] = None
    safety_rating: Optional[str] = None  # 'S'atisfactory / 'C'onditional / 'U'nsatisfactory
    safety_rating_date: Optional[str] = None
    mcs150_outdated: Optional[str] = None  # 'Y' / 'N'
    total_power_units: Optional[int] = None
    total_drivers: Optional[int] = None
    phy_city: Optional[str] = None
    phy_state: Optional[str] = None
    phy_street: Optional[str] = None
    driver_insp: Optional[int] = None
    driver_oos_insp: Optional[int] = None
    vehicle_insp: Optional[int] = None
    vehicle_oos_insp: Optional[int] = None
    crash_total: Optional[int] = None
    fatal_crash: Optional[int] = None
    inj_crash: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "CarrierSnapshot":
        """Build from a QCMobile response.

        Accepts either the full response ({"content": {"carrier": {...}}}) or
        the bare carrier object.
        """
        content = payload.get("content", payload)
        carrier = content.get("carrier", content) if isinstance(content, dict) else {}
        return cls(
            dot_number=_to_int(carrier.get("dotNumber")),
            legal_name=carrier.get("legalName"),
            dba_name=carrier.get("dbaName"),
            allowed_to_operate=carrier.get("allowedToOperate"),
            status_code=carrier.get("statusCode"),
            oos_date=carrier.get("oosDate"),
            safety_rating=carrier.get("safetyRating"),
            safety_rating_date=carrier.get("safetyRatingDate"),
            mcs150_outdated=carrier.get("mcs150Outdated"),
            total_power_units=_to_int(carrier.get("totalPowerUnits")),
            total_drivers=_to_int(carrier.get("totalDrivers")),
            phy_city=carrier.get("phyCity"),
            phy_state=carrier.get("phyState"),
            phy_street=carrier.get("phyStreet"),
            driver_insp=_to_int(carrier.get("driverInsp")),
            driver_oos_insp=_to_int(carrier.get("driverOosInsp")),
            vehicle_insp=_to_int(carrier.get("vehicleInsp")),
            vehicle_oos_insp=_to_int(carrier.get("vehicleOosInsp")),
            crash_total=_to_int(carrier.get("crashTotal")),
            fatal_crash=_to_int(carrier.get("fatalCrash")),
            inj_crash=_to_int(carrier.get("injCrash")),
            raw=carrier if isinstance(carrier, dict) else {},
        )

    @property
    def display_name(self) -> str:
        return self.dba_name or self.legal_name or "(unknown)"

    def oos_rate(self, kind: str) -> Optional[float]:
        """Out-of-service rate for 'driver' or 'vehicle' inspections, if computable."""
        insp = self.driver_insp if kind == "driver" else self.vehicle_insp
        oos = self.driver_oos_insp if kind == "driver" else self.vehicle_oos_insp
        if insp and oos is not None and insp > 0:
            return oos / insp
        return None


@dataclass
class AuthorityRecord:
    """Subset of the /authority endpoint response."""

    common_authority: Optional[str] = None  # 'A'ctive / 'I'nactive / 'N'one
    contract_authority: Optional[str] = None
    broker_authority: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "AuthorityRecord":
        content = payload.get("content", payload)
        items: List[Dict[str, Any]] = []
        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            items = [content]
        auth: Dict[str, Any] = {}
        for item in items:
            a = item.get("carrierAuthority", item) if isinstance(item, dict) else {}
            if a:
                auth = a
                break
        return cls(
            common_authority=auth.get("commonAuthorityStatus"),
            contract_authority=auth.get("contractAuthorityStatus"),
            broker_authority=auth.get("brokerAuthorityStatus"),
            raw=auth,
        )
