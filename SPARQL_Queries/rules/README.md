# Rules (SPARQL Update)

`run_all_rules.ru` implements rules R0-R6 as SPARQL `INSERT ... WHERE` operations. Numeric comparisons
(runway >= minimum, distance > range) are not expressible in OWL 2 RL, so they are encoded here.
The same logic is implemented in `src/reasoner.py`, whose output is checked against an independent
recomputation (`src/independent_check.py`) in `src/tests.py`.

| Rule | Derives | Condition |
|------|---------|-----------|
| R0 | `fd:longestRunwayM` | MAX of the airport's runway lengths |
| R1 | `fd:isSuitableFor` | longest runway >= `fd:minRunwayM` |
| R2 | `fd:blockedBy`, `a fd:BlockedSegment` | crosses an ACTIVE restricted zone, or an ACTIVE hazard with severity >= 3 |
| R3 | `fd:exceedsRangeOf` | segment distance > `fd:rangeKm` |
| R4 | `fd:isFeasibleFor` | not blocked, within range, both endpoints operational and suitable |
| R5 | `fd:hasDiversionCandidate` | suitable, operational, distance <= remaining range |
| R6 | `a fd:HubAirport` | >= 14 incident segments |

OWL parts (subClassOf, subPropertyOf, domain/range, inverseOf, Symmetric, Transitive) come from the
GraphDB ruleset **OWL2-RL (Optimized)** or **RDFS-Plus (Optimized)**.
