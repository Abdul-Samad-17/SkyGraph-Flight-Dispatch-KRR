"""Matplotlib visualisations: network overview, reroute example, ontology schema diagram."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch, FancyArrowPatch
from routing import *
import make_dataset as md

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Visualization")
ZC = {"RestrictedZone": "#d62728", "ProhibitedZone": "#8c1c1c", "AdvisoryZone": "#bcbd22"}
HC = {"Thunderstorm": "#1f77b4", "Turbulence": "#9ecae1", "VolcanicAsh": "#7f7f7f", "Icing": "#17becf"}


def base_map(ax, kg, title):
    for z in md.ZONES:
        ax.add_patch(Polygon(z[4], closed=True, fc=ZC[z[2]], ec=ZC[z[2]], alpha=0.18 if z[3] else 0.06, ls="-" if z[3] else "--", lw=1.2))
        cx = sum(p[0] for p in z[4]) / len(z[4]); cy = sum(p[1] for p in z[4]) / len(z[4])
        ax.text(cx, cy, z[0] + ("" if z[3] else "\n(inactive)"), ha="center", va="center", fontsize=7, color=ZC[z[2]], clip_on=True)
    for h in md.HAZARDS:
        ax.add_patch(Polygon(h[5], closed=True, fc=HC[h[2]], ec=HC[h[2]], alpha=0.30 if h[4] else 0.08, hatch="//" if h[4] else None, lw=1))
        cx = sum(p[0] for p in h[5]) / len(h[5]); cy = sum(p[1] for p in h[5]) / len(h[5])
        ax.text(cx, cy, "%s\nsev %d%s" % (h[0], h[3], "" if h[4] else " (expired)"), ha="center", va="center", fontsize=6.5, color="#222", clip_on=True)
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude"); ax.set_title(title, fontsize=11)
    ax.grid(alpha=0.2)


def pts(kg, s):
    a, b = kg.seg_endpoints(s)
    g = kg.g
    return ((py(g.value(a, F("longitude"))), py(g.value(b, F("longitude")))), (py(g.value(a, F("latitude"))), py(g.value(b, F("latitude")))))


def overview(kg):
    fig, ax = plt.subplots(figsize=(15, 8.5))
    base_map(ax, kg, "Flight-dispatch knowledge graph - %d airports, %d segments (red dashed = blocked by an ACTIVE zone/hazard, rule R2)" % (len(kg.airports), len(kg.segments)))
    for s in kg.segments:
        xs, ys = pts(kg, s)
        blocked = F("BlockedSegment") in kg.g.types(s)
        ax.plot(xs, ys, color="#d62728" if blocked else "#9aa0a6", lw=0.9 if blocked else 0.5, ls="--" if blocked else "-", alpha=0.85 if blocked else 0.6, zorder=2)
    hubs = set(kg.g.instances(F("HubAirport")))
    for code, a in kg.airports.items():
        lon, lat = py(kg.g.value(a, F("longitude"))), py(kg.g.value(a, F("latitude")))
        closed = TRUE not in kg.g.objects(a, F("isOperational"))
        ax.scatter(lon, lat, s=70 if a in hubs else 28, c="black" if closed else ("#ff7f0e" if a in hubs else "#2ca02c"), marker="X" if closed else "o", zorder=3, edgecolors="white", linewidths=0.6)
        ax.annotate(code, (lon, lat), xytext=(3, 3), textcoords="offset points", fontsize=6.5, zorder=4)
    ax.scatter([], [], c="#ff7f0e", s=60, label="hub airport (inferred, R6)"); ax.scatter([], [], c="#2ca02c", s=28, label="airport")
    ax.scatter([], [], c="black", marker="X", s=50, label="closed airport (GIL)")
    ax.plot([], [], color="#d62728", ls="--", label="blocked segment (inferred)"); ax.plot([], [], color="#9aa0a6", label="open segment")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xlim(-5, 120); ax.set_ylim(-2, 54)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "kg_network_overview.png"), dpi=130); plt.close(fig)


def reroute(kg, o, d, ac, fname, xlim, ylim, title):
    r = kg.route(kg.find_airport(o), kg.find_airport(d), kg.find_aircraft(ac))
    fig, ax = plt.subplots(figsize=(11, 7.5))
    base_map(ax, kg, title)
    for code, a in kg.airports.items():
        lon, lat = py(kg.g.value(a, F("longitude"))), py(kg.g.value(a, F("latitude")))
        if xlim[0] <= lon <= xlim[1] and ylim[0] <= lat <= ylim[1]:
            ax.scatter(lon, lat, s=22, c="#2ca02c", zorder=3); ax.annotate(code, (lon, lat), xytext=(3, 3), textcoords="offset points", fontsize=8)
    sp = r.get("spatial_only")
    if sp:
        cs = sp["codes"]
        for c1, c2 in zip(cs, cs[1:]):
            s = kg.seg_by_pair[frozenset((kg.airports[c1], kg.airports[c2]))]
            xs, ys = pts(kg, s); ax.plot(xs, ys, color="#d62728", lw=2.5, ls="--", zorder=5)
        ax.plot([], [], color="#d62728", lw=2.5, ls="--", label="purely spatial shortest path: %s (%.0f km) - NOT allowed" % ("-".join(cs), sp["km"]))
    cs = r["codes"]
    for c1, c2 in zip(cs, cs[1:]):
        s = kg.seg_by_pair[frozenset((kg.airports[c1], kg.airports[c2]))]
        xs, ys = pts(kg, s); ax.plot(xs, ys, color="#1a9850", lw=3, zorder=6)
    ax.plot([], [], color="#1a9850", lw=3, label="rule-validated route: %s (%.0f km)" % ("-".join(cs), r["total_km"]))
    ax.legend(loc="lower left", fontsize=8); ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fname), dpi=130); plt.close(fig)


def schema():
    fig, ax = plt.subplots(figsize=(16, 9)); ax.axis("off"); ax.set_xlim(0, 16.4); ax.set_ylim(0, 9)
    boxes = {
     "Airport": (1.6, 6.6), "InternationalAirport": (0.2, 8.1), "RegionalAirport": (2.8, 8.1), "HubAirport*": (5.5, 8.1), "Runway": (1.6, 4.6), "Country": (5.0, 6.6),
     "RouteSegment": (7.6, 5.2), "BlockedSegment*": (7.6, 3.6), "AirspaceZone": (11.0, 6.8), "RestrictedZone": (11.0, 5.4), "ProhibitedZone": (13.8, 4.0), "AdvisoryZone": (13.8, 5.4),
     "WeatherHazard": (11.0, 2.2), "AircraftType": (3.0, 1.4), "WidebodyAircraft": (0.2, 0.2), "NarrowbodyAircraft": (3.0, 0.2), "TurbopropAircraft": (5.9, 0.2),
     "DispatchScenario": (7.6, 1.0), "PositionDistance": (7.6, 7.4)}
    w, h = 2.3, 0.7
    for n, (x, y) in boxes.items():
        inf = n.endswith("*")
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03", fc="#fff3cd" if inf else "#d9ecff", ec="#b8860b" if inf else "#1f5f99", lw=1.4))
        ax.text(x + w / 2, y + h / 2, n.replace("*", " (inferred)"), ha="center", va="center", fontsize=8)
    def c(n): x, y = boxes[n]; return (x + w / 2, y + h / 2)
    def arrow(a, b, label="", style="-|>", color="#333", rad=0.0, dash=False):
        p = FancyArrowPatch(c(a), c(b), arrowstyle=style, mutation_scale=11, color=color, lw=1.1, connectionstyle="arc3,rad=%s" % rad, ls="--" if dash else "-", shrinkA=18, shrinkB=18)
        ax.add_patch(p)
        if label:
            ax.text((c(a)[0] + c(b)[0]) / 2, (c(a)[1] + c(b)[1]) / 2 + 0.12, label, fontsize=7, ha="center", color=color, bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.8))
    for a, b in (("InternationalAirport", "Airport"), ("RegionalAirport", "Airport"), ("HubAirport*", "Airport"), ("BlockedSegment*", "RouteSegment"), ("RestrictedZone", "AirspaceZone"),
                 ("AdvisoryZone", "AirspaceZone"), ("ProhibitedZone", "RestrictedZone"), ("WidebodyAircraft", "AircraftType"), ("NarrowbodyAircraft", "AircraftType"), ("TurbopropAircraft", "AircraftType")):
        arrow(a, b, "", style="-|>", color="#1f5f99")
    arrow("Airport", "Runway", "hasRunway / runwayOf", color="#2e7d32"); arrow("Airport", "Country", "locatedIn", color="#2e7d32")
    arrow("RouteSegment", "Airport", "connectsFrom / connectsTo", color="#2e7d32", rad=0.15); arrow("RouteSegment", "AirspaceZone", "crossesZone", color="#2e7d32", rad=-0.1)
    arrow("RouteSegment", "WeatherHazard", "affectedByHazard", color="#2e7d32", rad=0.1)
    arrow("Airport", "AircraftType", "isSuitableFor (R1)", color="#b8860b", dash=True, rad=0.2); arrow("RouteSegment", "AircraftType", "isFeasibleFor (R4) / exceedsRangeOf (R3)", color="#b8860b", dash=True, rad=-0.15)
    arrow("DispatchScenario", "AircraftType", "forAircraft", color="#2e7d32"); arrow("DispatchScenario", "Airport", "hasDiversionCandidate (R5)", color="#b8860b", dash=True, rad=0.25)
    arrow("PositionDistance", "DispatchScenario", "ofScenario", color="#2e7d32", rad=-0.3); arrow("PositionDistance", "Airport", "toAirport", color="#2e7d32")
    ax.set_title("Ontology schema (T-Box): blue = subClassOf, green = asserted object properties, gold/dashed = inferred by rules", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "ontology_schema.png"), dpi=130); plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    kg = DispatchKG()
    overview(kg)
    reroute(kg, "KHI", "DXB", "B737-800", "reroute_khi_dxb.png", (48, 78), (21, 36), "Reroute: KHI to DXB, B737-800 (direct leg crosses active RZ-ALPHA)")
    reroute(kg, "ISB", "LHR", "A320-200", "reroute_isb_lhr.png", (-5, 78), (22, 54), "Reroute: ISB to LHR, A320 (direct leg crosses active PZ-BRAVO)")
    schema()
    print(sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
