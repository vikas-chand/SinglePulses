#!/usr/bin/env python3
"""Per-bin all-model parameter tables (b2 format) for any burst.
Usage: gen_param_tables.py --trig <TRIG>
Writes results/convention_check/sed_grid_<TRIG>/tables/{TINT,binN}_params.md
plus ALL_MODELS_TABLES.md. Winner rows marked; EAC columns; dAIC."""
import argparse, os, re
import numpy as np
from astropy.table import Table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    a = ap.parse_args()
    T = a.trig
    grid = f"results/convention_check/sed_grid_{T}"
    os.makedirs(f"{grid}/tables", exist_ok=True)
    t = Table.read(f"results/convention_check/{T}/spectral_fits.ecsv")
    prefixes = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})

    def params_of(p):
        out = []
        for c in t.colnames:
            m = re.match(rf"^{p}_([A-Z0-9_]+)_ERR$", c)
            if m and not m.group(1).endswith(("NEG", "POS")) \
                    and not m.group(1).startswith("EAC"):
                out.append(m.group(1))
        return out

    combined = [f"# {T} — all models, all bins\n"]
    for row in t:
        blk = int(row["BLOCK"])
        tag = "TINT" if blk == -1 else f"bin{blk}"
        aics = {p: float(row[f"{p}_AIC"]) for p in prefixes
                if np.isfinite(row[f"{p}_AIC"])}
        if not aics:
            continue
        order = sorted(aics, key=aics.get)
        win = order[0]
        L = [f"# {tag}  [{row['T_START']:.2f}, {row['T_STOP']:.2f}] s — "
             f"all {len(order)} models (AIC-sorted)\n",
             "| model | AIC | dAIC | valid | parameters |",
             "|---|---|---|---|---|"]
        for p in order:
            parts = []
            for suf in params_of(p):
                col = f"{p}_{suf}"
                v = float(row[col])
                if not np.isfinite(v):
                    continue
                lo = row.get(f"{col}_NEG_ERR", np.nan)
                hi = row.get(f"{col}_POS_ERR", np.nan)
                if np.isfinite(lo) and np.isfinite(hi):
                    parts.append(f"{suf}={v:.4g} {float(lo):+.2g}/{float(hi):+.2g}")
                else:
                    e = float(row.get(f"{col}_ERR", np.nan))
                    parts.append(f"{suf}={v:.4g} ±{e:.2g}" if np.isfinite(e)
                                 else f"{suf}={v:.4g}")
            for d in ("N0", "N1", "N2", "N5", "B0", "B1"):
                c = f"{p}_EAC_{d}"
                if c in t.colnames and np.isfinite(float(row[c])):
                    parts.append(f"EAC_{d.lower()}={float(row[c]):.3f}")
            valid = bool(row[f"{p}_VALID"]) if f"{p}_VALID" in t.colnames else None
            L.append(f"| {p}{' **(winner)**' if p == win else ''} | "
                     f"{aics[p]:.1f} | {aics[p]-aics[win]:.2f} | "
                     f"{'yes' if valid else 'NO'} | {'; '.join(parts)} |")
        txt = "\n".join(L) + "\n"
        open(f"{grid}/tables/{tag}_params.md", "w").write(txt)
        combined.append(txt)
    open(f"{grid}/tables/ALL_MODELS_TABLES.md", "w").write("\n\n".join(combined))
    print(f"{T}: tables for {len(t)} bins -> {grid}/tables/")


if __name__ == "__main__":
    main()
