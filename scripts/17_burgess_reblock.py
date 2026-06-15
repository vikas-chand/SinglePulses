#!/usr/bin/env python
"""
Burgess+2014-faithful Bayesian re-blocking for the 6 common bursts.

Burgess method (ApJL 784 L43, sec. 2): time bins set by a Bayesian-blocks
algorithm (Scargle 2013) run on the *NaI count rate, 8-300 keV* of the
single brightest detector -- i.e. on BINNED count rates, not photon events.

Our production pipeline instead ran EVENT-mode BB on 8-900 keV with a merge
step; for the two faint bursts (090719A, 110920A) that collapsed to a single
sliver block at the wrong time. This script reproduces Burgess's binning and
writes block files to results/burgess_repro/blocks/ (production untouched).

Output schema matches results/bb_blocks_spectral_<trig>.ecsv so that
10_spectral_fit_burst.py --blocks-file <path> can fit on these bins.
"""
import warnings; warnings.filterwarnings('ignore')
import os, glob
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.stats import bayesian_blocks

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data'); RES = os.path.join(BASE, 'results')
OUTB = os.path.join(RES, 'burgess_repro', 'blocks'); os.makedirs(OUTB, exist_ok=True)

BURG = ['bn081224887', 'bn090719063', 'bn100707032',
        'bn110721200', 'bn110920546', 'bn130427324']

ELO, EHI = 8.0, 300.0     # Burgess blocking band
DT = 0.064                # light-curve resolution for count-rate BB
P0 = 0.01                 # false-alarm prior (standard / conservative)

single = Table.read(os.path.join(RES, 'single_pulse_grbs.ecsv'),
                    format='ascii.ecsv')
bkg = Table.read(os.path.join(RES, 'background_intervals_prototype.ecsv'),
                 format='ascii.ecsv')


def load_nai(trig, det, elo=ELO, ehi=EHI):
    f = sorted(glob.glob(f'{DATA}/{trig}/glg_tte_{det}_*.fit*'))
    if not f:
        return None
    with fits.open(f[0]) as h:
        ev = h['EVENTS'].data
        t0 = next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
        tt = np.asarray(ev['TIME']) - t0
        eb = h['EBOUNDS'].data
        emid = 0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
        m = (emid[ev['PHA']] >= elo) & (emid[ev['PHA']] <= ehi)
    return np.sort(tt[m])


def burst_window(tt):
    """Burst EMISSION interval (T100-like) from the brightest-NaI 8-300 keV LC.

    Burgess's Fig-1 bins span only the pulse, not quiet pre/post background.
    A too-wide window would make the time-integrated seed background-dominated,
    which rails the blackbody (kT->1) and poisons every per-block BB fit (the
    engine seeds all blocks from T_INT). So we trim to the significant region.
    """
    dt = 0.256
    edges = np.arange(-50, 150, dt); ctr = 0.5*(edges[:-1]+edges[1:])
    cnt, _ = np.histogram(tt, bins=edges); rate = cnt/dt
    # background level from quiet ends (robust median of |t|>30 s region)
    quiet = (ctr < -20) | (ctr > 60)
    b = np.median(rate[quiet]) if quiet.any() else np.median(rate)
    noise = np.sqrt(max(b, 1e-6)/dt)
    net = rate - b
    # 3-bin (~0.75 s) boxcar smooth, then 4.5-sigma threshold (Fermi floor)
    k = np.ones(3)/3.0
    sm = np.convolve(net, k, mode='same')
    above = sm > 4.5*noise
    if not above.any():
        pk = ctr[int(np.argmax(rate))]; return pk-5.0, pk+15.0
    pk = int(np.argmax(sm))
    # walk out from the peak while still above ~1 sigma (contiguous emission)
    lo = pk
    while lo > 0 and sm[lo-1] > 1.0*noise:
        lo -= 1
    hi = pk
    while hi < len(sm)-1 and sm[hi+1] > 1.0*noise:
        hi += 1
    return float(ctr[lo]-0.5), float(ctr[hi]+0.5)


def burgess_blocks(tt, lo, hi):
    """Binned count-rate Bayesian blocks (fitness='measures'), Burgess-style."""
    edges = np.arange(lo, hi + DT, DT); ctr = 0.5*(edges[:-1]+edges[1:])
    cnt, _ = np.histogram(tt, bins=edges)
    rate = cnt / DT; err = np.sqrt(np.maximum(cnt, 1)) / DT
    bb_edges = bayesian_blocks(ctr, rate, err, fitness='measures', p0=P0)
    return bb_edges, edges, rate


def block_significance(tt_det, s, e, pre, post):
    """Crude per-block S/N: net rate vs Poisson noise, using a flat bkg level
    estimated from the detector's own pre/post windows. For tie-break only."""
    dur = max(e - s, 1e-3)
    n_src = int(((tt_det >= s) & (tt_det < e)).sum())
    # background level (counts/s) from pre+post windows
    bt = 0.0; bc = 0
    for (a, b) in (pre, post):
        bt += max(b - a, 1e-3); bc += int(((tt_det >= a) & (tt_det < b)).sum())
    brate = bc / bt if bt > 0 else 0.0
    b_in = brate * dur
    net = n_src - b_in
    sig = net / np.sqrt(max(n_src + b_in, 1.0))
    return float(sig)


summary = []
for trig in BURG:
    sp = single[single['TRIGGER_NAME'] == trig]
    brightest = str(sp[0]['DETECTOR']).strip() if len(sp) else None
    bk = bkg[bkg['TRIGGER_NAME'] == trig]
    nai_dets = sorted({str(r['DETECTOR']).strip() for r in bk
                       if str(r['DETECTOR']).strip().startswith('n')})
    if brightest not in nai_dets and brightest is not None:
        # make sure the canonical (brightest) detector is in the block file
        nai_dets = sorted(set(nai_dets) | {brightest})
    # choose the detector whose events define the bins: the brightest NaI
    edge_det = brightest if brightest else (nai_dets[0] if nai_dets else None)
    tt = load_nai(trig, edge_det)
    if tt is None or tt.size < 50:
        summary.append((trig, edge_det, 0, 'NO DATA'))
        continue
    lo, hi = burst_window(tt)
    bb_edges, _, _ = burgess_blocks(tt, lo, hi)
    nblk = len(bb_edges) - 1

    rows = []
    bk_win = {str(r['DETECTOR']).strip():
              ((float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])),
               (float(r['BKG_POS_START']), float(r['BKG_POS_STOP'])))
              for r in bk}
    for det in nai_dets:
        tt_d = load_nai(trig, det)
        if tt_d is None:
            continue
        pre, post = bk_win.get(det, ((-50, -10), (hi+10, hi+50)))
        for i in range(nblk):
            s, e = float(bb_edges[i]), float(bb_edges[i+1])
            sig = block_significance(tt_d, s, e, pre, post)
            rows.append((trig, det, i, s, e, sig, False, 1, 2))
    t = Table(rows=rows, names=['TRIGGER_NAME', 'DETECTOR', 'BLOCK_INDEX',
              'T_START', 'T_STOP', 'SIGNIFICANCE', 'IS_MERGED',
              'CONSTITUENT_COUNT', 'POLY_ORDER'])
    outp = os.path.join(OUTB, f'bb_blocks_spectral_{trig}.ecsv')
    t.write(outp, format='ascii.ecsv', overwrite=True)
    summary.append((trig, edge_det, nblk, f'wrote {len(t)} rows '
                    f'({len(nai_dets)} dets x {nblk} blocks)'))

print(f'{"trigger":13s} {"edge_det":8s} {"Nblk":>4s}  note')
for trig, det, nblk, note in summary:
    print(f'{trig:13s} {str(det):8s} {nblk:>4d}  {note}')
print(f'\nBlocks -> {OUTB}')
