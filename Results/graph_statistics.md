# Graph statistics

| Measure | Value |
|---|---|
| T-Box (ontology) triples | 259 |
| A-Box (instance) triples | 2105 |
| Explicit triples total | 2364 |
| Inferred triples (not stored in the A-Box) | 3048 |
| Airports | 38 |
| Runways | 60 |
| Route segments | 153 |
| Aircraft types | 6 |
| Countries (typed by inference) | 21 |
| Zones | 4 |
| Hazards | 5 |
| Scenarios | 6 |
| Blocked segments (inferred) | 45 |
| Hub airports (inferred) | 5 |

## Explicit A-Box triples by rdf:type

| Class | Type assertions |
|---|---|
| fd:RouteSegment | 153 |
| fd:PositionDistance | 94 |
| fd:Runway | 60 |
| fd:Airport | 38 |
| fd:InternationalAirport | 32 |
| fd:DispatchScenario | 6 |
| fd:RegionalAirport | 6 |
| fd:WeatherHazard | 5 |
| fd:WidebodyAircraft | 3 |
| fd:NarrowbodyAircraft | 2 |
| fd:RestrictedZone | 2 |
| fd:ProhibitedZone | 1 |
| fd:TurbopropAircraft | 1 |
| fd:AdvisoryZone | 1 |

## Explicit A-Box triples by property

| Property | Triples |
|---|---|
| fd:distanceKm | 247 |
| rdfs:label | 233 |
| fd:connectedTo | 153 |
| fd:connectsTo | 153 |
| fd:connectsFrom | 153 |
| fd:ofScenario | 94 |
| fd:toAirport | 94 |
| fd:hasRunway | 60 |
| fd:designator | 60 |
| fd:runwayLengthM | 60 |
| fd:crossesZone | 46 |
| fd:icaoCode | 38 |
| fd:latitude | 38 |
| fd:longitude | 38 |
| fd:locatedIn | 38 |
| fd:iataCode | 38 |
| fd:isOperational | 38 |
| fd:affectedByHazard | 32 |
| fd:isoCode | 21 |
| fd:isActive | 9 |
| fd:forAircraft | 6 |
| fd:minRunwayM | 6 |
| fd:rangeKm | 6 |
| fd:icaoTypeCode | 6 |
| fd:currentLongitude | 6 |
| fd:remainingRangeKm | 6 |
| fd:currentLatitude | 6 |
| fd:cruiseSpeedKmh | 6 |
| fd:hazardType | 5 |
| fd:severity | 5 |

## Inferred triples by rule

| Rule | Triples |
|---|---|
| R0 | 38 |
| R1 | 208 |
| R2 | 93 |
| R3 | 103 |
| R4 | 544 |
| R5 | 61 |
| R6 | 5 |
| owl:SymmetricProperty | 306 |
| owl:TransitiveProperty | 1138 |
| owl:inverseOf | 60 |
| rdfs:domain | 27 |
| rdfs:range | 4 |
| rdfs:subClassOf | 1 |
| rdfs:subClassOf (transitive) | 1 |
| rdfs:subPropertyOf | 459 |