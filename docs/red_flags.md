# Pickup Fraud Red Flags — Field Checklist

A practical checklist for verifying a carrier at the moment of pickup, compiled
from FBI IC3 guidance on cyber-enabled cargo theft ([PSA 2026-04-30](https://www.ic3.gov/PSA/2026/PSA260430)),
FMCSA public data semantics, and industry loss-prevention practice. The
`carrier-verify` rules engine automates the *data* checks; the *physical*
checks are listed here because software alone cannot do them.

## Automated by this tool (FMCSA data)

| Check | Severity | Why |
|---|---|---|
| Carrier not allowed to operate | RED | Operating authority revoked or denied |
| Out-of-service order on file | RED | Legally barred from operating |
| Record status not active | RED | Possible reincarnated/abandoned identity |
| Unsatisfactory safety rating | RED | Unfit carrier; also a chameleon-carrier signal |
| No active common/contract authority | RED | "Carrier" may be an unlicensed shell |
| Booked name ≠ FMCSA record name | RED | Classic deceptive-pickup signature |
| Conditional safety rating | YELLOW | Elevated risk; verify insurance |
| MCS-150 outdated | YELLOW | Stale filings correlate with shells |
| Zero power units | YELLOW | Paper carrier with no trucks |
| OOS rates > 2x national average | YELLOW | Poorly maintained or ghost fleet |

## Physical checks at the gate (not automatable by API)

1. **USDOT on the truck matches the dispatch.** Read the number off the cab door
   (not from paperwork the driver hands you) and run it through this tool.
2. **Magnetic or freshly applied USDOT signage** over different paint — treat as
   suspicious; photograph it.
3. **Driver identity:** photograph driver, CDL, tractor plate, and trailer number
   at pickup (explicitly recommended by FBI IC3).
4. **Late equipment substitutions** ("our truck broke down, this one's picking up
   instead") — re-verify the new unit from scratch.
5. **Driver phone dispatch mismatch:** driver doesn't know the broker/load details
   they should know.
6. **Seal discipline:** record seal type and number at the gate; verify against
   the BOL on outbound.

## Booking-time checks (upstream of the gate)

- Email domain of the "carrier" is a free provider or a look-alike domain
  (`acmetruckingg.com`) — IC3-flagged pattern.
- Authority granted or reinstated very recently, followed by immediate bidding
  on high-value loads.
- Contact phone/address changed on FMCSA record days before the load.
- Rate significantly below market (bait pricing to win the load).
