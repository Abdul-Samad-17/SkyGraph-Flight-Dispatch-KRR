# ✈ SkyGraph — Dynamic Flight Dispatch & Weather Routing Knowledge System

> AI-3001 Knowledge Representation & Reasoning — Course Project

An academic prototype that builds a knowledge graph, ontology, and inference rules to eliminate infeasible airports and route segments (aircraft range, runway length, restricted airspace, weather hazards) before any path is optimised. Features explainable, independently re-validated routes and a GraphRAG copilot for natural-language dispatch queries.

---

## Team SkyGraph

| Name | Roll No. |
|---|---|
| Huzaifa Mudassar | 24i-0050 |
| Abdul Samad | 24i-0095 |
| Shaheed Khan | 24i-0037 |

---

## Project Phases

| Phase | Deliverable | Key Artifacts |
|---|---|---|
| **Iteration 1** | Dataset, 15 competency questions, OWL ontology, RDF Knowledge Graph (2,105 A-Box triples), GraphDB guide, 16 SPARQL queries, inference rules (R0–R6 + OWL), visualisations, progress report | `Dataset/` `Ontology/` `RDF_Knowledge_Graph/` `SPARQL_Queries/` `Results/` `Visualization/` `Report/` |
| **Phase 2** | Hybrid neuro-symbolic reasoning — TransE link prediction with symbolic rule filtering | `src/embeddings.py` `Results/phase2_embedding_results.json` |
| **Phase 3** | GraphRAG dispatcher copilot, constraint-aware routing, re-validation guard, evaluation | `src/copilot.py` `src/routing.py` `src/evaluate.py` `Results/phase3_evaluation.md` `Results/copilot_demo.md` |

---

## Quick Start

**Requirements:** Python 3.9+, `numpy`, `matplotlib` (optional: `python-docx` for report generation)

```bash
# Rebuild every artifact from the curated CSV dataset
python src/run_everything.py

# Run the automated test suite (27 tests)
python src/tests.py

# Query the copilot (offline, no LLM needed)
python src/copilot.py --no-llm "Find an alternate route from Karachi to Dubai for a B737-800"

# Interactive mode
python src/copilot.py -i

# With optional LLM verbalisation
ANTHROPIC_API_KEY=<key> python src/copilot.py "Why can't an A380 fly Karachi to Dubai direct?"
```

The core system (parser, reasoner, routing, copilot) is **dependency-free standard-library Python**.

---

## Repository Layout

```
├── Dataset/                  Curated CSV files (airports, aircraft, segments, hazards, etc.)
├── Ontology/                 T-Box — OWL ontology in Turtle format
├── RDF_Knowledge_Graph/      A-Box — populated knowledge graph + inferred facts
├── SPARQL_Queries/           16 SPARQL queries + inference rules
│   └── rules/                SPARQL Update rules (R0–R6)
├── Results/                  Query outputs, CQ mapping, statistics, Phase 2/3 results
│   └── csv/                  Per-query CSV result files
├── Visualization/            Knowledge graph and routing visualisations (PNG)
├── Report/                   Project reports (Iteration 1 + Final)
├── src/                      All source code
│   ├── build_kg.py           RDF knowledge graph builder
│   ├── reasoner.py           Rule-based inference engine
│   ├── routing.py            Constraint-aware route planner
│   ├── copilot.py            GraphRAG dispatcher copilot
│   ├── embeddings.py         TransE knowledge graph embeddings
│   ├── evaluate.py           Evaluation framework
│   └── ...                   Supporting modules
├── GRAPHDB_GUIDE.md          Guide for loading the KG in GraphDB
└── PROTEGE_GUIDE.md          Guide for viewing the ontology in Protege
```

---

## Key Features

- **OWL Ontology** with classes for Airports, Aircraft, RouteSegments, Hazards, RestrictedZones, and Scenarios
- **Rule-based Inference** (R0–R6): suitability checks, blockage detection, feasibility reasoning, diversion candidate identification, hub classification
- **16 SPARQL Queries** covering basic graph patterns, FILTER, OPTIONAL, UNION, aggregation, multi-hop, property paths, subqueries, and ASK
- **Constraint-aware Routing** using Dijkstra over the feasible subgraph with re-validation
- **GraphRAG Copilot** that answers natural-language dispatch questions with full evidence and SPARQL provenance
- **Re-validation Guard** that catches hallucinated routes, invented distances, and infeasible legs
- **TransE Embeddings** for link prediction filtered through symbolic rules

---

## Tools & Technologies

- Python (core system)
- RDF / OWL / SPARQL 1.1
- GraphDB (triple store)
- Protege (ontology editor)
- Turtle (.ttl) serialisation
- TransE (knowledge graph embeddings)

---

## License

Academic project — not for operational use.
