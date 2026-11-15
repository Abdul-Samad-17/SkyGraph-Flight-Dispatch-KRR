PREFIX fd:   <https://krr.example.org/fd/ontology#>
PREFIX fdr:  <https://krr.example.org/fd/data/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

# ======================================================================
# Dispatch rules R0-R6 as ONE SPARQL Update request (operations run in order).
# GraphDB: SPARQL tab -> switch to "Update" -> paste -> Run.   (Run it ONCE; re-running is harmless, INSERT is idempotent.)
# Order matters: R0 -> R1 -> R2 -> R3 -> R4 (needs R1,R2,R3) -> R5 (needs R1) -> R6.
# ======================================================================

# R0  longest runway of every airport (aggregation MAX)
INSERT { ?a fd:longestRunwayM ?m }
WHERE  { { SELECT ?a (MAX(?len) AS ?m)
           WHERE { ?a fd:hasRunway ?r . ?r fd:runwayLengthM ?len }
           GROUP BY ?a } } ;

# R1  airport suitable for aircraft  <=  longest runway >= aircraft minimum runway
INSERT { ?a fd:isSuitableFor ?ac }
WHERE  { ?a fd:longestRunwayM ?m .
         ?ac fd:minRunwayM ?min .
         FILTER (?m >= ?min) } ;

# R2a segment blocked by an ACTIVE restricted (or prohibited) zone
INSERT { ?s fd:blockedBy ?z . ?s a fd:BlockedSegment }
WHERE  { VALUES ?zc { fd:RestrictedZone fd:ProhibitedZone }
         ?s fd:crossesZone ?z .
         ?z a ?zc ; fd:isActive true . } ;

# R2b segment blocked by an ACTIVE hazard of severity >= 3
INSERT { ?s fd:blockedBy ?h . ?s a fd:BlockedSegment }
WHERE  { ?s fd:affectedByHazard ?h .
         ?h fd:isActive true ; fd:severity ?sev .
         FILTER (?sev >= 3) } ;

# R3  segment longer than the aircraft's maximum range
INSERT { ?s fd:exceedsRangeOf ?ac }
WHERE  { ?s a fd:RouteSegment ; fd:distanceKm ?d .
         ?ac fd:rangeKm ?r .
         FILTER (?d > ?r) } ;

# R4  segment feasible for aircraft: not blocked, within range, both endpoints operational and suitable
INSERT { ?s fd:isFeasibleFor ?ac }
WHERE  { ?s a fd:RouteSegment ; fd:connectsFrom ?a ; fd:connectsTo ?b .
         ?ac fd:rangeKm ?rg .
         ?a fd:isSuitableFor ?ac . ?b fd:isSuitableFor ?ac .
         ?a fd:isOperational true . ?b fd:isOperational true .
         FILTER NOT EXISTS { ?s a fd:BlockedSegment }
         FILTER NOT EXISTS { ?s fd:exceedsRangeOf ?ac } } ;

# R5  diversion candidate: suitable + operational airport within the scenario's remaining range
INSERT { ?sc fd:hasDiversionCandidate ?a }
WHERE  { ?sc a fd:DispatchScenario ; fd:forAircraft ?ac ; fd:remainingRangeKm ?rem .
         ?pd fd:ofScenario ?sc ; fd:toAirport ?a ; fd:distanceKm ?d .
         ?a fd:isSuitableFor ?ac ; fd:isOperational true .
         FILTER (?d <= ?rem) } ;

# R6  hub airport: at least 14 incident route segments (aggregation COUNT)
INSERT { ?a a fd:HubAirport }
WHERE  { { SELECT ?a (COUNT(DISTINCT ?s) AS ?n)
           WHERE { { ?s fd:connectsFrom ?a } UNION { ?s fd:connectsTo ?a } }
           GROUP BY ?a
           HAVING (COUNT(DISTINCT ?s) >= 14) } }
