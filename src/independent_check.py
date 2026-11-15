"""Independent re-computation of the rule outputs straight from the CSV/geometry data (no RDF involved).
Used to cross-validate the reasoner output and to produce the expected SPARQL results."""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometry import haversine_km, segment_crosses_polygon
import make_dataset as md

HUB_MIN_DEGREE = 14


def compute():
    A = {a[0]: a for a in md.AIRPORTS}
    IA = {a[1]: a for a in md.AIRPORTS}
    AC = {a[0]: a for a in md.AIRCRAFT}
    longest = {a[0]: max(l for _, l in a[9]) for a in md.AIRPORTS}
    suitable = {(i, ac) for i in A for ac in AC if longest[i] >= AC[ac][5]}
    segs = []
    for p in md.SEGMENT_PAIRS:
        x, y = (IA[v][0] for v in p.split("-"))
        segs.append((x, y))
    dist = {s: round(haversine_km(A[s[0]][5], A[s[0]][6], A[s[1]][5], A[s[1]][6]), 1) for s in segs}
    zinfo = {z[0]: z for z in md.ZONES}
    hinfo = {h[0]: h for h in md.HAZARDS}
    blocked = {}
    for s in segs:
        p1 = (A[s[0]][6], A[s[0]][5]); p2 = (A[s[1]][6], A[s[1]][5])
        by = []
        for z in md.ZONES:
            if segment_crosses_polygon(p1, p2, z[4]) and z[2] in ("RestrictedZone", "ProhibitedZone") and z[3]:
                by.append(z[0])
        for h in md.HAZARDS:
            if segment_crosses_polygon(p1, p2, h[5]) and h[4] and h[3] >= 3:
                by.append(h[0])
        if by:
            blocked[s] = by
    exceeds = {(s, ac) for s in segs for ac in AC if dist[s] > AC[ac][4]}
    feasible = {(s, ac) for s in segs for ac in AC
                if s not in blocked and (s, ac) not in exceeds
                and all((e, ac) in suitable and A[e][7] for e in s)}
    div = {}
    for sc in md.SCENARIOS:
        sid, _, acid, rem, lat, lon = sc
        div[sid] = sorted(
            [(round(haversine_km(lat, lon, A[i][5], A[i][6]), 1), i) for i in A
             if round(haversine_km(lat, lon, A[i][5], A[i][6]), 1) <= rem and (i, acid) in suitable and A[i][7]])
    deg = {}
    for s in segs:
        for e in s:
            deg[e] = deg.get(e, 0) + 1
    hubs = sorted(i for i, d in deg.items() if d >= HUB_MIN_DEGREE)
    return dict(A=A, IA=IA, AC=AC, longest=longest, suitable=suitable, segs=segs, dist=dist, blocked=blocked,
                exceeds=exceeds, feasible=feasible, div=div, deg=deg, hubs=hubs, zinfo=zinfo, hinfo=hinfo)


if __name__ == "__main__":
    r = compute()
    print("suitable pairs", len(r["suitable"]), "blocked", len(r["blocked"]), "exceeds", len(r["exceeds"]),
          "feasible", len(r["feasible"]), "hubs", r["hubs"])
    for k, v in r["div"].items():
        print(k, [(i, d) for d, i in v])
