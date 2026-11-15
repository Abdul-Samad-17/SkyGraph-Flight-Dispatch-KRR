# GraphDB guide (about 10 minutes)

1. **Create the repository**: Setup -> Repositories -> *Create new repository* -> *GraphDB repository*. Repository ID `flightdispatch`. **Ruleset: `OWL2-RL (Optimized)`** (or `RDFS-Plus (Optimized)`). Save.
2. **Import** (Import -> Upload RDF files -> select, then *Import* with default settings):
   - `Ontology/flight_dispatch_ontology.ttl`
   - `RDF_Knowledge_Graph/flight_dispatch_kg.ttl`
   - Take a screenshot of the success message (required evidence).
3. **Run the rules once**: SPARQL tab -> choose **Update** (not Query) -> paste `SPARQL_Queries/rules/run_all_rules.ru` -> Run. It derives `longestRunwayM`, `isSuitableFor`, `blockedBy`/`BlockedSegment`, `exceedsRangeOf`, `isFeasibleFor`, `hasDiversionCandidate` and `HubAirport`. (Running it twice is harmless.)
   *Alternative without reasoning/rules*: create the repository with ruleset "No inference" and additionally import `RDF_Knowledge_Graph/inferred_facts.ttl` (all inferences pre-materialised by `src/reasoner.py`).
4. **Run the queries**: paste each `SPARQL_Queries/q01...q16*.rq` into the SPARQL tab (Query mode). Compare with `Results/expected_query_results.md` / `Results/csv/qNN.csv` (ties may be ordered differently). Save screenshots or CSV exports into `Results/`.
5. **Visual graph**: Explore -> Visual graph -> easy graph -> enter `https://krr.example.org/fd/data/airport-OPIS` -> expand `connectedTo`, `hasRunway`, `locatedIn`. Screenshot into `Visualization/`.
6. **Check the count**: SPARQL `SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }` - expect the explicit triples (2,364 = T-Box 259 + A-Box 2,105) plus whatever the ruleset infers (GraphDB's own count is higher because it also materialises RDFS/OWL axiomatic triples).

Troubleshooting: *query returns 0 rows* -> rules not run yet (q06, q09-q16) or ruleset set to "No inference" (q15 needs symmetric `connectedTo`; q08 works either way). *Update fails to parse* -> make sure you pasted the whole file and chose Update mode.
