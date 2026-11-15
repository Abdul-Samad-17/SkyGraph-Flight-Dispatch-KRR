# Phase 3 evaluation

## KG-grounded copilot vs independently computed gold answers

| ID | Question | Result | Detail |
|---|---|---|---|
| E1 | Find an alternate route from Karachi to Dubai for a B737-800 | PASS | gold KHI-UET-DXB 1861.0 km | copilot KHI-UET-DXB 1861.0 km |
| E2 | Route from Islamabad to Dubai for an A380 | PASS | gold ISB-DXB 1925.5 km | copilot ISB-DXB 1925.5 km |
| E3 | Find a route from Islamabad to London for an A320 | PASS | gold ISB-KBL-TAS-IST-LHR 6941.7 km | copilot ISB-KBL-TAS-IST-LHR 6941.7 km |
| E4 | Find an alternate route avoiding the thunderstorm from Lahore to Doha for a B787-9 | PASS | gold LHE-FSD-DXB-DOH 2364.6 km | copilot LHE-FSD-DXB-DOH 2364.6 km |
| E5 | Route from Islamabad to Chitral for an ATR72 | PASS | gold: no feasible route; copilot status=no_route |
| E6 | Route from Islamabad to Gilgit for an ATR72 | PASS | gold: no feasible route; copilot status=no_route |
| E7 | Find a route from Chitral to Dubai for an A320 | PASS | gold: no feasible route; copilot status=no_route |
| E8 | Route from Karachi to Islamabad for an ATR72 | PASS | gold KHI-ISB 1108.9 km | copilot KHI-ISB 1108.9 km |
| E9 | Diversion candidates for scenario S1 | PASS | gold 18 candidates | copilot 18 |
| E10 | Diversion candidates for scenario S6 | PASS | gold 0 candidates | copilot 0 |
| E11 | Which airports can handle an A380? | PASS | gold 33 airports | copilot 33 |
| E12 | Why can't an A380 fly Karachi to Dubai direct? | PASS | gold blocked by ['RZ-ALPHA'] |

**12 / 12 correct.** Gold answers come from `src/independent_check.py` (recomputed from the CSV data with no RDF/rules involved).  

## Re-validation guard against hallucinated answers (simulated LLM outputs)

| Case | Should be accepted | Validator accepted | Correct | Problems found |
|---|---|---|---|---|
| faithful KG answer | True | True | yes | - |
| direct blocked leg presented as valid | False | False | yes | route KHI-DXB is not feasible: KHI-DXB: blocked by active zone 'Restricted Zone Alpha (fictional naval exercise area)' |
| airport not in evidence | False | False | yes | airport LHR is not supported by the retrieved evidence |
| invented distance | False | False | yes | number 5000 is not in the retrieved evidence |
| route that does not exist | False | False | yes | airport BKK is not supported by the retrieved evidence; route KHI-BKK-DXB is not feasible: no route segment KHI-BKK exists; BKK-DXB: blocked by active zone 'Restricted Zone Alpha (fictional naval exercise area)' |
| leg beyond ATR range presented as valid | False | False | yes | route ISB-DXB is not feasible: ISB-DXB: distance 1926 km exceeds the ATR 72-600 maximum range of 1528 km |

## LLM-only baseline (no KG)

Not run in this build (no API key available offline). Run `ANTHROPIC_API_KEY=... python src/evaluate.py` to fill this section: each LLM-only route is audited against the KG and violations are listed.