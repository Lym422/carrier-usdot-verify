import json
from pathlib import Path

import pytest

from carrier_verify.models import CarrierSnapshot
from carrier_verify.redflags import Severity, evaluate, name_similarity, verdict

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> CarrierSnapshot:
    return CarrierSnapshot.from_api(json.loads((FIXTURES / name).read_text()))


def codes(findings):
    return {f.code for f in findings}


def test_clean_carrier_passes():
    carrier = load("carrier_clean.json")
    findings = evaluate(carrier, expected_name="Acme Trucking, LLC")
    assert verdict(findings) == Severity.INFO
    assert "NAME_MISMATCH" not in codes(findings)


def test_risky_carrier_hard_stops():
    carrier = load("carrier_risky.json")
    findings = evaluate(carrier)
    assert verdict(findings) == Severity.RED
    got = codes(findings)
    assert "NOT_ALLOWED_TO_OPERATE" in got
    assert "OOS_ORDER" in got
    assert "MCS150_OUTDATED" in got
    assert "ZERO_POWER_UNITS" in got
    assert "HIGH_DRIVER_OOS_RATE" in got
    assert "HIGH_VEHICLE_OOS_RATE" in got


def test_name_mismatch_is_red():
    carrier = load("carrier_clean.json")
    findings = evaluate(carrier, expected_name="Totally Different Logistics")
    assert verdict(findings) == Severity.RED
    assert "NAME_MISMATCH" in codes(findings)


def test_dba_name_matches():
    carrier = load("carrier_risky.json")
    findings = evaluate(carrier, expected_name="PF Express")
    assert "NAME_MISMATCH" not in codes(findings)


def test_name_similarity_ignores_suffixes():
    assert name_similarity("ACME TRUCKING LLC", "Acme Trucking, Inc.") == pytest.approx(1.0)
    assert name_similarity("ACME TRUCKING", "ZENITH HAULERS") < 0.5


def test_conditional_rating_is_yellow_not_red():
    carrier = load("carrier_clean.json")
    carrier.safety_rating = "C"
    findings = evaluate(carrier)
    assert verdict(findings) == Severity.YELLOW


def test_oos_rate_needs_minimum_inspections():
    carrier = load("carrier_clean.json")
    carrier.driver_insp, carrier.driver_oos_insp = 3, 3  # 100% but tiny sample
    findings = evaluate(carrier)
    assert "HIGH_DRIVER_OOS_RATE" not in codes(findings)
