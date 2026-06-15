#!/usr/bin/env python
"""Figure: why the 'same' Bayesian-blocks method gives different bins than Burgess.
Same burst (110721A), same algorithm — the segmentation is set by two unpublished
knobs: the false-alarm prior p0 and the count-rate resolution dt."""
import warnings; warnings.filterwarnings('ignore')
import glob, numpy as np
from astropy.io import fits
from astropy.stats import bayesian_blocks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

trig, det = 'bn110721200', 'n6'
ELO, EHI = 8.0, 300.0
f = sorted(glob.glob(f'data/{trig}/glg_tte_{det}_*.fit*'))[0]
with fits.open(f) as h:
    ev = h['EVENTS'].data
    t0 = next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
    tt = np.asarray(ev['TIME']) - t0
    eb = h['EBOUNDS'].data
    emid = 0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
    tt = np.sort(tt[(emid[ev['PHA']] >= ELO) & (emid[ev['PHA']] <= EHI)])
lo, hi = -2, 24


def blocks(dt, p0):
    e = np.arange(lo, hi+dt, dt); c = 0.5*(e[:-1]+e[1:])
    cnt, _ = np.histogram(tt, bins=e); rate = cnt/dt
    err = np.sqrt(np.maximum(cnt, 1))/dt
    return bayesian_blocks(c, rate, err, fitness='measures', p0=p0)


def lc(dt):
    e = np.arange(lo, hi+dt, dt); c = 0.5*(e[:-1]+e[1:])
    cnt, _ = np.histogram(tt, bins=e)
    return c, cnt/dt


def draw(ax, dt_lc, edges, title, color):
    c, r = lc(dt_lc)
    ax.step(c, r, where='mid', color='0.4', lw=0.8)
    for i in range(len(edges)-1):
        s, e = edges[i], edges[i+1]
        m = (tt >= s) & (tt < e); rr = m.sum()/max(e-s, 1e-3)
        ax.plot([s, e], [rr, rr], color=color, lw=2.6)
        ax.axvline(s, color=color, ls=':', lw=0.6, alpha=0.6)
    ax.set_xlim(lo, hi); ax.set_xlabel('Time since trigger [s]')
    ax.set_ylabel('Count rate [s$^{-1}$]')
    ax.set_title(title)
    ax.tick_params(direction='in', which='both', top=True, right=True)
    ax.minorticks_on()


fig = plt.figure(figsize=(13, 8))
ax1 = fig.add_subplot(2, 2, 1)
e_ours = blocks(0.064, 0.01)
draw(ax1, 0.064, e_ours, f'OUR default: dt=64 ms, p0=0.01  ->  {len(e_ours)-1} blocks',
     'crimson')
ax2 = fig.add_subplot(2, 2, 2)
e_burg = blocks(2.0, 0.005)
draw(ax2, 0.256, e_burg,
     f'Burgess-like: dt=2 s, p0=0.005  ->  {len(e_burg)-1} blocks (his ~5-7)',
     'navy')

# bottom-left: nblocks vs p0 for several dt
ax3 = fig.add_subplot(2, 2, 3)
p0s = np.array([0.5, 0.1, 0.05, 0.01, 0.005, 0.001])
for dt, mk in [(0.064, 'o-'), (0.256, 's-'), (1.0, '^-'), (2.0, 'd-')]:
    ns = [len(blocks(dt, p)) - 1 for p in p0s]
    ax3.plot(p0s, ns, mk, label=f'dt={dt:g} s')
ax3.axhspan(5, 7, color='gold', alpha=0.35, label='Burgess ~5-7')
ax3.set_xscale('log'); ax3.set_xlabel('false-alarm prior $p_0$')
ax3.set_ylabel('number of blocks'); ax3.set_title('110721A: block count vs $p_0$ and $dt$')
ax3.legend(fontsize=8, framealpha=0.9, edgecolor='0.6')
ax3.tick_params(direction='in', which='both', top=True, right=True); ax3.minorticks_on()

# bottom-right: text takeaway
ax4 = fig.add_subplot(2, 2, 4); ax4.axis('off')
ax4.text(0.0, 1.0,
         'Why "same method" gives different bins:\n\n'
         '1. p0 (false-alarm prior): the penalty for adding a\n'
         '   change-point. Lower p0 -> fewer blocks. Burgess\n'
         '   never published his value.\n\n'
         '2. dt (count-rate resolution): finer light curve ->\n'
         '   more resolvable change-points. We used 64 ms TTE;\n'
         '   GBM CTIME rates are ~0.256-1 s -> far fewer blocks.\n\n'
         '3. Background subtraction: NO effect (a constant\n'
         '   offset does not move change-points).\n\n'
         '4. events vs measures mode: minor.\n\n'
         '=> Bayesian Blocks has a FREE regularization parameter.\n'
         '   "Same algorithm" != "same bins" unless (p0, dt,\n'
         '   implementation) are all matched. Burgess used his\n'
         '   own code (Burgess+2014 ApJ 784,17), not astropy.\n'
         '   Matching his count exactly would be circular; instead\n'
         '   we show conclusions are robust across (p0, dt).',
         va='top', ha='left', fontsize=10, family='monospace')

fig.suptitle('GRB 110721A — the Bayesian-block count is set by unpublished knobs, '
             'not by the algorithm', fontsize=12)
fig.tight_layout()
fig.savefig('results/figures/fig_bb_why_different.png', dpi=160, bbox_inches='tight')
print('wrote results/figures/fig_bb_why_different.png |',
      f'ours={len(e_ours)-1} burgesslike={len(e_burg)-1}')
