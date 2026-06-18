#!/usr/bin/env python
"""Point-6 teaching figure: LAT-LLE Bayesian-blocks light curve (bn150902733).
Shows the high-energy (>30 MeV) emission and its Bayesian blocks alongside the
GBM (8-900 keV) pulse, motivating a time-resolved cutoff/extra-break search."""
import warnings; warnings.filterwarnings('ignore')
import os, glob
import numpy as np
from astropy.io import fits
from astropy.stats import bayesian_blocks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data'); FIG = os.path.join(BASE, 'results', 'figures')
trig = 'bn150902733'
lo, hi = -5, 30

def _style(ax):
    ax.tick_params(direction='in', which='both', top=True, right=True)
    ax.minorticks_on()

# --- LLE (>30 MeV) events ---
with fits.open(f'{DATA}/{trig}/gll_lle_{trig}_v00.fit') as h:
    ev = h['EVENTS'].data
    t0 = next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
    tlle = np.asarray(ev['TIME']) - t0
tlle = tlle[(tlle >= lo) & (tlle <= hi)]

# --- GBM n0 (8-900 keV) for context ---
tte = sorted(glob.glob(f'{DATA}/{trig}/glg_tte_n0_*.fit*'))[0]
with fits.open(tte) as h:
    ev = h['EVENTS'].data
    t0g = next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
    tg = np.asarray(ev['TIME']) - t0g
    eb = h['EBOUNDS'].data
    emid = 0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
    tg = tg[(emid[ev['PHA']] >= 8) & (emid[ev['PHA']] <= 900)]
tg = tg[(tg >= lo) & (tg <= hi)]

fig, ax = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True,
                       gridspec_kw={'hspace': 0.06})

# GBM panel
bw = 0.256
eg = np.arange(lo, hi+bw, bw); cg, _ = np.histogram(tg, bins=eg)
ax[0].step(0.5*(eg[:-1]+eg[1:]), cg/bw, where='mid', color='0.35', lw=0.8)
ax[0].set_ylabel('GBM n0 rate\n[s$^{-1}$], 8–900 keV')
ax[0].set_title(f'{trig}: keV pulse vs. >30 MeV (LAT-LLE) emission')
_style(ax[0])

# LLE panel: coarse histogram + Bayesian blocks
bwl = 1.0
el = np.arange(lo, hi+bwl, bwl); cl, _ = np.histogram(tlle, bins=el)
ax[1].step(0.5*(el[:-1]+el[1:]), cl/bwl, where='mid', color='0.5', lw=0.8,
           label='LLE counts (1 s)')
edges = bayesian_blocks(tlle, fitness='events', p0=0.05)
for i in range(len(edges)-1):
    s, e = edges[i], edges[i+1]
    m = (tlle >= s) & (tlle < e)
    rr = m.sum()/max(e-s, 1e-3)
    ax[1].plot([s, e], [rr, rr], color='darkgreen', lw=2.6,
               label='LLE Bayesian blocks' if i == 0 else None)
    ax[1].axvline(s, color='darkgreen', ls=':', lw=0.6, alpha=0.5)
ax[1].set_ylabel('LLE rate [s$^{-1}$]\n>30 MeV')
ax[1].set_xlabel('Time since trigger [s]'); ax[1].set_xlim(lo, hi)
ax[1].legend(framealpha=0.9, edgecolor='0.6', fontsize=9)
_style(ax[1])
fig.savefig(f'{FIG}/fig_teach_lle_bb.png', dpi=200, bbox_inches='tight')
print('wrote', f'{FIG}/fig_teach_lle_bb.png', '| LLE events:', tlle.size,
      '| blocks:', len(edges)-1)
