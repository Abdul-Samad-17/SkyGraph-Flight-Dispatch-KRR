"""Phase 2 - Hybrid neuro-symbolic reasoning (Option D): TransE link prediction + symbolic rule filtering.

Task: predict missing airport-airport route links (fd:connectedTo) from the KG, then let the symbolic
layer (aircraft range, runway suitability, operational status, active zones/hazards) accept or reject every
suggestion with an explicit reason. Pure numpy; deterministic (fixed seeds).
"""
import os, sys, json, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routing import *
from geometry import haversine_km, segment_crosses_polygon
import make_dataset as md

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "Results")
SEED = 7


def runway_bucket(m):
    return "bucket-short" if m < 2000 else "bucket-medium" if m < 3000 else "bucket-long" if m < 3700 else "bucket-xlong"


def build_dataset(kg):
    """Airport-centric triples (segment reification deliberately excluded to avoid leaking hidden edges)."""
    g = kg.g
    triples, edges = [], set()
    for s, _, o in g.triples(None, F("connectedTo"), None):
        if s != o and F("Airport") in g.types(s) and (o, s) not in edges:
            edges.add((s, o))
    # undirected unique edges (each segment stored once)
    und = sorted({tuple(sorted(e, key=str)) for e in edges}, key=lambda e: (str(e[0]), str(e[1])))
    side = []
    for a in sorted(g.instances(F("Airport")), key=str):
        side.append((a, "locatedIn", g.value(a, F("locatedIn"))))
        for t in sorted(g.types(a), key=str):
            if t in (F("InternationalAirport"), F("RegionalAirport"), F("HubAirport")):
                side.append((a, "type", t))
        side.append((a, "runwayClass", FDR + runway_bucket(py(g.value(a, F("longestRunwayM"))))))
        side.append((a, "operational", FDR + ("yes" if TRUE in g.objects(a, F("isOperational")) else "no")))
    return und, side


class TransE:
    def __init__(self, n_ent, n_rel, dim=32, seed=SEED):
        rng = np.random.default_rng(seed)
        b = 6 / np.sqrt(dim)
        self.E = rng.uniform(-b, b, (n_ent, dim)); self.R = rng.uniform(-b, b, (n_rel, dim))
        self.R /= np.linalg.norm(self.R, axis=1, keepdims=True)
        self.dim = dim

    def score(self, h, r, t):          # lower = more plausible
        return np.sum((self.E[h] + self.R[r] - self.E[t]) ** 2, axis=-1)

    def fit(self, triples, n_ent, epochs=300, lr=0.02, margin=1.0, batch=128, seed=SEED, neg_pool=None):
        rng = np.random.default_rng(seed)
        T = np.array(triples)
        pool = np.arange(n_ent) if neg_pool is None else np.array(neg_pool)
        for ep in range(epochs):
            self.E /= np.maximum(np.linalg.norm(self.E, axis=1, keepdims=True), 1e-9)
            idx = rng.permutation(len(T))
            for i in range(0, len(T), batch):
                B = T[idx[i:i + batch]]
                h, r, t = B[:, 0], B[:, 1], B[:, 2]
                corrupt_head = rng.random(len(B)) < 0.5
                nh = np.where(corrupt_head, rng.choice(pool, len(B)), h)
                nt = np.where(corrupt_head, t, rng.choice(pool, len(B)))
                pos = self.E[h] + self.R[r] - self.E[t]
                neg = self.E[nh] + self.R[r] - self.E[nt]
                loss = margin + np.sum(pos ** 2, 1) - np.sum(neg ** 2, 1)
                m = (loss > 0).astype(float)[:, None]
                gp, gn = 2 * pos * m, 2 * neg * m
                np.add.at(self.E, h, -lr * gp); np.add.at(self.E, t, lr * gp)
                np.add.at(self.R, r, -lr * (gp - gn))
                np.add.at(self.E, nh, lr * gn); np.add.at(self.E, nt, -lr * gn)
        return self


def split_edges(und, kg, frac=0.2, seed=SEED):
    """Hold out ~frac of the undirected edges, keeping every airport at degree >= 2 in training."""
    rng = random.Random(seed)
    deg = {}
    for a, b in und:
        deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
    order = list(und); rng.shuffle(order)
    test, n_test = [], int(round(frac * len(und)))
    for a, b in order:
        if len(test) >= n_test:
            break
        if deg[a] > 2 and deg[b] > 2:
            test.append((a, b)); deg[a] -= 1; deg[b] -= 1
    ts = set(test)
    train = [e for e in und if e not in ts]
    return train, test


def run_experiment(kg=None, dim=32, epochs=300, verbose=True):
    kg = kg or DispatchKG()
    und, side = build_dataset(kg)
    train_e, test_e = split_edges(und, kg)
    ents = sorted({x for e in und for x in e} | {s[0] for s in side} | {s[2] for s in side}, key=str)
    eid = {e: i for i, e in enumerate(ents)}
    rels = ["connectedTo", "locatedIn", "type", "runwayClass", "operational"]
    rid = {r: i for i, r in enumerate(rels)}
    tri = []
    for a, b in train_e:
        tri.append((eid[a], rid["connectedTo"], eid[b])); tri.append((eid[b], rid["connectedTo"], eid[a]))
    for a, r, o in side:
        tri.append((eid[a], rid[r], eid[o]))
    airports = sorted({x for e in und for x in e}, key=str)
    aid = [eid[a] for a in airports]
    model = TransE(len(ents), len(rels), dim=dim).fit(tri, len(ents), epochs=epochs, neg_pool=aid)
    known = {(eid[a], eid[b]) for a, b in train_e} | {(eid[b], eid[a]) for a, b in train_e}
    allpos = known | {(eid[a], eid[b]) for a, b in test_e} | {(eid[b], eid[a]) for a, b in test_e}
    train_deg = {}
    for a, b in train_e:
        train_deg[eid[a]] = train_deg.get(eid[a], 0) + 1; train_deg[eid[b]] = train_deg.get(eid[b], 0) + 1
    ll = {eid[a]: (py(kg.g.value(a, F("latitude"))), py(kg.g.value(a, F("longitude")))) for a in airports}

    def rank_of(h, t, scorer):
        cands = [c for c in aid if c != h and ((h, c) not in allpos or c == t)]
        sc = {c: scorer(h, c) for c in cands}
        better = sum(1 for c in cands if c != t and sc[c] < sc[t])
        ties = sum(1 for c in cands if c != t and sc[c] == sc[t])
        return better + 1 + ties / 2.0   # average rank for ties

    rng = random.Random(SEED)
    scorers = {
        "TransE": lambda h, c: float(model.score(h, rid["connectedTo"], c)),
        "Popularity (training degree)": lambda h, c: -train_deg.get(c, 0),
        "Geographic nearest": lambda h, c: haversine_km(*ll[h], *ll[c]),
        "Random": lambda h, c: rng.random(),
    }
    metrics = {}
    for name, sc in scorers.items():
        ranks = []
        for a, b in test_e:
            ranks.append(rank_of(eid[a], eid[b], sc)); ranks.append(rank_of(eid[b], eid[a], sc))
        ranks = np.array(ranks)
        metrics[name] = {"MRR": round(float(np.mean(1.0 / ranks)), 3), "Hits@1": round(float(np.mean(ranks <= 1)), 3),
                         "Hits@3": round(float(np.mean(ranks <= 3)), 3), "Hits@10": round(float(np.mean(ranks <= 10)), 3),
                         "MeanRank": round(float(np.mean(ranks)), 2), "queries": int(len(ranks))}
    info = {"entities": len(ents), "train_edges": len(train_e), "test_edges": len(test_e), "dim": dim, "epochs": epochs, "metrics": metrics}
    if verbose:
        print(json.dumps(info, indent=1))
    return kg, model, eid, ents, airports, train_e, test_e, info


# ---------------------------------------------------------------- hybrid layer
_POLY = None


def _polygons():
    global _POLY
    if _POLY is None:
        _POLY = {}
        for z in md.ZONES:
            _POLY[FDR + "zone-" + z[0]] = z[4]
        for h in md.HAZARDS:
            _POLY[FDR + "hazard-" + h[0]] = h[5]
    return _POLY


def symbolic_check(kg, a, b, ac):
    """Would a NEW direct leg a-b be feasible for aircraft ac? Returns list of rejection reasons ([] = accept)."""
    g = kg.g
    why = []
    d = haversine_km(py(g.value(a, F("latitude"))), py(g.value(a, F("longitude"))), py(g.value(b, F("latitude"))), py(g.value(b, F("longitude"))))
    rng_ = py(g.value(ac, F("rangeKm")))
    if d > rng_:
        why.append("distance %.0f km exceeds range %d km" % (d, rng_))
    for e in (a, b):
        if not g.has(e, F("isSuitableFor"), ac):
            why.append("%s runway too short" % kg.code(e))
        if TRUE not in g.objects(e, F("isOperational")):
            why.append("%s not operational" % kg.code(e))
    p1 = (py(g.value(a, F("longitude"))), py(g.value(a, F("latitude")))); p2 = (py(g.value(b, F("longitude"))), py(g.value(b, F("latitude"))))
    for uri, poly in _polygons().items():
        if not segment_crosses_polygon(p1, p2, poly):
            continue
        is_zone = "zone-" in uri
        active = TRUE in g.objects(uri, F("isActive"))
        if is_zone and active and F("RestrictedZone") in g.types(uri):
            why.append("would cross active restricted zone '%s'" % kg.name(uri))
        if (not is_zone) and active and py(g.value(uri, F("severity"))) >= SEVERITY_THRESHOLD:
            why.append("would cross active hazard '%s'" % kg.name(uri))
    return why


def suggest_links(kg, model, eid, airports, train_e, airport_iata, aircraft_text, k=5):
    """Top-k TransE link suggestions for an airport, each verified by the symbolic layer."""
    a = kg.find_airport(airport_iata); ac = kg.find_aircraft(aircraft_text)
    if a is None or ac is None:
        return {"error": "unknown airport or aircraft"}
    existing = {e for pair in train_e for e in [pair]}
    linked = {b for (x, b) in train_e if x == a} | {x for (x, b) in train_e if b == a}
    cands = [c for c in airports if c != a and c not in linked]
    # also exclude links that exist in the full network (test edges are 'missing' links we hope to recover)
    sc = sorted(cands, key=lambda c: (float(model.score(eid[a], 0, eid[c])), str(c)))[:k]
    rows = []
    for c in sc:
        why = symbolic_check(kg, a, c, ac)
        rows.append({"airport": kg.code(c), "transe_score": round(float(model.score(eid[a], 0, eid[c])), 3), "accepted": not why, "reasons": why})
    return {"from": kg.code(a), "aircraft": kg.name(ac), "suggestions": rows}


def hybrid_stats(kg, model, eid, airports, train_e, k=5):
    """For every airport x aircraft: share of TransE top-k suggestions that the symbolic layer rejects."""
    rej = tot = 0
    by_ac = {}
    for key, ac in sorted(kg.aircraft.items()):
        r = t = 0
        for a in airports:
            linked = {b for (x, b) in train_e if x == a} | {x for (x, b) in train_e if b == a}
            cands = [c for c in airports if c != a and c not in linked]
            top = sorted(cands, key=lambda c: (float(model.score(eid[a], 0, eid[c])), str(c)))[:k]
            for c in top:
                t += 1
                if symbolic_check(kg, a, c, ac):
                    r += 1
        by_ac[key] = {"suggestions": t, "rejected_by_rules": r, "rejected_pct": round(100.0 * r / t, 1)}
        rej += r; tot += t
    return {"k": k, "total_suggestions": tot, "rejected": rej, "rejected_pct": round(100.0 * rej / tot, 1), "by_aircraft": by_ac}


def main():
    kg, model, eid, ents, airports, train_e, test_e, info = run_experiment()
    hy = hybrid_stats(kg, model, eid, airports, train_e)
    demo = suggest_links(kg, model, eid, airports, train_e, "ISB", "ATR72", k=5)
    out = {"link_prediction": info, "hybrid_rule_filtering": hy, "demo_ISB_ATR72": demo}
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "phase2_embedding_results.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"hybrid": hy, "demo": demo}, indent=1))


if __name__ == "__main__":
    main()
