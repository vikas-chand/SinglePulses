#!/usr/bin/env python
"""
Coarse LLE-driven Bayesian blocks -- the high-E arm of the two-tier scheme
(Vikas 2026-07-17; ported from LATBright GRB260226A s02p/s03l).

Why: for LLE-bearing bursts, the fine NaI-driven GBM blocks (scripts/27b) have
near-zero LLE (30-100 MeV) counts per bin, so the high-energy component -- a cutoff
above the peak, a Guiriec Band+CPL saddle, or an extra hard power-law -- cannot be
constrained bin-by-bin. This makes a SEPARATE, COARSER time grid driven by the LLE
counts, where LLE actually has statistics. The joint NaI+BGO+LLE(+LAT) fits run in
THESE coarse intervals FIRST (high-E shape), then the fine GBM grid runs separately.

Method (mirrors scripts/27b, but on the LLE time series):
  - TimeSeriesBuilder.from_lat_lle on the LLE event/POINTING/rsp triplet
  - set_background_interval from the APPROVED 'lle' window (scripts/39 GUI) if present,
    else the brightest-NaI window (inherited), else a synthetic wide window
  - create_time_bins(method='bayesblocks', p0=0.01, use_background=True)   [bksub BB,
    LATBright bb_edges_lle_bksub_p0_1e-2 recipe]
  - 27b's trim_edges + significance-merge, with a LOWER floor (LLE is sparse: 3 sigma,
    cf Burgess 3-sigma spectral floor, vs NaI's 5)
  - write bb_blocks_lle_<trig>.ecsv (DETECTOR='lle'), SAME schema as 27b so the fit
    engine (scripts/10 --blocks-file) reads it unchanged.

CRITICAL (LATBright E2E audit C1-C3): from_lat_lle needs the LLE POINTING file
(gll_pt_*.fit), NOT the LAT FT2 -- wrong file => FitFailed on every LLE plugin. We
reuse scripts/10.find_lle_files, which already returns gll_pt in the ft2 slot.
"""
import os, sys, glob, argparse
import numpy as np
from astropy.table import Table
import importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data'); RES = os.path.join(BASE, 'results')


def _load(mod_file, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, 'scripts', mod_file))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


# reuse 27b's TESTED trim/merge/significance helpers + scripts/10's proven LLE resolver
_r27b = _load('27b_reblock_3ml.py', 'r27b')
trim_edges = _r27b.trim_edges
merge_low_significance = _r27b.merge_low_significance
bin_net_counts = _r27b.bin_net_counts
_s10 = _load('10_spectral_fit_burst.py', 's10')
find_lle_files = _s10.find_lle_files          # (lle_evt, gll_pt POINTING, rsp) or (None,)*3

P0 = 0.01                     # LATBright LLE BB p0=1e-2 (bksub / use_background)
SIGMA_FLOOR_LLE = 3.0         # LLE is sparse -> lower detection floor than NaI's 5


def lle_reblock(trig, bkg, out_dir, floor=SIGMA_FLOOR_LLE, verbose=False):
    from threeML.utils.data_builders import TimeSeriesBuilder
    bk = bkg[bkg['TRIGGER_NAME'] == trig]
    if len(bk) == 0:
        return trig, 0, 'no bkg row'
    lle_f, pt_f, rsp_f = find_lle_files(trig)
    if lle_f is None:
        return trig, 0, 'no LLE files'

    # --- background window: approved 'lle' row -> inherited brightest-NaI -> synthetic
    bkw = {str(r['DETECTOR']).strip():
           ((float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])),
            (float(r['BKG_POS_START']), float(r['BKG_POS_STOP']))) for r in bk}
    if 'lle' in bkw:
        (pre, post), bsrc = bkw['lle'], 'approved-lle'
    else:
        nai = sorted([d for d in bkw if d.startswith('n')])
        if nai:
            (pre, post), bsrc = bkw[nai[0]], 'inherited-nai'
        else:
            pre, post, bsrc = (-50.0, -10.0), (300.0, 400.0), 'synthetic'

    # --- source (emission) window from the approved catalog; BB searches within it ---
    try:
        s1, s2 = float(bk[0]['SRC_START']), float(bk[0]['SRC_STOP'])
        if not (np.isfinite(s1) and np.isfinite(s2) and s2 > s1):
            raise ValueError
    except (TypeError, ValueError, KeyError):
        s1, s2 = float(pre[1]), float(post[0])       # fall back to the whole gap

    # --- LLE time series (POINTING file in the ft2 slot; see module docstring) ---
    tsb = TimeSeriesBuilder.from_lat_lle('lle', lle_file=lle_f, ft2_file=pt_f,
                                         rsp_file=rsp_f, verbose=False)
    tsb.set_background_interval(f'{pre[0]}-{pre[1]}', f'{post[0]}-{post[1]}')
    tsb.create_time_bins(s1, s2, method='bayesblocks', p0=P0, use_background=True)
    ts = tsb._time_series
    bins = ts.bins
    starts = list(map(float, bins.start_times)); stops = list(map(float, bins.stop_times))
    n_bb = len(starts)

    # --- 27b hybrid: drop sub-floor edges, then merge interior sub-floor blocks ---
    starts, stops = trim_edges(starts, stops, ts, floor)
    starts, stops, sigs, merged, cnt = merge_low_significance(starts, stops, ts, floor)
    n = len(starts)

    rows = [(trig, 'lle', i, float(starts[i]), float(stops[i]),
             float(sigs[i]), bool(merged[i]), int(cnt[i]), -1) for i in range(n)]
    t = Table(rows=rows, names=['TRIGGER_NAME', 'DETECTOR', 'BLOCK_INDEX', 'T_START',
              'T_STOP', 'SIGNIFICANCE', 'IS_MERGED', 'CONSTITUENT_COUNT', 'POLY_ORDER'])
    os.makedirs(out_dir, exist_ok=True)
    t.write(os.path.join(out_dir, f'bb_blocks_lle_{trig}.ecsv'),
            format='ascii.ecsv', overwrite=True)
    if verbose:
        print(f'  {trig} [lle, bkg={bsrc}]: src=[{s1:.2f},{s2:.2f}]  '
              f'BB={n_bb} -> {n} coarse blocks (floor {floor:g} sigma)')
        for i in range(n):
            print(f'    blk {i}: {starts[i]:8.2f}-{stops[i]:8.2f}  sig={sigs[i]:6.1f}  '
                  f'dt={stops[i]-starts[i]:6.2f}s  merged={merged[i]}  n_const={cnt[i]}')
    return trig, n, f'BB={n_bb}->{n} (bkg={bsrc})'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bkg-file', default=os.path.join(RES, 'background_intervals.ecsv'),
                    help='approved background/source catalog (has the lle row if reviewed)')
    ap.add_argument('--out-dir', default=os.path.join(RES, 'clean_blocks_lle'),
                    help='output dir for bb_blocks_lle_<trig>.ecsv')
    ap.add_argument('--sigma', type=float, default=SIGMA_FLOOR_LLE,
                    help='per-block LLE detection floor (default 3; NaI uses 5)')
    ap.add_argument('--triggers', nargs='*',
                    help='specific triggers; default = every burst with LLE data')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    if not os.path.exists(args.bkg_file):
        sys.exit(f'bkg file not found: {args.bkg_file}')
    bkg = Table.read(args.bkg_file, format='ascii.ecsv')
    trigs = args.triggers or sorted(
        os.path.dirname(f).split(os.sep)[-1]
        for f in glob.glob(os.path.join(DATA, '*', 'gll_lle_*.fit*')))
    print(f'LLE coarse blocks: {len(trigs)} burst(s), floor={args.sigma:g} sigma, '
          f'p0={P0} -> {args.out_dir}', flush=True)
    ok = 0
    for trig in trigs:
        try:
            _, n, msg = lle_reblock(trig, bkg, args.out_dir, floor=args.sigma,
                                    verbose=args.verbose)
            print(f'  {trig}: {n} LLE blocks  [{msg}]', flush=True)
            ok += 1 if n else 0
        except Exception as e:
            print(f'  {trig}: FAILED {type(e).__name__}: {str(e)[:120]}', flush=True)
    print(f'DONE: {ok}/{len(trigs)} produced LLE blocks -> {args.out_dir}', flush=True)


if __name__ == '__main__':
    main()
