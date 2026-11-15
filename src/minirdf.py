"""Minimal, dependency-free RDF toolkit: Turtle parser/serializer + indexed triple store.

Supports the Turtle subset used in this project: @prefix/PREFIX, <iri>, prefixed names, `a`,
predicate lists (;), object lists (,), blank-node property lists [ ... ], typed/plain/lang literals,
bare numbers/booleans and # comments. Collections `( ... )` and long (triple-quoted) strings are not used.
"""
import re
from collections import namedtuple, defaultdict

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
XSD = "http://www.w3.org/2001/XMLSchema#"
FD = "https://krr.example.org/fd/ontology#"
FDR = "https://krr.example.org/fd/data/"

RDF_TYPE = RDF + "type"

Lit = namedtuple("Lit", "value datatype lang")     # value always str
BNode = namedtuple("BNode", "id")


def lit(value, datatype=None, lang=None):
    return Lit(str(value), datatype, lang)


def lit_int(v):
    return Lit(str(int(v)), XSD + "integer", None)


def lit_dec(v):
    return Lit(("%.4f" % v).rstrip("0").rstrip(".") if "." in ("%.4f" % v) else str(v), XSD + "decimal", None)


def lit_bool(b):
    return Lit("true" if b else "false", XSD + "boolean", None)


def py(term):
    """Convert a Lit to a native Python value (IRIs/BNodes returned unchanged)."""
    if not isinstance(term, Lit):
        return term
    dt = term.datatype
    if dt == XSD + "integer" or dt == XSD + "nonNegativeInteger":
        return int(term.value)
    if dt == XSD + "decimal" or dt == XSD + "double" or dt == XSD + "float":
        return float(term.value)
    if dt == XSD + "boolean":
        return term.value in ("true", "1")
    return term.value


class TurtleError(Exception):
    pass


_PNAME = re.compile(r"[A-Za-z][A-Za-z0-9_\-]*:[A-Za-z0-9_\-\.%]*|:[A-Za-z0-9_\-\.%]*")
_NUM = re.compile(r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?")


class _Parser:
    def __init__(self, text):
        self.t = text
        self.i = 0
        self.prefixes = {}
        self.triples = []
        self.bn = 0

    def err(self, msg):
        line = self.t.count("\n", 0, self.i) + 1
        raise TurtleError("line %d: %s near %r" % (line, msg, self.t[self.i:self.i + 30]))

    def ws(self):
        t = self.t
        n = len(t)
        while self.i < n:
            c = t[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif c == "#":
                while self.i < n and t[self.i] != "\n":
                    self.i += 1
            else:
                break

    def peek(self):
        self.ws()
        return self.t[self.i] if self.i < len(self.t) else ""

    def startswith(self, s):
        self.ws()
        return self.t.startswith(s, self.i)

    def expect(self, ch):
        self.ws()
        if self.t[self.i:self.i + len(ch)] != ch:
            self.err("expected %r" % ch)
        self.i += len(ch)

    def newb(self):
        self.bn += 1
        return BNode("b%d" % self.bn)

    def parse(self):
        while True:
            self.ws()
            if self.i >= len(self.t):
                break
            if self.startswith("@prefix") or self.t[self.i:self.i + 6].upper() == "PREFIX":
                self.prefix_decl()
            elif self.startswith("@base") or self.t[self.i:self.i + 4].upper() == "BASE":
                self.err("@base not supported")
            else:
                self.statement()
        return self.triples

    def prefix_decl(self):
        sparql = not self.startswith("@prefix")
        self.i += 6 if sparql else 7
        self.ws()
        m = re.compile(r"([A-Za-z][A-Za-z0-9_\-]*)?:").match(self.t, self.i)
        if not m:
            self.err("bad prefix name")
        name = m.group(1) or ""
        self.i = m.end()
        iri = self.iriref()
        self.prefixes[name] = iri
        if not sparql:
            self.expect(".")

    def iriref(self):
        self.ws()
        if self.t[self.i] != "<":
            self.err("expected <iri>")
        j = self.t.index(">", self.i)
        iri = self.t[self.i + 1:j]
        self.i = j + 1
        return iri

    def statement(self):
        subj = self.subject()
        self.pred_obj_list(subj)
        self.expect(".")

    def subject(self):
        c = self.peek()
        if c == "[":
            return self.bnode_plist()
        return self.resource()

    def bnode_plist(self):
        self.expect("[")
        b = self.newb()
        if self.peek() != "]":
            self.pred_obj_list(b)
        self.expect("]")
        return b

    def resource(self):
        c = self.peek()
        if c == "<":
            return self.iriref()
        m = _PNAME.match(self.t, self.i)
        if not m:
            self.err("expected IRI or prefixed name")
        tok = m.group(0)
        if tok.endswith("."):
            tok = tok[:-1]
        self.i += len(tok)
        pfx, local = tok.split(":", 1)
        if pfx not in self.prefixes:
            self.err("unknown prefix %r" % pfx)
        return self.prefixes[pfx] + local

    def pred_obj_list(self, subj):
        while True:
            self.ws()
            if self.t.startswith("a", self.i) and self.t[self.i + 1:self.i + 2] in " \t\r\n":
                self.i += 1
                pred = RDF_TYPE
            else:
                pred = self.resource()
            while True:
                obj = self.obj()
                self.triples.append((subj, pred, obj))
                if self.peek() == ",":
                    self.i += 1
                    continue
                break
            if self.peek() == ";":
                while self.peek() == ";":
                    self.i += 1
                if self.peek() in (".", "]"):
                    break
                continue
            break

    def obj(self):
        c = self.peek()
        if c == "[":
            return self.bnode_plist()
        if c == '"':
            return self.literal()
        if c == "<":
            return self.iriref()
        if self.t.startswith("true", self.i) and not re.match(r"true[A-Za-z0-9_:\-]", self.t[self.i:self.i + 6]):
            self.i += 4
            return Lit("true", XSD + "boolean", None)
        if self.t.startswith("false", self.i) and not re.match(r"false[A-Za-z0-9_:\-]", self.t[self.i:self.i + 7]):
            self.i += 5
            return Lit("false", XSD + "boolean", None)
        m = _NUM.match(self.t, self.i)
        if m and (c.isdigit() or c in "+-."):
            tok = m.group(0)
            self.i = m.end()
            if "e" in tok.lower():
                dt = "double"
            elif "." in tok:
                dt = "decimal"
            else:
                dt = "integer"
            return Lit(tok, XSD + dt, None)
        return self.resource()

    def literal(self):
        t = self.t
        i = self.i + 1
        buf = []
        while True:
            if i >= len(t):
                self.err("unterminated string")
            ch = t[i]
            if ch == "\\":
                nxt = t[i + 1]
                buf.append({"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "'": "'"}.get(nxt, nxt))
                i += 2
                continue
            if ch == '"':
                break
            buf.append(ch)
            i += 1
        self.i = i + 1
        value = "".join(buf)
        if self.t.startswith("^^", self.i):
            self.i += 2
            dt = self.resource() if self.peek() != "<" else self.iriref()
            return Lit(value, dt, None)
        if self.t.startswith("@", self.i):
            m = re.compile(r"@([A-Za-z]+(-[A-Za-z0-9]+)*)").match(t, self.i)
            self.i = m.end()
            return Lit(value, None, m.group(1))
        return Lit(value, None, None)


def parse_turtle(text):
    p = _Parser(text)
    return p.parse()


class Graph:
    def __init__(self, triples=()):
        self.spo = defaultdict(lambda: defaultdict(set))
        self.pos = defaultdict(lambda: defaultdict(set))
        self.osp = defaultdict(lambda: defaultdict(set))
        self._n = 0
        for t in triples:
            self.add(*t)

    def __len__(self):
        return self._n

    def add(self, s, p, o):
        if o in self.spo[s][p]:
            return False
        self.spo[s][p].add(o)
        self.pos[p][o].add(s)
        self.osp[o][s].add(p)
        self._n += 1
        return True

    def has(self, s, p, o):
        return s in self.spo and p in self.spo[s] and o in self.spo[s][p]

    def triples(self, s=None, p=None, o=None):
        if s is not None:
            if s not in self.spo:
                return
            plist = [p] if p is not None else list(self.spo[s].keys())
            for pp in plist:
                for oo in list(self.spo[s].get(pp, ())):
                    if o is None or oo == o:
                        yield (s, pp, oo)
        elif p is not None:
            if p not in self.pos:
                return
            olist = [o] if o is not None else list(self.pos[p].keys())
            for oo in olist:
                for ss in list(self.pos[p].get(oo, ())):
                    yield (ss, p, oo)
        elif o is not None:
            for ss, ps in list(self.osp.get(o, {}).items()):
                for pp in ps:
                    yield (ss, pp, o)
        else:
            for ss in list(self.spo.keys()):
                for pp in list(self.spo[ss].keys()):
                    for oo in list(self.spo[ss][pp]):
                        yield (ss, pp, oo)

    def objects(self, s, p):
        return list(self.spo.get(s, {}).get(p, ()))

    def subjects(self, p, o):
        return list(self.pos.get(p, {}).get(o, ()))

    def value(self, s, p, default=None):
        objs = self.spo.get(s, {}).get(p)
        if not objs:
            return default
        return sorted(objs, key=str)[0]

    def pyvalue(self, s, p, default=None):
        v = self.value(s, p)
        return default if v is None else py(v)

    def types(self, s):
        return set(self.objects(s, RDF_TYPE))

    def instances(self, cls):
        return set(self.subjects(RDF_TYPE, cls))

    def all(self):
        return set(self.triples())

    def update(self, triples):
        n = 0
        for t in triples:
            if self.add(*t):
                n += 1
        return n


# ------------------------------ serializer --------------------------------
_LOCAL_OK = re.compile(r"^[A-Za-z0-9_]([A-Za-z0-9_\-]*[A-Za-z0-9_])?$")


def _esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


class Serializer:
    def __init__(self, prefixes):
        self.prefixes = dict(prefixes)   # name -> iri

    def term(self, t):
        if isinstance(t, Lit):
            v = '"%s"' % _esc(t.value)
            if t.lang:
                return v + "@" + t.lang
            if t.datatype:
                return v + "^^" + self.iri(t.datatype)
            return v
        if isinstance(t, BNode):
            return "_:" + t.id
        return self.iri(t)

    def iri(self, iri):
        if iri == RDF_TYPE:
            return "a"
        best = None
        for name, base in self.prefixes.items():
            if iri.startswith(base):
                local = iri[len(base):]
                if _LOCAL_OK.match(local) and (best is None or len(base) > len(best[1])):
                    best = (name, base, local)
        if best:
            return "%s:%s" % (best[0], best[2])
        return "<%s>" % iri

    def dump(self, triples, header=None):
        out = []
        if header:
            out.extend("# " + l if l else "#" for l in header.split("\n"))
            out.append("")
        for name, base in self.prefixes.items():
            out.append("@prefix %s: <%s> ." % (name, base))
        out.append("")
        by_s = defaultdict(lambda: defaultdict(list))
        for s, p, o in triples:
            by_s[s][p].append(o)
        def key_s(s):
            return str(s)
        for s in sorted(by_s, key=key_s):
            preds = by_s[s]
            plist = sorted(preds, key=lambda p: (p != RDF_TYPE, str(p)))
            lines = []
            for p in plist:
                objs = sorted(preds[p], key=lambda o: (isinstance(o, Lit), str(o)))
                lines.append("    %s %s" % (self.iri(p), " , ".join(self.term(o) for o in objs)))
            out.append(self.term(s) + "\n" + " ;\n".join(lines) + " .")
            out.append("")
        return "\n".join(out)


DEFAULT_PREFIXES = {
    "fd": FD, "fdr": FDR, "owl": OWL, "rdf": RDF, "rdfs": RDFS, "xsd": XSD,
}
