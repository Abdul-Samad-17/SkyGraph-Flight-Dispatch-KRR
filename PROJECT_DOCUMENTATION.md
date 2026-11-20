# SkyGraph: Dynamic Flight Dispatch & Weather Routing Knowledge System
## Master Project Documentation & Developer Handbook

**Course:** AI-3001 Knowledge Representation & Reasoning (Fall 2026)  
**Institution:** FAST National University of Computer and Emerging Sciences (FAST-NUCES), Islamabad  
**Team Name:** SkyGraph  
**Team Roster:**
- **Huzaifa Mudassar** — `24i-0050` (Section AI-5B)
- **Abdul Samad** — `24i-0095` (Section AI-5B)
- **Shaheed Khan** — `24i-0037` (Section AI-5B)

**Official GitHub Repository:**  
[https://github.com/Abdul-Samad-17/SkyGraph-Flight-Dispatch-KRR](https://github.com/Abdul-Samad-17/SkyGraph-Flight-Dispatch-KRR)

---

## Table of Contents
1. [Executive Overview & Problem Space](#1-executive-overview--problem-space)
2. [Core Architecture & Technical Stack](#2-core-architecture--technical-stack)
3. [Complete Repository & File Structure](#3-complete-repository--file-structure)
4. [GitHub Collaboration & Team Workflow Guide](#4-github-collaboration--team-workflow-guide)
5. [Comprehensive Phase-by-Phase Breakdown of Work Completed](#5-comprehensive-phase-by-phase-breakdown-of-work-completed)
   - [Phase 1: Dataset, Ontology, Knowledge Graph, Rules & SPARQL](#phase-1-iteration-1--foundational-krr-pipeline)
   - [Phase 2: Hybrid Neuro-Symbolic Link Prediction (TransE + Rules)](#phase-2-neuro-symbolic-reasoning-transe--symbolic-filtering)
   - [Phase 3: GraphRAG Flight Dispatcher Copilot & Hallucination Guard](#phase-3-graphrag-copilot--constraint-aware-routing)
6. [Detailed Codebase Architecture (Module by Module)](#6-detailed-codebase-architecture-module-by-module)
7. [Rule Engine & Inference Traces (R0–R6)](#7-rule-engine--inference-traces-r0r6)
8. [SPARQL Query Catalog & Semantic Features](#8-sparql-query-catalog--semantic-features)
9. [Verification, Validation & Automated Testing](#9-verification-validation--automated-testing)
10. [Future Phase Upgrades & Industrial Expansion Catalog](#10-future-phase-upgrades--industrial-expansion-catalog)
11. [Command Reference & Reproduction Cheat Sheet](#11-command-reference--reproduction-cheat-sheet)

---

## 1. Executive Overview & Problem Space

Flight dispatch is a mission-critical operational process in civil aviation. Before any commercial aircraft departs, flight dispatchers must plan and validate a flight path that accounts for dynamic weather hazards (thunderstorms, severe turbulence, volcanic ash, structural icing), active restricted airspace (military corridors, naval exercise areas, prohibited zones), and physical aircraft performance envelopes (maximum fuel range, minimum runway requirements, cruise speed).

### The Flaw in Traditional Routing
Standard aviation pathfinding tools and commercial map routers rely heavily on purely spatial algorithms (such as unconstrained Dijkstra or A* on distance). When airspace is closed or extreme weather develops, spatial routers seek the shortest geometric path. This frequently leads to catastrophic dispatch failures:
- Selecting an alternate airport whose runway is too short for a heavy widebody aircraft (e.g. routing an Airbus A380 to a 2,400 m runway when it requires 3,000 m).
- Routing regional turboprops (e.g. ATR 72) over oceanic or long-haul legs that exceed their maximum fuel endurance.
- Generating detour trajectories that clip active prohibited airspace.
- Diverting emergency flights to closed or inoperative aerodromes.

### The SkyGraph Solution: Constraint Elimination Before Path Optimization
SkyGraph resolves this by enforcing a strict symbolic knowledge representation pipeline:
1. All domain facts (airports, physical runways, aircraft models, route network segments, airspace boundaries, dynamic weather polygons, in-flight emergency scenarios) are structured into a formal **Resource Description Framework (RDF)** Knowledge Graph.
2. An expressive **Web Ontology Language (OWL 2 RL)** ontology defines the domain taxonomy, properties, and constraints.
3. A forward-chaining **symbolic inference engine** executes OWL axioms and seven custom production dispatch rules (**R0 through R6**).
4. The rules evaluate numeric thresholds, operational statuses, and spatial intersections, dynamically deriving facts such as `:isSuitableFor`, `:blockedBy`, `:exceedsRangeOf`, and `:isFeasibleFor`.
5. Pathfinding (Dijkstra) is executed strictly on the **rule-derived feasible subgraph**. Infeasible legs and airports are completely eliminated before any path calculation begins.
6. Every recommendation includes an auditable derivation trace, backed by a natural-language **GraphRAG Copilot** with an anti-hallucination verification guard.

---

## 2. Core Architecture & Technical Stack

SkyGraph was engineered with strict software engineering discipline. The core system runs with **zero external dependencies** using standard Python 3.9+ libraries.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION & ETL LAYER                      │
│   airports.csv | runways.csv | aircraft.csv | segments.csv             │
│   zones.csv | hazards.csv | scenarios.csv                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Haversine & Ray-Casting (src/geometry.py)
┌───────────────────────────────────▼────────────────────────────────────┐
│                  KNOWLEDGE MODEL & GRAPH STORAGE LAYER                 │
│   Ontology (T-Box): Ontology/flight_dispatch_ontology.ttl              │
│   A-Box Graph: RDF_Knowledge_Graph/flight_dispatch_kg.ttl (2,105 triples)│
│   MiniRDF Triple Store (src/minirdf.py) + GraphDB OWL2-RL Repository   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Forward-Chaining Inference
┌───────────────────────────────────▼────────────────────────────────────┐
│                    SYMBOLIC REASONING ENGINE (R0 - R6)                 │
│   src/reasoner.py + SPARQL_Queries/rules/run_all_rules.ru              │
│   Derives 3,048 inferred facts: suitability, blockages, feasibility    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Feasible Subgraph (:isFeasibleFor)
┌───────────────────────────────────▼────────────────────────────────────┐
│                 CONSTRAINT-AWARE ROUTING & COPILOT LAYER               │
│   - Dijkstra Routing Engine (src/routing.py)                           │
│   - GraphRAG Dispatcher Copilot (src/copilot.py)                       │
│   - Anti-Hallucination Re-validation Guard                             │
│   - TransE Neuro-Symbolic Link Prediction (src/embeddings.py)          │
└────────────────────────────────────────────────────────────────────────┘
```

### Technology Matrix
- **Core Platform:** Python 3.9+ (Standard Library: `math`, `heapq`, `re`, `json`, `csv`, `collections`, `urllib`).
- **Knowledge Representation:** W3C RDF 1.1 (Turtle format), W3C OWL 2 (RL Profile), W3C SPARQL 1.1 Query & Update.
- **Ontology & Graph Stores:** Ontotext GraphDB Free/SE, Protégé 5.6+ with HermiT / Pellet reasoners.
- **Machine Learning & Math:** Pure `numpy` (TransE knowledge graph embeddings, vector ranking loss).
- **Visualization:** `matplotlib` (network overview maps, reroute diagrams, ontology schema).
- **Documentation & Publishing:** LaTeX (IEEEtran double-column conference template) and `python-docx` (Word reports).

---

## 3. Complete Repository & File Structure

Below is the definitive file manifest of the repository. Every file has an exact operational role.

```
AI3001_Final_Project/
├── .gitignore                                 # Git ignore file (caches, virtualenvs, OS artifacts)
├── GRAPHDB_GUIDE.md                           # Step-by-step instructions for loading KG into Ontotext GraphDB
├── PROTEGE_GUIDE.md                           # Step-by-step instructions for verifying ontology in Protégé
├── README.md                                  # Repository landing page with quickstart, team roster, and phase tables
│
├── Dataset/                                   # Curated aviation operational datasets
│   ├── aircraft.csv                           # 6 aircraft performance envelopes (range, min runway, cruise speed)
│   ├── airports.csv                           # 38 aerodromes (ICAO, IATA, lat/lon, operational flag, category)
│   ├── countries.csv                          # Country mappings (ISO code, full name)
│   ├── hazards.csv                            # 5 weather hazard polygons (type, severity 1-5, active flag)
│   ├── runways.csv                            # 60 physical runways with airport code, designator, length in meters
│   ├── scenarios.csv                          # 6 emergency diversion scenarios (position, aircraft, remaining range)
│   ├── segments.csv                           # 153 undirected airway segments between airport pairs
│   ├── SOURCES.md                             # Dataset provenance, OpenAP/OurAirports alignment, curation notes
│   └── zones.csv                              # 4 airspace boundary polygons (restricted, prohibited, advisory)
│
├── Ontology/                                  # Knowledge Schema (T-Box)
│   └── flight_dispatch_ontology.ttl           # OWL 2 RL ontology in Turtle syntax (19 classes, 38 properties)
│
├── RDF_Knowledge_Graph/                       # Instance Data (A-Box) & Inferred Knowledge
│   ├── flight_dispatch_kg.ttl                 # 2,105 explicit RDF assertions generated by ETL
│   ├── inferred_facts.ttl                     # 3,048 materialized inferred triples from reasoner
│   └── segment_geometry.json                  # Intermediate precomputed segment lengths and polygon intersections
│
├── Report/                                    # Formal project deliverables
│   ├── AI3001_Final_Project_Report.docx       # Complete Word report covering Phases 1, 2, and 3
│   ├── AI3001_Iteration1_Report.docx          # Official Iteration 1 Word progress report
│   ├── AI3001_Iteration1_Report.tex           # Formal IEEE-format double-column LaTeX report
│   └── KRR_Project.pdf                        # Final compiled PDF project report (submitted)
│
├── Results/                                   # Empirical outputs, evaluations, and query dumps
│   ├── copilot_demo.md                        # Complete transcript of GraphRAG copilot sessions across 8 queries
│   ├── cq_mapping.csv                         # Tabular Competency Question to SPARQL/reasoning mapping
│   ├── cq_mapping.md                          # Markdown Competency Question mapping with question taxonomy
│   ├── expected_query_results.md              # Complete textual reference outputs for queries q01 through q16
│   ├── graph_statistics.md                    # Detailed graph metrics (triple counts, degree distributions, classes)
│   ├── inference_examples.md                  # Comprehensive traces for all 7 inference rules + 5 negative checks
│   ├── phase2_embedding_results.json          # TransE training metrics, Hits@K, and symbolic filter rejection rates
│   ├── phase3_evaluation.json                 # JSON evaluation results (12/12 passing against gold standard)
│   ├── phase3_evaluation.md                   # Evaluation report analyzing copilot accuracy and guard resilience
│   └── csv/                                   # Individual CSV output files for every SPARQL query
│       ├── q01.csv ... q16.csv                # 16 separate CSV result files matching SPARQL queries
│
├── SPARQL_Queries/                            # Executable SPARQL query suite
│   ├── q01_airports_in_pakistan.rq            # Basic Graph Pattern (BGP) matching
│   ├── q02_long_runways_filter.rq             # Numeric threshold filtering (runways >= 3500m)
│   ├── q03_active_hazards_optional.rq         # OPTIONAL pattern join with active hazard filtering
│   ├── q04_neighbours_union.rq                # Bidirectional connectivity via UNION
│   ├── q05_airports_per_country_aggregation.rq# Aggregation (COUNT, GROUP BY) over aerodromes
│   ├── q06_blocked_segments_per_cause.rq      # Inferred blockage aggregation by cause entity (Rule R2)
│   ├── q07_countries_behind_hazard_multihop.rq# 4-hop join: Hazard -> Segment -> Airport -> Country
│   ├── q08_reachability_property_path.rq      # Transitive network reachability via property paths (+ operator)
│   ├── q09_two_leg_feasible_routes.rq         # Two-hop route search over inferred feasible subgraph (Rule R4)
│   ├── q10_diversion_candidates_s1.rq         # Emergency diversion candidates ranked by distance (Rule R5)
│   ├── q11_atr_only_airports.rq               # Negation reasoning via FILTER NOT EXISTS
│   ├── q12_suitable_airports_per_aircraft.rq  # Suitability aggregation per aircraft class (Rules R0, R1)
│   ├── q13_ask_direct_feasibility.rq          # Boolean feasibility verification using ASK query
│   ├── q14_explain_blocked_segment.rq         # Explainability query returning cause entity and label
│   ├── q15_two_hop_suitable_airports.rq       # Two-hop sequence path over suitable destination aerodromes
│   ├── q16_hub_airports.rq                    # Hub aerodrome retrieval based on inferred degree (Rule R6)
│   └── rules/                                 # Forward-chaining rule scripts
│       ├── README.md                          # Guide for executing rules inside GraphDB
│       └── run_all_rules.ru                   # Unified SPARQL 1.1 Update script implementing R0-R6
│
├── src/                                       # Core Python source code
│   ├── build_kg.py                            # ETL script: transforms CSVs into RDF Turtle graph
│   ├── build_report.py                        # Compiles live project data into Word reports
│   ├── copilot.py                             # GraphRAG dispatcher copilot and anti-hallucination guard
│   ├── demo_transcripts.py                    # Generates benchmark copilot transcripts
│   ├── embeddings.py                          # TransE link prediction model + symbolic rule filter
│   ├── evaluate.py                            # Evaluation harness comparing copilot against gold standard
│   ├── expected_results.py                    # Independent computation of expected query row counts
│   ├── generate_reports.py                    # Helper data definitions for report generation
│   ├── geometry.py                            # Haversine distance and 2D segment-polygon ray casting
│   ├── independent_check.py                   # Ground-truth mathematical verifier (calculates directly from CSVs)
│   ├── llm.py                                 # Optional LLM connector (Anthropic Claude API client)
│   ├── make_dataset.py                        # Dataset validator, bounding filter, and synthetic hazard generator
│   ├── make_visuals.py                        # Matplotlib visualizer for route maps and rerouting diagrams
│   ├── minirdf.py                             # Custom dependency-free RDF Turtle parser and triple store
│   ├── reasoner.py                            # Forward-chaining OWL 2 RL and dispatch rule engine (R0-R6)
│   ├── routing.py                             # Constraint-aware Dijkstra router over feasible subgraph
│   ├── run_everything.py                      # Master pipeline runner: regenerates all artifacts from CSVs
│   └── tests.py                               # Automated test harness containing 27 unit/integration tests
│
└── Visualization/                             # Visual assets
    ├── kg_network_overview.png                # Full route network map with hubs, closed airports, and hazards
    ├── ontology_schema.png                    # Complete visual diagram of OWL ontology classes and properties
    ├── reroute_isb_lhr.png                    # Visual reroute diagram: Islamabad to London for Airbus A320
    └── reroute_khi_dxb.png                    # Visual reroute diagram: Karachi to Dubai for Boeing 737
```

---

## 4. GitHub Collaboration & Team Workflow Guide

All three team members must collaborate directly on the shared repository. Follow these exact instructions to ensure clean version control.

### 4.1 Initial Setup for Team Members (Huzaifa & Shaheed)
1. **Accept GitHub Invite:** Ensure you have accepted the collaborator invitation sent to your GitHub account by Abdul Samad.
2. **Clone the Repository:** Open your terminal or Command Prompt and clone the repo:
   ```bash
   git clone https://github.com/Abdul-Samad-17/SkyGraph-Flight-Dispatch-KRR.git
   cd SkyGraph-Flight-Dispatch-KRR
   ```
3. **Configure Your Git Identity:**
   ```bash
   git config user.name "Your Full Name"
   git config user.email "your_student_email@nu.edu.pk"
   ```
4. **Setup Python Environment:**
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate

   # Install optional libraries (core engine needs none, but these are for visuals/embeddings/reports):
   pip install numpy matplotlib python-docx
   ```
5. **Verify Local Setup:**
   Run the test suite to ensure the environment is working properly:
   ```bash
   python src/tests.py
   ```
   You should see: `Ran 27 tests in ... OK`.

### 4.2 Standard Daily Development Workflow
To avoid overwriting each other's work or causing git conflicts, follow the **branch-and-pull** workflow:

1. **Always Pull Latest Changes Before Starting:**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Create a Dedicated Feature Branch:**
   ```bash
   # Examples:
   git checkout -b feature/phase2-gnn
   git checkout -b feature/copilot-enhancements
   git checkout -b feature/real-weather-feed
   ```
3. **Make Edits & Test Locally:**
   Never commit broken code. Always run the automated test suite before staging files:
   ```bash
   python src/tests.py
   ```
4. **Stage and Commit with Meaningful Messages:**
   Use standard commit prefixes:
   - `feat:` for new capabilities or algorithms
   - `fix:` for bug fixes
   - `docs:` for documentation or report updates
   - `test:` for adding or updating unit tests
   - `refactor:` for code cleanup without changing logic

   ```bash
   git add src/your_updated_file.py
   git commit -m "feat: implement altitude bounding in segment feasibility check"
   ```
5. **Push Your Branch to GitHub:**
   ```bash
   git push origin feature/your-branch-name
   ```
6. **Open a Pull Request (PR):**
   Go to the GitHub repository page, click **Compare & pull request**, describe your changes, and have another team member review and merge it into `main`.

---

## 5. Comprehensive Phase-by-Phase Breakdown of Work Completed

### Phase 1 (Iteration 1) — Foundational KRR Pipeline
**Status:** 100% Completed, Verified & Submitted.

1. **Competency Questions:** Formulated 15 formal CQs categorized into basic retrieval, numeric filtering, country-level aggregation, multi-hop joins, transitive reachability, non-monotonic negation, emergency diversion ranking, explainability, and hub classification.
2. **Ontology (T-Box):** Designed in Protégé and serialized in Turtle syntax. Implemented 19 classes, 18 object properties, 20 datatype properties, disjointness axioms across all primary entities, inverse properties (`hasRunway`/`runwayOf`), symmetry (`connectedTo`), transitivity (`networkReachable`), and strict cardinality restrictions.
3. **ETL & Knowledge Graph (A-Box):** Automated generation of 2,105 explicit RDF assertions from 8 relational CSV files. Computed spherical great-circle distances for all 153 flight segments. Precalculated 2D polygon intersection geometries for 4 airspace zones and 5 weather hazard polygons. Reified scenario distances into 72 `PositionDistance` facts.
4. **Symbolic Inference Engine:** Implemented forward-chaining reasoning covering OWL 2 RL schema rules and seven domain dispatch rules (R0–R6). Inferred 3,048 new facts with full provenance tracking.
5. **SPARQL Validation Suite:** Executed 16 SPARQL queries (`q01.rq` to `q16.rq`), verifying every row against ground-truth recomputations and dumping individual CSV results.
6. **GraphDB Integration:** Verified repository initialization under the `OWL2-RL (Optimized)` profile, confirmed execution of `run_all_rules.ru`, and verified visual graph exploration.
7. **Reports & Guides:** Authored the official progress report in IEEE two-column LaTeX format (`AI3001_Iteration1_Report.tex`), compiled the final submission PDF (`KRR_Project.pdf`), and created detailed guides for GraphDB and Protégé.

---

### Phase 2: Neuro-Symbolic Reasoning (TransE + Symbolic Filtering)
**Status:** Completed Prototype with Empirical Results (`src/embeddings.py`, `Results/phase2_embedding_results.json`).

Phase 2 implements a hybrid neuro-symbolic link prediction pipeline:
1. **Motivation:** Pure knowledge graphs often have missing edges (unasserted direct flight routes). Pure machine learning models (like TransE) can predict missing links based on airport embeddings, but they are "blind" to physical constraints—frequently recommending links that violate aircraft range or cross restricted airspace.
2. **Dataset Construction:** Airport-centric triples are extracted from the graph (aerodrome connectivity, country location, airport category, runway length class, and operational flag). Flight segment reification nodes are deliberately excluded to prevent edge leakage.
3. **Edge Splitting:** 20% of undirected edges are held out as a test set, while ensuring that every airport maintains a degree $\ge 2$ in the training graph.
4. **TransE Implementation:** Pure NumPy implementation of TransE with margin ranking loss:
   $$\mathcal{L} = \max(0, \gamma + d(h + r, t) - d(h' + r, t'))$$
   Trained for 300 epochs with embedding dimension $d=32$, margin $\gamma=1.0$, learning rate $\eta=0.02$, and batch size 128.
5. **Evaluation Against Baselines:** Tested in filtered ranking mode against Popularity (degree), Geographic Proximity (Haversine), and Random baselines.
   - TransE achieves **Mean Reciprocal Rank (MRR) of 0.288**, **Hits@1 of 18.0%**, **Hits@3 of 32.8%**, and **Hits@10 of 49.2%**.
6. **Symbolic Guard Filter:** Every candidate link predicted by TransE is passed through the symbolic rule engine (`symbolic_check()`), which evaluates:
   - Does the distance exceed the aircraft maximum range?
   - Is either aerodrome's runway shorter than required?
   - Is either airport inoperative?
   - Does the direct vector cross an active restricted zone or severe weather hazard?
7. **Empirical Finding:** Across all airport-aircraft pairs, the symbolic layer rejected **60.3% of TransE's top-5 suggestions**, with explicit causal explanations for every rejection. The rejection rate was highest for range-constrained aircraft (82.1% for the ATR 72-600), proving that machine learning candidate generation must be gated by symbolic constraints.

---

### Phase 3: GraphRAG Copilot & Constraint-Aware Routing
**Status:** Completed Prototype with Evaluation Suite (`src/copilot.py`, `src/routing.py`, `src/evaluate.py`).

Phase 3 builds a natural-language flight dispatch assistant that bridges conversational interaction with deterministic knowledge graph reasoning:
1. **Interactive & CLI Copilot:** Supports natural language dispatch queries, e.g.:
   - *"Find an alternate route from Karachi to Dubai for a B737-800 avoiding Restricted Zone Alpha"*
   - *"Diversion candidates for scenario S1"*
   - *"Why can't an A380 fly Karachi to Dubai direct?"*
   - *"Which airports can handle an A380?"*
2. **Intent & Entity Parsing:** Regular-expression and alias parsing maps natural-language queries to specific aircraft types, airport codes (ICAO/IATA/city names), avoidance targets (named storms, restricted zones), and diversion scenarios.
3. **Query Provenance:** Automatically synthesizes and displays the exact SPARQL query used to retrieve evidence, giving dispatchers complete transparency.
4. **Constraint-Aware Dijkstra Router:** Computes optimal multi-hop paths strictly over the feasible subgraph derived by Rule R4. If the spatially shortest path is blocked, the engine explains exactly why the direct path was rejected and provides feasible alternatives.
5. **Anti-Hallucination Re-validation Guard (`validate_text`):**
   - Verifies that every airport code in the output exists in the retrieved evidence.
   - Verifies that every proposed route is either produced by the KG pathfinder or independently passes feasibility validation.
   - Audits numerical figures (distances, runway lengths) against retrieved evidence.
   - If an LLM verbalization fails validation, the system automatically falls back to the deterministic knowledge graph answer.
6. **Evaluation Results:** 12 out of 12 benchmark questions passed against independent ground-truth Python calculations (`Results/phase3_evaluation.md`). The guard successfully caught 100% of simulated hallucinations (invented distances, unsupported airports, and range violations).

---

## 6. Detailed Codebase Architecture (Module by Module)

Every script in `src/` has a well-defined boundary:

### `src/minirdf.py`
A lightweight, dependency-free RDF engine:
- **`_Parser`:** Recursive-descent parser supporting W3C Turtle subset (`@prefix`, `PREFIX`, prefixed names, IRIs, predicate/object lists, blank nodes, typed/plain literals, booleans, and numbers).
- **`Graph`:** Indexed triple store maintaining three hash maps: `spo` (subject-predicate-object), `pos` (predicate-object-subject), and `osp` (object-subject-predicate). Provides fast pattern matching, instance lookups, and property traversals.
- **`Serializer`:** Formats triple sets back into clean, sorted Turtle syntax with automatic prefix abbreviation.

### `src/geometry.py`
Pure-math geospatial algorithms:
- **`haversine_km(lat1, lon1, lat2, lon2)`:** Calculates spherical distance across the Earth ($R=6371.0\text{ km}$).
- **`segments_intersect(p1, p2, p3, p4)`:** Evaluates 2D closed line-segment intersection using orientation determinants and collinear bounding box checks.
- **`point_in_polygon(pt, poly)`:** Ray-casting algorithm to determine if a point lies within a polygon.
- **`segment_crosses_polygon(p1, p2, poly)`:** Checks if a route segment touches or crosses any edge of a polygon or has endpoints inside it.

### `src/make_dataset.py`
Data generation and validation harness:
- Defines the 38 airports, 60 runways, 6 aircraft models, 153 route segments, 4 airspace zones, 5 weather hazards, and 6 diversion scenarios.
- Validates data integrity: checks for self-loops, duplicate reversed segments, and ensures every referenced airport exists.

### `src/build_kg.py`
ETL pipeline:
- Reads CSVs from `Dataset/`, derives Haversine distances and polygon intersections, asserts explicit facts, and serializes `RDF_Knowledge_Graph/flight_dispatch_kg.ttl`.
- Saves geometric intersection metadata into `segment_geometry.json`.

### `src/reasoner.py`
The inference heart of SkyGraph:
- **`owl_pass()`:** Evaluates RDFS and OWL 2 RL rules (transitive closure of `subClassOf` and `subPropertyOf`, property propagation, `inverseOf` derivation, `SymmetricProperty` symmetry, `TransitiveProperty` chaining, and `rdfs:domain`/`rdfs:range` typing).
- **`rules_pass()`:** Evaluates rules R0 through R6.
- **`validate()`:** Audits the graph for logical violations (disjointness breaches, missing runways, invalid cardinalities).
- **`write_inferred()`:** Materializes all derived triples into `RDF_Knowledge_Graph/inferred_facts.ttl`.

### `src/routing.py`
Pathfinding and route validation:
- **`DispatchKG`:** High-level wrapper over the reasoned graph, caching airport lookups, aircraft envelopes, and feasible segments.
- **`_dijkstra()`:** Priority-queue shortest path search over specified edge sets.
- **`route()`:** Computes the best feasible route, generates alternative paths by edge-banning, compares against the unconstrained spatial path, and records explanations for rejected direct legs.
- **`validate_route()`:** Independent auditor verifying that every leg of a proposed route is feasible.
- **`diversions()`:** Finds all suitable, operational airports within remaining range for an in-flight aircraft.

### `src/copilot.py`
Natural language interface:
- **`Copilot`:** Parses natural language queries, identifies aircraft and airport entities, constructs provenance SPARQL, executes routing or diversion retrieval, generates human-readable answers, and applies the `validate_text` guard.
- Provides interactive shell (`python src/copilot.py -i`) and JSON output modes.

### `src/embeddings.py`
Neuro-symbolic link prediction:
- Contains the `TransE` class, dataset construction, training loop, evaluation metrics (MRR, Hits@K), and the `symbolic_check()` gate.

### `src/evaluate.py`
Automated evaluation runner:
- Benchmarks copilot queries against `independent_check.py` gold-standard results.
- Runs simulated hallucination tests against the `validate_text` guard.
- Outputs `Results/phase3_evaluation.json` and `Results/phase3_evaluation.md`.

### `src/independent_check.py`
Zero-RDF ground truth:
- Implements direct Python calculation from raw CSV data without using any RDF or rule engines. Serves as an independent verifier for all test assertions.

### `src/tests.py`
Unit and integration test suite:
- 27 unit tests verifying data integrity, ontology completeness, rule correctness, negative edge cases, routing accuracy, and SPARQL query syntax.

---

## 7. Rule Engine & Inference Traces (R0–R6)

The symbolic engine implements seven domain-specific production rules:

| Rule | Name | Premise / Logical Condition | Consequent / Derived Fact |
|---|---|---|---|
| **R0** | Longest Runway | For each airport, find $\max(\text{runwayLengthM})$ across all physical runways. | `(airport, fd:longestRunwayM, max_length)` |
| **R1** | Runway Suitability | `longestRunwayM >= aircraft.minRunwayM` | `(airport, fd:isSuitableFor, aircraft)` |
| **R2** | Airspace & Hazard Blocking | Segment crosses active `RestrictedZone` OR active `WeatherHazard` with `severity >= 3`. | `(segment, fd:blockedBy, blocker)` and `segment a fd:BlockedSegment` |
| **R3** | Range Exceedance | `segment.distanceKm > aircraft.rangeKm` | `(segment, fd:exceedsRangeOf, aircraft)` |
| **R4** | Segment Feasibility | NOT blocked, within range, and both endpoint airports are operational and suitable. | `(segment, fd:isFeasibleFor, aircraft)` |
| **R5** | Diversion Candidate | Scenario distance $\le$ remaining range, airport operational, and airport suitable. | `(scenario, fd:hasDiversionCandidate, airport)` |
| **R6** | Hub Classification | Airport has incident route segments $\ge 14$. | `airport a fd:HubAirport` |

### Provenance Tracking
Every inferred triple in `src/reasoner.py` stores its derivation history:
```python
self.deriv[triple] = (rule_id, human_readable_description, [premise_triples])
```
This enables the copilot to explain not just *what* was decided, but *why* (e.g. citing Rule R2 when a flight is rerouted around active naval exercises).

---

## 8. SPARQL Query Catalog & Semantic Features

The repository contains 16 formal SPARQL queries in `SPARQL_Queries/`:

| Query File | Target Competency Question | Semantic Features Tested | Expected Rows |
|---|---|---|---|
| `q01_airports_in_pakistan.rq` | CQ1: Pakistani airports & coordinates | Basic Graph Pattern (BGP), variable projection | 10 rows |
| `q02_long_runways_filter.rq` | CQ2: Runways $\ge 3,500\text{ m}$ | Numeric `FILTER (?length >= 3500)` | 37 rows |
| `q03_active_hazards_optional.rq` | CQ12: Weather hazards & affected legs | `OPTIONAL`, boolean `FILTER (?active = true)` | 32 rows |
| `q04_neighbours_union.rq` | CQ9: Direct connections from Islamabad | Bidirectional `UNION` pattern | 23 rows |
| `q05_airports_per_country_aggregation.rq` | CQ3: Airport counts per nation | `COUNT(?airport)`, `GROUP BY`, range typing | 21 rows |
| `q06_blocked_segments_per_cause.rq` | CQ5: Inferred segment blockages | Rule R2 inference, `COUNT(?segment)`, `ORDER BY DESC` | 5 rows |
| `q07_countries_behind_hazard_multihop.rq` | CQ6: Nations affected by hazards | 4-hop join: Hazard $\to$ Segment $\to$ Airport $\to$ Country | 14 rows |
| `q08_reachability_property_path.rq` | CQ8: Full network reachability | Arbitrary-length property path `(connectsFrom\|connectsTo)+` | 37 rows |
| `q09_two_leg_feasible_routes.rq` | CQ7: Feasible two-leg paths (ISB-DXB) | Two-hop join over inferred `fd:isFeasibleFor` (R4) | 30 rows |
| `q10_diversion_candidates_s1.rq` | CQ10: Emergency diversions (Scenario S1)| Rule R5 inference, distance ordering | 18 rows |
| `q11_atr_only_airports.rq` | CQ11: Airports taking ATR 72 but not A320 | Non-monotonic negation via `FILTER NOT EXISTS` | 2 rows |
| `q12_suitable_airports_per_aircraft.rq` | CQ4: Suitable airports per fleet type | Rules R0, R1 inference + aggregation | 6 rows |
| `q13_ask_direct_feasibility.rq` | CQ13: Feasibility check (KHI-DXB, B737) | Boolean `ASK` query evaluating Rule R4 | `true` / `false` |
| `q14_explain_blocked_segment.rq` | CQ13: Explain cause of blockage | Explainability using `UNION` and `BIND` | 1 row |
| `q15_two_hop_suitable_airports.rq` | CQ9: Two-hop paths to suitable airports | Sequence property path `(connectedTo/connectedTo)` | 32 rows |
| `q16_hub_airports.rq` | CQ15: Hub aerodrome identification | Rule R6 inference querying `fd:HubAirport` | 5 rows |

---

## 9. Verification, Validation & Automated Testing

### 9.1 Automated Test Suite (`src/tests.py`)
SkyGraph includes an automated test harness covering 27 test cases:
- **`DataIntegrityTests`:** Validates that all 38 airports, 60 runways, 6 aircraft types, and 153 segments are structurally sound, coordinates fall within legitimate geographic bounds, and no duplicate segment keys exist.
- **`OntologyRequirementTests`:** Verifies that the ontology contains at least 10 classes, 8 properties, and 3 reasoning constructs (satisfying course rubrics).
- **`ReasoningRuleTests`:** Tests rules R0 through R6 against ground-truth recomputations.
- **`NegativeReasoningTests`:** Verifies that rules do **not** fire on inactive zones, advisory airspace, minor weather (severity < 3), expired hazards, or closed airports.
- **`RoutingTests`:** Verifies constraint-aware routing between Karachi and Dubai, and Islamabad and London.
- **`SPARQLQueryLintTests`:** Verifies that all 16 `.rq` files and the rule `.ru` file have declared prefixes and balanced curly braces.

### 9.2 Independent Verification (`src/independent_check.py`)
To prevent circular logic, `src/independent_check.py` independently computes runway suitability, distance thresholds, and polygon crossings using raw CSV data without invoking any RDF libraries. The reasoner's output matches this independent calculation with 100% agreement.

---

## 10. Future Phase Upgrades & Industrial Expansion Catalog

Based on our architectural research into commercial systems (**Lufthansa Systems Lido Flight 4D**, **Jeppesen OnSight**, **NAVBLUE N-FP**, **EUROCONTROL SWIM**, and **NASA ATMONTO**), the following upgrade catalog is designed for subsequent project phases:

### Upgrade A: 4D Trajectory & Atmospheric Modeling
- **Current State:** 2D great-circle distances on the spherical surface.
- **Upgrade:** Model altitude flight levels (FL) and temporal validity windows using the **W3C Time Ontology**.
- **Impact:** Allows aircraft to fly *over* low-altitude weather hazards (e.g. cruising at FL380 over a storm capped at FL250) or schedule passage through restricted military corridors that open after 18:00 UTC.

### Upgrade B: Airway Network & Navigation Fixes
- **Current State:** Direct airport-to-airport segments.
- **Upgrade:** Introduce `fd:Airway`, `fd:NavFix` (RNAV/RNP waypoints), `fd:SID` (Standard Instrument Departure), and `fd:STAR` (Standard Terminal Arrival Route).
- **Impact:** Reflects realistic air traffic management where flights follow structured high-altitude airway corridors rather than direct vectors.

### Upgrade C: Real-Time Open Data Ingestion
- **Current State:** Curated static CSV datasets.
- **Upgrade:** Connect live REST/API ingestion:
  - **OpenSky Network API:** Live ADS-B aircraft positions.
  - **AviationWeather.gov:** Live METAR and SIGMET feeds in IWXXM XML.
  - **Digital NOTAM Engine:** Ingestion of dynamic airspace notices into AIXM 5.1 structures.

### Upgrade D: Regulatory & Operational Constraints (ETOPS/EDTO & MEL)
- **Current State:** Static runway length and single maximum fuel range.
- **Upgrade:**
  - Model **ETOPS (Extended-range Twin-engine Operational Performance Standards)**: ensuring twin-engine jets remain within 60/120/180 minutes single-engine flying time from an adequate diversion aerodrome.
  - Model **MEL (Minimum Equipment List)**: temporary equipment degradations (e.g. inoperative auxiliary power unit or anti-icing system) that alter aircraft dispatch limits.

### Upgrade E: Advanced Graph Neural Networks (GNN)
- **Current State:** TransE vector embeddings on 38 airport nodes.
- **Upgrade:** Migrate to **Relational Graph Convolutional Networks (R-GCN)** or **Graph Attention Networks (GAT)** to support inductive reasoning over newly added aerodromes without complete retraining.

### Upgrade F: Interactive Geospatial Web Dashboard
- **Current State:** Terminal CLI and static Matplotlib PNG figures.
- **Upgrade:** A web dashboard (built with Streamlit, Dash, or React + Leaflet/Mapbox) rendering:
  - Real-time route ribbons over aeronautical dark maps.
  - Dynamic hazard polygons color-coded by severity.
  - Interactive flight dispatch queries with point-and-click diversion analysis.

---

## 11. Command Reference & Reproduction Cheat Sheet

All commands are executed from the repository root:

```bash
# 1. Regenerate all project artifacts from raw CSV datasets:
python src/run_everything.py

# 2. Run the complete automated test harness (27 tests):
python src/tests.py

# 3. Query the GraphRAG Copilot (offline mode, no LLM required):
python src/copilot.py --no-llm "Find an alternate route from Karachi to Dubai for a B737-800"

# 4. Start an interactive conversational copilot session:
python src/copilot.py -i

# 5. Query copilot with LLM verbalization (requires Anthropic API key):
ANTHROPIC_API_KEY="your-api-key" python src/copilot.py "Why can't an A380 fly Karachi to Dubai direct?"

# 6. Run Phase 2 TransE embedding training & rule filtering:
python src/embeddings.py

# 7. Run Phase 3 copilot evaluation benchmark:
python src/evaluate.py

# 8. Rebuild Word project reports:
python src/build_report.py
```

---
*SkyGraph Project — AI-3001 Knowledge Representation & Reasoning — Fall 2026*
