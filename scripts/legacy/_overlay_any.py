"""Overlay AI-vision background windows on a burst's brightest-NaI light curve.
Usage: _overlay_any.py <trigger> [<trigger> ...]   -> /tmp/ov_<trigger>.png"""
import os, sys, glob, json
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
LC = os.path.join(BASE, 'plots', 'lc_for_ai')
BIN = 1.024


def tte(trig, det):
    m = glob.glob(os.path.join(DATA, trig, f'glg_tte_{det}_*.fit*'))
    return m[0] if m else None


for trig in sys.argv[1:]:
    man = json.load(open(os.path.join(LC, f'{trig}_pending.json')))
    det = man['detectors'][0]['detector']      # brightest / smallest-angle NaI
    sel_all = json.load(open(os.path.join(LC, f'{trig}_ai_selections.json')))
    sel = sel_all.get(det) or list(sel_all.values())[0]
    f = tte(trig, det)
    if not f:
        print('no TTE', trig, det); continue
    with fits.open(f) as h:
        ev = h['EVENTS'].data
        t0 = next((hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header), 0.0)
        t = np.asarray(ev['TIME']) - t0
        pha = np.asarray(ev['PHA'])
        eb = h['EBOUNDS'].data
        emid = 0.5 * (np.asarray(eb['E_MIN']) + np.asarray(eb['E_MAX']))
    t = t[(emid[pha] >= 8.0) & (emid[pha] <= 900.0)]
    edges = np.arange(t.min(), t.max() + BIN, BIN)
    cnt, _ = np.histogram(t, bins=edges)
    ctr = 0.5 * (edges[:-1] + edges[1:])
    fig, ax = plt.subplots(figsize=(13, 4.0))
    ax.step(ctr, cnt / BIN, where='mid', color='k', lw=0.7)
    for (a, b), lab in [(sel['pre'], 'pre'), (sel['post'], 'post')]:
        ax.axvspan(a, b, color='gold', alpha=0.35,
                   label=f'{lab} [{a:.0f},{b:.0f}] ({b-a:.0f}s)')
    ax.set_title(f'{trig} ({det}) — conf={sel.get("confidence","?")} '
                 f'flags={sel.get("flags",[])}')
    ax.set_xlabel('Time since trigger (s)'); ax.set_ylabel('Counts s$^{-1}$')
    ax.legend(loc='upper right', fontsize=8); ax.grid(alpha=0.25)
    op = f'/tmp/ov_{trig}.png'
    fig.tight_layout(); fig.savefig(op, dpi=125); plt.close(fig)
    print('wrote', op)
