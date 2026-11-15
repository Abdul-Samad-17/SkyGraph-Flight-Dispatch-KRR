# Protege guide (about 5 minutes)

1. File -> Open -> `Ontology/flight_dispatch_ontology.ttl` (Turtle is accepted by Protege 5.5+; File -> Save as -> *RDF/XML* if your instructor wants OWL/XML).
2. Check **Entities** tab: 19 classes, 18 object properties, 20 data properties. **Classes** tab shows the hierarchy (Airport -> InternationalAirport/RegionalAirport/HubAirport; AirspaceZone -> RestrictedZone -> ProhibitedZone; ...).
3. Optionally open `RDF_Knowledge_Graph/flight_dispatch_kg.ttl` (File -> Open -> *Add to current window*) and run **Reasoner -> HermiT -> Start reasoner**. Expected: consistent, `fd:Country` and `fd:AircraftType` populated by inference, `networkReachable` closure inferred. HermiT does not evaluate the numeric rules R0-R6.
4. Screenshot the class hierarchy, the object-property tab (domain/range/inverse/symmetric/transitive flags) and the reasoner result.

## Optional: the R1 / R2 rules as SWRL (not executed in the build environment)
Protege -> Window -> Tabs -> SWRL Tab, then add (needs the SWRLAPI/Drools engine to execute; the SPARQL versions in `SPARQL_Queries/rules/` are the tested ones):
```
Airport(?a) ^ longestRunwayM(?a, ?m) ^ AircraftType(?c) ^ minRunwayM(?c, ?n) ^ swrlb:greaterThanOrEqual(?m, ?n) -> isSuitableFor(?a, ?c)
RouteSegment(?s) ^ crossesZone(?s, ?z) ^ RestrictedZone(?z) ^ isActive(?z, true) -> blockedBy(?s, ?z)
```
