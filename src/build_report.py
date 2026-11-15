"""Builds Report/AI3001_Iteration1_Report.docx and Report/AI3001_Final_Project_Report.docx from live project data."""
import os, sys, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reasoner import *
import generate_reports as gr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RES = os.path.join(ROOT, "Results"); VIS = os.path.join(ROOT, "Visualization"); REP = os.path.join(ROOT, "Report")
PH = "[fill in]"


def table(doc, header, rows, widths=None, size=8.5):
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(str(h)); r.bold = True; r.font.size = Pt(size)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; run = cells[i].paragraphs[0].add_run(str(v)); run.font.size = Pt(size)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return t


def para(doc, text, bold=False, italic=False, size=10.5):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = bold; r.italic = italic; r.font.size = Pt(size)
    return p


def bullets(doc, items, size=10.5):
    for it in items:
        p = doc.add_paragraph(style="List Bullet"); r = p.add_run(it); r.font.size = Pt(size)


def code(doc, text):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.name = "Consolas"; r.font.size = Pt(8)
    p.paragraph_format.left_indent = Inches(0.2)


def image(doc, name, caption, width=6.4):
    path = os.path.join(VIS, name)
    if os.path.exists(path):
        doc.add_picture(path, width=Inches(width)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = para(doc, caption, italic=True, size=9); p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def read_csv(q):
    with open(os.path.join(RES, "csv", q + ".csv"), newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def build(full):
    tb, ab = load_graphs(); r = Reasoner(tb, ab).run(); g = r.g
    doc = Document()
    st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(0.9); s.top_margin = s.bottom_margin = Inches(0.8)
    title = "AI-3001 Knowledge Representation & Reasoning - " + ("Final Project Report" if full else "Iteration 1 Progress Report")
    doc.add_heading(title, 0)
    para(doc, "Dynamic Flight Dispatch & Weather Routing Knowledge System (Transportation domain)", bold=True, size=12)
    table(doc, ["Item", "Details"], [
        ["Team name", "TeamName  " + PH], ["Member 1", "Huzaifa Mudassar (24i-0050), FAST-NUCES Islamabad, section AI-5B"],
        ["Member 2", PH], ["Member 3", PH], ["Iteration 1 deadline", "15 November 2026 (review and live demo)"],
        ["Status", "Academic prototype - not intended for operational use"]], widths=[1.6, 5.0])

    doc.add_heading("1. Overview", 1)
    para(doc, "Flight dispatchers must reroute flights around weather and closed airspace while respecting aircraft limits (maximum range, minimum runway length). "
              "Purely spatial routing can return a path that is shortest on paper but operationally impossible. This project encodes those constraints as an ontology plus explicit rules "
              "so that infeasible airports and segments are eliminated BEFORE any path optimisation, and every returned route can be explained and independently re-validated.")
    para(doc, "Pipeline: curated CSV data -> ETL (haversine distances, segment/zone/hazard geometry) -> RDF knowledge graph -> OWL/RDFS + SPARQL rules (R0-R6) -> "
              "SPARQL queries and constraint-aware shortest path -> " + ("hybrid embeddings (Phase 2) and a GraphRAG copilot (Phase 3)." if full else "(Phases 2-3: embeddings and GraphRAG copilot, planned for later iterations)."))

    doc.add_heading("2. Dataset, cleaning and transformation", 1)
    para(doc, "Study area: South Asia - Gulf - Europe - South-East/East Asia. Sources named by the project brief: OurAirports (airports, runways), OpenFlights (routes), OpenAP (aircraft), Natural Earth (zones), aviationweather.gov (weather).")
    para(doc, "Important data note: this build had no internet access, so the CSVs in /Dataset are CURATED, rounded values for 38 well-known airports and 6 aircraft types written in the style of those datasets, "
              "not machine-downloaded files. Zones, hazards and scenarios are FICTIONAL illustrations (no real closures are asserted). Before final submission the team should verify coordinates, runway lengths and aircraft figures "
              "against the original sources (see Dataset/SOURCES.md) and re-run src/run_everything.py - the whole pipeline regenerates automatically.", italic=True)
    table(doc, ["Table", "Rows", "Content"], [["airports.csv", len(g.instances(F("Airport"))), "ICAO, IATA, name, country, lat/lon, operational flag, category"],
                                               ["runways.csv", len(g.instances(F("Runway"))), "airport, designator, length (m)"],
                                               ["aircraft.csv", len(g.instances(F("AircraftType"))), "type, class, range (km), minimum runway (m), cruise speed"],
                                               ["segments.csv", len(g.instances(F("RouteSegment"))), "undirected airport pairs (route network)"],
                                               ["zones.csv / hazards.csv", "%d / %d" % (len(g.instances(F("AirspaceZone"))), len(g.instances(F("WeatherHazard")))), "fictional polygons, activity flag, hazard severity 1-5"],
                                               ["scenarios.csv", len(g.instances(F("DispatchScenario"))), "aircraft, position, remaining range"]], widths=[1.7, 0.9, 4.0])
    para(doc, "Cleaning / transformation steps (src/make_dataset.py, src/build_kg.py):", bold=True)
    bullets(doc, ["Restricted the data to one study region and removed any airport without coordinates or runway length; codes validated (every segment endpoint exists, no self-loops, no duplicate/reversed pairs).",
                  "Computed great-circle distance (haversine, R = 6371 km) for every segment, rounded to 0.1 km.",
                  "Computed segment-polygon intersections (straight line in the lon/lat plane, exact closed-segment intersection test) and stored them as fd:crossesZone / fd:affectedByHazard facts - cheaper and more transparent than GeoSPARQL for this iteration.",
                  "Materialised PositionDistance facts only for airports within 1.5 x remaining range of each scenario (SPARQL 1.1 has no trigonometric functions).",
                  "Left fd:Country and fd:AircraftType deliberately un-asserted so that they are inferred from rdfs:range / rdfs:subClassOf (visible inference demonstrations).",
                  "Schema constraints validated automatically (disjointness, cardinalities, existential restrictions): 0 violations."])
    para(doc, "URI design: ontology https://krr.example.org/fd/ontology# (prefix fd:), data https://krr.example.org/fd/data/ (prefix fdr:) with readable local names: "
              "fdr:airport-OPIS, fdr:runway-OPIS-15-33, fdr:aircraft-A380-800, fdr:segment-OPKC-OMDB, fdr:zone-RZ-ALPHA, fdr:hazard-STORM-1, fdr:country-PK, fdr:scenario-S1, fdr:dist-S1-OPKC.")

    doc.add_heading("3. Competency questions", 1)
    table(doc, ["ID", "Competency question", "Type", "Query", "Inference"], [[c[0], c[1], c[2], c[4], c[5]] for c in gr.CQS], widths=[0.5, 2.9, 1.2, 0.9, 1.1], size=8)
    para(doc, "Coverage: 5 multi-hop (CQ6-9, CQ14), 6 inference (CQ4, 5, 10, 11, 13, 15), 3 aggregation/filtering (CQ2, 3, 12) and 3 'LLM-hard' questions (CQ10, 13, 14) that need exact numeric constraints and geometry facts only the KG holds. Full mapping table: Results/cq_mapping.md.")

    doc.add_heading("4. Ontology (T-Box)", 1)
    image(doc, "ontology_schema.png", "Figure 1 - Ontology schema (blue: subClassOf; green: asserted properties; gold dashed: inferred properties).")
    classes = sorted(s for s, _, _ in tb.triples(None, RDF_TYPE, OWL + "Class"))
    table(doc, ["Class", "Role"], [[Reasoner.short(c), (tb.value(c, RDFS + "comment").value if tb.value(c, RDFS + "comment") else (tb.value(c, LABEL).value))] for c in classes], widths=[2.0, 4.6], size=8)
    para(doc, "%d classes, %d object properties, %d datatype properties." % (len(classes), len(list(tb.triples(None, RDF_TYPE, OWL + "ObjectProperty"))), len(list(tb.triples(None, RDF_TYPE, OWL + "DatatypeProperty")))))
    table(doc, ["Reasoning construct", "Where used"], [
        ["rdfs:subClassOf (hierarchies)", "InternationalAirport/RegionalAirport/HubAirport < Airport; Widebody/Narrowbody/Turboprop < AircraftType; Prohibited < Restricted < AirspaceZone; BlockedSegment < RouteSegment"],
        ["rdfs:subPropertyOf", "connectsFrom, connectsTo < hasEndpoint; connectedTo < networkReachable"],
        ["rdfs:domain / rdfs:range", "all properties; range of locatedIn makes countries fd:Country"],
        ["owl:inverseOf", "hasRunway / runwayOf"],
        ["owl:SymmetricProperty / TransitiveProperty", "connectedTo (symmetric); networkReachable (symmetric + transitive)"],
        ["owl:disjointWith", "Airport, Runway, AircraftType, RouteSegment, AirspaceZone, WeatherHazard, Country"],
        ["owl:Restriction (someValuesFrom, cardinality)", "Airport has a runway and a country; RouteSegment exactly one connectsFrom/connectsTo; AircraftType exactly one range/minRunway"],
        ["Rules R0-R6 (SPARQL Update / src/reasoner.py)", "numeric conditions not expressible in OWL 2 RL: suitability, blocking, range, feasibility, diversion, hubs"]], widths=[2.2, 4.4], size=8.5)
    para(doc, "T-Box vs A-Box: the ontology file (Ontology/flight_dispatch_ontology.ttl, %d triples) is the T-Box; Dataset-derived RDF (RDF_Knowledge_Graph/flight_dispatch_kg.ttl, %d triples) is the A-Box." % (len(set(tb.triples())), len(set(ab.triples()))))

    doc.add_heading("5. RDF knowledge graph and GraphDB", 1)
    infer = r.inferred_triples()
    table(doc, ["Measure", "Value"], [["A-Box triples (explicit instance data)", len(set(ab.triples()))], ["T-Box triples", len(set(tb.triples()))],
                                       ["Inferred triples (kept separate in inferred_facts.ttl)", len(infer)], ["Airports / runways / segments", "%d / %d / %d" % (len(g.instances(F("Airport"))), len(g.instances(F("Runway"))), len(g.instances(F("RouteSegment"))))],
                                       ["Blocked segments / hubs (inferred)", "%d / %d" % (len(g.instances(F("BlockedSegment"))), len(g.instances(F("HubAirport"))))]], widths=[4.0, 2.6])
    para(doc, "GraphDB steps (details in GRAPHDB_GUIDE.md): (1) create repository with ruleset OWL2-RL (Optimized); (2) import Ontology/flight_dispatch_ontology.ttl and RDF_Knowledge_Graph/flight_dispatch_kg.ttl; "
              "(3) run SPARQL_Queries/rules/run_all_rules.ru once as a SPARQL Update; (4) run q01-q16 and compare with Results/expected_query_results.md; (5) take the Visual Graph screenshot (explore fdr:airport-OPIS) and add it to /Visualization.")
    para(doc, "Screenshot placeholder: [insert GraphDB import-success screenshot and Visual Graph screenshot here - these require the team's GraphDB installation].", italic=True)
    image(doc, "kg_network_overview.png", "Figure 2 - Network overview: hubs (orange), closed airport (X), blocked segments (red dashed), zones and hazards.")
    image(doc, "reroute_khi_dxb.png", "Figure 3 - Reroute example: the spatially shortest KHI-DXB leg is blocked; the rule-validated route goes via UET.", 5.6)

    doc.add_heading("6. SPARQL queries", 1)
    qfiles = sorted(f for f in os.listdir(os.path.join(ROOT, "SPARQL_Queries")) if f.endswith(".rq"))
    rows = []
    for f in qfiles:
        first = open(os.path.join(ROOT, "SPARQL_Queries", f), encoding="utf-8").read().split("\n")
        desc = [l for l in first if l.startswith("# ")][0][2:]
        q = f[:3]
        rows.append([f, desc.split("|")[1].strip() if "|" in desc else "", len(read_csv(q)) - 1])
    table(doc, ["File", "Feature demonstrated", "Expected rows"], rows, widths=[2.8, 3.0, 0.8], size=8)
    para(doc, "Feature coverage: basic pattern (q01), FILTER (q02), OPTIONAL (q03), UNION (q04, q09), aggregation COUNT/GROUP BY (q05-q07, q12, q16), multi-hop (q07, q09, q15), property paths (q08, q15), inference-dependent (q06, q09-q12, q13-q16), FILTER NOT EXISTS (q11), ASK (q13), BIND (q14). Sample results:")
    for q, n in (("q10", 6), ("q09", 5), ("q06", 6)):
        data = read_csv(q); table(doc, data[0], data[1:1 + n], size=8)
        para(doc, "(%s: first %d of %d rows; complete expected results in Results/expected_query_results.md)" % (q, min(n, len(data) - 1), len(data) - 1), italic=True, size=8.5)
    para(doc, "Verification note: the sandbox used to build this project had no SPARQL engine or internet. The .rq files are standard SPARQL 1.1 and were lint-checked (balanced braces, declared prefixes); "
              "the 'expected results' were computed by an independent Python implementation of the same logic over the reasoned graph, whose rule outputs equal a from-scratch recomputation on the CSV data. "
              "The first thing to do in GraphDB is to run each query and compare with the expected rows.", italic=True)

    doc.add_heading("7. Inference examples", 1)
    ex = open(os.path.join(RES, "inference_examples.md"), encoding="utf-8").read().split("\n")
    for line in ex[4:]:
        if line.startswith("## "):
            doc.add_heading(line[3:], 2)
        elif line.startswith("**") or line.startswith("- "):
            para(doc, line.replace("**", "").lstrip("- "), size=9.5) if not line.startswith("- ") else bullets(doc, [line[2:].replace("`", "")], size=9.5)
        elif line.strip():
            para(doc, line.replace("`", ""), size=9.5)

    doc.add_heading("8. Progress report", 1)
    table(doc, ["Area", "Status"], [
        ["Dataset + cleaning pipeline", "Complete (curated data; to be verified against original sources)"],
        ["15 competency questions + mapping", "Complete"], ["Ontology (Turtle, Protege-ready)", "Complete: %d classes, 30+ properties, 8 reasoning constructs" % len(classes)],
        ["RDF KG (>= 500 triples)", "Complete: %d A-Box triples" % len(set(ab.triples()))], ["Inference (rules R0-R6 + OWL)", "Complete; verified against independent recomputation"],
        ["16 SPARQL queries + expected results", "Complete; execution in GraphDB to be confirmed by team"],
        ["GraphDB import + screenshots", "Pending team action (needs local GraphDB)"], ["Protege open + HermiT check + screenshot", "Pending team action"],
        ["Live-demo preparation", "Pending (each member must be able to explain every part)"]], widths=[2.8, 3.8])
    para(doc, "Issues faced and how they were handled:", bold=True)
    bullets(doc, ["OWL cannot compare numbers (runway >= minimum, distance > range) -> encoded as SPARQL Update rules R0-R6 and mirrored in Python.",
                  "SPARQL 1.1 has no trigonometry -> distances and polygon intersections are precomputed in the ETL step.",
                  "Segments are undirected but stored once -> connectedTo declared symmetric; queries use UNION / direction-agnostic paths so they work with or without reasoning.",
                  "SPARQL property paths do not support {n,m} -> bounded hops written as explicit sequences.",
                  "Test-driven fixes: automated tests caught two copilot parsing bugs (plural 'hazards', 'to X from Y' order) before delivery."])
    para(doc, "Individual contributions (each member to complete):", bold=True)
    table(doc, ["Member", "Contribution"], [["Huzaifa Mudassar (24i-0050)", PH], ["Member 2", PH], ["Member 3", PH]], widths=[2.4, 4.2])
    para(doc, "Automated testing: 27 unit/integration tests (python src/tests.py) cover data integrity, ontology requirements, rule correctness against an independent computation, "
              "negative cases (inactive zone, advisory zone, low-severity hazard, expired hazard, closed airport), routing edge cases and SPARQL file linting.")

    if full:
        res = json.load(open(os.path.join(RES, "phase2_embedding_results.json")))
        doc.add_heading("9. Phase 2 - Hybrid neuro-symbolic reasoning (embeddings + rules)", 1)
        lp = res["link_prediction"]
        para(doc, "Task: predict missing route links (fd:connectedTo). A TransE model (numpy, dimension %d, %d epochs, margin ranking loss) was trained on airport-centric triples (connectivity, country, airport class, runway-length class, operational flag; segment nodes excluded to avoid leaking held-out edges). "
                  "%d of %d undirected edges (%.0f%%) were held out, keeping every airport at degree >= 2; evaluation is filtered ranking over both directions (%d queries)." % (
                      lp["dim"], lp["epochs"], lp["test_edges"], lp["train_edges"] + lp["test_edges"], 100.0 * lp["test_edges"] / (lp["train_edges"] + lp["test_edges"]), lp["metrics"]["TransE"]["queries"]))
        table(doc, ["Model", "MRR", "Hits@1", "Hits@3", "Hits@10", "Mean rank"], [[k, v["MRR"], v["Hits@1"], v["Hits@3"], v["Hits@10"], v["MeanRank"]] for k, v in lp["metrics"].items()], size=9)
        para(doc, "Honest reading: on a graph this small TransE is roughly on par with a degree-popularity baseline and slightly behind plain geographic proximity; all clearly beat random. Single seed, so differences are not statistically established. "
                  "The embedding's value here is as a candidate generator; the symbolic layer supplies correctness.")
        hy = res["hybrid_rule_filtering"]
        para(doc, "Hybrid step: for every airport and aircraft the top-%d TransE suggestions were passed through the symbolic checks (range, runway suitability, operational status, active zones/hazards). "
                  "%d of %d suggestions (%.1f%%) were rejected, each with an explicit reason; the rejection rate is highest for the range-limited ATR 72 (%.1f%%)." % (hy["k"], hy["rejected"], hy["total_suggestions"], hy["rejected_pct"], hy["by_aircraft"]["ATR72-600"]["rejected_pct"]))
        doc.add_heading("10. Phase 3 - GraphRAG flight dispatcher copilot", 1)
        para(doc, "Architecture: natural-language request -> intent and entity parsing (aircraft, airports, avoid-list, scenario) -> SPARQL shown for provenance -> retrieval and constraint-aware Dijkstra over the reasoned KG -> evidence labelled explicit/inferred -> "
                  "verbalisation (Anthropic API if ANTHROPIC_API_KEY is set, otherwise a deterministic KG verbaliser) -> re-validation guard. Routes always come from the KG search; the guard rejects any answer that mentions an airport absent from the evidence, "
                  "a route that is not approved or not independently valid, or a number that is not in the evidence, and then falls back to the KG-derived answer.")
        ev = json.load(open(os.path.join(RES, "phase3_evaluation.json")))
        table(doc, ["ID", "Question", "Result", "Detail"], [[x["id"], x["question"], "PASS" if x["pass"] else "FAIL", x["detail"]] for x in ev["kg_grounded"]], widths=[0.4, 2.7, 0.6, 2.9], size=8)
        para(doc, "KG-grounded copilot: %s correct against gold answers recomputed independently from the raw data." % ev["kg_grounded_pass"])
        table(doc, ["Simulated hallucination", "Correctly handled"], [[x["case"], "yes" if x["ok"] else "NO"] for x in ev["guard_tests"]], widths=[4.6, 2.0], size=8.5)
        para(doc, "LLM-only baseline: not run in this build (no API access offline). The script src/evaluate.py runs it when ANTHROPIC_API_KEY is set and audits every LLM route against the KG. "
                  "No LLM-only numbers are reported here because none were measured.", italic=True)
        doc.add_heading("11. Limitations and ethics", 1)
        bullets(doc, ["Academic prototype - NOT for operational flight planning. Aircraft limits are simplified (single range and minimum-runway figure; no payload, wind, fuel reserves, ETOPS or NOTAMs).",
                      "Segments are straight lines in the lon/lat plane for intersection tests, not great circles; route distances are great-circle.",
                      "Zones, hazards and scenarios are fictional; real airspace data would need authoritative AIP/NOTAM sources.",
                      "Curated airport/aircraft values must be verified against the original datasets (see Dataset/SOURCES.md).",
                      "Link-prediction results are from a small graph and a single seed."])
    os.makedirs(REP, exist_ok=True)
    name = "AI3001_Final_Project_Report.docx" if full else "AI3001_Iteration1_Report.docx"
    doc.save(os.path.join(REP, name))
    return name


if __name__ == "__main__":
    print(build(False)); print(build(True))
