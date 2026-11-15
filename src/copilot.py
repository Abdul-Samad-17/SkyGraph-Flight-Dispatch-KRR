"""Phase 3 - GraphRAG flight-dispatch copilot (academic prototype, NOT for operational use).

natural-language request -> intent/entity parsing -> SPARQL (shown for provenance) -> retrieval over the reasoned KG ->
evidence (explicit vs inferred facts) -> verbalisation (LLM if a key is set, else deterministic) -> re-validation guard.
Routes always come from the KG, never from the language model; any LLM text is checked against the graph before display.
"""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routing import *
import llm

PREFIXES = ("PREFIX fd:  <https://krr.example.org/fd/ontology#>\nPREFIX fdr: <https://krr.example.org/fd/data/>\n"
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n")
AC_PATTERNS = {
    "A380-800": r"\ba[\s\-]?380\b|\b380\b", "B777-300ER": r"\b(?:b|boeing)?[\s\-]?777(?:[\s\-]?300\s?er)?\b",
    "B787-9": r"\b(?:b|boeing)?[\s\-]?787(?:[\s\-]?9)?\b|dreamliner", "A320-200": r"\ba[\s\-]?320(?:[\s\-]?200|neo)?\b",
    "B737-800": r"\b(?:b|boeing)?[\s\-]?737(?:[\s\-]?800)?\b", "ATR72-600": r"\batr[\s\-]?72(?:[\s\-]?600)?\b|\batr\b",
}
HAZ_WORDS = {"punjab": ["hazard-STORM-1"], "karakoram": ["hazard-TURB-3"], "hindu kush": ["hazard-ICE-5"], "northern gulf": ["hazard-STORM-2"],
             "arabian sea": ["hazard-ASH-4"], "naval": ["zone-RZ-ALPHA"], "alpha": ["zone-RZ-ALPHA"], "bravo": ["zone-PZ-BRAVO"],
             "charlie": ["zone-RZ-CHARLIE"], "delta": ["zone-AZ-DELTA"]}
GENERIC = {"thunderstorm": "Thunderstorm", "storm": "Thunderstorm", "turbulence": "Turbulence", "icing": "Icing", "ash": "VolcanicAsh"}


def _lbl(kg, x):
    return kg.name(x)


class Copilot:
    def __init__(self, kg=None):
        self.kg = kg or DispatchKG()
        self.city_index = {}
        for code, a in self.kg.airports.items():
            n = self.kg.name(a).lower()
            for alias in {n, n.replace(" international airport", "").replace(" airport", "")}:
                pass
        self._build_names()

    def _build_names(self):
        kg = self.kg
        self.names = []   # (regex, airport)
        cities = {"OPIS": ["islamabad"], "OPKC": ["karachi"], "OPLA": ["lahore"], "OPPS": ["peshawar"], "OPMT": ["multan"], "OPFA": ["faisalabad"],
                  "OPQT": ["quetta"], "OPSD": ["skardu"], "OPGT": ["gilgit"], "OPCH": ["chitral"], "OMDB": ["dubai"], "OMAA": ["abu dhabi"],
                  "OMSJ": ["sharjah"], "OTHH": ["doha"], "OBBI": ["bahrain", "manama"], "OKBK": ["kuwait"], "OOMS": ["muscat"], "OERK": ["riyadh"],
                  "OEJN": ["jeddah"], "OEDF": ["dammam"], "VIDP": ["delhi"], "VABB": ["mumbai"], "VIAR": ["amritsar"], "VIJP": ["jaipur"],
                  "VAAH": ["ahmedabad"], "OAKB": ["kabul"], "OIIE": ["tehran"], "UTTT": ["tashkent"], "LTFM": ["istanbul"], "EGLL": ["london", "heathrow"],
                  "EDDF": ["frankfurt"], "LFPG": ["paris"], "VTBS": ["bangkok"], "WSSS": ["singapore"], "WMKK": ["kuala lumpur"], "ZBAA": ["beijing"],
                  "VGHS": ["dhaka"], "VCBI": ["colombo"]}
        for icao, names in cities.items():
            a = kg.by_icao[icao]
            for n in names:
                self.names.append((re.compile(r"\b" + re.escape(n) + r"\b", re.I), a))
        for code, a in kg.airports.items():
            self.names.append((re.compile(r"\b" + code + r"\b", re.I), a))
            self.names.append((re.compile(r"\b" + kg.g.value(a, F("icaoCode")).value + r"\b", re.I), a))

    # ------------------------------------------------------------- parsing
    def find_airports(self, text):
        hits = []
        for rx, a in self.names:
            for m in rx.finditer(text):
                hits.append((m.start(), a))
        hits.sort(key=lambda x: x[0])
        out = []
        for _, a in hits:
            if a not in out:
                out.append(a)
        return out, hits

    def find_aircraft(self, text):
        for key, pat in AC_PATTERNS.items():
            if re.search(pat, text, re.I):
                return self.kg.aircraft[key]
        return None

    def find_avoid(self, text):
        t = text.lower()
        m = re.search(r"\b(avoid(?:ing)?|bypass(?:ing)?|around|without crossing|steer clear of|not through|except)\b(.*)", t)
        if not m:
            return set(), []
        tail = m.group(2)
        found, notes = set(), []
        for mid in re.finditer(r"\b(storm|turb|ash|ice)[\s\-_]?(\d)\b", tail):
            key = {"storm": "STORM", "turb": "TURB", "ash": "ASH", "ice": "ICE"}[mid.group(1)] + "-" + mid.group(2)
            found.add(FDR + "hazard-" + key)
        for mid in re.finditer(r"\b(rz|pz|az)[\s\-_]?(alpha|bravo|charlie|delta)\b", tail):
            found.add(FDR + "zone-" + mid.group(1).upper() + "-" + mid.group(2).upper())
        for w, uris in HAZ_WORDS.items():
            if re.search(r"\b" + re.escape(w) + r"\b", tail):
                for u in uris:
                    found.add(FDR + u)
        if not found:
            for w, typ in GENERIC.items():
                if re.search(r"\b" + w + r"\b", tail):
                    for h in self.kg.hazards:
                        if self.kg.g.value(h, F("hazardType")).value == typ:
                            found.add(h)
        if re.search(r"\bsector\s+[a-z0-9]+\b", tail):
            notes.append("The named sector cannot be mapped to a specific hazard/zone in the KG%s; all ACTIVE blockers (zones, hazards with severity >= 3) always apply." % (
                " - I therefore avoided every hazard of the type you mentioned" if found else ""))
        if not found and not notes:
            notes.append("No known hazard/zone matched the 'avoid' phrase; all ACTIVE blockers still apply.")
        return found, notes

    def parse(self, text):
        t = text.strip()
        low = t.lower()
        aps, hits = self.find_airports(t)
        ac = self.find_aircraft(t)
        intent = {"text": t, "airports": aps, "aircraft": ac, "avoid": set(), "notes": []}
        if re.search(r"\b(divert|diversion|alternate airport|nearest suitable|emergency landing)\b", low):
            m = re.search(r"\bscenario[\s\-]*s?(\d)\b|\bs([1-9])\b", low)
            if m:
                intent.update(type="diversion", scenario=("S" + (m.group(1) or m.group(2))))
                return intent
            rng_m = re.search(r"(\d{2,5})\s*km", low)
            pos = re.search(r"(-?\d{1,2}(?:\.\d+)?)\s*[,;/]\s*(-?\d{1,3}(?:\.\d+)?)", low)
            if ac and rng_m and pos:
                intent.update(type="diversion_adhoc", remaining=float(rng_m.group(1)), lat=float(pos.group(1)), lon=float(pos.group(2)))
                return intent
            intent.update(type="clarify", message="For a diversion I need either a scenario id (S1-S6) or: aircraft type, remaining range in km and position as 'lat, lon'.")
            return intent
        if re.search(r"\b(why|explain|not feasible|infeasible|can't|cannot|can not|isn't|is not|blocked)\b", low) and len(aps) >= 2 and not re.search(r"\bfind\b", low):
            intent.update(type="explain")
            return intent
        if re.search(r"\b(route|reroute|re-route|path|fly|flight|get from|alternate route|dispatch)\b", low) and len(aps) >= 2:
            avoid, notes = self.find_avoid(t)
            # origin / destination from 'from X to Y' when present
            origin, dest = aps[0], aps[1]
            mm = re.search(r"\bfrom\b(.*?)\bto\b(.*)", t, re.I)
            if mm:
                a1, _ = self.find_airports(mm.group(1)); a2, _ = self.find_airports(mm.group(2))
                if a1 and a2:
                    origin, dest = a1[0], a2[0]
            else:
                mm = re.search(r"\bto\b(.*?)\bfrom\b(.*)", t, re.I)
                if mm:
                    a2, _ = self.find_airports(mm.group(1)); a1, _ = self.find_airports(mm.group(2))
                    if a1 and a2:
                        origin, dest = a1[0], a2[0]
            intent.update(type="route", origin=origin, dest=dest, avoid=avoid, notes=notes)
            return intent
        if re.search(r"\bhub", low):
            intent.update(type="hubs"); return intent
        if re.search(r"\b(suitable|can land|can handle|handle|accommodate|runway)\b", low) and ac:
            intent.update(type="suitable"); return intent
        if re.search(r"\b(hazards?|storms?|weather|restricted|closures?|closed|zones?)\b", low):
            intent.update(type="hazards"); return intent
        intent.update(type="help"); return intent

    # ---------------------------------------------------------- SPARQL text
    def sparql_for(self, it):
        kg = self.kg
        sh = lambda u: "fdr:" + u[len(FDR):]
        ty = it["type"]
        if ty == "route":
            ac = sh(it["aircraft"]); filt = ""
            for u in sorted(it["avoid"], key=str):
                prop = "fd:crossesZone" if "/zone-" in u else "fd:affectedByHazard"
                filt += "  FILTER NOT EXISTS { ?s %s %s }\n" % (prop, sh(u))
            return (PREFIXES + "# step 1: fetch every segment the rules proved feasible for the aircraft (R1-R4); path search (Dijkstra) runs on this subgraph\n"
                    "SELECT ?s ?from ?to ?km WHERE {\n  ?s fd:isFeasibleFor %s ; fd:connectsFrom ?from ; fd:connectsTo ?to ; fd:distanceKm ?km .\n%s}" % (ac, filt))
        if ty in ("diversion",):
            return PREFIXES + "SELECT ?iata ?km WHERE {\n  fdr:scenario-%s fd:hasDiversionCandidate ?a .\n  ?a fd:iataCode ?iata .\n  ?pd fd:ofScenario fdr:scenario-%s ; fd:toAirport ?a ; fd:distanceKm ?km .\n} ORDER BY ?km" % (it["scenario"], it["scenario"])
        if ty == "diversion_adhoc":
            return (PREFIXES + "# ad-hoc position: distances are computed with the haversine formula in the application (SPARQL 1.1 has no trig functions),\n"
                    "# then airports are filtered with the same rule R5 conditions\nSELECT ?iata ?longest WHERE {\n  ?a fd:isSuitableFor %s ; fd:isOperational true ; fd:iataCode ?iata ; fd:longestRunwayM ?longest .\n}" % sh(it["aircraft"]))
        if ty == "explain":
            return (PREFIXES + "SELECT ?reasonType ?reason WHERE {\n  { ?s fd:blockedBy ?r . ?r rdfs:label ?reason . BIND(\"blocked\" AS ?reasonType) }\n"
                    "  UNION { ?s fd:exceedsRangeOf ?r . ?r rdfs:label ?reason . BIND(\"range\" AS ?reasonType) }\n}  # ?s bound to the segment between the two airports")
        if ty == "suitable":
            return PREFIXES + "SELECT ?iata ?longest WHERE {\n  ?a fd:isSuitableFor %s ; fd:iataCode ?iata ; fd:longestRunwayM ?longest .\n} ORDER BY DESC(?longest)" % sh(it["aircraft"])
        if ty == "hubs":
            return PREFIXES + "SELECT ?iata WHERE { ?a a fd:HubAirport ; fd:iataCode ?iata }"
        if ty == "hazards":
            return PREFIXES + "SELECT ?label ?severity ?active WHERE { ?h a fd:WeatherHazard ; rdfs:label ?label ; fd:severity ?severity ; fd:isActive ?active }"
        return ""

    # ------------------------------------------------------------ retrieval
    def answer(self, text, use_llm=True):
        kg = self.kg
        it = self.parse(text)
        ty = it["type"]
        out = {"question": text, "intent": ty, "evidence": [], "approved_routes": [], "warnings": [], "data": {}}
        if ty == "help":
            out["answer"] = ("I can: (1) find a feasible route, e.g. 'Find an alternate route from Karachi to Dubai for a B737-800 avoiding the Restricted Zone Alpha'; "
                             "(2) list diversion candidates, e.g. 'Diversion candidates for scenario S1'; (3) explain, e.g. 'Why can't an A380 fly Karachi to Dubai direct?'; "
                             "(4) list airports suitable for an aircraft, hubs, or active hazards.")
            out["sparql"] = ""; out["validation"] = {"valid": True, "problems": []}; return out
        if ty == "clarify":
            out["answer"] = it["message"]; out["sparql"] = ""; out["validation"] = {"valid": True, "problems": []}; return out
        needs_ac = ty in ("route", "diversion_adhoc", "suitable")
        if ty in ("route", "explain") and it["aircraft"] is None:
            it["aircraft"] = kg.aircraft["A320-200"]; it["notes"].append("No aircraft type recognised - assuming the Airbus A320-200.")
        if needs_ac and it["aircraft"] is None:
            out["answer"] = "Please tell me the aircraft type (A380, B777, B787, A320, B737 or ATR72)."; out["sparql"] = ""; out["validation"] = {"valid": True, "problems": []}; return out
        out["sparql"] = self.sparql_for(it)
        ev = out["evidence"]
        if ty == "route":
            r = kg.route(it["origin"], it["dest"], it["aircraft"], frozenset(it["avoid"]))
            out["data"] = {"status": r["status"], "codes": r.get("codes"), "km": r.get("total_km")}
            out["notes"] = it["notes"]
            facts = self._route_facts(r)
            ev.extend(facts)
            if r["status"] == "ok":
                out["approved_routes"].append(r["codes"])
                for alt in r.get("alternatives", []):
                    out["approved_routes"].append(alt["codes"])
            base = self._route_text(r, it)
            out["data"]["result"] = r
        elif ty == "explain":
            a, b = it["airports"][0], it["airports"][1]
            ac = it["aircraft"]
            s = kg.seg_by_pair.get(frozenset((a, b)))
            if s is None:
                base = "There is no direct route segment between %s and %s in the network, so a direct flight is not modelled." % (kg.code(a), kg.code(b))
            else:
                why = kg.why_not_feasible(s, ac)
                if why:
                    base = "The direct segment %s-%s (%.0f km) is NOT feasible for the %s: %s." % (kg.code(a), kg.code(b), kg.seg_dist(s), kg.name(ac), "; ".join(why))
                    for b_ in kg.g.objects(s, F("blockedBy")):
                        ev.append("%s fd:blockedBy %s [inferred: R2]" % (kg.name(s), kg.name(b_)))
                    if kg.g.has(s, F("exceedsRangeOf"), ac):
                        ev.append("%s fd:exceedsRangeOf %s [inferred: R3]" % (kg.name(s), kg.name(ac)))
                else:
                    base = "The direct segment %s-%s (%.0f km) IS feasible for the %s: it is not blocked, within range, and both runways and operational status are suitable." % (
                        kg.code(a), kg.code(b), kg.seg_dist(s), kg.name(ac))
                    ev.append("%s fd:isFeasibleFor %s [inferred: R4]" % (kg.name(s), kg.name(ac)))
                    out["approved_routes"].append([kg.code(a), kg.code(b)])
            out["data"] = {"segment": None if s is None else kg.name(s)}
        elif ty == "diversion":
            sc = kg.scenario(it["scenario"])
            if sc is None:
                base = "Unknown scenario %s (available: S1-S6)." % it["scenario"]
            else:
                rows = kg.scenario_candidates(it["scenario"])
                out["data"] = {"scenario": sc["id"], "candidates": [(c, d) for c, _, d, _ in rows]}
                if not rows:
                    base = "Scenario %s (%s, %s with %d km remaining): there is NO suitable, operational airport within range." % (sc["id"], sc["label"], kg.name(sc["aircraft"]), sc["remaining"])
                else:
                    top = ", ".join("%s (%.0f km)" % (c, d) for c, _, d, _ in rows[:8])
                    base = "Scenario %s (%s, %s, %d km remaining): %d diversion candidate%s, nearest first: %s%s." % (
                        sc["id"], sc["label"], kg.name(sc["aircraft"]), sc["remaining"], len(rows), "" if len(rows) == 1 else "s", top, " ..." if len(rows) > 8 else "")
                for c, _, d, L in rows[:6]:
                    ev.append("%s fd:hasDiversionCandidate %s - %.0f km, longest runway %d m [inferred: R5]" % (sc["id"], c, d, L))
        elif ty == "diversion_adhoc":
            rows, rej = kg.diversions(it["aircraft"], it["lat"], it["lon"], it["remaining"])
            out["data"] = {"candidates": [(c, d) for c, _, d, _ in rows]}
            if rows:
                base = "For the %s at (%.2f, %.2f) with %d km remaining: %d candidate%s, nearest first: %s." % (
                    kg.name(it["aircraft"]), it["lat"], it["lon"], it["remaining"], len(rows), "" if len(rows) == 1 else "s", ", ".join("%s (%.0f km)" % (c, d) for c, _, d, _ in rows[:8]))
            else:
                base = "For the %s at (%.2f, %.2f) with %d km remaining there is NO suitable, operational airport in range." % (kg.name(it["aircraft"]), it["lat"], it["lon"], it["remaining"])
            if rej:
                base += " Excluded within range: " + "; ".join("%s (%.0f km, %s)" % r for r in rej[:5]) + "."
            for c, _, d, L in rows[:6]:
                ev.append("%s suitable for %s, %.0f km away, longest runway %d m [inferred: R1]" % (c, kg.name(it["aircraft"]), d, L))
        elif ty == "suitable":
            ac = it["aircraft"]
            ap = sorted(((kg.code(a), py(kg.g.value(a, F("longestRunwayM")))) for a in kg.airports.values() if kg.g.has(a, F("isSuitableFor"), ac)),
                        key=lambda x: (-x[1], x[0]))
            out["data"] = {"airports": [c for c, _ in ap]}
            base = "%d of %d airports can handle the %s (needs a %d m runway): %s." % (len(ap), len(kg.airports), kg.name(ac), py(kg.g.value(ac, F("minRunwayM"))), ", ".join("%s (%d m)" % x for x in ap))
            ev.append("longest runway >= fd:minRunwayM => fd:isSuitableFor [inferred: R0, R1]")
        elif ty == "hubs":
            hubs = sorted(kg.code(a) for a in kg.g.instances(F("HubAirport")))
            out["data"] = {"hubs": hubs}
            base = "Hub airports (at least %d route segments): %s." % (HUB_MIN_DEGREE, ", ".join(hubs))
            ev.append("airports with >= %d incident segments are typed fd:HubAirport [inferred: R6]" % HUB_MIN_DEGREE)
        elif ty == "hazards":
            lines = []
            for h in kg.hazards:
                lines.append("%s - %s, severity %d, %s" % (kg.name(h), kg.g.value(h, F("hazardType")).value, py(kg.g.value(h, F("severity"))),
                                                           "ACTIVE" if TRUE in kg.g.objects(h, F("isActive")) else "inactive"))
            for z in kg.zones:
                lines.append("%s - %s, %s" % (kg.name(z), "restricted" if F("RestrictedZone") in kg.g.types(z) else "advisory only",
                                              "ACTIVE" if TRUE in kg.g.objects(z, F("isActive")) else "inactive"))
            out["data"] = {"items": len(lines)}
            base = "Hazards and zones in the KG (hazards block segments only when ACTIVE and severity >= %d; restricted/prohibited zones when ACTIVE):\n- " % SEVERITY_THRESHOLD + "\n- ".join(lines)
            ev.append("fd:isActive and fd:severity [explicit]")
        out["draft"] = base
        out["answer"], out["answer_source"], out["validation"] = self._finalise(base, out, use_llm)
        return out

    # -------------------------------------------------------------- helpers
    def _route_facts(self, r):
        kg = self.kg
        ev = []
        if r["status"] == "ok":
            for leg in r["legs"]:
                ev.append("segment %s-%s: %.0f km, feasible for %s [inferred: %s - %s]" % (leg["from"], leg["to"], leg["km"], kg.name(r["aircraft"]), leg["rule"], leg["because"]))
        for w in r.get("direct_rejected", []):
            ev.append("direct %s-%s rejected: %s" % (kg.code(r["origin"]), kg.code(r["dest"]), w))
        if r.get("spatial_only"):
            ev.append("spatial-only shortest path %s (%.0f km) rejected: %s" % ("-".join(r["spatial_only"]["codes"]), r["spatial_only"]["km"], " | ".join(r["spatial_only"]["problems"])))
        return ev

    def _route_text(self, r, it):
        kg = self.kg
        ac = kg.name(r["aircraft"])
        notes = (" " + " ".join(it["notes"])) if it["notes"] else ""
        if r["status"] == "trivial":
            return r["message"]
        if r["status"] == "no_route":
            txt = r["message"]
            if r.get("direct_rejected"):
                txt += " Direct leg problems: " + "; ".join(r["direct_rejected"]) + "."
            if r.get("shortest_unconstrained"):
                u = r["shortest_unconstrained"]
                txt += " The purely geographic shortest path %s (%.0f km) is rejected: %s." % ("-".join(u["codes"]), u["km"], " | ".join(u["problems"]))
            return txt + notes
        legs = "; ".join("%s to %s %.0f km" % (l["from"], l["to"], l["km"]) for l in r["legs"])
        txt = "Recommended route for the %s: %s (%d leg%s, %.0f km total, about %.1f h at cruise). Legs: %s." % (
            ac, "-".join(r["codes"]), len(r["legs"]), "" if len(r["legs"]) == 1 else "s", r["total_km"], r["time_h"], legs)
        if r.get("direct_rejected"):
            txt += " The direct %s-%s leg is not allowed: %s." % (kg.code(r["origin"]), kg.code(r["dest"]), "; ".join(r["direct_rejected"]))
        if r.get("spatial_only"):
            txt += " A purely spatial router would pick %s (%.0f km), which is not allowed: %s." % ("-".join(r["spatial_only"]["codes"]), r["spatial_only"]["km"], " | ".join(r["spatial_only"]["problems"]))
        if r.get("alternatives"):
            txt += " Alternatives: " + "; ".join("%s (%.0f km)" % ("-".join(a["codes"]), a["km"]) for a in r["alternatives"]) + "."
        txt += " Every leg was re-validated against the graph: %s." % ("passed" if r["revalidation"]["valid"] else "FAILED - " + "; ".join(r["revalidation"]["problems"]))
        return txt + notes

    def _finalise(self, base, out, use_llm):
        """Verbalise (LLM optional) then re-validate against the graph; fall back to the KG draft on any violation."""
        ans, src = base, "knowledge-graph verbaliser (no LLM)"
        if use_llm and llm.available():
            sysmsg = ("You are a flight-dispatch assistant for an academic prototype. Rewrite the DRAFT as a short, clear answer for a dispatcher. "
                      "Use ONLY airports, routes and numbers that appear in the DRAFT or EVIDENCE. Never invent or alter routes, distances or reasons. "
                      "Keep every route exactly as given.")
            prompt = "QUESTION: %s\n\nDRAFT:\n%s\n\nEVIDENCE:\n%s" % (out["question"], base, "\n".join(out["evidence"]))
            cand = llm.ask(sysmsg, prompt)
            if cand:
                v = self.validate_text(cand, out, base)
                if v["valid"]:
                    return cand, "LLM verbalisation (validated against the KG)", v
                out["warnings"].append("LLM answer rejected by the re-validation guard: " + "; ".join(v["problems"]) + " - showing the KG-derived answer instead.")
        return ans, src, self.validate_text(ans, out, base)

    NEG = re.compile(r"\b(not|cannot|can't|blocked|infeasible|rejected|exceeds|no |never|unsafe|avoid|violat|prohibit)", re.I)

    def validate_text(self, text, out, draft):
        """Guard: (1) every airport code is known and allowed, (2) every presented route is approved or independently valid,
        (3) every large number appears in the draft/evidence."""
        kg = self.kg
        problems = []
        allowed_text = draft + " " + " ".join(out["evidence"]) + " " + out["question"]
        allowed_codes = set(re.findall(r"\b[A-Z]{3,4}\b", allowed_text))
        known = set(kg.airports) | set(kg.by_icao)
        for c in set(re.findall(r"\b[A-Z]{3,4}\b", text)):
            if c in known and c not in allowed_codes:
                problems.append("airport %s is not supported by the retrieved evidence" % c)
        ac = None
        m = re.search(r"aircraft_uri", "")
        for sent in re.split(r"(?<=[.!?])\s+|\n", text):
            if self.NEG.search(sent):
                continue
            for seq in re.findall(r"\b[A-Z]{3}(?:\s*(?:->|→|–|—|-|to)\s*[A-Z]{3})+\b", sent):
                codes = re.findall(r"[A-Z]{3}", seq)
                codes = [c for c in codes if c in kg.airports]
                if len(codes) < 2:
                    continue
                if codes in out["approved_routes"]:
                    continue
                legs_ok = {frozenset(p) for r_ in out["approved_routes"] for p in zip(r_, r_[1:])}
                if all(frozenset(p) in legs_ok for p in zip(codes, codes[1:])):
                    continue
                acx = out.get("data", {}).get("result", {}).get("aircraft")
                if acx is None:
                    continue
                v = kg.validate_route(codes, acx, frozenset(out.get("data", {}).get("result", {}).get("avoid", [])))
                if not v["valid"]:
                    problems.append("route %s is not feasible: %s" % ("-".join(codes), "; ".join(v["problems"])))
                elif codes not in out["approved_routes"] and out["intent"] == "route":
                    problems.append("route %s was not produced by the KG search" % "-".join(codes))
        nums = {int(round(float(x))) for x in re.findall(r"\d+(?:\.\d+)?", allowed_text)}
        for x in re.findall(r"\b\d{3,}(?:\.\d+)?\b", text):
            if int(round(float(x))) not in nums and not any(abs(int(round(float(x))) - n) <= 1 for n in nums):
                problems.append("number %s is not in the retrieved evidence" % x)
        return {"valid": not problems, "problems": problems}


def render(out, show_sparql=True):
    lines = ["Q: " + out["question"], "", "ANSWER (%s):" % out.get("answer_source", ""), out["answer"], ""]
    if out.get("evidence"):
        lines.append("EVIDENCE (explicit vs inferred facts in the KG):")
        lines.extend(" - " + e for e in out["evidence"])
        lines.append("")
    for w in out.get("warnings", []):
        lines.append("WARNING: " + w)
    lines.append("VALIDATION: " + ("passed" if out["validation"]["valid"] else "FAILED: " + "; ".join(out["validation"]["problems"])))
    if show_sparql and out.get("sparql"):
        lines += ["", "SPARQL used for retrieval:", out["sparql"]]
    return "\n".join(lines)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Flight dispatch GraphRAG copilot (academic prototype)")
    ap.add_argument("question", nargs="*", help="natural-language request")
    ap.add_argument("--no-llm", action="store_true", help="never call an LLM")
    ap.add_argument("--no-sparql", action="store_true"); ap.add_argument("--json", action="store_true")
    ap.add_argument("-i", "--interactive", action="store_true")
    a = ap.parse_args(argv)
    cp = Copilot()
    def go(q):
        o = cp.answer(q, use_llm=not a.no_llm)
        if a.json:
            o = {k: v for k, v in o.items() if k != "data"}
            print(json.dumps(o, indent=1, default=str))
        else:
            print(render(o, not a.no_sparql))
    if a.interactive or not a.question:
        print("Flight dispatch copilot - academic prototype, not for operational use. Type a request (empty line to quit).")
        while True:
            try:
                q = input("> ").strip()
            except EOFError:
                break
            if not q:
                break
            go(q); print()
    else:
        go(" ".join(a.question))


if __name__ == "__main__":
    main()
