# carrier-verify

**Open-source carrier identity verification against public FMCSA data — a
first line of defense against deceptive pickups and freight fraud.**

Cargo theft and freight fraud cost the U.S. supply chain up to **$35 billion a
year**, and the fastest-growing attack is the *deceptive pickup*: a criminal
using a fake or stolen carrier identity walks into a facility and is handed a
loaded trailer. The FBI's [IC3 advisory](https://www.ic3.gov/PSA/2026/PSA260430)
recommends independently verifying every carrier before releasing a load —
this tool automates the public-data half of that verification in one command.

```text
$ carrier-verify check "USDOT 1234567" --expect-name "ACME TRUCKING LLC"
USDOT 1234567: ACME TRUCKING LLC
  Location: FONTANA, CA
  Power units: 42  Drivers: 55
  Verdict: GREEN — PASS
```

```text
$ carrier-verify check 7654321 --expect-name "Reliable Haulers"
USDOT 7654321: PF EXPRESS
  Verdict: RED — HOLD
    [RED] NOT_ALLOWED_TO_OPERATE: FMCSA lists this carrier as NOT allowed to operate.
    [RED] OOS_ORDER: Carrier has an out-of-service order dated 2026-02-01.
    [RED] NAME_MISMATCH: Booked carrier 'Reliable Haulers' does not match FMCSA
          record 'PF EXPRESS' (similarity 0.13). Possible deceptive pickup / identity misuse.
```

## What it does

- **Looks up any carrier** by USDOT number (or name / MC docket) via FMCSA's
  public [QCMobile API](https://mobile.fmcsa.dot.gov/QCDevsite/).
- **Runs a red-flag rules engine** informed by FBI IC3 guidance: revoked
  authority, out-of-service orders, safety ratings, stale MCS-150 filings,
  zero-truck "paper carriers," abnormal out-of-service inspection rates.
- **Matches identity against your booking**: pass `--expect-name` from the rate
  confirmation and get a RED alert when the truck's USDOT resolves to a
  different company — the classic deceptive-pickup signature.
- **Accepts raw OCR strings**: `"US DOT# I23456O"` is normalized (confusable
  characters corrected) before lookup, so it drops directly into camera/OCR
  pipelines reading numbers off cab doors at yard gates.
- **GREEN / YELLOW / RED verdicts** designed for gate workflows: RED is rare
  and actionable; ambiguity is YELLOW (a 15-second human check), never noise.

## Install

```bash
pip install carrier-verify        # once published; or:
pip install git+https://github.com/Lym422/carrier-usdot-verify
```

Get a **free** FMCSA web key at <https://mobile.fmcsa.dot.gov/QCDevsite/> and:

```bash
export FMCSA_WEBKEY=your_key_here
```

## Library use

```python
from carrier_verify import QCMobileClient, evaluate, verdict, normalize_usdot

dot = normalize_usdot("USDOT 1234567").value      # OCR-tolerant normalization
client = QCMobileClient()                          # reads FMCSA_WEBKEY
carrier = client.get_carrier(dot)
authority = client.get_authority(dot)

findings = evaluate(carrier, authority=authority, expected_name="ACME TRUCKING LLC")
print(verdict(findings))                           # Severity.RED / YELLOW / INFO
for f in findings:
    print(f.severity, f.code, f.message)
```

Exit codes: `0` pass/verify, `1` RED hold, `2` input or API error — usable
directly in gate automation scripts.

## Why this exists

Digital carrier vetting verifies paperwork. Roadside intelligence networks
verify that carriers exist somewhere. But at the one moment fraud can actually
be *stopped* — when a trailer is released at a gate — verification is still a
clipboard. This project is part of a broader effort to build an open,
vendor-neutral **physical verification layer for freight custody transfer**:
carrier identity (this tool), plus camera-based USDOT reading and multi-type
cargo-seal recognition (open benchmark and models — roadmap below).

See [docs/red_flags.md](docs/red_flags.md) for the full pickup-fraud checklist,
including the physical checks no API can automate.

## Roadmap

- [ ] SAFER company-snapshot fallback when QCMobile is unavailable
- [ ] Batch mode (`carrier-verify batch loads.csv`)
- [ ] FMCSA census-file offline mode (no API key required)
- [ ] Synthetic gate-imagery benchmark for USDOT OCR (separate repo)
- [ ] Multi-type cargo seal detection dataset & baseline models (separate repo)

## Data & disclaimers

All data comes from public FMCSA sources; accuracy and freshness are FMCSA's.
A GREEN verdict means *no public-data red flags*, *not* that a carrier is
legitimate — pair with physical checks (see checklist) and commercial vetting
where appropriate. Not legal advice; not affiliated with FMCSA or USDOT.

## License

Apache-2.0 — see [LICENSE](LICENSE).
