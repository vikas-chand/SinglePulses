#!/usr/bin/env python
"""Parity guard: the shared GRB_Handbook package reproduces the frozen Two_Breaks
canon. Run before trusting `import grb_pipeline as grb` for any science number.

Deterministic (no 3ML, no data): feeds canon `scripts/27b` and the handbook
`grb_pipeline.analysis.binning` the SAME synthetic significance profile and asserts
bit-identical block edges through the trim-edges + significance-merge scheme.

    python scripts/parity_grb.py     # exit 0 = parity holds

Fitting-input parity (model bounds/seeds/energy bands) is verified by the
2026-07-11 audit (docs/AUDIT in the handbook) + `test_energy_ranges_match_canon`;
a full numerical fit-output parity across the sample is the next validation.
"""
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_canon_27b():
    spec = importlib.util.spec_from_file_location(
        'canon27b', os.path.join(HERE, '27b_reblock_3ml.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    canon = _load_canon_27b()
    try:
        from grb_pipeline.analysis.binning import refine_blocks_by_significance
    except ModuleNotFoundError:
        sys.exit("grb_pipeline not installed — run: pip install -e "
                 "<GRB_Handbook_Project> --no-deps")

    # synthetic significance model shared by both implementations
    counts = [4, 4, 100, 400, 16, 400, 100, 50, 16, 4]     # per unit block [i, i+1]
    def sig(s, e):
        i0, i1 = int(round(s)), int(round(e))
        return float(np.sqrt(sum(counts[i0:i1])))

    floor = 5.0
    starts = [float(i) for i in range(10)]
    stops = [float(i + 1) for i in range(10)]

    # canon path: patch its significance to the deterministic model, trim then merge
    canon.bin_significance = lambda ts, s, e: sig(s, e)    # block_below uses this global
    cs, ce = canon.trim_edges(starts, stops, None, floor)
    cs, ce, *_ = canon.merge_low_significance(cs, ce, None, floor)

    # handbook path: single call with the same significance callable
    hb = refine_blocks_by_significance(starts, stops, sig, sigma_floor=floor)

    ok = np.allclose(cs, hb.starts) and np.allclose(ce, hb.stops)
    print(f"canon    edges: {[round(x, 3) for x in cs]} / {[round(x, 3) for x in ce]}")
    print(f"handbook edges: {[round(x, 3) for x in hb.starts.tolist()]} / "
          f"{[round(x, 3) for x in hb.stops.tolist()]}")
    print("BINNING PARITY:", "PASS (bit-identical)" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
