#!/usr/bin/env python3
"""Per-burst REPRODUCTION RECORD: the exact code state that made the paper.

PI question (2026-08-17): "do you have notebook ready that with final codes and
state of the codes (parameter ranges etc or whatever was final to produce those
plots)?" — the notebook shows the chain; THIS shows the exact state:
  * git commit + whether any producing script was dirty at render time
  * every producing script with its SHA-256 as recorded in the product sidecars
    (so a reader can verify the file on disk is the file that ran)
  * the exact argv of every figure/table producer
  * the model menu WITH ITS PARAMETER BOUNDS as the engine defines them
  * the approved Stage-1 selections and the block table used
Usage: make_repro_record.py --trig <TRIG> [--out <dir>]
"""
import argparse, glob, hashlib, importlib.util, json, os, subprocess, sys
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except Exception:
        return "MISSING"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    T = a.trig
    os.chdir(ROOT)
    L = [f"# {T} — reproduction record",
         "",
         "The exact code state that produced this burst's paper products. Verify",
         "any script by comparing its SHA-256 on disk with the value recorded",
         "here (which came from the product sidecar written at render time).",
         ""]

    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "scripts", "dev"],
                           capture_output=True, text=True).stdout.strip()
    L += ["## Repository state", "",
          f"- commit: `{head}`",
          f"- uncommitted changes under `scripts/`+`dev/` at record time: "
          f"{'YES — see list below' if dirty else 'none'}"]
    if dirty:
        L += ["", "```", dirty, "```"]
    L.append("")

    # producing scripts, from sidecars
    L += ["## Producing scripts (SHA-256 as recorded when each product was made)",
          "", "| script | sha256 recorded | sha256 on disk now | match |",
          "|---|---|---|---|"]
    seen = {}
    for p in sorted(glob.glob(f"results/convention_check/sed_grid_{T}/*.json")) + \
             sorted(glob.glob(f"results/sweep106/{T}/*.json")) + \
             sorted(glob.glob(f"results/convention_check/param_evolution/{T}*.json")):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        s, h = d.get("script"), d.get("script_sha256")
        if s and h and s not in seen:
            seen[s] = h
    for s, h in sorted(seen.items()):
        disk = sha(os.path.join("scripts", s))
        if disk == "MISSING":
            disk = sha(os.path.join("dev", s))
        L.append(f"| `{s}` | `{h[:16]}…` | `{disk[:16]}…` | "
                 f"{'YES' if disk == h else '**NO — script changed since render**'} |")
    L.append("")

    # exact argv per product
    L += ["## Exact commands (argv recorded per product)", "", "```"]
    cmds = set()
    for p in sorted(glob.glob(f"results/convention_check/sed_grid_{T}/*.json")):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if d.get("argv"):
            cmds.add(f"python scripts/{d['script']} " + " ".join(d["argv"]))
    for c in sorted(cmds)[:6]:
        L.append(c)
    if len(cmds) > 6:
        L.append(f"# … {len(cmds)-6} more (one per model/bin panel; same form)")
    L += ["python3 scripts/41e_sed_montage.py --trig " + T,
          "python dev/rebuild_step9_canonical.py --trig " + T,
          "python3 dev/gen_param_tables.py --trig " + T,
          "python scripts/10_spectral_fit_burst.py --trigger " + T +
          " --include-bgo --no-log --models highe \\",
          "    --blocks-file results/sweep106/" + T +
          "/blocks/bb_blocks_spectral_" + T + ".ecsv \\",
          "    --bkg-file results/background_intervals.ecsv --out-dir "
          "results/campaign20_fam/" + T + "_highe",
          "```", ""]

    # model menu with bounds
    L += ["## Model menu and parameter bounds (from the engine, final state)", ""]
    try:
        spec = importlib.util.spec_from_file_location(
            "eng", os.path.join("scripts", "10_spectral_fit_burst.py"))
        eng = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(eng)
        allspecs = (list(eng.MODEL_SPECS) + list(eng.SHAPE_MODEL_SPECS) +
                    list(eng.HIGHE_MODEL_SPECS))
        L += ["| model | prefix | n_params | bounds / notes |", "|---|---|---|---|"]
        for s in allspecs:
            b = s.get("bounds") or s.get("param_bounds") or {}
            btxt = "; ".join(f"{k}∈{v}" for k, v in list(b.items())[:4]) if b else \
                "set in the model builder (see `build` in the spec)"
            L.append(f"| {s.get('name')} | `{s.get('prefix')}` | "
                     f"{s.get('n_params')} | {btxt} |")
        L += ["", "Bounds enforced at fit time (engine source, authoritative):",
              "```"]
        srclines = open(os.path.join("scripts",
                                     "10_spectral_fit_burst.py")).read().splitlines()
        for i, line in enumerate(srclines):
            if ".bounds = (" in line or ".bounds=(" in line:
                L.append(f"{i+1}: {line.strip()}")
        L += ["```", ""]
    except Exception as exc:
        L += [f"(could not import the engine to dump bounds: {exc})", ""]

    # inputs
    L += ["## Inputs (never re-derived)", ""]
    try:
        bk = Table.read("results/background_intervals.ecsv")
        rows = bk[[str(x).strip() == T for x in bk["TRIGGER_NAME"]]]
        L += ["Approved Stage-1 selections (`results/background_intervals.ecsv`):",
              "", "| det | bkg pre | bkg post | source | approved by |", "|---|---|---|---|---|"]
        for r in rows:
            L.append(f"| {str(r['DETECTOR']).strip()} | "
                     f"({float(r['BKG_NEG_START']):.2f}, {float(r['BKG_NEG_STOP']):.2f}) | "
                     f"({float(r['BKG_POS_START']):.2f}, {float(r['BKG_POS_STOP']):.2f}) | "
                     f"({float(r['SRC_START']):.2f}, {float(r['SRC_STOP']):.2f}) | "
                     f"{str(r['APPROVED_BY']).strip() if 'APPROVED_BY' in bk.colnames else '?'} |")
        L.append("")
    except Exception as exc:
        L += [f"(selections unreadable: {exc})", ""]
    blk = f"results/sweep106/{T}/blocks/bb_blocks_spectral_{T}.ecsv"
    L += [f"Block table: `{blk}`",
          f"- sha256 `{sha(blk)[:16]}…`",
          "- reused unchanged from the 2026-08-12 binning run; re-deriving blocks",
          "  per convention would break cross-burst comparability.", ""]
    fits = f"results/convention_check/{T}/spectral_fits.ecsv"
    if os.path.exists(fits):
        t = Table.read(fits)
        n = len({c[:-4] for c in t.colnames if c.endswith("_AIC")})
        L += [f"Canonical fit table: `{fits}`",
              f"- sha256 `{sha(fits)[:16]}…`; {n} models × {len(t)} spectra",
              "- canonicalization: best optimizer minimum per (bin, model) across",
              "  all invocations we possess (multistart luck reaches ΔAIC ≈ 9).", ""]
    L += ["## Notebook", "",
          "`notebooks/Two_Breaks_single_GRB_pipeline.ipynb` (config "
          f"`notebooks/configs/{T}.yaml`) runs the same chain interactively and",
          "contains no LLM calls. It imports the engine above, so the model menu",
          "and bounds it uses are the same objects listed here. It fits one",
          "representative block (the full source window) rather than the whole",
          "per-bin grid — to regenerate the paper's per-bin panels use the",
          "commands in the section above.", ""]
    out_dir = a.out or f"results/sweep106/{T}"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"REPRODUCTION_{T}.md")
    open(path, "w").write("\n".join(L) + "\n")
    print(f"{T}: wrote {path} ({len(seen)} producing scripts, {len(cmds)} argv records)")


if __name__ == "__main__":
    sys.exit(main())
