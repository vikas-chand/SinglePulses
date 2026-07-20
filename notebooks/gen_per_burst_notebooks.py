#!/usr/bin/env python
"""Generate one END-TO-END notebook per GRB from the scripts/37 template.

Each output notebook is standalone: set nothing, just Run All. It stamps
BURST and repoints the result paths at the human re-analysis dirs
(clean_blocks_human_final / clean_per_burst_human_final /
background_intervals_human_clean.ecsv). Pure templating — no compute.

Usage:
  python notebooks/gen_per_burst_notebooks.py                 # all clean bursts
  python notebooks/gen_per_burst_notebooks.py bn110721200 ... # specific bursts
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "notebooks", "Two_Breaks_single_GRB_pipeline.ipynb")
OUTDIR = os.path.join(ROOT, "notebooks", "per_burst")
CLEAN_CAT = os.path.join(ROOT, "results", "background_intervals_human_clean.ecsv")

# (old -> new) substitutions applied to every cell line
SUBS = [
    ('clean_blocks/bb_blocks_spectral_', 'clean_blocks_human_final/bb_blocks_spectral_'),
    ('clean_per_burst/', 'clean_per_burst_human_final/'),
    ('background_intervals_clean.ecsv', 'background_intervals_human_clean.ecsv'),
    ('background_intervals.ecsv', 'background_intervals_human_clean.ecsv'),
]


def burst_list(argv):
    if argv:
        return list(argv)
    from astropy.table import Table
    t = Table.read(CLEAN_CAT, format="ascii.ecsv")
    return sorted(set(str(x) for x in t["TRIGGER_NAME"]))


def stamp(nb, burst):
    out = copy.deepcopy(nb)
    for cell in out["cells"]:
        src = cell.get("source", [])
        new = []
        for line in src:
            if line.lstrip().startswith('BURST = "bn'):
                indent = line[: len(line) - len(line.lstrip())]
                line = f'{indent}BURST = "{burst}"     # end-to-end notebook for this GRB\n'
            for a, b in SUBS:
                line = line.replace(a, b)
            new.append(line)
        cell["source"] = new
    return out


def main(argv):
    nb = json.load(open(TEMPLATE))
    os.makedirs(OUTDIR, exist_ok=True)
    bursts = burst_list(argv)
    for b in bursts:
        out = stamp(nb, b)
        path = os.path.join(OUTDIR, f"{b}.ipynb")
        json.dump(out, open(path, "w"), indent=1)
    print(f"wrote {len(bursts)} per-burst notebooks -> {OUTDIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
