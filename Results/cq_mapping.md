# Competency questions and mapping

| ID | Competency question | Type | KG elements | Query | Inference needed |
|---|---|---|---|---|---|
| CQ1 | Which airports are in Pakistan, and what are their IATA/ICAO codes and coordinates? | Basic | Airport, Country; locatedIn, iataCode, icaoCode, latitude, longitude | q01 | - |
| CQ2 | Which runways are longer than 3,500 m and at which airport? | Filtering | Airport, Runway; hasRunway, runwayLengthM, designator | q02 | - |
| CQ3 | How many airports and runways does each country have? | Aggregation | Airport, Runway, Country; locatedIn, hasRunway | q05 | Range of locatedIn types Country |
| CQ4 | How many airports can each aircraft type use (runway suitability)? | Inference + aggregation | Airport, AircraftType; isSuitableFor, longestRunwayM, minRunwayM | q12 | R0, R1 |
| CQ5 | Which route segments are blocked and by which active zone or hazard? | Inference + aggregation | RouteSegment, RestrictedZone, WeatherHazard; blockedBy, crossesZone, affectedByHazard, isActive, severity | q06 | R2 (+ subClassOf: ProhibitedZone is a RestrictedZone) |
| CQ6 | Which countries contain airports at the end of a segment affected by an ACTIVE hazard? | Multi-hop (hazard-segment-airport-country) | WeatherHazard, RouteSegment, Airport, Country; affectedByHazard, connectsFrom/connectsTo, locatedIn | q07 | - |
| CQ7 | What two-leg routes exist from Islamabad to Dubai for an A380 where both legs are feasible? | Multi-hop + inference | RouteSegment, AircraftType; isFeasibleFor, distanceKm, connectsFrom/connectsTo | q09 | R1-R4 |
| CQ8 | Which airports are reachable from Islamabad over the network (any number of hops)? | Multi-hop (property path) | Airport; connectedTo (symmetric) | q08 | Symmetric/subPropertyOf (path also written direction-agnostic) |
| CQ9 | Which airports are directly connected to Islamabad, and which airports exactly two hops away can take an A380? | Multi-hop (UNION / sequence path) | Airport, RouteSegment; connectedTo, isSuitableFor, distanceKm | q04, q15 | Symmetric connectedTo, R1 |
| CQ10 | For a diversion scenario (A380, 1,500 km remaining), which airports are valid diversion candidates? | Inference; LLM-hard | DispatchScenario, PositionDistance, Airport; hasDiversionCandidate, remainingRangeKm, distanceKm, isOperational | q10 | R5 (uses R0, R1) |
| CQ11 | Which airports can take the ATR 72 but not the A320? | Inference; negation | Airport, AircraftType; isSuitableFor, longestRunwayM | q11 | R1 + FILTER NOT EXISTS |
| CQ12 | Which hazards exist, how severe and active are they, and which segments do they affect? | Filtering / optional | WeatherHazard, RouteSegment; severity, isActive, hazardType, affectedByHazard | q03 | - |
| CQ13 | Is the direct Karachi-Dubai segment feasible for the B737-800, and if not, why? | Explainability; LLM-hard | RouteSegment, AircraftType; isFeasibleFor, blockedBy, exceedsRangeOf | q13, q14 | R2, R3, R4 |
| CQ14 | What is the shortest FEASIBLE route from Karachi to Dubai for a B737-800 when blocked segments must be avoided? | Multi-hop + optimisation; LLM-hard | RouteSegment, AircraftType; isFeasibleFor, distanceKm | src/routing.py (Dijkstra on the feasible subgraph; subgraph fetched with the Phase-3 SPARQL) | R1-R4 |
| CQ15 | Which airports are hubs (at least 14 incident route segments)? | Inference (aggregation) | Airport, HubAirport, RouteSegment; connectsFrom/connectsTo | q16 | R6 |

Coverage: multi-hop = CQ6, CQ7, CQ8, CQ9, CQ14 (5); inference = CQ4, CQ5, CQ10, CQ11, CQ13, CQ15 (6); aggregation/filtering = CQ2, CQ3, CQ12 (3); LLM-hard (needs exact numeric constraints and geometry facts) = CQ10, CQ13, CQ14 (3).