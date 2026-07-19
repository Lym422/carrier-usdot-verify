"""carrier-verify CLI.

Examples:
    carrier-verify check 1234567
    carrier-verify check "USDOT 1234567" --expect-name "ACME TRUCKING LLC" --json
    carrier-verify search "acme trucking"
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .client import QCMobileClient, QCMobileError
from .models import CarrierSnapshot
from .redflags import Severity, evaluate, verdict
from .validate import normalize_usdot

_COLORS = {"RED": "\033[91m", "YELLOW": "\033[93m", "INFO": "\033[92m"}
_RESET = "\033[0m"
_VERDICT_LABEL = {"RED": "RED — HOLD", "YELLOW": "YELLOW — VERIFY", "INFO": "GREEN — PASS"}


def _paint(sev: str, text: str, color: bool) -> str:
    return f"{_COLORS.get(sev, '')}{text}{_RESET}" if color else text


def cmd_check(args: argparse.Namespace) -> int:
    norm = normalize_usdot(args.dot_number)
    if not norm.ok:
        print(f"error: invalid USDOT input: {norm.reason}", file=sys.stderr)
        return 2
    client = QCMobileClient(webkey=args.webkey)
    carrier = client.get_carrier(norm.value)
    authority = None
    try:
        authority = client.get_authority(norm.value)
    except QCMobileError:
        pass  # authority endpoint is best-effort

    findings = evaluate(carrier, authority=authority, expected_name=args.expect_name)
    overall = verdict(findings)

    if args.json:
        out = {
            "usdot": norm.value,
            "carrier": {k: v for k, v in asdict(carrier).items() if k != "raw"},
            "verdict": overall.value,
            "findings": [asdict(f) for f in findings],
        }
        print(json.dumps(out, indent=2, default=str))
    else:
        color = sys.stdout.isatty() and not args.no_color
        print(f"USDOT {norm.value}: {carrier.display_name}")
        loc = ", ".join(x for x in (carrier.phy_city, carrier.phy_state) if x)
        if loc:
            print(f"  Location: {loc}")
        if carrier.total_power_units is not None:
            print(f"  Power units: {carrier.total_power_units}  Drivers: {carrier.total_drivers}")
        print(f"  Verdict: {_paint(overall.value, _VERDICT_LABEL[overall.value], color)}")
        for f in findings:
            print(f"    [{_paint(f.severity.value, f.severity.value, color)}] {f.code}: {f.message}")
        if not findings:
            print("    no findings")
    return 1 if overall == Severity.RED else 0


def cmd_search(args: argparse.Namespace) -> int:
    client = QCMobileClient(webkey=args.webkey)
    results = client.search_by_name(args.name, size=args.size)
    for item in results:
        snap = CarrierSnapshot.from_api(item)
        loc = ", ".join(x for x in (snap.phy_city, snap.phy_state) if x)
        print(f"{snap.dot_number}\t{snap.display_name}\t{loc}")
    if not results:
        print("no results", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="carrier-verify",
        description="Verify a motor carrier against public FMCSA data and flag pickup fraud risks.",
    )
    p.add_argument("--webkey", help="FMCSA QCMobile web key (or set FMCSA_WEBKEY)")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="check a carrier by USDOT number")
    c.add_argument("dot_number", help="USDOT number (raw OCR strings accepted)")
    c.add_argument("--expect-name", help="carrier name from the rate confirmation / booking")
    c.add_argument("--json", action="store_true", help="machine-readable output")
    c.add_argument("--no-color", action="store_true")
    c.set_defaults(func=cmd_check)

    s = sub.add_parser("search", help="search carriers by name")
    s.add_argument("name")
    s.add_argument("--size", type=int, default=20)
    s.set_defaults(func=cmd_search)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except QCMobileError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
