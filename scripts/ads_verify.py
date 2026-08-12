#!/usr/bin/env python
"""Verify the `literature:` citations in notebooks/configs/*.yaml against NASA ADS.

WHAT THIS DOES *NOT* DO
-----------------------
It never writes, invents or edits a `finding:` string, and never sets
`consistent:`. Those are human science judgements (see the Section-10 rule in
scripts/37: literature is "entered/verified by a human ... never auto-filled, to
avoid fabricated values"). This module only answers a narrow, factual question:

    "does the paper this `ref:` names actually exist in ADS, and is it the one
     the author/year/journal fields claim?"

so a typo'd volume or a mis-remembered year is caught before it reaches a draft.

USAGE
    python scripts/ads_verify.py --all                 # every config with literature
    python scripts/ads_verify.py --grb bn110721200     # one burst
    python scripts/ads_verify.py --all --refresh       # ignore cache, re-query ADS

TOKEN
    ADS_DEV_KEY in the environment, else parsed from the repo-root .env.
    Get/rotate one at https://ui.adsabs.harvard.edu/user/settings/token
    With no token this degrades to cache-only and reports UNVERIFIED — it never
    raises, so notebooks stay runnable offline.

STATUSES
    VERIFIED    resolved to one record; claimed surname+year agree
    MISMATCH    resolved, but the claimed surname/year disagree -> FIX THE CONFIG
    AMBIGUOUS   several records matched; needs a DOI/bibcode in the ref
    NOT-FOUND   ADS knows no such paper -> check the citation
    UNVERIFIED  no token and not cached (not a failure)
"""
import os, re, sys, json, time, argparse
from urllib import request, parse, error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "results", "ads_cache.json")
API = "https://api.adsabs.harvard.edu/v1/search/query"
FIELDS = "bibcode,first_author,year,title,doi,volume,page,pub"


# ----------------------------------------------------------------- token
def load_token():
    """ADS_DEV_KEY from the environment, else from the repo-root .env."""
    tok = os.environ.get("ADS_DEV_KEY") or os.environ.get("ADS_TOKEN")
    if tok:
        return tok.strip()
    envf = os.path.join(ROOT, ".env")
    if os.path.exists(envf):
        with open(envf) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() in ("ADS_DEV_KEY", "ADS_TOKEN"):
                    return v.strip().strip('"').strip("'")
    return None


# ----------------------------------------------------------------- cache
def load_cache():
    try:
        with open(CACHE) as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_cache(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(c, fh, indent=1, sort_keys=True)
    os.replace(tmp, CACHE)


# ----------------------------------------------------------------- parsing
BIBCODE_RE = re.compile(r"\b(\d{4}[A-Za-z0-9.&]{5}[\d.]{4}[A-Za-z.][\d.]{4}[A-Z])\b")
DOI_RE     = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", re.I)
ARXIV_RE   = re.compile(r"arxiv:\s*([\d]{4}\.[\d]{4,5})", re.I)
# "Axelsson2012 (ApJ 757, L31)" / "Iyyani 2013 (MNRAS 433, 2739)"
NAME_YEAR  = re.compile(r"([A-Z][A-Za-z'\-]+)\s*,?\s*(?:et al\.?)?\s*\(?(\d{4})")
JOURNAL    = re.compile(r"\(([A-Za-z&.\s]+?)\s+(\d+)\s*,\s*([A-Za-z]?\d+)")


def parse_ref(ref):
    """Pull whatever identifiers a human-written ref string happens to carry."""
    d = {"raw": ref}
    m = DOI_RE.search(ref)
    if m:
        d["doi"] = m.group(1).rstrip(").,;")
    m = ARXIV_RE.search(ref)
    if m:
        d["arxiv"] = m.group(1)
    m = BIBCODE_RE.search(ref)
    if m:
        d["bibcode"] = m.group(1)
    m = NAME_YEAR.search(ref)
    if m:
        d["surname"], d["year"] = m.group(1), m.group(2)
    m = JOURNAL.search(ref)
    if m:
        d["bibstem"] = m.group(1).strip().replace(".", "").replace(" ", "")
        d["volume"], d["page"] = m.group(2), m.group(3)
    return d


def build_queries(d):
    """Ordered ADS queries, most specific first."""
    qs = []
    if d.get("doi"):
        qs.append(f'doi:"{d["doi"]}"')
    if d.get("arxiv"):
        qs.append(f'arxiv:{d["arxiv"]}')
    if d.get("bibcode"):
        qs.append(f'bibcode:{d["bibcode"]}')
    sn, yr = d.get("surname"), d.get("year")
    bs, vol, pg = d.get("bibstem"), d.get("volume"), d.get("page")
    if sn and yr:
        stems = [bs] if bs else []
        # ApJ Letters: ADS indexes bibstem 'ApJL' though the bibcode reads 'ApJ...L'
        if bs == "ApJ" and pg and str(pg).upper().startswith("L"):
            stems = ["ApJL", "ApJ"]
        for stem in stems:
            if vol and pg:
                p = str(pg).lstrip("Ll") if stem == "ApJL" else pg
                qs.append(f'author:"{sn}" year:{yr} bibstem:{stem} volume:{vol} page:{p}')
            if vol:
                qs.append(f'author:"{sn}" year:{yr} bibstem:{stem} volume:{vol}')
            qs.append(f'author:"{sn}" year:{yr} bibstem:{stem}')
        qs.append(f'author:"{sn}" year:{yr}')
    # de-duplicate, keep order
    seen, out = set(), []
    for q in qs:
        if q not in seen:
            seen.add(q); out.append(q)
    return out


# ----------------------------------------------------------------- ADS call
def ads_query(q, token, rows=5, timeout=25):
    url = API + "?" + parse.urlencode({"q": q, "fl": FIELDS, "rows": rows})
    req = request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with request.urlopen(req, timeout=timeout) as fh:
        body = json.loads(fh.read().decode())
    return body["response"]["numFound"], body["response"]["docs"]


def resolve(ref, token, cache, refresh=False):
    """Resolve one ref string -> {status, bibcode, title, ...}. Never raises."""
    key = ref.strip()
    if not refresh and key in cache:
        return cache[key]
    d = parse_ref(ref)
    if token is None:
        return {"status": "UNVERIFIED", "reason": "no ADS token", "parsed": d}
    rec = {"status": "NOT-FOUND", "parsed": d}
    try:
        for q in build_queries(d):
            n, docs = ads_query(q, token)
            if n == 0:
                continue
            if n > 1 and not (d.get("doi") or d.get("bibcode") or d.get("arxiv")):
                # keep looking for a more specific query; remember the ambiguity
                rec = {"status": "AMBIGUOUS", "query": q, "n": n, "parsed": d,
                       "candidates": [x.get("bibcode") for x in docs[:5]]}
                continue
            doc = docs[0]
            rec = {"status": "VERIFIED", "query": q, "n": n, "parsed": d,
                   "bibcode": doc.get("bibcode"),
                   "first_author": doc.get("first_author"),
                   "year": doc.get("year"),
                   "title": (doc.get("title") or [""])[0],
                   "doi": (doc.get("doi") or [None])[0],
                   "pub": doc.get("pub")}
            # cross-check what the human claimed against what ADS returned
            problems = []
            if d.get("surname") and doc.get("first_author"):
                if d["surname"].lower() not in doc["first_author"].lower():
                    problems.append(f'first author is "{doc["first_author"]}", '
                                    f'ref says "{d["surname"]}"')
            if d.get("year") and doc.get("year") and str(d["year"]) != str(doc["year"]):
                problems.append(f'year is {doc["year"]}, ref says {d["year"]}')
            if problems:
                rec["status"] = "MISMATCH"
                rec["problems"] = problems
            break
    except error.HTTPError as e:
        return {"status": "UNVERIFIED", "reason": f"HTTP {e.code}", "parsed": d}
    except Exception as e:
        return {"status": "UNVERIFIED", "reason": f"{type(e).__name__}", "parsed": d}
    rec["_checked_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cache[key] = rec
    return rec


def split_refs(ref):
    """A ref field may cite several papers, separated by ' / '.

    Split only on a WHITESPACE-delimited slash: DOIs contain '/' too
    (10.3847/1538-4357/abf24d) but never with surrounding spaces.
    """
    parts = [p.strip() for p in re.split(r"\s+/\s+", ref) if p.strip()]
    return parts or [ref]


def verify_config(path, token, cache, refresh=False):
    """Verify one config's literature block. Returns list of (ref, record)."""
    import yaml
    with open(path) as fh:
        cfg = yaml.safe_load(fh) or {}
    out = []
    for entry in (cfg.get("literature") or []):
        for ref in split_refs(str(entry.get("ref", ""))):
            out.append((ref, resolve(ref, token, cache, refresh)))
    return out


ICON = {"VERIFIED": "OK  ", "MISMATCH": "FIX ", "AMBIGUOUS": "AMB ",
        "NOT-FOUND": "MISS", "UNVERIFIED": "----"}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grb", help="single trigger, e.g. bn110721200")
    ap.add_argument("--all", action="store_true", help="every config with a literature block")
    ap.add_argument("--refresh", action="store_true", help="ignore cache, re-query ADS")
    a = ap.parse_args()

    token = load_token()
    if token is None:
        print("NOTE: no ADS token (env ADS_DEV_KEY or .env) — cache-only mode.\n")
    cache = load_cache()
    cfgdir = os.path.join(ROOT, "notebooks", "configs")
    if a.grb:
        paths = [os.path.join(cfgdir, f"{a.grb}.yaml")]
    elif a.all:
        import glob
        paths = sorted(glob.glob(os.path.join(cfgdir, "*.yaml")))
    else:
        ap.error("give --grb <trigger> or --all")

    tally = {}
    for p in paths:
        res = verify_config(p, token, cache, a.refresh)
        if not res:
            continue
        print(f"\n=== {os.path.basename(p)} ===")
        for ref, rec in res:
            st = rec["status"]; tally[st] = tally.get(st, 0) + 1
            print(f"  [{ICON.get(st, st)}] {ref[:78]}")
            if st == "VERIFIED":
                print(f"         -> {rec['bibcode']}  {rec['first_author']} ({rec['year']})")
                print(f"            {rec['title'][:88]}")
            elif st == "MISMATCH":
                print(f"         -> {rec['bibcode']}  {rec['first_author']} ({rec['year']})")
                for pr in rec.get("problems", []):
                    print(f"            !! {pr}")
            elif st == "AMBIGUOUS":
                print(f"            {rec.get('n')} matches: {rec.get('candidates')}")
                print(f"            add a DOI or bibcode to the ref to disambiguate")
            elif st == "NOT-FOUND":
                print(f"            no ADS record — check the citation")
            else:
                print(f"            {rec.get('reason', '')}")
    save_cache(cache)
    print(f"\ntally: {tally}   (cache: {CACHE})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
