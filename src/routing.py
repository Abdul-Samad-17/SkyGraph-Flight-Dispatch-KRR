"""Dispatch engine: constraint-aware routing over the reasoned knowledge graph.

Pipeline:  (1) rules have already removed infeasible segments (fd:isFeasibleFor per aircraft)
           (2) optional per-request 'avoid' filters remove more segments
           (3) Dijkstra over what is left        (4) independent re-validation of the final route
"""
import os, sys, heapq, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reasoner import *
from geometry import haversine_km

TRUE = lit_bool(True)


class DispatchKG:
    def __init__(self, tbox=None, abox=None):
        if tbox is None:
            tbox, abox = load_graphs()
        self.reasoner = Reasoner(tbox, abox).run()
        self.g = self.reasoner.g
        g = self.g
        self.airports = {}
        for a in g.instances(F("Airport")):
            code = g.value(a, F("iataCode")).value
            self.airports[code] = a
        self.by_icao = {g.value(a, F("icaoCode")).value: a for a in self.airports.values()}
        self.aircraft = {}
        for ac in g.instances(F("AircraftType")):
            self.aircraft[ac[len(FDR + "aircraft-"):]] = ac
        self.segments = sorted(g.instances(F("RouteSegment")), key=str)
        self.seg_by_pair = {}
        for s in self.segments:
            a, b = g.value(s, F("connectsFrom")), g.value(s, F("connectsTo"))
            self.seg_by_pair[frozenset((a, b))] = s
        self.hazards = sorted(g.instances(F("WeatherHazard")), key=str)
        self.zones = sorted(g.instances(F("AirspaceZone")), key=str)

    # ------------------------------------------------------------ lookups
    def code(self, a):
        return self.g.value(a, F("iataCode")).value

    def name(self, x):
        v = self.g.value(x, LABEL)
        return v.value if v is not None else str(x)

    def find_airport(self, text):
        t = text.strip().lower()
        for code, a in self.airports.items():
            if t == code.lower() or t == self.g.value(a, F("icaoCode")).value.lower():
                return a
        for code, a in self.airports.items():
            n = self.name(a).lower()
            city = n.replace(" international airport", "").replace(" airport", "")
            if t == n or t == city:
                return a
        return None

    def find_aircraft(self, text):
        t = re.sub(r"[\s_\-]", "", text.lower())
        for key, ac in self.aircraft.items():
            k = re.sub(r"[\s_\-]", "", key.lower())
            icao = self.g.value(ac, F("icaoTypeCode")).value.lower()
            label = re.sub(r"[\s_\-]", "", self.name(ac).lower())
            if t in (k, icao, label) or (len(t) >= 4 and (t in k or k.startswith(t))):
                return ac
        return None

    def aircraft_key(self, ac):
        return ac[len(FDR + "aircraft-"):]

    # ------------------------------------------------------- segment facts
    def seg_endpoints(self, s):
        return self.g.value(s, F("connectsFrom")), self.g.value(s, F("connectsTo"))

    def seg_dist(self, s):
        return py(self.g.value(s, F("distanceKm")))

    def why_not_feasible(self, s, ac, avoid=frozenset()):
        """Human-readable list of the reasons a segment is NOT feasible for the aircraft ([] if feasible)."""
        g = self.g
        why = []
        for b in g.objects(s, F("blockedBy")):
            why.append("blocked by active %s '%s'" % ("zone" if F("AirspaceZone") in g.types(b) else "hazard", self.name(b)))
        if g.has(s, F("exceedsRangeOf"), ac):
            why.append("distance %.0f km exceeds the %s maximum range of %d km" % (self.seg_dist(s), self.name(ac), py(g.value(ac, F("rangeKm")))))
        for e in self.seg_endpoints(s):
            if not g.has(e, F("isSuitableFor"), ac):
                why.append("%s runway too short (%d m < %d m required)" % (self.code(e), py(g.value(e, F("longestRunwayM"))), py(g.value(ac, F("minRunwayM")))))
            if TRUE not in g.objects(e, F("isOperational")):
                why.append("%s is not operational" % self.code(e))
        already = set(g.objects(s, F("blockedBy")))
        for x in avoid:
            if x in already:
                continue
            if g.has(s, F("crossesZone"), x) or g.has(s, F("affectedByHazard"), x):
                why.append("crosses '%s' which the dispatcher asked to avoid" % self.name(x))
        return why

    def feasible_segments(self, ac, avoid=frozenset()):
        out = []
        for s in self.segments:
            if not self.g.has(s, F("isFeasibleFor"), ac):
                continue
            if any(self.g.has(s, F("crossesZone"), x) or self.g.has(s, F("affectedByHazard"), x) for x in avoid):
                continue
            out.append(s)
        return out

    # ------------------------------------------------------------- routing
    def _dijkstra(self, src, dst, edges, banned=frozenset()):
        adj = {}
        for s in edges:
            if s in banned:
                continue
            a, b = self.seg_endpoints(s)
            d = self.seg_dist(s)
            adj.setdefault(a, []).append((b, d, s)); adj.setdefault(b, []).append((a, d, s))
        pq = [(0.0, self.code(src), src, [])]
        best = {}
        while pq:
            dist, _, node, path = heapq.heappop(pq)
            if node in best and best[node] <= dist:
                continue
            best[node] = dist
            if node == dst:
                return dist, path
            for nxt, d, s in sorted(adj.get(node, []), key=lambda x: (x[1], self.code(x[0]))):
                if nxt not in best:
                    heapq.heappush(pq, (round(dist + d, 6), self.code(nxt), nxt, path + [(node, nxt, s)]))
        return None

    def route(self, origin, dest, ac, avoid=frozenset(), k_alternatives=2):
        """Return a result dict. status in: ok | trivial | no_route | invalid"""
        g = self.g
        res = {"origin": origin, "dest": dest, "aircraft": ac, "avoid": sorted(avoid, key=str), "notes": []}
        if origin == dest:
            res.update(status="trivial", legs=[], total_km=0.0, message="Origin and destination are the same airport.")
            return res
        for role, ap in (("origin", origin), ("destination", dest)):
            if TRUE not in g.objects(ap, F("isOperational")):
                res.update(status="no_route", message="%s airport %s is not operational." % (role.capitalize(), self.code(ap)), legs=[])
                return res
            if not g.has(ap, F("isSuitableFor"), ac):
                res.update(status="no_route", legs=[], message="%s airport %s cannot handle the %s (longest runway %d m, needs %d m)." % (
                    role.capitalize(), self.code(ap), self.name(ac), py(g.value(ap, F("longestRunwayM"))), py(g.value(ac, F("minRunwayM")))))
                return res
        edges = self.feasible_segments(ac, avoid)
        found = self._dijkstra(origin, dest, edges)
        # why not direct?
        direct = self.seg_by_pair.get(frozenset((origin, dest)))
        if direct is not None:
            w = self.why_not_feasible(direct, ac, avoid)
            if w:
                res["direct_rejected"] = w
        elif direct is None:
            res["notes"].append("No direct segment %s-%s exists in the network." % (self.code(origin), self.code(dest)))
        if not found:
            res.update(status="no_route", legs=[], message="No feasible route from %s to %s for the %s after applying all aircraft, airport and airspace constraints." % (
                self.code(origin), self.code(dest), self.name(ac)))
            # explain the nearest blocked alternative
            unconstrained = self._dijkstra(origin, dest, self.segments)
            if unconstrained:
                bad = []
                for a, b, s in unconstrained[1]:
                    w = self.why_not_feasible(s, ac, avoid)
                    if w:
                        bad.append("%s-%s: %s" % (self.code(a), self.code(b), "; ".join(w)))
                res["shortest_unconstrained"] = {"codes": [self.code(origin)] + [self.code(b) for _, b, _ in unconstrained[1]],
                                                 "km": round(unconstrained[0], 1), "problems": bad}
            else:
                res["notes"].append("The airports are not connected in the network at all.")
            return res
        total, path = found
        res.update(status="ok", total_km=round(total, 1), legs=self._legs(path, ac))
        res["codes"] = [self.code(origin)] + [self.code(b) for _, b, _ in path]
        res["time_h"] = round(total / py(g.value(ac, F("cruiseSpeedKmh"))), 2)
        # shortest unconstrained (for comparison) - the "spatial-only" tool answer
        un = self._dijkstra(origin, dest, self.segments)
        if un and abs(un[0] - total) > 0.05:
            res["spatial_only"] = {"codes": [self.code(origin)] + [self.code(b) for _, b, _ in un[1]], "km": round(un[0], 1),
                                   "problems": ["%s-%s: %s" % (self.code(a), self.code(b), "; ".join(self.why_not_feasible(s, ac, avoid)))
                                                for a, b, s in un[1] if self.why_not_feasible(s, ac, avoid)]}
        # alternatives: ban each leg of the best route in turn
        alts, seen = [], {tuple(res["codes"])}
        for leg in path:
            alt = self._dijkstra(origin, dest, edges, banned={leg[2]})
            if alt:
                codes = tuple([self.code(origin)] + [self.code(b) for _, b, _ in alt[1]])
                if codes not in seen:
                    seen.add(codes); alts.append({"codes": list(codes), "km": round(alt[0], 1), "legs": self._legs(alt[1], ac)})
        alts.sort(key=lambda a: (a["km"], a["codes"]))
        res["alternatives"] = alts[:k_alternatives]
        res["revalidation"] = self.validate_route(res["codes"], ac, avoid)
        return res

    def _legs(self, path, ac):
        legs = []
        for a, b, s in path:
            deriv = self.reasoner.deriv.get((s, F("isFeasibleFor"), ac))
            legs.append({"from": self.code(a), "to": self.code(b), "km": self.seg_dist(s), "segment": s,
                         "rule": deriv[0] if deriv else "explicit", "because": deriv[1] if deriv else ""})
        return legs

    # ------------------------------------------------------- re-validation
    def validate_route(self, codes, ac, avoid=frozenset()):
        """Independent check of a route given as IATA codes: every leg must exist and be feasible. Returns dict(valid, problems)."""
        problems = []
        if len(codes) < 2:
            return {"valid": False, "problems": ["route needs at least two airports"]}
        for c1, c2 in zip(codes, codes[1:]):
            a, b = self.airports.get(c1), self.airports.get(c2)
            if a is None or b is None:
                problems.append("unknown airport in leg %s-%s" % (c1, c2)); continue
            s = self.seg_by_pair.get(frozenset((a, b)))
            if s is None:
                problems.append("no route segment %s-%s exists" % (c1, c2)); continue
            w = self.why_not_feasible(s, ac, avoid)
            if w:
                problems.append("%s-%s: %s" % (c1, c2, "; ".join(w)))
            elif not self.g.has(s, F("isFeasibleFor"), ac):
                problems.append("%s-%s: not derived feasible" % (c1, c2))
        return {"valid": not problems, "problems": problems}

    # ----------------------------------------------------------- diversion
    def diversions(self, ac, lat, lon, remaining_km):
        """Airports that are suitable, operational and within remaining_km of (lat, lon), nearest first."""
        g = self.g
        out, rejected = [], []
        for code, a in sorted(self.airports.items()):
            d = haversine_km(lat, lon, py(g.value(a, F("latitude"))), py(g.value(a, F("longitude"))))
            d = round(d, 1)
            if d > remaining_km:
                continue
            if TRUE not in g.objects(a, F("isOperational")):
                rejected.append((code, d, "not operational")); continue
            if not g.has(a, F("isSuitableFor"), ac):
                rejected.append((code, d, "runway too short (%d m < %d m)" % (py(g.value(a, F("longestRunwayM"))), py(g.value(ac, F("minRunwayM")))))); continue
            out.append((code, self.name(a), d, py(g.value(a, F("longestRunwayM")))))
        out.sort(key=lambda x: (x[2], x[0]))
        return out, sorted(rejected, key=lambda x: x[1])

    def scenario(self, sid):
        sc = FDR + "scenario-" + sid.upper()
        if not self.g.instances(F("DispatchScenario")) or sc not in self.g.instances(F("DispatchScenario")):
            return None
        g = self.g
        return {"id": sid.upper(), "uri": sc, "label": self.name(sc), "aircraft": g.value(sc, F("forAircraft")),
                "remaining": py(g.value(sc, F("remainingRangeKm"))), "lat": py(g.value(sc, F("currentLatitude"))),
                "lon": py(g.value(sc, F("currentLongitude")))}

    def scenario_candidates(self, sid):
        """Candidates as derived by rule R5 (reified PositionDistance facts)."""
        sc = self.scenario(sid)
        rows = []
        for a in self.g.objects(sc["uri"], F("hasDiversionCandidate")):
            pd = [p for p in self.g.subjects(F("toAirport"), a) if self.g.has(p, F("ofScenario"), sc["uri"])][0]
            rows.append((self.code(a), self.name(a), py(self.g.value(pd, F("distanceKm"))), py(self.g.value(a, F("longestRunwayM")))))
        return sorted(rows, key=lambda r: (r[2], r[0]))
