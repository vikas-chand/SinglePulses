#!/usr/bin/env python
"""Teaching figures for Khushboo's presentation deck.
  fig_teach_bayesian_blocks.png  — count LC + Bayesian-block edges (bn150902733)
  fig_teach_sample.png           — Busby-Lazzati sample: fluence & T90, LAT flagged
  fig_teach_schematic.png        — thermal+non-thermal vs 2SBPL (nu_m, nu_c) cartoon
"""
import warnings; warnings.filterwarnings('ignore')
import os, glob
import numpy as np
from astropy.io import fits
from astropy.table import Table
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data'); RES = os.path.join(BASE, 'results')
FIG = os.path.join(RES, 'figures'); os.makedirs(FIG, exist_ok=True)

def _style(ax):
    ax.tick_params(direction='in', which='both', top=True, right=True)
    ax.minorticks_on()

# ---------- 1. Bayesian-blocks light curve ----------
trig, det = 'bn150902733', 'n0'
tte = sorted(glob.glob(f'{DATA}/{trig}/glg_tte_{det}_*.fit*'))[0]
with fits.open(tte) as h:
    ev = h['EVENTS'].data
    t0 = next((hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header), 0.0)
    tt = np.asarray(ev['TIME']) - t0
    eb = h['EBOUNDS'].data
    emid = 0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
    tt = tt[(emid[ev['PHA']] >= 8) & (emid[ev['PHA']] <= 900)]
bb = Table.read(f'{RES}/bb_blocks_spectral_{trig}.ecsv', format='ascii.ecsv')
bb = bb[bb['DETECTOR'] == det]; bb.sort('T_START')
lo, hi = -10, 30
binw = 0.256
edges = np.arange(lo, hi+binw, binw)
cnt, _ = np.histogram(tt, bins=edges); rate = cnt/binw
ctr = 0.5*(edges[:-1]+edges[1:])
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.step(ctr, rate, where='mid', color='0.35', lw=0.8, label='counts (256 ms)')
for i, r in enumerate(bb):
    s, e = float(r['T_START']), float(r['T_STOP'])
    if e < lo or s > hi: continue
    m = (tt >= s) & (tt < e)
    rr = m.sum()/max(e-s, 1e-3)
    ax.plot([s, e], [rr, rr], color='crimson', lw=2.4,
            label='Bayesian block' if i == 0 else None)
    ax.axvline(s, color='crimson', ls=':', lw=0.7, alpha=0.6)
ax.set_xlim(lo, hi); ax.set_xlabel('Time since trigger [s]')
ax.set_ylabel('Count rate [s$^{-1}$]'); _style(ax)
ax.set_title(f'Bayesian Blocks define the time bins  —  {trig} ({det}, 8–900 keV)')
ax.legend(framealpha=0.9, edgecolor='0.6')
fig.tight_layout(); fig.savefig(f'{FIG}/fig_teach_bayesian_blocks.png', dpi=200)
plt.close(fig)

# ---------- 2. Busby-Lazzati sample overview ----------
sp = Table.read(f'{RES}/single_pulse_grbs.ecsv', format='ascii.ecsv')
flu = np.asarray(sp['FLUENCE'], float); t90 = np.asarray(sp['T90'], float)
lat = np.asarray(sp['HAS_LAT'], bool)
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
ax[0].hist(np.log10(flu), bins=18, color='#4477aa', edgecolor='k', alpha=0.85)
ax[0].set_xlabel(r'$\log_{10}$ fluence [erg cm$^{-2}$]')
ax[0].set_ylabel('GRBs'); _style(ax[0])
ax[0].set_title('Fluence (250× span)')
ax[1].scatter(t90[~lat], flu[~lat], s=22, c='0.5', label='GBM only')
ax[1].scatter(t90[lat], flu[lat], s=34, c='crimson', marker='*',
              label=f'has LAT ({lat.sum()})')
ax[1].set_xscale('log'); ax[1].set_yscale('log')
ax[1].set_xlabel(r'$T_{90}$ [s]'); ax[1].set_ylabel('fluence [erg cm$^{-2}$]')
_style(ax[1]); ax[1].legend(framealpha=0.9, edgecolor='0.6')
ax[1].set_title('T$_{90}$ vs fluence')
fig.suptitle(f'Single-pulse sample (Busby & Lazzati selection):  {len(sp)} GRBs')
fig.tight_layout(); fig.savefig(f'{FIG}/fig_teach_sample.png', dpi=200)
plt.close(fig)

# ---------- 3. Thermal+non-thermal vs 2SBPL schematic (nuFnu) ----------
E = np.logspace(0, 4, 500)   # keV
def band(E, a=-1.0, b=-2.3, Ep=200.0):
    Ec = (a-b)*Ep/(2+a)
    f = np.where(E < Ec, (E/100)**(a)*np.exp(-E*(2+a)/Ep),
                 (E/100)**(b)*((a-b)*Ep/(100*(2+a)))**(a-b)*np.exp(b-a))
    return f*E**2
def bb(E, kT=30.0):
    return E**2 * (E**2/(np.exp(np.clip(E/kT,0,700))-1))
def sbpl2(E, a1=-0.6, a2=-1.1, b=-2.3, Eb1=40.0, Eb2=300.0):
    # piecewise nuFnu cartoon with two breaks
    f = np.where(E<Eb1, (E/Eb1)**a1,
        np.where(E<Eb2, (E/Eb1)**a2*(Eb1/Eb1)**0, (E/Eb2)**b*(Eb2/Eb1)**a2))
    return f*E**2
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
# left: Band + BB
nt = band(E); th = bb(E)*8e-3
ax[0].loglog(E, nt/nt.max(), 'b-', lw=2, label='non-thermal (Band)')
ax[0].loglog(E, th/th.max()*0.6, 'r--', lw=2, label='thermal (BB, kT)')
ax[0].loglog(E, nt/nt.max()+th/th.max()*0.6, 'k-', lw=1, alpha=0.5, label='sum')
ax[0].axvline(200, color='b', ls=':', lw=0.8); ax[0].text(200, 1.3, '$E_p$', color='b')
ax[0].axvline(85, color='r', ls=':', lw=0.8); ax[0].text(60, 1.3, '$kT$', color='r')
ax[0].set_ylim(1e-2, 3); ax[0].set_xlabel('Energy [keV]')
ax[0].set_ylabel(r'$\nu F_\nu$ (arb.)'); _style(ax[0])
ax[0].legend(fontsize=8, framealpha=0.9, edgecolor='0.6')
ax[0].set_title('Thermal + non-thermal (Burgess+2014)')
# right: 2SBPL synchrotron with nu_m, nu_c
s = sbpl2(E)
ax[1].loglog(E, s/np.nanmax(s), 'g-', lw=2, label='2SBPL (synchrotron)')
ax[1].axvline(40, color='purple', ls=':', lw=1); ax[1].text(28, 1.3, r'$\nu_c$', color='purple')
ax[1].axvline(300, color='darkorange', ls=':', lw=1); ax[1].text(300, 1.3, r'$\nu_m=E_p$', color='darkorange')
ax[1].set_ylim(1e-2, 3); ax[1].set_xlabel('Energy [keV]')
ax[1].set_ylabel(r'$\nu F_\nu$ (arb.)'); _style(ax[1])
ax[1].legend(fontsize=8, framealpha=0.9, edgecolor='0.6')
ax[1].set_title('Two breaks: cooling ($\\nu_c$) + injection ($\\nu_m$)')
fig.suptitle('Two interpretations of the same spectral curvature')
fig.tight_layout(); fig.savefig(f'{FIG}/fig_teach_schematic.png', dpi=200)
plt.close(fig)

print('wrote 3 teaching figures to', FIG)
