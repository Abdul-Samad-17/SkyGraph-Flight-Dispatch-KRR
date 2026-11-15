"""Computes the EXPECTED result of every SPARQL query in /SPARQL_Queries (plain Python over the
reasoned graph) and writes Results/expected_query_results.md + Results/csv/*.csv.
Use it to cross-check what GraphDB returns when you run the .rq files."""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reasoner import *
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "Results")
R = lambda k, i: FDR + k + "-" + i


def lab(g, x):
    v = g.value(x, LABEL)
    return v.value if v is not None else str(x)


def compute_all(g):
    out = {}
    iata = lambda a: g.value(a, F("iataCode")).value
    airports = sorted(g.instances(F("Airport")), key=str)
    # q01
    rows = []
    for a in airports:
        if g.has(a, F("locatedIn"), R("country", "PK")):
            rows.append((iata(a), g.value(a, F("icaoCode")).value, lab(g, a), py(g.value(a, F("latitude"))), py(g.value(a, F("longitude")))))
    out["q01"] = (["iata", "icao", "name", "lat", "lon"], sorted(rows))
    # q02
    rows = []
    for a in airports:
        for r in g.objects(a, F("hasRunway")):
            L = py(g.value(r, F("runwayLengthM")))
            if L > 3500:
                rows.append((iata(a), g.value(r, F("designator")).value, L))
    out["q02"] = (["iata", "designator", "length"], sorted(rows, key=lambda r: (-r[2], r[0])))
    # q03
    rows = []
    for h in g.instances(F("WeatherHazard")):
        segs = sorted(lab(g, s) for s in g.subjects(F("affectedByHazard"), h))
        base = (lab(g, h), g.value(h, F("hazardType")).value, py(g.value(h, F("severity"))), str(py(g.value(h, F("isActive")))).lower())
        for s in (segs or [""]):
            rows.append(base + (s,))
    out["q03"] = (["hazard", "type", "severity", "active", "segment"], sorted(rows, key=lambda r: (-r[2], r[0], r[4])))
    # q04
    rows = set()
    for s in g.subjects(F("connectsFrom"), R("airport", "OPIS")):
        rows.add((iata(g.value(s, F("connectsTo"))), py(g.value(s, F("distanceKm")))))
    for s in g.subjects(F("connectsTo"), R("airport", "OPIS")):
        rows.add((iata(g.value(s, F("connectsFrom"))), py(g.value(s, F("distanceKm")))))
    out["q04"] = (["iata", "distance"], sorted(rows, key=lambda r: (r[1], r[0])))
    # q05
    cnt = defaultdict(lambda: [set(), 0])
    for a in airports:
        c = g.value(a, F("locatedIn"))
        cnt[lab(g, c)][0].add(a)
        cnt[lab(g, c)][1] += len(g.objects(a, F("hasRunway")))
    rows = [(k, len(v[0]), v[1]) for k, v in cnt.items()]
    out["q05"] = (["country", "airports", "runways"], sorted(rows, key=lambda r: (-r[1], r[0])))
    # q06
    cnt = defaultdict(set)
    for s, _, c in g.triples(None, F("blockedBy"), None):
        cnt[c].add(s)
    rows = [(str(c), lab(g, c), len(v)) for c, v in cnt.items()]
    rows = [(c.replace(FDR, "fdr:"), l, n) for c, l, n in rows]
    out["q06"] = (["cause", "label", "blockedSegments"], sorted(rows, key=lambda r: (-r[2], r[1])))
    # q07
    cnt = defaultdict(set)
    for h in g.instances(F("WeatherHazard")):
        if lit_bool(True) in g.objects(h, F("isActive")):
            for s in g.subjects(F("affectedByHazard"), h):
                for p in (F("connectsFrom"), F("connectsTo")):
                    a = g.value(s, p)
                    cnt[lab(g, g.value(a, F("locatedIn")))].add(a)
    rows = [(k, len(v)) for k, v in cnt.items()]
    out["q07"] = (["country", "airportsAffected"], sorted(rows, key=lambda r: (-r[1], r[0])))
    # q08  (undirected reachability over connectedTo)
    adj = defaultdict(set)
    for s, _, o in g.triples(None, F("connectedTo"), None):
        adj[s].add(o); adj[o].add(s)
    seen, stack = set(), [R("airport", "OPIS")]
    while stack:
        n = stack.pop()
        for m in adj[n]:
            if m not in seen:
                seen.add(m); stack.append(m)
    seen.discard(R("airport", "OPIS"))
    out["q08"] = (["iata"], sorted((iata(a),) for a in seen))
    # q09
    A380 = R("aircraft", "A380-800")
    feas = {s for s in g.instances(F("RouteSegment")) if g.has(s, F("isFeasibleFor"), A380)}
    def ends(s): return g.value(s, F("connectsFrom")), g.value(s, F("connectsTo"))
    rows = []
    for s1 in feas:
        e1 = ends(s1)
        if R("airport", "OPIS") not in e1: continue
        m = e1[0] if e1[1] == R("airport", "OPIS") else e1[1]
        for s2 in feas:
            e2 = ends(s2)
            if s2 == s1 or R("airport", "OMDB") not in e2 or m not in e2: continue
            rows.append((iata(m), py(g.value(s1, F("distanceKm"))), py(g.value(s2, F("distanceKm"))),
                         round(py(g.value(s1, F("distanceKm"))) + py(g.value(s2, F("distanceKm"))), 1)))
    out["q09"] = (["via", "d1", "d2", "total"], sorted(rows, key=lambda r: (r[3], r[0])))
    # q10
    rows = []
    sc = R("scenario", "S1")
    for pd in g.subjects(F("ofScenario"), sc):
        a = g.value(pd, F("toAirport"))
        if g.has(sc, F("hasDiversionCandidate"), a):
            rows.append((iata(a), lab(g, a), py(g.value(pd, F("distanceKm")))))
    out["q10"] = (["iata", "name", "distance"], sorted(rows, key=lambda r: (r[2], r[0])))
    # q11
    ATR, A320 = R("aircraft", "ATR72-600"), R("aircraft", "A320-200")
    rows = [(iata(a), lab(g, a), py(g.value(a, F("longestRunwayM")))) for a in airports
            if g.has(a, F("isSuitableFor"), ATR) and not g.has(a, F("isSuitableFor"), A320)]
    out["q11"] = (["iata", "name", "longestRunway"], sorted(rows))
    # q12
    cnt = defaultdict(set)
    for a, _, ac in g.triples(None, F("isSuitableFor"), None):
        cnt[ac].add(a)
    rows = [(lab(g, ac), py(g.value(ac, F("minRunwayM"))), len(v)) for ac, v in cnt.items()]
    out["q12"] = (["aircraft", "minRunway", "suitableAirports"], sorted(rows, key=lambda r: (-r[1], r[0])))
    # q13
    out["q13"] = (["ask"], [(str(g.has(R("segment", "OPKC-OMDB"), F("isFeasibleFor"), R("aircraft", "B737-800"))).lower(),)])
    # q14
    s = R("segment", "OPKC-OMDB"); rows = []
    for r in g.objects(s, F("blockedBy")): rows.append(("blocked by active zone/hazard", lab(g, r)))
    for r in g.objects(s, F("exceedsRangeOf")): rows.append(("distance exceeds aircraft range", lab(g, r)))
    out["q14"] = (["reasonType", "reason"], sorted(rows))
    # q15
    rows = set()
    for x in adj[R("airport", "OPIS")]:
        for y in adj[x]:
            if y != R("airport", "OPIS") and g.has(y, F("isSuitableFor"), A380):
                rows.add((iata(y), lab(g, g.value(y, F("locatedIn")))))
    out["q15"] = (["iata", "country"], sorted(rows, key=lambda r: (r[1], r[0])))
    # q16
    rows = []
    for a in g.instances(F("HubAirport")):
        segs = set(g.subjects(F("connectsFrom"), a)) | set(g.subjects(F("connectsTo"), a))
        rows.append((iata(a), lab(g, a), len(segs)))
    out["q16"] = (["iata", "name", "segments"], sorted(rows, key=lambda r: (-r[2], r[0])))
    return out


TITLES = {
 "q01": "CQ1 Airports in Pakistan (basic pattern)", "q02": "CQ2 Runways longer than 3,500 m (FILTER)",
 "q03": "CQ12 Hazards with optional affected segments (OPTIONAL)", "q04": "CQ9a Neighbours of ISB (UNION)",
 "q05": "CQ3 Airports/runways per country (aggregation)", "q06": "CQ5 Blocked segments per cause (inference R2 + aggregation)",
 "q07": "CQ6 Countries behind active hazards (multi-hop)", "q08": "CQ8 Reachable from ISB (property path)",
 "q09": "CQ7 Two-leg feasible routes ISB->DXB for A380 (multi-hop + R4)", "q10": "CQ10 Diversion candidates scenario S1 (R5)",
 "q11": "CQ11 ATR-only airports (R1 + NOT EXISTS)", "q12": "CQ4 Suitable airports per aircraft (R0/R1 + aggregation)",
 "q13": "CQ13 ASK KHI->DXB feasible for B737-800", "q14": "CQ13 Why KHI->DXB is not feasible (explainability)",
 "q15": "CQ9 Airports 2 hops from ISB suitable for A380 (property path + inference)", "q16": "CQ15 Hub airports (R6)",
}


def main():
    os.makedirs(os.path.join(RES, "csv"), exist_ok=True)
    tb, ab = load_graphs(); g = Reasoner(tb, ab).run().g
    res = compute_all(g)
    md = ["# Expected SPARQL results", "",
          "Computed in plain Python over the reasoned graph (`src/expected_results.py`). After running each `.rq` in GraphDB, "
          "the rows must match (GraphDB may order ties differently). Run `src/run_everything.py` to regenerate.", ""]
    for q in sorted(res):
        head, rows = res[q]
        with open(os.path.join(RES, "csv", q + ".csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(head); w.writerows(rows)
        md.append("## %s - %s  (%d rows)" % (q, TITLES[q], len(rows))); md.append("")
        md.append("| " + " | ".join(head) + " |"); md.append("|" + "---|" * len(head))
        for r in rows[:40]:
            md.append("| " + " | ".join(str(v) for v in r) + " |")
        if len(rows) > 40:
            md.append("| ... %d more rows in csv/%s.csv |" % (len(rows) - 40, q) + " |" * (len(head) - 1))
        md.append("")
    with open(os.path.join(RES, "expected_query_results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    for q in sorted(res):
        print(q, len(res[q][1]), "rows")
    return res


if __name__ == "__main__":
    main()
