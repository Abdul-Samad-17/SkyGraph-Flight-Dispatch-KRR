"""Forward-chaining reasoner = OWL/RDFS subset + the dispatch rules R0-R6, with derivation provenance.

OWL/RDFS subset: subClassOf, subPropertyOf, domain, range, inverseOf, SymmetricProperty, TransitiveProperty.
Dispatch rules (identical semantics to SPARQL_Queries/rules/*.ru):
  R0 longestRunwayM   R1 isSuitableFor   R2 blockedBy/BlockedSegment   R3 exceedsRangeOf
  R4 isFeasibleFor    R5 hasDiversionCandidate   R6 HubAirport (degree >= HUB_MIN_DEGREE)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minirdf import *

HERE = os.path.dirname(os.path.abspath(__file__))
ONTO = os.path.join(HERE, "..", "Ontology", "flight_dispatch_ontology.ttl")
KG = os.path.join(HERE, "..", "RDF_Knowledge_Graph", "flight_dispatch_kg.ttl")
INF = os.path.join(HERE, "..", "RDF_Knowledge_Graph", "inferred_facts.ttl")

HUB_MIN_DEGREE = 14
SEVERITY_THRESHOLD = 3

SUBCLASS, SUBPROP = RDFS + "subClassOf", RDFS + "subPropertyOf"
DOMAIN, RANGE = RDFS + "domain", RDFS + "range"
INVERSE = OWL + "inverseOf"
SYMM, TRANS = OWL + "SymmetricProperty", OWL + "TransitiveProperty"
LABEL = RDFS + "label"
F = lambda x: FD + x


class Derivations(dict):
    """inferred triple -> (rule id, human description, [premise triples])"""


def load_graphs(onto=ONTO, kg=KG):
    tbox = Graph(parse_turtle(open(onto, encoding="utf-8").read()))
    abox = Graph(parse_turtle(open(kg, encoding="utf-8").read()))
    return tbox, abox


def _closure_pairs(g, pred):
    """transitive closure of a schema relation -> dict node -> set(ancestors)"""
    up = {}
    for s, _, o in g.triples(None, pred, None):
        if not isinstance(s, BNode) and not isinstance(o, BNode):
            up.setdefault(s, set()).add(o)
    changed = True
    while changed:
        changed = False
        for s in list(up):
            for o in list(up[s]):
                for o2 in up.get(o, ()):
                    if o2 not in up[s]:
                        up[s].add(o2); changed = True
    return up


class Reasoner:
    def __init__(self, tbox, abox):
        self.g = Graph()
        for t in tbox.triples():
            self.g.add(*t)
        for t in abox.triples():
            self.g.add(*t)
        self.explicit = self.g.all()
        self.deriv = Derivations()

    # -------------------------------------------------------------- helpers
    def _infer(self, t, rule, desc, premises):
        if self.g.add(*t):
            self.deriv[t] = (rule, desc, list(premises))
            return True
        return False

    # ------------------------------------------------------------ OWL pass
    def owl_pass(self):
        g = self.g
        changed = False
        sub = _closure_pairs(g, SUBCLASS)
        for c, ups in sub.items():
            for u in ups:
                # premise chain approximated by direct statements along the path
                changed |= self._infer((c, SUBCLASS, u), "rdfs:subClassOf (transitive)", "subClassOf is transitive", [])
        sp = _closure_pairs(g, SUBPROP)
        for p, ups in sp.items():
            for u in ups:
                changed |= self._infer((p, SUBPROP, u), "rdfs:subPropertyOf (transitive)", "subPropertyOf is transitive", [])
        # subPropertyOf propagation
        for p, ups in sp.items():
            for s, _, o in list(g.triples(None, p, None)):
                for q in ups:
                    changed |= self._infer((s, q, o), "rdfs:subPropertyOf",
                                           "%s is a sub-property of %s" % (self.short(p), self.short(q)), [(s, p, o), (p, SUBPROP, q)])
        # inverseOf
        for p, _, q in list(g.triples(None, INVERSE, None)):
            for a, b in ((p, q), (q, p)):
                for s, _, o in list(g.triples(None, a, None)):
                    if not isinstance(o, Lit):
                        changed |= self._infer((o, b, s), "owl:inverseOf", "%s is the inverse of %s" % (self.short(b), self.short(a)),
                                               [(s, a, o), (p, INVERSE, q)])
        # symmetric
        for p in list(g.subjects(RDF_TYPE, SYMM)):
            for s, _, o in list(g.triples(None, p, None)):
                changed |= self._infer((o, p, s), "owl:SymmetricProperty", "%s is symmetric" % self.short(p), [(s, p, o), (p, RDF_TYPE, SYMM)])
        # transitive
        for p in list(g.subjects(RDF_TYPE, TRANS)):
            moved = True
            while moved:
                moved = False
                for a, _, b in list(g.triples(None, p, None)):
                    for _, _, c in list(g.triples(b, p, None)):
                        if self._infer((a, p, c), "owl:TransitiveProperty", "%s is transitive" % self.short(p),
                                       [(a, p, b), (b, p, c), (p, RDF_TYPE, TRANS)]):
                            moved = True; changed = True
        # domain / range
        for p, _, d in list(g.triples(None, DOMAIN, None)):
            if isinstance(d, BNode):
                continue
            for s, _, o in list(g.triples(None, p, None)):
                changed |= self._infer((s, RDF_TYPE, d), "rdfs:domain", "domain of %s is %s" % (self.short(p), self.short(d)), [(s, p, o), (p, DOMAIN, d)])
        for p, _, r in list(g.triples(None, RANGE, None)):
            if isinstance(r, BNode) or str(r).startswith(XSD):
                continue
            for s, _, o in list(g.triples(None, p, None)):
                if not isinstance(o, Lit):
                    changed |= self._infer((o, RDF_TYPE, r), "rdfs:range", "range of %s is %s" % (self.short(p), self.short(r)), [(s, p, o), (p, RANGE, r)])
        # type propagation via subClassOf
        sub = _closure_pairs(g, SUBCLASS)
        for s, _, c in list(g.triples(None, RDF_TYPE, None)):
            for u in sub.get(c, ()):
                changed |= self._infer((s, RDF_TYPE, u), "rdfs:subClassOf", "%s is a subclass of %s" % (self.short(c), self.short(u)),
                                       [(s, RDF_TYPE, c), (c, SUBCLASS, u)])
        return changed

    @staticmethod
    def short(iri):
        for base, pfx in ((FD, "fd:"), (FDR, "fdr:"), (RDFS, "rdfs:"), (RDF, "rdf:"), (OWL, "owl:"), (XSD, "xsd:")):
            if isinstance(iri, str) and iri.startswith(base):
                return pfx + iri[len(base):]
        return str(iri)

    # ------------------------------------------------------- dispatch rules
    def rules_pass(self):
        g = self.g
        ch = False
        TRUE = lit_bool(True)
        # R0 longest runway (aggregation MAX)
        for a in sorted(g.instances(F("Airport")), key=str):
            best, prem = None, []
            for r in g.objects(a, F("hasRunway")):
                L = g.value(r, F("runwayLengthM"))
                if L is not None:
                    v = py(L)
                    prem.append((r, F("runwayLengthM"), L))
                    best = v if best is None else max(best, v)
            if best is not None:
                ch |= self._infer((a, F("longestRunwayM"), lit_int(best)), "R0", "longest runway = MAX over the airport's runway lengths", prem)
        # R1 suitability
        acs = [ac for ac in g.subjects(F("minRunwayM"), None)] if False else sorted({s for s, _, _ in g.triples(None, F("minRunwayM"), None)}, key=str)
        for a in sorted(g.instances(F("Airport")), key=str):
            lr = g.value(a, F("longestRunwayM"))
            if lr is None:
                continue
            for ac in acs:
                mn = g.value(ac, F("minRunwayM"))
                if py(lr) >= py(mn):
                    ch |= self._infer((a, F("isSuitableFor"), ac), "R1", "longest runway >= aircraft minimum runway",
                                      [(a, F("longestRunwayM"), lr), (ac, F("minRunwayM"), mn)])
        # R2 blocked segments
        for s in sorted(g.instances(F("RouteSegment")), key=str):
            for z in g.objects(s, F("crossesZone")):
                if F("RestrictedZone") in g.types(z) and TRUE in g.objects(z, F("isActive")):
                    ch |= self._infer((s, F("blockedBy"), z), "R2", "segment crosses an ACTIVE restricted zone",
                                      [(s, F("crossesZone"), z), (z, RDF_TYPE, F("RestrictedZone")), (z, F("isActive"), TRUE)])
            for h in g.objects(s, F("affectedByHazard")):
                sev = g.value(h, F("severity"))
                if TRUE in g.objects(h, F("isActive")) and sev is not None and py(sev) >= SEVERITY_THRESHOLD:
                    ch |= self._infer((s, F("blockedBy"), h), "R2", "segment crosses an ACTIVE hazard of severity >= %d" % SEVERITY_THRESHOLD,
                                      [(s, F("affectedByHazard"), h), (h, F("isActive"), TRUE), (h, F("severity"), sev)])
            if g.objects(s, F("blockedBy")):
                b = g.objects(s, F("blockedBy"))[0]
                ch |= self._infer((s, RDF_TYPE, F("BlockedSegment")), "R2", "segment has at least one blocking zone/hazard", [(s, F("blockedBy"), b)])
        # R3 exceeds range
        for s in sorted(g.instances(F("RouteSegment")), key=str):
            d = g.value(s, F("distanceKm"))
            for ac in acs:
                rg = g.value(ac, F("rangeKm"))
                if d is not None and rg is not None and py(d) > py(rg):
                    ch |= self._infer((s, F("exceedsRangeOf"), ac), "R3", "segment distance > aircraft maximum range",
                                      [(s, F("distanceKm"), d), (ac, F("rangeKm"), rg)])
        # R4 feasibility
        for s in sorted(g.instances(F("RouteSegment")), key=str):
            fr, to = g.value(s, F("connectsFrom")), g.value(s, F("connectsTo"))
            blocked = bool(g.objects(s, F("blockedBy")))
            for ac in acs:
                if blocked or g.has(s, F("exceedsRangeOf"), ac):
                    continue
                if all(g.has(x, F("isSuitableFor"), ac) and TRUE in g.objects(x, F("isOperational")) for x in (fr, to)):
                    ch |= self._infer((s, F("isFeasibleFor"), ac), "R4",
                                      "not blocked, within range, both endpoints operational and suitable",
                                      [(s, F("connectsFrom"), fr), (s, F("connectsTo"), to), (fr, F("isSuitableFor"), ac), (to, F("isSuitableFor"), ac),
                                       (fr, F("isOperational"), TRUE), (to, F("isOperational"), TRUE)])
        # R5 diversion candidates
        for sc in sorted(g.instances(F("DispatchScenario")), key=str):
            ac, rem = g.value(sc, F("forAircraft")), g.value(sc, F("remainingRangeKm"))
            if ac is None or rem is None:
                continue
            for pd in g.subjects(F("ofScenario"), sc):
                a, d = g.value(pd, F("toAirport")), g.value(pd, F("distanceKm"))
                if py(d) <= py(rem) and g.has(a, F("isSuitableFor"), ac) and TRUE in g.objects(a, F("isOperational")):
                    ch |= self._infer((sc, F("hasDiversionCandidate"), a), "R5", "suitable, operational airport within remaining range",
                                      [(sc, F("forAircraft"), ac), (sc, F("remainingRangeKm"), rem), (pd, F("distanceKm"), d),
                                       (a, F("isSuitableFor"), ac), (a, F("isOperational"), TRUE)])
        # R6 hubs
        for a in sorted(g.instances(F("Airport")), key=str):
            segs = set(g.subjects(F("connectsFrom"), a)) | set(g.subjects(F("connectsTo"), a))
            if len(segs) >= HUB_MIN_DEGREE:
                ch |= self._infer((a, RDF_TYPE, F("HubAirport")), "R6", "airport has >= %d incident route segments (COUNT aggregation)" % HUB_MIN_DEGREE,
                                  [(s, F("connectsFrom") if g.has(s, F("connectsFrom"), a) else F("connectsTo"), a) for s in sorted(segs, key=str)][:3])
        return ch

    def run(self):
        for _ in range(20):
            c1 = self.owl_pass()
            c2 = self.rules_pass()
            if not (c1 or c2):
                break
        return self

    def inferred_triples(self):
        return {t for t in self.deriv if t not in self.explicit}


def validate(g):
    """Schema-level constraint checks (disjointness, cardinalities, existential restrictions, referential integrity)."""
    problems = []
    for a, _, b in list(g.triples(None, OWL + "disjointWith", None)):
        both = g.instances(a) & g.instances(b)
        for x in both:
            problems.append("DISJOINT violation: %s is both %s and %s" % (x, a, b))
    for s in g.instances(F("RouteSegment")):
        for p in ("connectsFrom", "connectsTo"):
            if len(g.objects(s, F(p))) != 1:
                problems.append("CARDINALITY: %s must have exactly one %s" % (s, p))
        if g.value(s, F("connectsFrom")) == g.value(s, F("connectsTo")):
            problems.append("SELF-LOOP segment %s" % s)
        for p in ("connectsFrom", "connectsTo"):
            ap = g.value(s, F(p))
            if ap is not None and F("Airport") not in g.types(ap):
                problems.append("DANGLING endpoint %s of %s" % (ap, s))
    for a in g.instances(F("Airport")):
        if not g.objects(a, F("hasRunway")):
            problems.append("RESTRICTION: airport %s has no runway" % a)
        if len(g.objects(a, F("locatedIn"))) != 1:
            problems.append("RESTRICTION: airport %s must be located in exactly one country" % a)
    for ac in g.instances(F("AircraftType")):
        for p in ("rangeKm", "minRunwayM"):
            if len(g.objects(ac, F(p))) != 1:
                problems.append("CARDINALITY: aircraft %s must have exactly one %s" % (ac, p))
    for sc in g.instances(F("DispatchScenario")):
        if len(g.objects(sc, F("forAircraft"))) != 1:
            problems.append("CARDINALITY: scenario %s must have exactly one aircraft" % sc)
    return problems


def write_inferred(r, path=INF):
    ser = Serializer(DEFAULT_PREFIXES)
    inf = sorted(r.inferred_triples(), key=str)
    hdr = ("Materialised inferences (OWL/RDFS subset + dispatch rules R0-R6) generated by src/reasoner.py.\n"
           "These triples are NOT stored in flight_dispatch_kg.ttl; load this file only if your GraphDB repository has no reasoning/rules enabled.")
    with open(path, "w", encoding="utf-8") as f:
        f.write(ser.dump(inf, hdr))
    return len(inf)


def main():
    tbox, abox = load_graphs()
    r = Reasoner(tbox, abox).run()
    prob = validate(r.g)
    n = write_inferred(r)
    print("explicit triples (T-Box + A-Box):", len(r.explicit))
    print("inferred triples:", n)
    from collections import Counter
    c = Counter(r.deriv[t][0] for t in r.inferred_triples())
    for k, v in sorted(c.items()):
        print("  %-28s %d" % (k, v))
    print("validation problems:", len(prob))
    for p in prob[:20]:
        print("  -", p)


if __name__ == "__main__":
    main()
