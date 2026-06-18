"""Overlay the AI-vision background windows on each pilot burst's brightest-NaI
light curve (gold pre/post shading) for visual verification. Saves PNGs to /tmp."""
import os, glob, json
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
LCDIR = os.path.join(BASE, 'plots', 'lc_for_ai')

PILOTS = {'bn260105973': 'n1', 'bn150902733': 'n3', 'bn130427324': 'n9'}
BIN = 1.024


def tte(trig, det):
    m = glob.glob(os.path.join(DATA, trig, f'glg_tte_{det}_*.fit*'))
    return m[0] if m else None


def trigtime(hdul):
    for h in hdul:
        if 'TRIGTIME' in h.header:
            return float(h.header['TRIGTIME'])
    return 0.0


outs = []
for trig, det in PILOTS.items():
    f = tte(trig, det)
    if not f:
        print('no TTE', trig, det); continue
    with fits.open(f) as h:
        ev = h['EVENTS'].data
        t0 = trigtime(h)
        t = np.asarray(ev['TIME']) - t0
        pha = np.asarray(ev['PHA'])
        eb = h['EBOUNDS'].data
        emin = np.asarray(eb['E_MIN']); emax = np.asarray(eb['E_MAX'])
    emid = 0.5 * (emin + emax)
    keep = (emid[pha] >= 8.0) & (emid[pha] <= 900.0)
    t = t[keep]
    sel = json.load(open(os.path.join(LCDIR, f'{trig}_ai_selections.json')))[det]
    lo, hi = t.min(), t.max()
    edges = np.arange(lo, hi + BIN, BIN)
    cnt, _ = np.histogram(t, bins=edges)
    rate = cnt / BIN
    ctr = 0.5 * (edges[:-1] + edges[1:])

    fig, ax = plt.subplots(figsize=(13, 4.2))
    ax.step(ctr, rate, where='mid', color='k', lw=0.7)
    for (a, b), lab in [(sel['pre'], 'pre'), (sel['post'], 'post')]:
        ax.axvspan(a, b, color='gold', alpha=0.35,
                   label=f'{lab} [{a:.0f},{b:.0f}]')
    ax.set_xlabel('Time since trigger (s)'); ax.set_ylabel('Counts s$^{-1}$')
    ax.set_title(f'{trig} ({det}) — AI-vision background windows '
                 f'(conf={sel["confidence"]})')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(alpha=0.25)
    op = f'/tmp/pilot_{trig}_{det}.png'
    fig.tight_layout(); fig.savefig(op, dpi=130); plt.close(fig)
    outs.append(op)
    print('wrote', op)
print('OUTS:', ','.join(outs))
