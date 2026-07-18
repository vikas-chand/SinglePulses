#!/usr/bin/env python
"""
Coarse LLE-driven Bayesian blocks -- the high-E arm of the two-tier scheme
(Vikas 2026-07-17; method from LATBright GRB260226A s02p/s03l).

Why: for LLE-bearing bursts, the fine NaI-driven GBM blocks (scripts/27b) have
near-zero LLE (30-100 MeV) counts per bin, so the high-energy component -- a cutoff
above the peak, a Guiriec Band+CPL saddle, or an extra hard power-law -- cannot be
constrained bin-by-bin. This makes a SEPARATE, COARSER time grid driven by the LLE
counts, where LLE actually has statistics. The joint NaI+BGO+LLE(+LAT) fits run in
THESE coarse intervals FIRST (high-E shape), then the fine GBM grid runs separately.

Method (self-contained; astropy + numpy only, no threeML):
  - read the LLE event file, restrict STRICTLY to the 30-100 MeV science band
    (this is the whole point -- the blocks must reflect the LLE band that gets fit)
  - measure the off-source background rate in the pre/post windows (30-100 MeV)
  - astropy.stats.bayesian_blocks(fitness='events', p0=0.01) on the 30-100 MeV event
    times inside the approved source window -> candidate change points
  - drop leading/trailing blocks below a 3-sigma detection floor (LLE is sparse; cf
    Burgess 3-sigma), then merge any interior sub-floor block into its weaker neighbor
  - GATE: bursts with no real LLE signal (peak block < 3 sigma) get NO LLE grid --
    they use the fine GBM blocks and inherit the NaI background at fit time.
  - write bb_blocks_lle_<trig>.ecsv (DETECTOR='lle'), SAME schema as 27b so the fit
    engine (scripts/10 --blocks-file) reads it unchanged.

Background-window preference: approved 'lle' row (scripts/39 GUI) -> inherited
brightest-NaI -> synthetic. LLE triplet resolver requires the gll_pt POINTING file
(NOT the LAT FT2; LATBright E2E audit C1-C3) and a common version across the triplet.
"""
import os, sys, glob, re, argparse
import numpy as np
from astropy.table import Table
from astropy.io import fits
from astropy.stats import bayesian_blocks

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data'); RES = os.path.join(BASE, 'results')

P0 = 0.01                     # LATBright LLE BB p0=1e-2
SIGMA_FLOOR_LLE = 3.0         # LLE is sparse -> lower detection floor than NaI's 5
LLE_LO, LLE_HI = 30.0, 100.0  # MeV science band (== engine LLE_RANGES 30000-100000 keV)


def _version(path):
    m = re.search(r'_v(\d+)\.', os.path.basename(path))
    return m.group(1) if m else None


def find_lle_triplet(trig):
    """(lle_event, gll_pt POINTING, rsp) for this burst, preferring a COMMON version.
    Requires gll_pt (from_lat_lle FitFails on the LAT FT2). (None,)*3 if incomplete."""
    base = os.path.join(DATA, trig)
    lle = sorted(glob.glob(os.path.join(base, 'gll_lle_*.fit*')))
    pt = sorted(glob.glob(os.path.join(base, 'gll_pt_*.fit*')))       # POINTING only
    rsp = sorted(glob.glob(os.path.join(base, 'gll_cspec_*.rsp*'))
                 + glob.glob(os.path.join(base, 'gll_lle_*.rsp*')))
    if not (lle and pt and rsp):
        return None, None, None
    # prefer a version shared by lle+pt (avoid mixed-version DRMs)
    for L in reversed(lle):
        v = _version(L)
        P = next((p for p in pt if _version(p) == v), None)
        if P is not None:
            R = next((r for r in rsp if _version(r) == v), rsp[-1])
            return L, P, R
    return lle[-1], pt[-1], rsp[-1]


def _windows(bk):
    bkw = {str(r['DETECTOR']).strip():
           ((float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])),
            (float(r['BKG_POS_START']), float(r['BKG_POS_STOP']))) for r in bk}
    if 'lle' in bkw:
        return bkw['lle'][0], bkw['lle'][1], 'approved-lle'
    nai = sorted([d for d in bkw if d.startswith('n')])
    if nai:
        return bkw[nai[0]][0], bkw[nai[0]][1], 'inherited-nai'
    return (-50.0, -10.0), (300.0, 400.0), 'synthetic'


def _load_lle_band_events(trig):
    """(sorted 30-100 MeV event times rel. trigger, GTI array Nx2 rel. trigger)
    or (None, None). THE single loader for every LLE gate in the pipeline."""
    lle_f, _, _ = find_lle_triplet(trig)
    if lle_f is None:
        return None, None
    with fits.open(lle_f) as h:
        ev = h['EVENTS'].data
        t0 = h['PRIMARY'].header.get('TRIGTIME', 0.0)
        e = np.asarray(ev['ENERGY'], dtype=float)      # MeV
        t = np.asarray(ev['TIME'], dtype=float) - t0
        try:
            gti = np.column_stack([np.asarray(h['GTI'].data['START'], float) - t0,
                                   np.asarray(h['GTI'].data['STOP'], float) - t0])
        except Exception:
            gti = (np.array([[t.min(), t.max()]]) if t.size else np.zeros((0, 2)))
    band = (e >= LLE_LO) & (e <= LLE_HI)
    return np.sort(t[band]), gti


def _exposure(gti, a, b):
    """Live time of [a,b] = overlap with the GTIs."""
    if b <= a or gti is None or gti.shape[0] == 0:
        return 0.0
    return float(np.sum(np.maximum(
        0.0, np.minimum(gti[:, 1], b) - np.maximum(gti[:, 0], a))))


def lima_sigma(tt, gti, pre, post, a, b):
    """Li & Ma (1983) Eq. 17 significance of on-interval [a,b] vs the pooled
    off-windows pre+post, GTI-aware, signed by the excess. THE shared statistic
    for the Stage-1 LLE review gate (scripts/39) AND the 27c grid (one gate,
    Codex ultra audit HIGH #8; replaces the naive (Non-b)/sqrt(b), CRITICAL #3)."""
    t_on = _exposure(gti, a, b)
    t_off = _exposure(gti, *pre) + _exposure(gti, *post)
    if t_on <= 0 or t_off <= 0:
        return 0.0
    n_on = int(((tt >= a) & (tt < b)).sum())
    n_off = int(((tt >= pre[0]) & (tt < pre[1])).sum()
                + ((tt >= post[0]) & (tt < post[1])).sum())
    if n_on + n_off == 0:
        return 0.0
    alpha = t_on / t_off
    term_on = (n_on * np.log((1.0 + alpha) / alpha
                             * n_on / (n_on + n_off))) if n_on > 0 else 0.0
    term_off = (n_off * np.log((1.0 + alpha)
                               * n_off / (n_on + n_off))) if n_off > 0 else 0.0
    val = term_on + term_off
    s = np.sqrt(2.0 * val) if val > 0 else 0.0
    return float(np.sign(n_on - alpha * n_off) * s)


def lle_detection_sigma(trig, pre, post, s1, s2):
    """Whole-source Li&Ma detection significance — the Stage-1 review gate.
    Returns (sigma, n_src_events); (0.0, 0) when no LLE data."""
    tt, gti = _load_lle_band_events(trig)
    if tt is None:
        return 0.0, 0
    n_src = int(((tt >= s1) & (tt <= s2)).sum())
    return lima_sigma(tt, gti, tuple(pre), tuple(post), s1, s2), n_src


def lle_reblock(trig, bkg, out_dir, floor=SIGMA_FLOOR_LLE, p0=P0, verbose=False):
    bk = bkg[bkg['TRIGGER_NAME'] == trig]
    if len(bk) == 0:
        return trig, 0, 'no bkg row'
    lle_f, pt_f, rsp_f = find_lle_triplet(trig)
    if lle_f is None:
        return trig, 0, 'no LLE triplet'
    pre, post, bsrc = _windows(bk)
    try:
        s1, s2 = float(bk[0]['SRC_START']), float(bk[0]['SRC_STOP'])
        if not (np.isfinite(s1) and np.isfinite(s2) and s2 > s1):
            raise ValueError
    except (TypeError, ValueError, KeyError):
        s1, s2 = float(pre[1]), float(post[0])

    # --- 30-100 MeV LLE events + GTIs via THE shared loader; the shared Li&Ma
    # statistic (lima_sigma) is the same one Stage-1's review gate uses ---
    tt, gti = _load_lle_band_events(trig)
    if tt is None:
        return trig, 0, 'no LLE triplet'
    if _exposure(gti, *pre) + _exposure(gti, *post) <= 0:
        return trig, 0, f'no LIVE background exposure (bkg={bsrc}) — no LLE grid'
    if _exposure(gti, s1, s2) <= 0:
        return trig, 0, 'approved source has no LIVE LLE exposure — no LLE grid'

    def sig(a, b):
        return lima_sigma(tt, gti, pre, post, a, b)

    src = tt[(tt >= s1) & (tt <= s2)]
    if src.size < 5:                                   # too few LLE counts to bin
        return trig, 0, f'sparse ({src.size} evt in 30-100 MeV, bkg={bsrc}) — no LLE grid'

    edges = np.asarray(bayesian_blocks(src, fitness='events', p0=p0), dtype=float)
    starts = list(edges[:-1]); stops = list(edges[1:])
    n_bb = len(starts)

    # GATE: no real signal anywhere -> no LLE grid (fall back to GBM bins downstream)
    if max((sig(a, b) for a, b in zip(starts, stops)), default=0.0) < floor:
        return trig, 0, (f'no LLE signal (peak <{floor:g} sigma Li&Ma, {src.size} evt, '
                         f'bkg={bsrc}) — will use GBM bins')

    # drop leading/trailing sub-floor (pure-background) blocks
    while len(starts) > 1 and sig(starts[0], stops[0]) < floor:
        starts.pop(0); stops.pop(0)
    while len(starts) > 1 and sig(starts[-1], stops[-1]) < floor:
        starts.pop(); stops.pop()

    # merge interior sub-floor blocks into the weaker neighbor. Bounded by the
    # block count (each merge removes one block), so silent guard exhaustion is
    # impossible (Codex ultra audit MED #27).
    merged = [False] * len(starts); cnt = [1] * len(starts)
    for _ in range(max(n_bb, 1)):
        if len(starts) <= 1:
            break
        sigs = [sig(starts[i], stops[i]) for i in range(len(starts))]
        i = next((k for k, s in enumerate(sigs) if s < floor), None)
        if i is None:
            break
        if i == 0:
            j = 1
        elif i == len(starts) - 1:
            j = i - 1
        else:
            j = i - 1 if sigs[i - 1] <= sigs[i + 1] else i + 1
        lo, hi = min(i, j), max(i, j)
        starts[lo:hi + 1] = [starts[lo]]; stops[lo:hi + 1] = [stops[hi]]
        merged[lo:hi + 1] = [True]; cnt[lo:hi + 1] = [cnt[lo] + cnt[hi]]
    n = len(starts)
    sigs = [sig(starts[i], stops[i]) for i in range(n)]
    # every OUTPUT block must clear the floor, else the grid is refused —
    # a merged-to-one block below floor must not become a science grid
    if not all(s >= floor for s in sigs):
        return trig, 0, (f'merged grid does not clear the {floor:g}-sigma floor '
                         f'(min {min(sigs):.1f}) — no LLE grid')

    rows = [(trig, 'lle', i, float(starts[i]), float(stops[i]),
             float(sigs[i]), bool(merged[i]), int(cnt[i]), -1) for i in range(n)]
    t_out = Table(rows=rows, names=['TRIGGER_NAME', 'DETECTOR', 'BLOCK_INDEX', 'T_START',
                  'T_STOP', 'SIGNIFICANCE', 'IS_MERGED', 'CONSTITUENT_COUNT', 'POLY_ORDER'])
    os.makedirs(out_dir, exist_ok=True)
    # Standard `bb_blocks_spectral_<trig>.ecsv` name (in its OWN out-dir, so no clash
    # with the GBM fine grid) so scripts/29 --blocks-dir + scripts/10 --blocks-file
    # read it unchanged. get_canonical_bins picks canonical_det='lle' -> grid_type=
    # lle_coarse + a NaI eff-area reference (scripts/10, Codex-audit-fixed).
    t_out.write(os.path.join(out_dir, f'bb_blocks_spectral_{trig}.ecsv'),
                format='ascii.ecsv', overwrite=True)
    if verbose:
        print(f'  {trig} [lle 30-100 MeV, bkg={bsrc}]: src=[{s1:.2f},{s2:.2f}]  '
              f'{src.size} evt  brate={brate:.2f}/s  BB={n_bb} -> {n} (floor {floor:g}s)')
        for i in range(n):
            print(f'    blk {i}: {starts[i]:8.2f}-{stops[i]:8.2f}  sig={sigs[i]:6.1f}  '
                  f'dt={stops[i]-starts[i]:6.2f}s  merged={merged[i]}  n_const={cnt[i]}')
    return trig, n, f'BB={n_bb}->{n} (bkg={bsrc})'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bkg-file', default=os.path.join(RES, 'background_intervals.ecsv'))
    ap.add_argument('--out-dir', default=os.path.join(RES, 'clean_blocks_lle'))
    ap.add_argument('--sigma', type=float, default=SIGMA_FLOOR_LLE)
    ap.add_argument('--p0', type=float, default=P0)
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
    print(f'LLE coarse blocks (30-100 MeV): {len(trigs)} burst(s), floor={args.sigma:g}, '
          f'p0={args.p0} -> {args.out_dir}', flush=True)
    ok = 0
    for trig in trigs:
        try:
            _, n, msg = lle_reblock(trig, bkg, args.out_dir, floor=args.sigma,
                                    p0=args.p0, verbose=args.verbose)
            print(f'  {trig}: {n} LLE blocks  [{msg}]', flush=True)
            ok += 1 if n else 0
        except Exception as e:
            print(f'  {trig}: FAILED {type(e).__name__}: {str(e)[:120]}', flush=True)
    print(f'DONE: {ok}/{len(trigs)} produced an LLE grid -> {args.out_dir}', flush=True)


if __name__ == '__main__':
    main()
