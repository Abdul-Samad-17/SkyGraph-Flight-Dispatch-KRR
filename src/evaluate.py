"""Phase 3 evaluation: KG-grounded copilot vs gold answers computed independently from the raw data,
guard-rail (hallucination) tests, and an optional LLM-only baseline (needs ANTHROPIC_API_KEY)."""
import os, sys, re, json, heapq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from copilot import *
import independent_check as ic
import llm

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "Results")


def gold_route(x, ac_id, src, dst):
    """Independent Dijkstra over the independently computed feasible segment set (IATA codes in/out)."""
    IA, A = x["IA"], x["A"]
    adj = {}
    for (a, b), acid in [(s, ac_id) for s in x["segs"]]:
        if (((a, b), acid) in x["feasible"]):
            d = x["dist"][(a, b)]
            adj.setdefault(a, []).append((b, d)); adj.setdefault(b, []).append((a, d))
    s, t = IA[src][0], IA[dst][0]
    pq, seen = [(0.0, IA[src][1], s, [s])], {}
    while pq:
        d, _, n, path = heapq.heappop(pq)
        if n in seen:
            continue
        seen[n] = d
        if n == t:
            return [A[i][1] for i in path], round(d, 1)
        for m, w in sorted(adj.get(n, [])):
            if m not in seen:
                heapq.heappush(pq, (round(d + w, 6), A[m][1], m, path + [m]))
    return None, None


QUESTIONS = [
 ("E1", "Find an alternate route from Karachi to Dubai for a B737-800", ("route", "B737-800", "KHI", "DXB")),
 ("E2", "Route from Islamabad to Dubai for an A380", ("route", "A380-800", "ISB", "DXB")),
 ("E3", "Find a route from Islamabad to London for an A320", ("route", "A320-200", "ISB", "LHR")),
 ("E4", "Find an alternate route avoiding the thunderstorm from Lahore to Doha for a B787-9", ("route", "B787-9", "LHE", "DOH")),
 ("E5", "Route from Islamabad to Chitral for an ATR72", ("route", "ATR72-600", "ISB", "CJL")),
 ("E6", "Route from Islamabad to Gilgit for an ATR72", ("route", "ATR72-600", "ISB", "GIL")),
 ("E7", "Find a route from Chitral to Dubai for an A320", ("route", "A320-200", "CJL", "DXB")),
 ("E8", "Route from Karachi to Islamabad for an ATR72", ("route", "ATR72-600", "KHI", "ISB")),
 ("E9", "Diversion candidates for scenario S1", ("div", "S1")),
 ("E10", "Diversion candidates for scenario S6", ("div", "S6")),
 ("E11", "Which airports can handle an A380?", ("suit", "A380-800")),
 ("E12", "Why can't an A380 fly Karachi to Dubai direct?", ("explain", "A380-800", "KHI", "DXB")),
]


def evaluate(cp, x):
    rows = []
    for qid, text, spec in QUESTIONS:
        o = cp.answer(text, use_llm=False)
        ok, detail = False, ""
        if spec[0] == "route":
            _, acid, s, d = spec
            codes, km = gold_route(x, acid, s, d)
            got = o["data"].get("codes"); gkm = o["data"].get("km")
            if codes is None:
                ok = o["data"].get("status") in ("no_route",) and got is None
                detail = "gold: no feasible route; copilot status=%s" % o["data"].get("status")
            else:
                ok = (got == codes and abs(gkm - km) < 0.11)
                detail = "gold %s %.1f km | copilot %s %s km" % ("-".join(codes), km, "-".join(got) if got else None, gkm)
            if ok and o["data"].get("result", {}).get("status") == "ok":
                ok = o["validation"]["valid"] and o["data"]["result"]["revalidation"]["valid"]
        elif spec[0] == "div":
            sid = spec[1]
            gold = [(x["A"][i][1], d) for d, i in x["div"][sid]]
            got = o["data"].get("candidates", [])
            ok = [c for c, _ in got] == [c for c, _ in gold] and all(abs(a[1] - b[1]) < 0.11 for a, b in zip(got, gold))
            detail = "gold %d candidates | copilot %d" % (len(gold), len(got))
        elif spec[0] == "suit":
            gold = sorted(x["A"][i][1] for (i, ac) in x["suitable"] if ac == spec[1])
            got = sorted(o["data"].get("airports", []))
            ok = gold == got; detail = "gold %d airports | copilot %d" % (len(gold), len(got))
        elif spec[0] == "explain":
            _, acid, s, d = spec
            seg = tuple(sorted((x["IA"][s][0], x["IA"][d][0])))
            key = [k for k in x["segs"] if tuple(sorted(k)) == seg][0]
            gold_blocked = key in x["blocked"]
            ok = gold_blocked and "NOT feasible" in o["answer"] and "Alpha" in o["answer"]
            detail = "gold blocked by %s" % x["blocked"].get(key)
        rows.append({"id": qid, "question": text, "pass": bool(ok), "detail": detail, "validation_passed": o["validation"]["valid"],
                     "answer": o["answer"][:400]})
    return rows


def guard_tests(cp):
    """Simulated hallucinated LLM answers: the validator must reject every bad one and accept the good one."""
    q = "Find an alternate route from Karachi to Dubai for a B737-800"
    base = cp.answer(q, use_llm=False)
    cases = [
        ("faithful KG answer", base["answer"], True),
        ("direct blocked leg presented as valid", "Fly KHI-DXB direct, 1188 km, it is the best option.", False),
        ("airport not in evidence", "Recommended route: KHI-UET-DXB via LHR is also possible.", False),
        ("invented distance", "Recommended route KHI-UET-DXB totals 5000 km.", False),
        ("route that does not exist", "Recommended route: KHI-BKK-DXB (1861 km).", False),
    ]
    out = []
    for name, text, expect_ok in cases:
        v = cp.validate_text(text, base, base["draft"])
        out.append({"case": name, "expected_valid": expect_ok, "validator_valid": v["valid"], "ok": v["valid"] == expect_ok, "problems": v["problems"]})
    q2 = "Find a route from Chitral to Dubai for an A320"
    # range violation: ATR on a 1926 km leg
    atr = cp.answer("Route from Islamabad to Dubai for an ATR72", use_llm=False)
    v = cp.validate_text("Recommended route for the ATR 72-600: ISB-DXB (1926 km).", atr, atr["draft"])
    out.append({"case": "leg beyond ATR range presented as valid", "expected_valid": False, "validator_valid": v["valid"], "ok": not v["valid"], "problems": v["problems"]})
    return out


def llm_only_baseline(cp, x):
    if not llm.available():
        return [{"id": qid, "status": "NOT RUN (set ANTHROPIC_API_KEY to run the LLM-only baseline)"} for qid, _, _ in QUESTIONS]
    rows = []
    for qid, text, spec in QUESTIONS:
        ans = llm.ask("You are a flight dispatch assistant. Answer concisely.", text)
        problems = []
        if ans and spec[0] == "route":
            ac = cp.kg.aircraft[spec[1]]
            for seq in re.findall(r"\b[A-Z]{3}(?:\s*(?:->|→|–|—|-|to)\s*[A-Z]{3})+\b", ans):
                codes = [c for c in re.findall(r"[A-Z]{3}", seq) if c in cp.kg.airports]
                if len(codes) >= 2:
                    v = cp.kg.validate_route(codes, ac)
                    if not v["valid"]:
                        problems.append("%s: %s" % ("-".join(codes), "; ".join(v["problems"])))
        rows.append({"id": qid, "status": "RUN" if ans else "API ERROR", "answer": (ans or "")[:400], "kg_violations": problems})
    return rows


def main():
    cp = Copilot(); x = ic.compute()
    rows = evaluate(cp, x)
    guard = guard_tests(cp)
    base = llm_only_baseline(cp, x)
    p = sum(r["pass"] for r in rows)
    out = {"kg_grounded": rows, "kg_grounded_pass": "%d/%d" % (p, len(rows)), "guard_tests": guard, "llm_only": base}
    with open(os.path.join(RES, "phase3_evaluation.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    md = ["# Phase 3 evaluation", "", "## KG-grounded copilot vs independently computed gold answers", "",
          "| ID | Question | Result | Detail |", "|---|---|---|---|"]
    for r in rows:
        md.append("| %s | %s | %s | %s |" % (r["id"], r["question"], "PASS" if r["pass"] else "FAIL", r["detail"]))
    md += ["", "**%d / %d correct.** Gold answers come from `src/independent_check.py` (recomputed from the CSV data with no RDF/rules involved).  " % (p, len(rows)), "",
           "## Re-validation guard against hallucinated answers (simulated LLM outputs)", "", "| Case | Should be accepted | Validator accepted | Correct | Problems found |", "|---|---|---|---|---|"]
    for g_ in guard:
        md.append("| %s | %s | %s | %s | %s |" % (g_["case"], g_["expected_valid"], g_["validator_valid"], "yes" if g_["ok"] else "NO", "; ".join(g_["problems"]) or "-"))
    md += ["", "## LLM-only baseline (no KG)", ""]
    if base and base[0]["status"].startswith("NOT RUN"):
        md.append("Not run in this build (no API key available offline). Run `ANTHROPIC_API_KEY=... python src/evaluate.py` to fill this section: each LLM-only route is audited against the KG and violations are listed.")
    else:
        md += ["| ID | Status | KG violations in the LLM-only answer |", "|---|---|---|"]
        for r in base:
            md.append("| %s | %s | %s |" % (r["id"], r["status"], "; ".join(r.get("kg_violations", [])) or "none found"))
    with open(os.path.join(RES, "phase3_evaluation.md"), "w") as f:
        f.write("\n".join(md))
    print("KG-grounded:", out["kg_grounded_pass"])
    for r in rows:
        print(" ", r["id"], "PASS" if r["pass"] else "FAIL", "|", r["detail"])
    for g_ in guard:
        print(" guard:", g_["case"], "OK" if g_["ok"] else "WRONG", g_["problems"][:1])


if __name__ == "__main__":
    main()
