#!/usr/bin/env python
"""
27b_reblock_3ml.py -- 3ML-native time binning (Bayesian-blocks + significance hybrid).

Implements the decided methodology IN ACCORDANCE WITH THE 3ML DOCUMENTATION:
  - per reference (brightest) NaI: TimeSeriesBuilder.from_gbm_tte ->
    set_background_interval(pre, post)  (poly_order=-1, auto via LRT);
  - create_time_bins(method='bayesblocks', p0=0.01, use_background=True)
    -> bin_by_bayesian_blocks for the variability structure;
  - per-block significance computed BY 3ML's Significance class
    (li_and_ma_equivalent_for_gaussian_background -- the modeled/polynomial-
    background case, Vianello 2018), exactly as 3ML's own bin_by_significance does;
  - TIGHTEN the source region to the actual burst-emission interval first
    (emission_window, ported from scripts/27): BB over a wide, mostly-quiet AI
    background window collapses to one block, which merging cannot undo;
  - DROP leading/trailing blocks below SIGMA_FLOOR (pure-background edges; ported
    from scripts/27's trim), then MERGE any remaining INTERIOR sub-floor block into
    its neighbour until every surviving block clears the floor (BB + sig hybrid);
  - write the SAME clean_blocks ECSV schema as scripts/27 (so scripts/10 reads it
    unchanged): the merged edges are replicated for every approved NaI.

Defaults: p0=0.01, use_background=True (the 3ML time-series tutorial); SIGMA_FLOOR=5
(per-block detection floor, user-set 2026-06-24; any bin below it is merged per the
trim-edges-then-merge-interior scheme below). cf Burgess 3sigma spectral-bin floor
and 3ML's bin_by_significance default sigma_level=10 / min_counts=1.

Requires the threeML conda env (export CALDB first). Run on one burst for
validation:  python scripts/27b_reblock_3ml.py --burst bn110721200 --out /tmp/cb3
Full sample (authoritative re-fit, fresh out-root):  python scripts/27b_reblock_3ml.py --out <root>/clean_blocks
"""
import os, glob, argparse, warnings
warnings.filterwarnings('ignore')
import numpy as np
from astropy.io import fits
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data'); RES = os.path.join(BASE, 'results')

ELO, EHI = 8.0, 900.0          # NaI band for the reference light curve
P0 = 0.01                       # 3ML tutorial value
USE_BACKGROUND = True           # 3ML tutorial value
SIGMA_FLOOR = 5.0              # per-block detection floor (user-set 2026-06-24);
                               # cf Burgess 3sigma, 3ML default sigma_level=10
SIG_TRIM = 4.5                 # PEAK-DETECTION threshold only (used at the `net[pk] <
                               # SIG_TRIM * noise` guard below). It is NOT the edge-trim
                               # threshold: trim_edges() is called with SIGMA_FLOOR (5.0).
                               # Comment corrected 2026-08-31 per PI ruling '5.0 sigma is
                               # right - fix the docs'; behaviour UNCHANGED.


def find_tte(trig, det):
    f = sorted(glob.glob(f'{DATA}/{trig}/glg_tte_{det}_*.fit*'))
    return f[-1] if f else None    # newest version (audit #19)


def load_nai(trig, det):
    """Raw NaI event times (trigger-relative), restricted to [ELO,EHI] -- used to
    locate the burst-emission interval before BB (ported from scripts/27)."""
    f = sorted(glob.glob(f'{DATA}/{trig}/glg_tte_{det}_*.fit*'))
    if not f:
        return None
    with fits.open(f[-1]) as h:    # newest version — SAME file as find_tte (audit #19)
        ev = h['EVENTS'].data
        t0 = next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
        tt = np.asarray(ev['TIME']) - t0
        eb = h['EBOUNDS'].data
        emid = 0.5 * (np.asarray(eb['E_MIN']) + np.asarray(eb['E_MAX']))
        m = (emid[ev['PHA']] >= ELO) & (emid[ev['PHA']] <= EHI)
    return np.sort(tt[m])


def emission_window(tt, lo, hi, brate):
    """Tighten [lo,hi] to the actual burst-emission interval (ported verbatim from
    scripts/27): the AI bkg window can be wide/offset, and BB over a mostly-quiet
    window collapses to one block -- which merging cannot undo."""
    dt = 0.256; e = np.arange(lo, hi + dt, dt); c = 0.5 * (e[:-1] + e[1:])
    cnt, _ = np.histogram(tt, bins=e); rate = cnt / dt
    noise = np.sqrt(max(brate, 1e-6) / dt)
    net = np.convolve(rate - brate, np.ones(3) / 3, mode='same')
    pk = int(np.argmax(net))
    if net[pk] < SIG_TRIM * noise:        # no clear peak: keep the full region
        return lo, hi
    L = pk
    while L > 0 and net[L - 1] > 1.0 * noise:
        L -= 1
    R = pk
    while R < len(net) - 1 and net[R + 1] > 1.0 * noise:
        R += 1
    return float(c[L] - 0.5), float(c[R] + 0.5)


def find_rsp(trig, det):
    f = sorted(glob.glob(f'{DATA}/{trig}/glg_cspec_{det}_*.rsp*'))
    return f[-1] if f else None    # newest version (audit #19)


def bin_significance(ts, s, e):
    """Per-interval significance AS 3ML COMPUTES IT (modeled/Gaussian background:
    Significance.li_and_ma_equivalent_for_gaussian_background, Vianello 2018)."""
    from threeML.utils.statistics.stats_tools import Significance
    o = float(ts.counts_over_interval(s, e))      # Non (observed counts)
    b = float(ts.get_total_poly_count(s, e))      # background counts
    sb = float(ts.get_total_poly_error(s, e))     # background 1-sigma error
    if sb <= 0:
        return 0.0
    return float(Significance(o, b).li_and_ma_equivalent_for_gaussian_background(sb))


def bin_net_counts(ts, s, e):
    """Net (background-subtracted) counts in [s,e] -- DIAGNOSTIC ONLY (printed in
    verbose mode; NOT a merge criterion: the scheme is significance-only)."""
    return float(ts.counts_over_interval(s, e)) - float(ts.get_total_poly_count(s, e))


def block_below(ts, s, e, floor):
    """A block is inadequate if its significance is below `floor` (significance-only
    scheme, user-set 2026-06-24): merge any bin below SIGMA_FLOOR per the scheme."""
    return bin_significance(ts, s, e) < floor


def trim_edges(starts, stops, ts, floor):
    """DROP leading/trailing blocks below `floor` (pure-background edges), keeping
    the contiguous emission span (ported from scripts/27's trim). Returns the
    trimmed starts, stops. If no block clears the floor, keep all (rare)."""
    s = list(map(float, starts)); e = list(map(float, stops))
    keep = [i for i in range(len(s)) if not block_below(ts, s[i], e[i], floor)]
    if not keep:
        return s, e
    i0, i1 = min(keep), max(keep)
    return s[i0:i1 + 1], e[i0:i1 + 1]


def merge_low_significance(starts, stops, ts, floor):
    """Greedily MERGE any block below `floor` (3ML significance) INTO THE NEXT
    block (the last block merges into its previous), until every block clears the
    floor or only one remains. After trim_edges the edges already clear the floor,
    so in practice this only merges INTERIOR sub-floor blocks. Returns starts,
    stops, sigmas, is_merged, n_const."""
    s = list(map(float, starts)); e = list(map(float, stops))
    cnt = [1] * len(s); merged = [False] * len(s)
    while len(s) > 1:
        sig = [bin_significance(ts, s[i], e[i]) for i in range(len(s))]
        below = [i for i in range(len(s)) if block_below(ts, s[i], e[i], floor)]
        if not below:
            break
        i = min(below, key=lambda k: sig[k])
        if i < len(s) - 1:                 # merge INTO THE NEXT block
            e[i] = e[i + 1]; del s[i + 1]; del e[i + 1]
            cnt[i] += cnt[i + 1]; del cnt[i + 1]; del merged[i + 1]; merged[i] = True
        else:                              # last block: merge into previous
            e[i - 1] = e[i]; del s[i]; del e[i]
            cnt[i - 1] += cnt[i]; del cnt[i]; del merged[i]; merged[i - 1] = True
    sig = [bin_significance(ts, s[i], e[i]) for i in range(len(s))]
    return s, e, sig, merged, cnt


def reblock_burst(trig, single, bkg, out_dir, verbose=False):
    from threeML.utils.data_builders import TimeSeriesBuilder
    bk = bkg[bkg['TRIGGER_NAME'] == trig]
    if len(bk) == 0:
        return trig, '-', 0, 'no bkg row'
    sp = single[single['TRIGGER_NAME'] == trig]
    brightest = str(sp[0]['DETECTOR']).strip() if len(sp) else None
    # ONLY approved detectors define the grid. The old code re-introduced a
    # DESELECTED sample-catalog "brightest" NaI and then gave it the first
    # approved detector's background window (proven on bn201104001: grid built
    # on rejected n3 with n6's window — Codex ultra audit CRITICAL #1).
    nai = sorted({str(r['DETECTOR']).strip() for r in bk
                  if str(r['DETECTOR']).strip().startswith('n')})
    if not nai:
        return trig, '-', 0, 'no approved NaI'
    bkw = {str(r['DETECTOR']).strip(): ((float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])),
           (float(r['BKG_POS_START']), float(r['BKG_POS_STOP']))) for r in bk}
    if brightest in nai:
        edet = brightest
    else:
        # deterministic among APPROVED NaIs: the one with the most counts in
        # its own background gap (its own windows, its own events)
        best_cnt = -1
        edet = nai[0]
        for d in nai:
            td = load_nai(trig, d)
            if td is None:
                continue
            p_, q_ = bkw[d]
            c = int(((td >= p_[1]) & (td <= q_[0])).sum())
            if c > best_cnt:
                best_cnt, edet = c, d
        if verbose and brightest:
            print(f'  {trig}: catalog-brightest {brightest} NOT approved — '
                  f'grid from approved {edet}')
    pre, post = bkw[edet]                     # STRICTLY this detector's own windows
    tte = find_tte(trig, edet)
    if tte is None:
        return trig, edet, 0, 'no TTE'
    # --- tighten the source region to the actual emission interval (raw events) ---
    tt = load_nai(trig, edet)
    if tt is None or tt.size < 30:
        return trig, edet, 0, 'too few events'
    bt = (pre[1] - pre[0]) + (post[1] - post[0])
    bc = int(((tt >= pre[0]) & (tt < pre[1])).sum() + ((tt >= post[0]) & (tt < post[1])).sum())
    brate = bc / bt if bt > 0 else 0.0
    # Prefer the EXPLICIT human/AI-approved source window (SRC_START/SRC_STOP from the
    # gated approval catalog, scripts/39); fall back to the emission_window heuristic
    # only when the catalog has no source column / value for this burst.
    src_explicit = None
    if 'SRC_START' in bk.colnames and 'SRC_STOP' in bk.colnames:
        try:
            s1, s2 = float(bk[0]['SRC_START']), float(bk[0]['SRC_STOP'])
            if np.isfinite(s1) and np.isfinite(s2) and s2 > s1:
                src_explicit = (s1, s2)
        except (TypeError, ValueError):
            src_explicit = None
    if src_explicit is not None:
        # Tighten the BB search to the emission WITHIN the approved window, rather than
        # trusting [s1,s2] verbatim: an over-wide approved source (or a GUI misclick)
        # would otherwise let BB run over a mostly-quiet span and collapse. emission_
        # window returns the bounds unchanged when no clear peak is found, so an already
        # tight approved window is preserved. The result is CLIPPED to the approved
        # interval — the walk-out padding must never escape the human gate (Codex
        # ultra audit HIGH #15; matches the handbook binning.py clip).
        src_lo, src_hi = emission_window(tt, src_explicit[0], src_explicit[1], brate)
        src_lo = max(float(src_lo), src_explicit[0])
        src_hi = min(float(src_hi), src_explicit[1])
        src_kind = 'approved+tightened'
    else:
        src_lo, src_hi = emission_window(tt, float(pre[1]), float(post[0]), brate)
        src_kind = 'heuristic'
    # --- 3ML time series for the reference detector ---
    tsb = TimeSeriesBuilder.from_gbm_tte(edet, tte, rsp_file=find_rsp(trig, edet), verbose=False)
    tsb.set_background_interval(f'{pre[0]}-{pre[1]}', f'{post[0]}-{post[1]}')   # poly auto (LRT)
    tsb.create_time_bins(src_lo, src_hi, method='bayesblocks', p0=P0, use_background=USE_BACKGROUND)
    ts = tsb._time_series
    bins = ts.bins
    starts = list(map(float, bins.start_times)); stops = list(map(float, bins.stop_times))
    n_bb = len(starts)
    # --- BB + significance hybrid: drop sub-floor edges, then merge interior ---
    starts, stops = trim_edges(starts, stops, ts, SIGMA_FLOOR)
    starts, stops, sigs, merged, cnt = merge_low_significance(starts, stops, ts, SIGMA_FLOOR)
    n_final = len(starts)
    if verbose:
        print(f'  {trig} [{edet}]: src=[{src_lo:.3f},{src_hi:.3f}] ({src_kind}) BB={n_bb} '
              f'-> trim+merge(>= {SIGMA_FLOOR:g} sigma)={n_final}')
        for i in range(n_final):
            net = bin_net_counts(ts, starts[i], stops[i])
            print(f'    blk {i}: {starts[i]:8.3f}-{stops[i]:8.3f}  sig={sigs[i]:6.1f}'
                  f'  net={net:8.1f}  dt={1000*(stops[i]-starts[i]):8.1f}ms'
                  f'  merged={merged[i]}  n_const={cnt[i]}')
    # --- write the same schema as scripts/27, edges shared across approved NaI ---
    rows = []
    for det in nai:
        for i in range(n_final):
            rows.append((trig, det, i, float(starts[i]), float(stops[i]),
                         float(sigs[i]), bool(merged[i]), int(cnt[i]), -1))
    t = Table(rows=rows, names=['TRIGGER_NAME', 'DETECTOR', 'BLOCK_INDEX', 'T_START',
              'T_STOP', 'SIGNIFICANCE', 'IS_MERGED', 'CONSTITUENT_COUNT', 'POLY_ORDER'])
    os.makedirs(out_dir, exist_ok=True)
    t.write(os.path.join(out_dir, f'bb_blocks_spectral_{trig}.ecsv'),
            format='ascii.ecsv', overwrite=True)
    return trig, edet, n_final, f'BB={n_bb}->{n_final}'


def main():
    global SIGMA_FLOOR
    ap = argparse.ArgumentParser()
    ap.add_argument('--burst', default=None, help='single trigger (validation); default = all')
    ap.add_argument('--out', default=os.path.join(RES, 'clean_blocks'), help='output dir')
    ap.add_argument('--sigma', type=float, default=SIGMA_FLOOR)
    ap.add_argument('--bkg', default=None, help='background ECSV (default: clean else prototype)')
    args = ap.parse_args()
    SIGMA_FLOOR = args.sigma

    single = Table.read(os.path.join(RES, 'single_pulse_grbs.ecsv'), format='ascii.ecsv')
    # Default search prefers the GATED approval catalog (carries SRC_*) over the
    # provisional clean/prototype catalogs.
    if args.bkg:
        bpath = args.bkg
    else:
        for cand in ('background_intervals.ecsv', 'background_intervals_clean.ecsv',
                     'background_intervals_prototype.ecsv'):
            bpath = os.path.join(RES, cand)
            if os.path.exists(bpath):
                break
    bkg = Table.read(bpath, format='ascii.ecsv')
    has_src = 'SRC_START' in bkg.colnames and 'SRC_STOP' in bkg.colnames
    print(f'bkg: {os.path.basename(bpath)} | sigma_floor={SIGMA_FLOOR:g} | '
          f'source={"approved (SRC_*)" if has_src else "HEURISTIC (no SRC_* -> emission_window)"} '
          f'| out={args.out}')
    if not has_src:
        print('  WARNING: this bkg catalog has no SRC_START/SRC_STOP; the source window '
              'will be the emission_window heuristic, not human/AI-approved.')

    if args.burst:
        trigs = [args.burst]
    else:
        trigs = sorted({os.path.basename(os.path.dirname(p)) for p in glob.glob(f'{DATA}/bn*/')})

    print(f'{"trigger":13s} {"det":4s} {"Nblk":>4s}  note')
    for trig in trigs:
        try:
            r = reblock_burst(trig, single, bkg, args.out, verbose=bool(args.burst))
        except Exception as exc:
            r = (trig, '-', 0, f'FAIL {type(exc).__name__}: {exc}')
        print(f'{r[0]:13s} {str(r[1]):4s} {r[2]:>4d}  {r[3]}')


if __name__ == '__main__':
    main()
