#!/usr/bin/env python
"""scripts/00_inventory.py — WHAT ALREADY EXISTS. Run this BEFORE building anything.

Vikas, 2026-08-13: *"should we make it hardwired that you work like an integrated
system that can go beyond but first look at the tools if they are already existing"*.

The rule lives at the top of AGENTS.md; this is the tool that makes obeying it cheaper
than ignoring it. It reads every script's own docstring and CLI, so it cannot go stale
the way a hand-written list does.

    python scripts/00_inventory.py                 # everything, grouped
    python scripts/00_inventory.py --find lightcurve   # search purpose + name + flags
    python scripts/00_inventory.py --produces png      # what makes figures

An entry here is a COMMITMENT: if a tool exists for a job, extend it rather than
writing a second one. Two implementations of one job is how a fixed bug comes back.
"""
import os, re, ast, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# cross-project tools that count as "already existing" (AGENTS.md)
EXTERNAL = [
    ("~/Desktop/LATBright/GRB260226A/plot_config.py",
     "figure style: apply_pub_style() + PUB — the reference implementation"),
    ("~/Desktop/Projects/reference_general_figure_style.md",
     "THE figure authority (cross-project default; project files may not contradict it)"),
    ("~/Desktop/LATBright/skills/",
     "GCN intelligence, QPO search, bibliography (ApJ), tables"),
    ("~/Desktop/Projects/CaptionHelper/",
     "caption-suggest: retrieval over ~8k published figure captions"),
    ("~/Desktop/Projects/GRB_Handbook_Project/grb_pipeline/",
     "the vendored analysis package (temporal.py, lightcurve, statistics)"),
    ("~/Desktop/Projects/Gor_GRBs_Beta/scripts/plot_190114C_with_data.py",
     "WORKING nuFnu-with-DATA plotter WE built: forward-folded unfolding "
     "(nuFnu_data = nuFnu_model*(obs-bkg)/pred), significance rebin (3 sigma / "
     "<=10 ch), per-detector cross-norm, delchi panels. READ THIS BEFORE "
     "touching scripts/41*"),
    ("~/Desktop/Projects/Gor_GRBs_Beta/mev_absorption/",
     "absorbed-Band fitting + GOR_FIG2/FIG_A3 replicas (RA-4)"),
]

GROUPS = [
    ("data & setup", r"^(0[0-9]|1[0-9])_"),
    ("selection & approval", r"(approval|approve|selection|picker|background)"),
    ("binning", r"(2[0-9]_|block)"),
    ("fitting", r"^(10_|29_|model_registry)"),
    ("products & figures", r"(3[0-9]_|4[0-9]_|plot|figure|panel|png)"),
    ("QC, audit & compare", r"(qc|validator|compare|audit|inventory)"),
]


def summarize(path):
    """(purpose, flags) from the file's own docstring + argparse calls."""
    try:
        src = open(path).read()
    except Exception:
        return "", []
    doc = ""
    try:
        mod = ast.parse(src)
        doc = (ast.get_docstring(mod) or "").strip()
    except Exception:
        m = re.search(r'"""(.*?)"""', src, re.S)
        doc = (m.group(1).strip() if m else "")
    # first sentence-ish line that is not the filename echo
    lines = [l.strip() for l in doc.splitlines() if l.strip()]
    purpose = ""
    for l in lines:
        if l.lower().startswith(os.path.basename(path).lower()[:6]):
            l = l.split("--", 1)[-1].split("—", 1)[-1].strip()
        if len(l) > 12:
            purpose = l
            break
    flags = sorted(set(re.findall(r'add_argument\(\s*["\'](--[a-z0-9\-]+)', src)))
    return purpose[:150], flags


def outputs(path):
    """What the script writes, from literal paths/extensions in the source."""
    try:
        src = open(path).read()
    except Exception:
        return []
    out = set()
    for ext in (".png", ".pdf", ".ecsv", ".json", ".md", ".csv", ".ipynb"):
        if re.search(r'["\'][^"\']*\%s' % ext.replace(".", r"\."), src):
            out.add(ext)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--find", help="search name, purpose and flags")
    ap.add_argument("--produces", help="filter by output extension, e.g. png")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "scripts", "*.py")))
    rows = []
    for f in files:
        name = os.path.basename(f)
        if name.startswith("_"):
            continue
        purpose, flags = summarize(f)
        rows.append((name, purpose, flags, outputs(f)))

    if a.find:
        q = a.find.lower()
        rows = [r for r in rows if q in r[0].lower() or q in r[1].lower()
                or any(q in x for x in r[2])]
    if a.produces:
        e = a.produces if a.produces.startswith(".") else "." + a.produces
        rows = [r for r in rows if e in r[3]]

    print(f"\nTOOL INVENTORY — {len(rows)} scripts in {os.path.relpath(ROOT)}/scripts\n"
          f"(AGENTS.md: inventory BEFORE you build. If a tool nearly does the job, "
          f"extend THAT tool.)\n")
    shown = set()
    for gname, pat in GROUPS:
        sel = [r for r in rows if re.search(pat, r[0], re.I) and r[0] not in shown]
        if not sel:
            continue
        print(f"── {gname} " + "─" * max(0, 62 - len(gname)))
        for name, purpose, flags, outs in sel:
            shown.add(name)
            print(f"  {name}")
            if purpose:
                print(f"      {purpose}")
            if flags:
                print(f"      flags: {' '.join(flags[:8])}")
            if outs:
                print(f"      writes: {' '.join(outs)}")
        print()
    rest = [r for r in rows if r[0] not in shown]
    if rest:
        print("── other " + "─" * 62)
        for name, purpose, flags, outs in rest:
            print(f"  {name}\n      {purpose}" if purpose else f"  {name}")
        print()
    if not a.find and not a.produces:
        print("── cross-project tools that also count " + "─" * 32)
        for p, what in EXTERNAL:
            mark = "✓" if os.path.exists(os.path.expanduser(p.rstrip("/"))) else "?"
            print(f"  {mark} {p}\n      {what}")
        print()


if __name__ == "__main__":
    main()
