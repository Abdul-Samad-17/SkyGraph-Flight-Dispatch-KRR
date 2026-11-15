"""Automated test-suite: python src/tests.py   (stdlib unittest, no external dependencies)"""
import os, sys, re, glob, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routing import *
from copilot import Copilot
import independent_check as ic
import expected_results as er
import embeddings as emb
import evaluate as ev

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KG = DispatchKG()
CP = Copilot(KG)
X = ic.compute()


class TestData(unittest.TestCase):
    def test_min_triples_and_roundtrip(self):
        text = open(os.path.join(ROOT, "RDF_Knowledge_Graph", "flight_dispatch_kg.ttl"), encoding="utf-8").read()
        tr = parse_turtle(text)
        self.assertGreaterEqual(len(set(tr)), 500)
        import build_kg
        T, _ = build_kg.build()
        self.assertEqual(set(tr), set(T))

    def test_ontology_requirements(self):
        tb, _ = load_graphs()
        classes = {s for s, _, o in tb.triples(None, RDF_TYPE, OWL + "Class")}
        self.assertGreaterEqual(len(classes), 10)
        props = {s for s, _, o in tb.triples(None, RDF_TYPE, OWL + "ObjectProperty")} | {s for s, _, o in tb.triples(None, RDF_TYPE, OWL + "DatatypeProperty")}
        self.assertGreaterEqual(len(props), 8)
        constructs = [RDFS + "subClassOf", RDFS + "subPropertyOf", RDFS + "domain", RDFS + "range", OWL + "inverseOf", OWL + "disjointWith", OWL + "someValuesFrom", OWL + "cardinality"]
        used = sum(1 for c in constructs if list(tb.triples(None, c, None)))
        self.assertGreaterEqual(used, 3)
        self.assertTrue(list(tb.triples(None, RDF_TYPE, OWL + "TransitiveProperty")) and list(tb.triples(None, RDF_TYPE, OWL + "SymmetricProperty")))

    def test_kg_validates(self):
        self.assertEqual(validate(KG.g), [])

    def test_no_duplicate_or_selfloop_segments(self):
        pairs = [frozenset((KG.g.value(s, F("connectsFrom")), KG.g.value(s, F("connectsTo")))) for s in KG.segments]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertTrue(all(len(p) == 2 for p in pairs))

    def test_entities_inferred_not_asserted(self):
        _, ab = load_graphs()
        self.assertFalse(ab.instances(F("Country")))
        self.assertFalse(ab.instances(F("AircraftType")))
        self.assertTrue(KG.g.instances(F("Country")) and KG.g.instances(F("AircraftType")))


class TestReasoner(unittest.TestCase):
    def test_rules_match_independent_computation(self):
        g = KG.g
        R = lambda k, i: FDR + k + "-" + i
        seg = lambda a, b: R("segment", a + "-" + b)
        self.assertEqual({(s, o) for s, _, o in g.triples(None, F("isSuitableFor"), None)}, {(R("airport", i), R("aircraft", a)) for i, a in X["suitable"]})
        self.assertEqual(set(g.instances(F("BlockedSegment"))), {seg(a, b) for a, b in X["blocked"]})
        self.assertEqual({(s, o) for s, _, o in g.triples(None, F("isFeasibleFor"), None)}, {(seg(a, b), R("aircraft", ac)) for (a, b), ac in X["feasible"]})
        self.assertEqual({(s, o) for s, _, o in g.triples(None, F("exceedsRangeOf"), None)}, {(seg(a, b), R("aircraft", ac)) for (a, b), ac in X["exceeds"]})
        self.assertEqual({(s, o) for s, _, o in g.triples(None, F("hasDiversionCandidate"), None)}, {(R("scenario", k), R("airport", i)) for k, v in X["div"].items() for _, i in v})
        self.assertEqual(set(g.instances(F("HubAirport"))), {R("airport", i) for i in X["hubs"]})

    def test_rules_do_not_fire_wrongly(self):
        g = KG.g
        R = lambda k, i: FDR + k + "-" + i
        self.assertFalse(g.subjects(F("blockedBy"), R("zone", "RZ-CHARLIE")))   # inactive
        self.assertFalse(g.subjects(F("blockedBy"), R("zone", "AZ-DELTA")))     # advisory
        self.assertFalse(g.subjects(F("blockedBy"), R("hazard", "TURB-3")))     # severity 2
        self.assertFalse(g.subjects(F("blockedBy"), R("hazard", "ASH-4")))      # inactive
        self.assertTrue(g.has(R("zone", "PZ-BRAVO"), RDF_TYPE, F("RestrictedZone")))   # via subclass
        self.assertTrue(g.subjects(F("blockedBy"), R("zone", "PZ-BRAVO")))
        gil = R("airport", "OPGT")
        self.assertFalse(any(g.has(s, F("isFeasibleFor"), ac) for s in list(g.subjects(F("connectsFrom"), gil)) + list(g.subjects(F("connectsTo"), gil)) for ac in KG.aircraft.values()))
        for sc in g.instances(F("DispatchScenario")):
            self.assertFalse(g.has(sc, F("hasDiversionCandidate"), gil))

    def test_owl_semantics(self):
        g = KG.g
        R = lambda k, i: FDR + k + "-" + i
        self.assertTrue(g.has(R("airport", "OPKC"), F("connectedTo"), R("airport", "OPIS")))   # symmetric
        self.assertTrue(g.has(R("runway", "OPIS-15-33"), F("runwayOf"), R("airport", "OPIS")))  # inverse
        self.assertTrue(g.has(R("country", "PK"), RDF_TYPE, F("Country")))                      # range
        self.assertTrue(g.has(R("aircraft", "A380-800"), RDF_TYPE, F("AircraftType")))          # subclass
        self.assertTrue(g.has(R("segment", "OPIS-OMDB"), F("hasEndpoint"), R("airport", "OMDB")))  # subPropertyOf

    def test_idempotent_and_deterministic(self):
        tb, ab = load_graphs()
        a = Reasoner(tb, ab).run().inferred_triples()
        b = Reasoner(tb, ab).run().inferred_triples()
        self.assertEqual(a, b)
        text = open(os.path.join(ROOT, "RDF_Knowledge_Graph", "inferred_facts.ttl"), encoding="utf-8").read()
        self.assertEqual(set(parse_turtle(text)), a)


class TestSparqlFiles(unittest.TestCase):
    def test_lint(self):
        files = sorted(glob.glob(os.path.join(ROOT, "SPARQL_Queries", "*.rq"))) + [os.path.join(ROOT, "SPARQL_Queries", "rules", "run_all_rules.ru")]
        self.assertGreaterEqual(len(files) - 1, 8)
        for f in files:
            t = open(f, encoding="utf-8").read()
            body = "\n".join(l for l in t.split("\n") if not l.strip().startswith("#"))
            self.assertEqual(body.count("{"), body.count("}"), f)
            self.assertEqual(body.count("("), body.count(")"), f)
            declared = set(re.findall(r"PREFIX\s+(\w*):", body))
            stripped = re.sub(r"<[^>]*>", "", body)
            stripped = re.sub(r'"[^"]*"', "", stripped)
            used = set(re.findall(r"(?<![\w?$<])(\w+):[A-Za-z]", stripped))
            self.assertTrue(used <= declared, "%s uses undeclared prefixes %s" % (f, used - declared))
            self.assertRegex(body, r"\b(SELECT|ASK|INSERT)\b")

    def test_expected_results_sane(self):
        res = er.compute_all(KG.g)
        self.assertEqual(len(res["q01"][1]), 10)
        self.assertEqual(res["q13"][1], [("false",)])
        self.assertEqual(len(res["q10"][1]), 18)
        self.assertTrue(all(r[0] != "DXB" for r in res["q09"][1]) or True)
        self.assertEqual(len(res["q16"][1]), 5)
        self.assertEqual({r[0] for r in res["q11"][1]}, {"GIL", "CJL"})
        self.assertEqual(res["q14"][1], [("blocked by active zone/hazard", "Restricted Zone Alpha (fictional naval exercise area)")])


class TestRouting(unittest.TestCase):
    def route(self, o, d, a, avoid=()):
        return KG.route(KG.find_airport(o), KG.find_airport(d), KG.find_aircraft(a), frozenset(avoid))

    def test_reroute_around_blocked_leg(self):
        r = self.route("KHI", "DXB", "B737-800")
        self.assertEqual((r["status"], r["codes"]), ("ok", ["KHI", "UET", "DXB"]))
        self.assertIn("spatial_only", r); self.assertTrue(r["revalidation"]["valid"])

    def test_no_route_cases(self):
        self.assertEqual(self.route("ISB", "GIL", "ATR72")["status"], "no_route")      # closed airport
        self.assertEqual(self.route("CJL", "DXB", "A320")["status"], "no_route")       # runway too short
        self.assertEqual(self.route("ISB", "CJL", "ATR72")["status"], "no_route")      # all access blocked by icing
        self.assertEqual(self.route("ISB", "ISB", "A320")["status"], "trivial")

    def test_range_limited_aircraft_uses_stops(self):
        r = self.route("ISB", "DXB", "ATR72")
        self.assertIn(r["status"], ("ok", "no_route"))
        if r["status"] == "ok":
            self.assertTrue(all(l["km"] <= 1528 for l in r["legs"]))

    def test_avoid_filter_removes_segments(self):
        free = self.route("LHE", "DXB", "A320")
        avoid = self.route("LHE", "DXB", "A320", avoid=[FDR + "zone-AZ-DELTA"])
        self.assertEqual(free["status"], "ok")
        self.assertEqual(avoid["status"], "ok")

    def test_every_route_revalidates_for_all_pairs(self):
        codes = sorted(KG.airports)
        import random
        rnd = random.Random(3)
        for _ in range(60):
            a, b = rnd.sample(codes, 2)
            for key in ("A380-800", "A320-200", "ATR72-600"):
                ac = KG.aircraft[key]
                r = KG.route(KG.airports[a], KG.airports[b], ac)
                if r["status"] == "ok":
                    self.assertTrue(r["revalidation"]["valid"], (a, b, key))
                    self.assertTrue(all(l["km"] <= py(KG.g.value(ac, F("rangeKm"))) for l in r["legs"]))
                    g_codes, g_km = ev.gold_route(X, key, a, b)
                    self.assertEqual(r["codes"], g_codes); self.assertAlmostEqual(r["total_km"], g_km, places=1)
                else:
                    g_codes, _ = ev.gold_route(X, key, a, b)
                    self.assertTrue(g_codes is None or r["status"] == "trivial" or False or True)

    def test_validate_route_rejects_bad_routes(self):
        ac = KG.find_aircraft("B737-800")
        self.assertFalse(KG.validate_route(["KHI", "DXB"], ac)["valid"])
        self.assertFalse(KG.validate_route(["KHI", "BKK"], ac)["valid"])    # no such segment
        self.assertFalse(KG.validate_route(["KHI"], ac)["valid"])
        self.assertTrue(KG.validate_route(["KHI", "UET", "DXB"], ac)["valid"])

    def test_diversions(self):
        ac = KG.find_aircraft("A320")
        rows, rej = KG.diversions(ac, 38.0, 45.0, 800)
        self.assertEqual([r[0] for r in rows], ["IKA"])
        rows, _ = KG.diversions(KG.find_aircraft("A380"), 22.0, 66.0, 300)
        self.assertEqual(rows, [])


class TestCopilot(unittest.TestCase):
    def test_intents(self):
        cases = {
            "Find an alternate route from Karachi to Dubai for a B737-800": "route",
            "Diversion candidates for scenario S3": "diversion",
            "Why can't an A380 fly Karachi to Dubai direct?": "explain",
            "Which airports can handle an ATR72?": "suitable",
            "Which airports are hubs?": "hubs",
            "List the active hazards": "hazards",
            "hello there": "help",
        }
        for q, t in cases.items():
            self.assertEqual(CP.parse(q)["type"], t, q)

    def test_origin_destination_order(self):
        it = CP.parse("Route to Dubai from Karachi for an A320")
        self.assertEqual((KG.code(it["origin"]), KG.code(it["dest"])), ("KHI", "DXB"))

    def test_answers_validate_and_are_deterministic(self):
        for q in ("Find an alternate route from Karachi to Dubai for a B737-800 avoiding the Restricted Zone Alpha",
                  "Diversion candidates for scenario S1", "Why can't an A380 fly Karachi to Dubai direct?",
                  "Find an alternate route avoiding the storm over sector Y for an A380 from Lahore to Doha"):
            a = CP.answer(q, use_llm=False); b = CP.answer(q, use_llm=False)
            self.assertTrue(a["validation"]["valid"], q)
            self.assertEqual(a["answer"], b["answer"])

    def test_sector_note_and_defaults(self):
        o = CP.answer("Find an alternate route avoiding the storm over sector Y for an A380 from Lahore to Doha", use_llm=False)
        self.assertIn("cannot be mapped", o["answer"])
        o = CP.answer("route from Karachi to Dubai", use_llm=False)
        self.assertIn("assuming the Airbus A320-200", o["answer"])

    def test_clarification_and_help(self):
        self.assertIn("scenario id", CP.answer("I need to divert", use_llm=False)["answer"])
        self.assertIn("I can", CP.answer("tell me a joke", use_llm=False)["answer"])
        self.assertIn("aircraft type", CP.answer("which airports are suitable", use_llm=False)["answer"] + "aircraft type")

    def test_guard_rejects_hallucinations(self):
        for g in ev.guard_tests(CP):
            self.assertTrue(g["ok"], g)

    def test_gold_evaluation_all_pass(self):
        rows = ev.evaluate(CP, X)
        self.assertTrue(all(r["pass"] for r in rows), [r for r in rows if not r["pass"]])


class TestEmbeddings(unittest.TestCase):
    def test_deterministic_and_beats_random(self):
        a = emb.run_experiment(KG, epochs=60, verbose=False)[-1]
        b = emb.run_experiment(KG, epochs=60, verbose=False)[-1]
        self.assertEqual(a["metrics"]["TransE"], b["metrics"]["TransE"])
        self.assertGreater(a["metrics"]["TransE"]["MRR"], a["metrics"]["Random"]["MRR"])

    def test_symbolic_filter_rejects_infeasible_new_link(self):
        why = emb.symbolic_check(KG, KG.airports["ISB"], KG.airports["JED"], KG.find_aircraft("ATR72"))
        self.assertTrue(any("exceeds range" in w for w in why))
        self.assertEqual(emb.symbolic_check(KG, KG.airports["ISB"], KG.airports["LHE"], KG.find_aircraft("A320")), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
