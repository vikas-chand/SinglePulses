#!/usr/bin/env python
"""Generate tiny per-GRB config files for the ONE config-driven notebook.
Config-file pattern (FermiPy-style): one notebook, one small yaml per GRB.
Only what VARIES goes here; detectors/background/source are looked up from the
catalog at runtime by the notebook."""
import os, sys
from astropy.table import Table
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "results", "background_intervals_human_clean.ecsv")
CFGDIR = os.path.join(ROOT, "notebooks", "configs")
SPECIAL = {"bn130427324": "2nd"}   # dev/special_bursts.md: analyse the 2nd pulse

def write_cfg(trig, depth="quick"):
    os.makedirs(CFGDIR, exist_ok=True)
    lines = [f"grb: {trig}", f"depth: {depth}   # quick (6 models+temporal) | full (24+LLE/LAT)"]
    if trig in SPECIAL:
        lines.append(f"special_pulse: '{SPECIAL[trig]}'   # analyse this pulse (special burst)")
    lines.append("notes: ''")
    open(os.path.join(CFGDIR, f"{trig}.yaml"), "w").write("\n".join(lines) + "\n")

def main(argv):
    if argv:
        bursts = argv
    else:
        t = Table.read(CATALOG, format="ascii.ecsv")
        bursts = sorted(set(str(x) for x in t["TRIGGER_NAME"]))
    for b in bursts:
        write_cfg(b)
    # a default config the notebook falls back to
    open(os.path.join(CFGDIR, "default.yaml"), "w").write(
        "grb: bn110721200   # override with env GRB=<trig> or GRB_CONFIG=<path>\n"
        "depth: quick\nnotes: ''\n")
    print(f"wrote {len(bursts)} configs + default.yaml -> {CFGDIR}/")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
