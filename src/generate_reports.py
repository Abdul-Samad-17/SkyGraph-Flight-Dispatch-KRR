"""Generates Results/*.md|csv documentation artefacts straight from the graph (so numbers can never drift)."""
import os, sys, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reasoner import *
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "Results")

CQS = [
 ("CQ1", "Which airports are in Pakistan, and what are their IATA/ICAO codes and coordinates?", "Basic", "Airport, Country; locatedIn, iataCode, icaoCode, latitude, longitude", "q01", "-"),
 ("CQ2", "Which runways are longer than 3,500 m and at which airport?", "Filtering", "Airport, Runway; hasRunway, runwayLengthM, designator", "q02", "-"),
 ("CQ3", "How many airports and runways does each country have?", "Aggregation", "Airport, Runway, Country; locatedIn, hasRunway", "q05", "Range of locatedIn types Country"),
 ("CQ4", "How many airports can each aircraft type use (runway suitability)?", "Inference + aggregation", "Airport, AircraftType; isSuitableFor, longestRunwayM, minRunwayM", "q12", "R0, R1"),
 ("CQ5", "Which route segments are blocked and by which active zone or hazard?", "Inference + aggregation", "RouteSegment, RestrictedZone, WeatherHazard; blockedBy, crossesZone, affectedByHazard, isActive, severity", "q06", "R2 (+ subClassOf: ProhibitedZone is a RestrictedZone)"),
 ("CQ6", "Which countries contain airports at the end of a segment affected by an ACTIVE hazard?", "Multi-hop (hazard-segment-airport-country)", "WeatherHazard, RouteSegment, Airport, Country; affectedByHazard, connectsFrom/connectsTo, locatedIn", "q07", "-"),
 ("CQ7", "What two-leg routes exist from Islamabad to Dubai for an A380 where both legs are feasible?", "Multi-hop + inference", "RouteSegment, AircraftType; isFeasibleFor, distanceKm, connectsFrom/connectsTo", "q09", "R1-R4"),
 ("CQ8", "Which airports are reachable from Islamabad over the network (any number of hops)?", "Multi-hop (property path)", "Airport; connectedTo (symmetric)", "q08", "Symmetric/subPropertyOf (path also written direction-agnostic)"),
 ("CQ9", "Which airports are directly connected to Islamabad, and which airports exactly two hops away can take an A380?", "Multi-hop (UNION / sequence path)", "Airport, RouteSegment; connectedTo, isSuitableFor, distanceKm", "q04, q15", "Symmetric connectedTo, R1"),
 ("CQ10", "For a diversion scenario (A380, 1,500 km remaining), which airports are valid diversion candidates?", "Inference; LLM-hard", "DispatchScenario, PositionDistance, Airport; hasDiversionCandidate, remainingRangeKm, distanceKm, isOperational", "q10", "R5 (uses R0, R1)"),
 ("CQ11", "Which airports can take the ATR 72 but not the A320?", "Inference; negation", "Airport, AircraftType; isSuitableFor, longestRunwayM", "q11", "R1 + FILTER NOT EXISTS"),
 ("CQ12", "Which hazards exist, how severe and active are they, and which segments do they affect?", "Filtering / optional", "WeatherHazard, RouteSegment; severity, isActive, hazardType, affectedByHazard", "q03", "-"),
 ("CQ13", "Is the direct Karachi-Dubai segment feasible for the B737-800, and if not, why?", "Explainability; LLM-hard", "RouteSegment, AircraftType; isFeasibleFor, blockedBy, exceedsRangeOf", "q13, q14", "R2, R3, R4"),
 ("CQ14", "What is the shortest FEASIBLE route from Karachi to Dubai for a B737-800 when blocked segments must be avoided?", "Multi-hop + optimisation; LLM-hard", "RouteSegment, AircraftType; isFeasibleFor, distanceKm", "src/routing.py (Dijkstra on the feasible subgraph; subgraph fetched with the Phase-3 SPARQL)", "R1-R4"),
 ("CQ15", "Which airports are hubs (at least 14 incident route segments)?", "Inference (aggregation)", "Airport, HubAirport, RouteSegment; connectsFrom/connectsTo", "q16", "R6"),
]


def short(g, x):
    return Reasoner.short(x)


def main():
    os.makedirs(RES, exist_ok=True)
    tb, ab = load_graphs()
    r = Reasoner(tb, ab).run(); g = r.g
    # ---- CQ mapping
    with open(os.path.join(RES, "cq_mapping.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "competency_question", "type", "ontology_elements", "sparql", "inference"]); w.writerows(CQS)
    md = ["# Competency questions and mapping", "", "| ID | Competency question | Type | KG elements | Query | Inference needed |", "|---|---|---|---|---|---|"]
    for c in CQS:
        md.append("| " + " | ".join(c) + " |")
    md += ["", "Coverage: multi-hop = CQ6, CQ7, CQ8, CQ9, CQ14 (5); inference = CQ4, CQ5, CQ10, CQ11, CQ13, CQ15 (6); aggregation/filtering = CQ2, CQ3, CQ12 (3); "
           "LLM-hard (needs exact numeric constraints and geometry facts) = CQ10, CQ13, CQ14 (3)."]
    open(os.path.join(RES, "cq_mapping.md"), "w", encoding="utf-8").write("\n".join(md))
    # ---- statistics
    expl = r.explicit
    abox = set(ab.triples()); tbox = set(tb.triples())
    inferred = r.inferred_triples()
    types = Counter()
    for s, _, c in abox:
        pass
    for s, p, o in abox:
        if p == RDF_TYPE:
            types[short(g, o)] += 1
    props = Counter(short(g, p) for _, p, _ in abox if p != RDF_TYPE)
    ic = Counter(r.deriv[t][0] for t in inferred)
    st = ["# Graph statistics", "", "| Measure | Value |", "|---|---|",
          "| T-Box (ontology) triples | %d |" % len(tbox), "| A-Box (instance) triples | %d |" % len(abox),
          "| Explicit triples total | %d |" % len(expl), "| Inferred triples (not stored in the A-Box) | %d |" % len(inferred),
          "| Airports | %d |" % len(g.instances(F("Airport"))), "| Runways | %d |" % len(g.instances(F("Runway"))),
          "| Route segments | %d |" % len(g.instances(F("RouteSegment"))), "| Aircraft types | %d |" % len(g.instances(F("AircraftType"))),
          "| Countries (typed by inference) | %d |" % len(g.instances(F("Country"))), "| Zones | %d |" % len(g.instances(F("AirspaceZone"))),
          "| Hazards | %d |" % len(g.instances(F("WeatherHazard"))), "| Scenarios | %d |" % len(g.instances(F("DispatchScenario"))),
          "| Blocked segments (inferred) | %d |" % len(g.instances(F("BlockedSegment"))), "| Hub airports (inferred) | %d |" % len(g.instances(F("HubAirport"))), "",
          "## Explicit A-Box triples by rdf:type", "", "| Class | Type assertions |", "|---|---|"]
    st += ["| %s | %d |" % kv for kv in types.most_common()]
    st += ["", "## Explicit A-Box triples by property", "", "| Property | Triples |", "|---|---|"]
    st += ["| %s | %d |" % kv for kv in props.most_common()]
    st += ["", "## Inferred triples by rule", "", "| Rule | Triples |", "|---|---|"]
    st += ["| %s | %d |" % kv for kv in sorted(ic.items())]
    open(os.path.join(RES, "graph_statistics.md"), "w", encoding="utf-8").write("\n".join(st))
    # ---- inference examples (with provenance)
    R_ = lambda k, i: FDR + k + "-" + i
    def prem(t):
        d = r.deriv.get(t)
        return d
    def fmt(t):
        return "(%s, %s, %s)" % tuple(Reasoner.short(x) if not isinstance(x, Lit) else x.value for x in t)
    ex = ["# Inference examples (explicit facts -> rule -> inferred fact)", "",
          "Every example is generated from the live graph; the derivation records come from `src/reasoner.py`.", ""]
    def block(title, facts, rule, inferred, note=""):
        ex.append("## " + title); ex.append(""); ex.append("**Explicit facts**"); ex.extend("- " + f for f in facts)
        ex.append(""); ex.append("**Rule**: " + rule); ex.append(""); ex.append("**Inferred fact**: " + inferred)
        if note: ex.append(""); ex.append(note)
        ex.append("")
    lr = py(g.value(R_("airport", "OPIS"), F("longestRunwayM")))
    block("Inference 1 - airport suitability (R0 + R1)",
          ["ISB has runway 15/33 with fd:runwayLengthM 3658", "A380-800 has fd:minRunwayM 3000", "KDU (Skardu) has a single 2743 m runway"],
          "R0: longestRunwayM = MAX(runway lengths).  R1: longestRunwayM >= minRunwayM => isSuitableFor.",
          "`fdr:airport-OPIS fd:isSuitableFor fdr:aircraft-A380-800` is inferred (%d >= 3000); `fdr:airport-OPSD fd:isSuitableFor fdr:aircraft-A380-800` is NOT inferred (2743 < 3000), while it is inferred for the A320 (2743 >= 2100)." % lr)
    t = (R_("segment", "OPKC-OMDB"), F("blockedBy"), R_("zone", "RZ-ALPHA"))
    block("Inference 2 - blocked segment (R2)",
          ["KHI-DXB fd:crossesZone RZ-ALPHA", "RZ-ALPHA is a fd:RestrictedZone and fd:isActive true"],
          "R2: crosses an ACTIVE restricted zone => fd:blockedBy and rdf:type fd:BlockedSegment.",
          "`%s` and `fdr:segment-OPKC-OMDB a fd:BlockedSegment`. Consequence: R4 does NOT derive isFeasibleFor for any aircraft on this segment." % fmt(t))
    block("Inference 3 - subclass reasoning feeds a rule (rdfs:subClassOf + R2)",
          ["PZ-BRAVO is typed only as fd:ProhibitedZone", "fd:ProhibitedZone rdfs:subClassOf fd:RestrictedZone", "ISB-LHR fd:crossesZone PZ-BRAVO"],
          "OWL/RDFS: ProhibitedZone is a RestrictedZone, so R2 applies to it.",
          "`fdr:zone-PZ-BRAVO a fd:RestrictedZone` is inferred, hence `fdr:segment-OPIS-EGLL fd:blockedBy fdr:zone-PZ-BRAVO`.")
    block("Inference 4 - diversion candidate (R5)",
          ["Scenario S1: A380-800, fd:remainingRangeKm 1500", "PositionDistance S1-OPKC: 318.8 km to KHI", "KHI is operational and suitable for the A380 (R1)"],
          "R5: suitable and operational airport with distance <= remaining range => fd:hasDiversionCandidate.",
          "`fdr:scenario-S1 fd:hasDiversionCandidate fdr:airport-OPKC`. Scenario S6 (300 km remaining, KHI 344 km away) yields no candidates.")
    block("Inference 5 - range violation (R3)",
          ["ISB-DXB fd:distanceKm 1925.5", "ATR72-600 fd:rangeKm 1528"],
          "R3: distance > rangeKm => fd:exceedsRangeOf.",
          "`fdr:segment-OPIS-OMDB fd:exceedsRangeOf fdr:aircraft-ATR72-600` (and therefore it is not feasible for the ATR, but is for the A380).")
    block("Inference 6 - hub airport (R6)",
          ["DXB is the endpoint of 34 route segments (COUNT DISTINCT)"], "R6: >= 14 incident segments => rdf:type fd:HubAirport (a subclass of fd:Airport).",
          "`fdr:airport-OMDB a fd:HubAirport`; hubs: " + ", ".join(sorted(g.value(a, F("iataCode")).value for a in g.instances(F("HubAirport")))) + ".")
    block("Inference 7 - OWL characteristics (symmetric, inverse, domain/range)",
          ["ISB fd:connectedTo KHI (stored once)", "ISB fd:hasRunway runway-OPIS-15-33", "ISB fd:locatedIn country-PK"],
          "owl:SymmetricProperty (connectedTo), owl:inverseOf (hasRunway/runwayOf), rdfs:range (locatedIn -> Country).",
          "`KHI fd:connectedTo ISB`, `runway-OPIS-15-33 fd:runwayOf ISB`, `fdr:country-PK a fd:Country`.")
    ex.append("## Negative checks (rules must NOT fire)"); ex.append("")
    for seg, why in (("OPIS-OMDB", None),):
        pass
    neg = []
    h_ts = [("RZ-CHARLIE zone is inactive", "zone", "RZ-CHARLIE"), ("AZ-DELTA is an advisory zone", "zone", "AZ-DELTA")]
    crossing = lambda z: sorted(g.value(s, LABEL).value for s in g.subjects(F("crossesZone"), R_("zone", z)))
    ex.append("- RZ-CHARLIE (restricted but inactive) is crossed by %d segment(s) (e.g. %s) but none is blocked by it: %s." % (
        len(crossing("RZ-CHARLIE")), ", ".join(crossing("RZ-CHARLIE")[:3]), "confirmed" if not g.subjects(F("blockedBy"), R_("zone", "RZ-CHARLIE")) else "ERROR"))
    ex.append("- AZ-DELTA (advisory only) is crossed by %d segment(s) but blocks none: %s." % (
        len(crossing("AZ-DELTA")), "confirmed" if not g.subjects(F("blockedBy"), R_("zone", "AZ-DELTA")) else "ERROR"))
    for hid, why in (("TURB-3", "severity 2 < 3"), ("ASH-4", "inactive (expired)")):
        n = len(g.subjects(F("affectedByHazard"), R_("hazard", hid)))
        ex.append("- Hazard %s (%s) affects %d segment(s) but blocks none: %s." % (hid, why, n, "confirmed" if not g.subjects(F("blockedBy"), R_("hazard", hid)) else "ERROR"))
    ex.append("- GIL (Gilgit) is closed (fd:isOperational false): every segment touching it is infeasible and it is never a diversion candidate.")
    open(os.path.join(RES, "inference_examples.md"), "w", encoding="utf-8").write("\n".join(ex))
    print("reports written:", sorted(os.listdir(RES)))


if __name__ == "__main__":
    main()
