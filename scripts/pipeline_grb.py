#!/usr/bin/env python
"""Authoritative Stage 2-3 science run — Two_Breaks INHERITING from GRB_Handbook.

    import grb_pipeline as grb

Two_Breaks now delegates the SCIENCE path (binning + spectral fitting) to the
shared, audited, parity-verified handbook package instead of its own duplicated
scripts. The frozen Stage-1 SELECTION instrument (scripts/39/00 GUIs) is
deliberately NOT touched — it stays the benchmark's fixed tool until the
human-vs-AI data collection is complete (Phase B).

    Phase A (this file):  binning + fitting  ->  grb_pipeline   [benchmark-safe]
    Phase B (later):      Stage-1 selection  ->  grb_pipeline   [after benchmark]

Parity with the frozen canon: `scripts/parity_grb.py` (binning, bit-identical) +
the 2026-07-11 handbook audit (fitting inputs) + energy bands matched to canon.

Run in the threeML env:
    conda activate threeML
    python scripts/pipeline_grb.py --trigger bn110721200
"""
import argparse
import os

import numpy as np
from astropy.table import Table

import grb_pipeline as grb                                   # <- the inheritance
from grb_pipeline.analysis.binning import HybridBinner
from grb_pipeline.analysis.fitting import SpectralEngine
from grb_pipeline.utils.heasoft import ensure_analysis_env

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
RESULTS = os.path.join(BASE, 'results')

# gated catalog preferred; fall back to the provisional algorithmic one
_GATED = os.path.join(RESULTS, 'background_intervals.ecsv')
_PROVISIONAL = os.path.join(RESULTS, 'background_intervals_clean.ecsv')


def load_windows(trigger):
    """Approved per-detector background windows for this burst, + which catalog."""
    path = _GATED if os.path.exists(_GATED) else _PROVISIONAL
    t = Table.read(path, format='ascii.ecsv')
    t = t[t['TRIGGER_NAME'] == trigger]
    if len(t) == 0:
        raise SystemExit(f'{trigger}: no windows in {os.path.basename(path)}')
    windows = {}
    for r in t:
        d = str(r['DETECTOR']).strip()
        windows[d] = {'pre': [float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])],
                      'post': [float(r['BKG_POS_START']), float(r['BKG_POS_STOP'])]}
    return windows, os.path.basename(path)


def find_files(trigger, det):
    from grb_pipeline.data.resolver import find_burst_files
    r = find_burst_files(trigger, [DATA], products=('tte', 'cspec_rsp'))
    return r.get('tte', {}).get(det), r.get('cspec_rsp', {}).get(det)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trigger', required=True)
    ap.add_argument('--ref', help='reference (brightest) NaI; default = first NaI')
    ap.add_argument('--source', nargs=2, type=float, metavar=('T1', 'T2'),
                    help='emission window (manual until Block-4 T_INT is ported)')
    ap.add_argument('--sigma-floor', type=float, default=5.0)
    ap.add_argument('--block', type=int, default=None,
                    help='fit only this block index (default: the most significant)')
    args = ap.parse_args()

    ensure_analysis_env()
    print(f'Two_Breaks/pipeline_grb  via grb_pipeline v{grb.__version__}\n')

    windows, cat = load_windows(args.trigger)
    dets = sorted(windows)
    nai = [d for d in dets if d.startswith('n')]
    ref = args.ref or (nai[0] if nai else dets[0])
    src = args.source
    if src is None:
        # crude default emission span inside the gap (Block-4 T_INT not yet ported)
        gap_lo = max(w['pre'][1] for w in windows.values())
        gap_hi = min(w['post'][0] for w in windows.values())
        src = [max(gap_lo + 1.0, -2.0), min(gap_hi - 1.0, 30.0)]
    print(f'windows: {cat}  detectors={dets}  ref={ref}  source={src}')

    # --- binning (grb.HybridBinner == frozen scripts/27b, parity-verified) ---
    from threeML.utils.data_builders import TimeSeriesBuilder
    tte, rsp = find_files(args.trigger, ref)
    tsb = TimeSeriesBuilder.from_gbm_tte(ref, tte, rsp_file=rsp, verbose=False)
    pre, post = windows[ref]['pre'], windows[ref]['post']
    tsb.set_background_interval(f'{pre[0]}-{pre[1]}', f'{post[0]}-{post[1]}')
    blocks = HybridBinner(sigma_floor=args.sigma_floor).bin(tsb, src[0], src[1])
    print(f'\nbinning: {len(blocks.starts)} blocks (sigma_floor={args.sigma_floor})')
    for i, (s, e, sg) in enumerate(zip(blocks.starts, blocks.stops,
                                       blocks.significances)):
        print(f'  block {i}: [{s:7.3f}, {e:7.3f}]  sigma={sg:6.1f}')

    # --- spectral fit (grb.SpectralEngine == frozen scripts/10, registry v1) ---
    blk = args.block
    if blk is None:
        blk = int(np.argmax(blocks.significances))
    det_records = []
    for d in dets:
        t, r = find_files(args.trigger, d)
        if t and r:
            det_records.append({'name': d, 'tte_file': t, 'response_file': r,
                                'background_pre': windows[d]['pre'],
                                'background_post': windows[d]['post']})
    b0, b1 = float(blocks.starts[blk]), float(blocks.stops[blk])
    print(f'\nspectral fit: block {blk} = [{b0:.3f}, {b1:.3f}] s, '
          f'{[d["name"] for d in det_records]}')
    from types import SimpleNamespace
    one = SimpleNamespace(starts=[b0], stops=[b1])
    out = SpectralEngine({}).fit(one, det_records, canonical_detector=ref,
                                 time_integrated_interval=[b0, b1])
    rec = out['bins'][0]
    aic = rec.get('selection', {}).get('aic', {})
    for name in sorted(aic, key=aic.get):
        m = rec['models'].get(name, {})
        print(f'  {name:10s} n2logL={m.get("n2logL", float("nan")):9.2f} '
              f'AIC={aic[name]:9.2f}')
    print(f'\n  BEST_AIC_MODEL: {rec.get("BEST_AIC_MODEL")}   '
          f'LRT DSBPL/SBPL={rec.get("LRT_DSBPL_SBPL"):.1f}')
    print('\nStage 2-3 ran through grb_pipeline. Stage-1 stays frozen for the benchmark.')


if __name__ == '__main__':
    main()
