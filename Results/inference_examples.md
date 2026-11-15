# Inference examples (explicit facts -> rule -> inferred fact)

Every example is generated from the live graph; the derivation records come from `src/reasoner.py`.

## Inference 1 - airport suitability (R0 + R1)

**Explicit facts**
- ISB has runway 15/33 with fd:runwayLengthM 3658
- A380-800 has fd:minRunwayM 3000
- KDU (Skardu) has a single 2743 m runway

**Rule**: R0: longestRunwayM = MAX(runway lengths).  R1: longestRunwayM >= minRunwayM => isSuitableFor.

**Inferred fact**: `fdr:airport-OPIS fd:isSuitableFor fdr:aircraft-A380-800` is inferred (3658 >= 3000); `fdr:airport-OPSD fd:isSuitableFor fdr:aircraft-A380-800` is NOT inferred (2743 < 3000), while it is inferred for the A320 (2743 >= 2100).

## Inference 2 - blocked segment (R2)

**Explicit facts**
- KHI-DXB fd:crossesZone RZ-ALPHA
- RZ-ALPHA is a fd:RestrictedZone and fd:isActive true

**Rule**: R2: crosses an ACTIVE restricted zone => fd:blockedBy and rdf:type fd:BlockedSegment.

**Inferred fact**: `(fdr:segment-OPKC-OMDB, fd:blockedBy, fdr:zone-RZ-ALPHA)` and `fdr:segment-OPKC-OMDB a fd:BlockedSegment`. Consequence: R4 does NOT derive isFeasibleFor for any aircraft on this segment.

## Inference 3 - subclass reasoning feeds a rule (rdfs:subClassOf + R2)

**Explicit facts**
- PZ-BRAVO is typed only as fd:ProhibitedZone
- fd:ProhibitedZone rdfs:subClassOf fd:RestrictedZone
- ISB-LHR fd:crossesZone PZ-BRAVO

**Rule**: OWL/RDFS: ProhibitedZone is a RestrictedZone, so R2 applies to it.

**Inferred fact**: `fdr:zone-PZ-BRAVO a fd:RestrictedZone` is inferred, hence `fdr:segment-OPIS-EGLL fd:blockedBy fdr:zone-PZ-BRAVO`.

## Inference 4 - diversion candidate (R5)

**Explicit facts**
- Scenario S1: A380-800, fd:remainingRangeKm 1500
- PositionDistance S1-OPKC: 318.8 km to KHI
- KHI is operational and suitable for the A380 (R1)

**Rule**: R5: suitable and operational airport with distance <= remaining range => fd:hasDiversionCandidate.

**Inferred fact**: `fdr:scenario-S1 fd:hasDiversionCandidate fdr:airport-OPKC`. Scenario S6 (300 km remaining, KHI 344 km away) yields no candidates.

## Inference 5 - range violation (R3)

**Explicit facts**
- ISB-DXB fd:distanceKm 1925.5
- ATR72-600 fd:rangeKm 1528

**Rule**: R3: distance > rangeKm => fd:exceedsRangeOf.

**Inferred fact**: `fdr:segment-OPIS-OMDB fd:exceedsRangeOf fdr:aircraft-ATR72-600` (and therefore it is not feasible for the ATR, but is for the A380).

## Inference 6 - hub airport (R6)

**Explicit facts**
- DXB is the endpoint of 34 route segments (COUNT DISTINCT)

**Rule**: R6: >= 14 incident segments => rdf:type fd:HubAirport (a subclass of fd:Airport).

**Inferred fact**: `fdr:airport-OMDB a fd:HubAirport`; hubs: DEL, DOH, DXB, ISB, KHI.

## Inference 7 - OWL characteristics (symmetric, inverse, domain/range)

**Explicit facts**
- ISB fd:connectedTo KHI (stored once)
- ISB fd:hasRunway runway-OPIS-15-33
- ISB fd:locatedIn country-PK

**Rule**: owl:SymmetricProperty (connectedTo), owl:inverseOf (hasRunway/runwayOf), rdfs:range (locatedIn -> Country).

**Inferred fact**: `KHI fd:connectedTo ISB`, `runway-OPIS-15-33 fd:runwayOf ISB`, `fdr:country-PK a fd:Country`.

## Negative checks (rules must NOT fire)

- RZ-CHARLIE (restricted but inactive) is crossed by 17 segment(s) (e.g. AUH-LHR, BAH-KWI, BOM-LHR) but none is blocked by it: confirmed.
- AZ-DELTA (advisory only) is crossed by 7 segment(s) but blocks none: confirmed.
- Hazard TURB-3 (severity 2 < 3) affects 3 segment(s) but blocks none: confirmed.
- Hazard ASH-4 (inactive (expired)) affects 3 segment(s) but blocks none: confirmed.
- GIL (Gilgit) is closed (fd:isOperational false): every segment touching it is infeasible and it is never a diversion candidate.