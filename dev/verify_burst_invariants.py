#!/usr/bin/env python3
"""Mechanical per-burst invariants — every defect the 2026-08-16/17 campaign
found, encoded as a check that runs in seconds.

Consolidation principle (PI, 2026-08-17: "consolidating what we had built and
make the agentic system work correctly"): a rule written in prose is a rule that
will be broken. Each check below exists because something actually went wrong,
and each names the incident so nobody weakens it without knowing the cost.

Usage:
  verify_burst_invariants.py --trig bn090530760            # one burst
  verify_burst_invariants.py --all                          # every burst with products
  verify_burst_invariants.py --trig <T> --paper paper/GRB090530
Exit code 0 = all invariants hold; 1 = at least one FAIL.
"""
import argparse, glob, json, os, re, sys
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OK, FAIL, SKIP = "PASS", "FAIL", "skip"


class Checks:
    def __init__(self, trig, paper_dir=None):
        self.trig, self.paper = trig, paper_dir
        self.rows = []

    def add(self, name, status, detail=""):
        self.rows.append((name, status, detail))

    # --- I1: the canonical table must hold the full model menu ---------------
    def i1_model_count(self):
        p = f"results/convention_check/{self.trig}/spectral_fits.ecsv"
        if not os.path.exists(p):
            return self.add("I1 24-model table", SKIP, "no canonical table")
        t = Table.read(p)
        n = len({c[:-4] for c in t.colnames if c.endswith("_AIC")})
        self.add("I1 24-model table", OK if n == 24 else FAIL,
                 f"{n} models x {len(t)} spectra "
                 f"(incident: NR-8 family-merge dropped 6 models silently)")

    # --- I2: step-9 QC must come from the canonical table, not sweep106 ------
    def i2_step9_provenance(self):
        stale = f"results/sweep106/{self.trig}/{self.trig}/spectral_fits.ecsv"
        png = f"results/sweep106/{self.trig}/{self.trig}_step9_qc.png"
        if not os.path.exists(png):
            return self.add("I2 step9 canonical", SKIP, "no step9 figure")
        marker = f"logs/campaign20/products/{self.trig}.t44b"
        if os.path.exists(marker):
            self.add("I2 step9 canonical", OK, "rebuilt via canonical shim")
        elif os.path.exists(stale):
            self.add("I2 step9 canonical", FAIL,
                     "stale sweep106 table exists and no t44b rebuild marker "
                     "(incident: b4 step9 contradicted its own paper's SEDs)")
        else:
            self.add("I2 step9 canonical", OK, "no stale table present")

    # --- I3: montages must show every model, refusals labelled --------------
    def i3_montage_completeness(self):
        mons = sorted(glob.glob(
            f"results/convention_check/sed_grid_{self.trig}/montage/*_montage_*.json"))
        if not mons:
            return self.add("I3 montage completeness", SKIP, "no montages")
        bad = []
        for m in mons:
            try:
                d = json.load(open(m))
            except Exception:
                bad.append(os.path.basename(m) + ":unreadable"); continue
            if d.get("n_panels") != 24:
                bad.append(f"{os.path.basename(m)}:{d.get('n_panels')} panels")
        self.add("I3 montage completeness", OK if not bad else FAIL,
                 f"{len(mons)} montages"
                 + ("" if not bad else "; " + "; ".join(bad[:3]))
                 + " (incident: 41e skipped NaN-AIC models, so engine-FAIL "
                   "cells were structurally invisible)")

    # --- I4: engine-FAIL cells must be visible in the montage sidecars ------
    def i4_enginefail_disclosed(self):
        p = f"results/convention_check/{self.trig}/spectral_fits.ecsv"
        if not os.path.exists(p):
            return self.add("I4 engine-FAIL disclosed", SKIP, "no table")
        note = (f"results/convention_check/sed_grid_{self.trig}/"
                "BROADBAND_NO_PANELS.txt")
        if os.path.exists(note):
            return self.add("I4 engine-FAIL disclosed", OK,
                            "broadband burst: SED grid unavailable and DISCLOSED "
                            "(LAT in fit, renderer has no LAT support)")
        t = Table.read(p)
        models = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})
        fails = set()
        for row in t:
            tag = "TINT" if int(row["BLOCK"]) == -1 else f"bin{int(row['BLOCK'])}"
            for m in models:
                sc = f"{m}_STATUS"
                if (sc in t.colnames and str(row[sc]).strip() == "FAIL") or \
                        not np.isfinite(float(row[f"{m}_AIC"])):
                    fails.add((tag, m))
        if not fails:
            return self.add("I4 engine-FAIL disclosed", OK, "no engine failures")
        missing = []
        for tag, m in fails:
            j = (f"results/convention_check/sed_grid_{self.trig}/montage/"
                 f"{self.trig}_montage_{tag}.json")
            if not os.path.exists(j):
                missing.append(f"{tag}/{m}:no montage"); continue
            d = json.load(open(j))
            if m not in (d.get("order") or []):
                missing.append(f"{tag}/{m}:absent from montage")
        self.add("I4 engine-FAIL disclosed", OK if not missing else FAIL,
                 f"{len(fails)} engine-FAIL cell(s)"
                 + ("" if not missing else "; " + "; ".join(missing[:3])))

    # --- I5: figure sidecar script hashes must match the scripts on disk ----
    def i5_script_hashes(self):
        import hashlib
        seen, bad = {}, []
        for p in glob.glob(f"results/convention_check/sed_grid_{self.trig}/*.json") + \
                 glob.glob(f"results/sweep106/{self.trig}/*.json"):
            try:
                d = json.load(open(p))
            except Exception:
                continue
            s, h = d.get("script"), d.get("script_sha256")
            if s and h:
                seen.setdefault(os.path.basename(s), h)
        if not seen:
            return self.add("I5 script hashes", SKIP, "no sidecars with hashes")
        for s, h in seen.items():
            for cand in (os.path.join("scripts", s), os.path.join("dev", s)):
                if os.path.exists(cand):
                    disk = hashlib.sha256(open(cand, "rb").read()).hexdigest()
                    if disk != h:
                        bad.append(s)
                    break
        self.add("I5 script hashes", OK if not bad else FAIL,
                 f"{len(seen)} producing scripts"
                 + ("" if not bad else f"; CHANGED since render: {', '.join(bad)}"))

    # --- I6: every paper figure must exist, case-exact ----------------------
    def i6_paper_figures(self):
        if not self.paper:
            return self.add("I6 paper figures", SKIP, "no paper dir given")
        tex = os.path.join(self.paper, "main.tex")
        if not os.path.exists(tex):
            return self.add("I6 paper figures", SKIP, "no main.tex")
        want = re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", open(tex).read())
        missing = [w for w in want
                   if not os.path.exists(os.path.join(self.paper, w))]
        self.add("I6 paper figures", OK if not missing else FAIL,
                 f"{len(want)} referenced"
                 + ("" if not missing else f"; MISSING {missing[:3]}")
                 + " (incident: uppercase/lowercase mismatch broke a Linux build)")

    # --- I7: the paper's winner claims must match the canonical table -------
    def i7_paper_winners(self):
        if not self.paper:
            return self.add("I7 paper winners", SKIP, "no paper dir")
        p = f"results/convention_check/{self.trig}/spectral_fits.ecsv"
        tex = os.path.join(self.paper, "main.tex")
        if not (os.path.exists(p) and os.path.exists(tex)):
            return self.add("I7 paper winners", SKIP, "missing inputs")
        t = Table.read(p)
        models = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})
        row = t[[int(r["BLOCK"]) == -1 for r in t]]
        if not len(row):
            return self.add("I7 paper winners", SKIP, "no TINT row")
        aics = {m: float(row[0][f"{m}_AIC"]) for m in models
                if np.isfinite(row[0][f"{m}_AIC"])}
        win = min(aics, key=aics.get)
        body = open(tex).read()
        # the integrated winner's AIC should appear in the text somewhere
        val = f"{aics[win]:.1f}"
        self.add("I7 paper winners", OK if val in body else FAIL,
                 f"TINT winner {win} AIC={val}"
                 + ("" if val in body else " NOT found in main.tex"))

    # --- I8: notebook must read the production selections catalog ----------
    def i8_notebook_catalog(self):
        nb = "notebooks/Two_Breaks_single_GRB_pipeline.ipynb"
        if not os.path.exists(nb):
            return self.add("I8 notebook catalog", SKIP, "no notebook")
        src = open(nb).read()
        bad = "background_intervals_human_clean.ecsv" in src and \
              "GRB_BKG_CATALOG" not in src
        self.add("I8 notebook catalog", FAIL if bad else OK,
                 "notebook must default to the production catalog "
                 "(incident: it read an 89-burst subset; 17 bursts, incl. a "
                 "papered one, could not be reproduced)")

    # --- I9: the trust anchor must stay LLM-free ---------------------------
    def i9_notebook_llm_free(self):
        nb = "notebooks/Two_Breaks_single_GRB_pipeline.ipynb"
        if not os.path.exists(nb):
            return self.add("I9 notebook LLM-free", SKIP, "no notebook")
        src = open(nb).read()
        hits = [b for b in ("grb_llm", "anthropic", "ANTHROPIC_API_KEY") if b in src]
        self.add("I9 notebook LLM-free", FAIL if hits else OK,
                 "PI ruling: the fitting notebook contains no LLM calls"
                 + (f"; FOUND {hits}" if hits else ""))

    # --- I10: published baselines must not be overwritten ------------------
    def i10_protected_baselines(self):
        prot = {"bn081125496", "bn081222204"}
        if self.trig not in prot:
            return self.add("I10 protected baseline", SKIP, "not a baseline burst")
        src = open("dev/merge_campaign_families.py").read()
        self.add("I10 protected baseline", OK if "PROTECTED" in src else FAIL,
                 "merge tool must refuse to touch papers #1/#2 tables")

    def run(self):
        for m in sorted(x for x in dir(self) if x.startswith("i")):
            try:
                getattr(self, m)()
            except Exception as exc:
                self.add(m, FAIL, f"checker crashed: {type(exc).__name__}: {exc}")
        return self.rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--paper")
    a = ap.parse_args()
    os.chdir(ROOT)
    trigs = ([os.path.basename(d) for d in
              sorted(glob.glob("results/convention_check/bn*"))
              if os.path.isdir(d)]
             if a.all else [a.trig])
    paper_of = {"bn081125496": "paper/GRB081125496", "bn081222204": "paper/GRB081222",
                "bn090530760": "paper/GRB090530", "bn090620400": "paper/GRB090620",
                "bn090719063": "paper/GRB090719", "bn090804940": "paper/GRB090804",
                "bn090809978": "paper/GRB090809"}
    nfail = 0
    for trig in trigs:
        if not trig:
            continue
        paper = a.paper or paper_of.get(trig)
        rows = Checks(trig, paper).run()
        bad = [r for r in rows if r[1] == FAIL]
        nfail += len(bad)
        head = f"{trig}: {sum(1 for r in rows if r[1]==OK)} pass, " \
               f"{len(bad)} FAIL, {sum(1 for r in rows if r[1]==SKIP)} skip"
        print(("\n" + head) if len(trigs) > 1 else f"\n{head}")
        for name, status, detail in rows:
            if len(trigs) > 1 and status != FAIL:
                continue
            print(f"  [{status}] {name}: {detail}")
    print(f"\nTOTAL FAILURES: {nfail}")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
