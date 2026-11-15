"""CSV -> RDF (Turtle) knowledge graph builder (the 'ETL' step).

Reads ../Dataset/*.csv, derives geometry facts (haversine distances, segment/zone/hazard
intersections) and writes ../RDF_Knowledge_Graph/flight_dispatch_kg.ttl (A-Box only).
"""
import csv, os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minirdf import *
from geometry import haversine_km, segment_crosses_polygon
import make_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "Dataset")
OUT = os.path.join(HERE, "..", "RDF_Knowledge_Graph")
LABEL = RDFS + "label"


def rdr(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fd(x):
    return FD + x


def res(kind, ident):
    return FDR + kind + "-" + ident


def poly_from(s):
    return [tuple(float(v) for v in pair.split(",")) for pair in s.split(";")]


def build():
    airports = rdr("airports.csv"); runways = rdr("runways.csv"); countries = rdr("countries.csv")
    aircraft = rdr("aircraft.csv"); segments = rdr("segments.csv"); zones = rdr("zones.csv")
    hazards = rdr("hazards.csv"); scenarios = rdr("scenarios.csv")
    T = []
    add = lambda s, p, o: T.append((s, p, o))

    ap = {a["icao"]: a for a in airports}
    # countries (deliberately NOT typed: fd:Country is inferred from rdfs:range of fd:locatedIn)
    for c in countries:
        r = res("country", c["code"])
        add(r, LABEL, lit(c["name"])); add(r, fd("isoCode"), lit(c["code"]))
    # airports
    for a in airports:
        r = res("airport", a["icao"])
        add(r, RDF_TYPE, fd("Airport"))
        add(r, RDF_TYPE, fd("InternationalAirport" if a["category"] == "I" else "RegionalAirport"))
        add(r, LABEL, lit(a["name"])); add(r, fd("iataCode"), lit(a["iata"])); add(r, fd("icaoCode"), lit(a["icao"]))
        add(r, fd("latitude"), lit_dec(float(a["latitude"]))); add(r, fd("longitude"), lit_dec(float(a["longitude"])))
        add(r, fd("isOperational"), lit_bool(a["operational"] == "true"))
        add(r, fd("locatedIn"), res("country", a["country_code"]))
    for rw in runways:
        rr = res("runway", rw["airport_icao"] + "-" + rw["designator"].replace("/", "-"))
        add(rr, RDF_TYPE, fd("Runway")); add(rr, fd("designator"), lit(rw["designator"]))
        add(rr, fd("runwayLengthM"), lit_int(rw["length_m"]))
        add(res("airport", rw["airport_icao"]), fd("hasRunway"), rr)
    # aircraft (typed only by their specific subclass; fd:AircraftType is inferred)
    for ac in aircraft:
        r = res("aircraft", ac["id"])
        add(r, RDF_TYPE, fd(ac["class"] + "Aircraft"))
        add(r, LABEL, lit(ac["label"])); add(r, fd("icaoTypeCode"), lit(ac["icao_type"]))
        add(r, fd("rangeKm"), lit_int(ac["range_km"])); add(r, fd("minRunwayM"), lit_int(ac["min_runway_m"]))
        add(r, fd("cruiseSpeedKmh"), lit_int(ac["cruise_kmh"]))
    # zones & hazards
    zpoly, hpoly = {}, {}
    for z in zones:
        r = res("zone", z["id"]); zpoly[z["id"]] = poly_from(z["polygon_lonlat"])
        add(r, RDF_TYPE, fd(z["class"])); add(r, LABEL, lit(z["label"])); add(r, fd("isActive"), lit_bool(z["active"] == "true"))
    for h in hazards:
        r = res("hazard", h["id"]); hpoly[h["id"]] = poly_from(h["polygon_lonlat"])
        add(r, RDF_TYPE, fd("WeatherHazard")); add(r, LABEL, lit(h["label"])); add(r, fd("hazardType"), lit(h["hazard_type"]))
        add(r, fd("severity"), lit_int(h["severity"])); add(r, fd("isActive"), lit_bool(h["active"] == "true"))
    # segments
    seg_rows = []
    for sgm in segments:
        a, b = ap[sgm["from_icao"]], ap[sgm["to_icao"]]
        dist = round(haversine_km(float(a["latitude"]), float(a["longitude"]), float(b["latitude"]), float(b["longitude"])), 1)
        sid = a["icao"] + "-" + b["icao"]
        r = res("segment", sid)
        add(r, RDF_TYPE, fd("RouteSegment")); add(r, LABEL, lit("%s-%s" % (a["iata"], b["iata"])))
        add(r, fd("connectsFrom"), res("airport", a["icao"])); add(r, fd("connectsTo"), res("airport", b["icao"]))
        add(r, fd("distanceKm"), lit_dec(dist))
        add(res("airport", a["icao"]), fd("connectedTo"), res("airport", b["icao"]))
        p1 = (float(a["longitude"]), float(a["latitude"])); p2 = (float(b["longitude"]), float(b["latitude"]))
        zs, hs = [], []
        for zid, poly in zpoly.items():
            if segment_crosses_polygon(p1, p2, poly):
                add(r, fd("crossesZone"), res("zone", zid)); zs.append(zid)
        for hid, poly in hpoly.items():
            if segment_crosses_polygon(p1, p2, poly):
                add(r, fd("affectedByHazard"), res("hazard", hid)); hs.append(hid)
        seg_rows.append({"segment": sid, "label": "%s-%s" % (a["iata"], b["iata"]), "distance_km": dist, "zones": zs, "hazards": hs})
    # scenarios + position distances
    ac_by_id = {ac["id"]: ac for ac in aircraft}
    n_pd = 0
    for sc in scenarios:
        r = res("scenario", sc["id"]); rem = float(sc["remaining_range_km"])
        add(r, RDF_TYPE, fd("DispatchScenario")); add(r, LABEL, lit(sc["label"]))
        add(r, fd("forAircraft"), res("aircraft", sc["aircraft_id"]))
        add(r, fd("remainingRangeKm"), lit_int(sc["remaining_range_km"]))
        add(r, fd("currentLatitude"), lit_dec(float(sc["current_lat"]))); add(r, fd("currentLongitude"), lit_dec(float(sc["current_lon"])))
        for a in airports:
            d = round(haversine_km(float(sc["current_lat"]), float(sc["current_lon"]), float(a["latitude"]), float(a["longitude"])), 1)
            if d <= make_dataset.DIST_WINDOW_FACTOR * rem:
                pd = res("dist", sc["id"] + "-" + a["icao"])
                add(pd, RDF_TYPE, fd("PositionDistance")); add(pd, fd("ofScenario"), r)
                add(pd, fd("toAirport"), res("airport", a["icao"])); add(pd, fd("distanceKm"), lit_dec(d)); n_pd += 1
    return T, seg_rows


def main():
    os.makedirs(OUT, exist_ok=True)
    T, seg_rows = build()
    ser = Serializer(DEFAULT_PREFIXES)
    hdr = ("Dynamic Flight Dispatch & Weather Routing - A-Box (instance data), generated by src/build_kg.py\n"
           "Source: curated CSVs in /Dataset (airports/runways/aircraft approximated from OurAirports/OpenFlights/OpenAP style data;\n"
           "zones, hazards and scenarios are FICTIONAL illustrations). Load together with Ontology/flight_dispatch_ontology.ttl")
    with open(os.path.join(OUT, "flight_dispatch_kg.ttl"), "w", encoding="utf-8") as f:
        f.write(ser.dump(T, hdr))
    with open(os.path.join(OUT, "segment_geometry.json"), "w") as f:
        json.dump(seg_rows, f, indent=1)
    print("A-Box triples written:", len(set(T)))


if __name__ == "__main__":
    main()
