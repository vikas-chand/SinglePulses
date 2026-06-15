#!/usr/bin/env python
"""
Sample-level figures from results/sample_all_models.ecsv (vision-bkg redo).
Validity-gated throughout (only *_VALID fits enter the population stats).

Figures (-> results/figures/):
  fig_model_fractions.png   — winner fractions: raw-AIC vs dAIC>=10 decision rule
  fig_curvature_split.png   — among curvature-required blocks: thermal/degenerate/2break
  fig_alpha_dist.png        — Band low-energy index alpha distribution + line of death
  fig_ep_kt.png             — Ep vs kT (Band+BB VALID blocks), Burgess+2014 style + Spearman
  fig_dsbpl_lrt.png         — DSBPL-vs-SBPL LRT distribution (the two-break significance)
"""
import warnings; warnings.filterwarnings('ignore')
import os
import numpy as np
from astropy.table import Table
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, 'results')
FIG = os.path.join(RES, 'figures')
os.makedirs(FIG, exist_ok=True)

am = Table.read(os.path.join(RES, 'sample_all_models.ecsv'), format='ascii.ecsv')
best = Table.read(os.path.join(RES, 'sample_best_per_block.ecsv'), format='ascii.ecsv')
N = len(am)
NB = len(set(str(x) for x in am['TRIGGER_NAME']))

PREFIX = {'Band': 'BAND', 'CPL': 'CPL', 'SBPL': 'SBPL', 'DSBPL': 'DSBPL',
          'Band+BB': 'BANDBB', 'CPL+BB': 'CPLBB'}
ORDER = ['Band', 'CPL', 'SBPL', 'DSBPL', 'Band+BB', 'CPL+BB']
COL = {'Band': '#4477aa', 'CPL': '#66ccee', 'SBPL': '#228833',
       'DSBPL': '#ccbb44', 'Band+BB': '#ee6677', 'CPL+BB': '#aa3377'}


def aic(row, nm):
    c = f'{PREFIX[nm]}_AIC'
    return float(row[c]) if (c in row.colnames and np.isfinite(row[c])) else np.inf


def valid(row, nm):
    c = f'{PREFIX[nm]}_VALID'
    if c not in row.colnames:
        return np.isfinite(aic(row, nm))
    return bool(row[c]) and np.isfinite(aic(row, nm))


def _style(ax):
    ax.tick_params(direction='in', which='both', top=True, right=True)
    ax.minorticks_on()


# ---------- Fig 1: model fractions, raw vs decision-rule ----------
from collections import Counter
raw = Counter(str(m) for m in best['BEST_MODEL'])
DEC = 10.0
dec = Counter()
for r in am:
    cand = {nm: aic(r, nm) for nm in PREFIX if valid(r, nm)}
    if not cand:
        dec['INCONCLUSIVE'] += 1; continue
    o = sorted(cand.items(), key=lambda x: x[1])
    dec[o[0][0] if (len(o) == 1 or o[1][1]-o[0][1] >= DEC) else 'INCONCLUSIVE'] += 1

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(ORDER)); w = 0.38
ax.bar(x - w/2, [100*raw.get(m, 0)/len(best) for m in ORDER], w,
       label='lowest-AIC (per block)', color=[COL[m] for m in ORDER], edgecolor='k', lw=0.5)
ax.bar(x + w/2, [100*dec.get(m, 0)/N for m in ORDER], w,
       label=f'decision rule (ΔAIC≥{DEC:.0f})', color=[COL[m] for m in ORDER],
       edgecolor='k', lw=0.5, alpha=0.55, hatch='//')
ax.set_xticks(x); ax.set_xticklabels(ORDER, rotation=20)
ax.set_ylabel('% of blocks'); _style(ax)
ax.set_title(f'Best-model fractions  ({N} blocks, {NB} bursts)\n'
             f'decision-rule INCONCLUSIVE = {100*dec.get("INCONCLUSIVE",0)/N:.0f}%')
ax.legend(framealpha=0.9, edgecolor='0.6')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig_model_fractions.png'), dpi=300)
plt.close(fig)

# ---------- Fig 2: curvature split ----------
SINGLE = ['Band', 'CPL', 'SBPL']; TWOB = ['DSBPL']; THERM = ['Band+BB', 'CPL+BB']
THR = 6.0
n_th = n_dg = n_2b = 0
for r in am:
    s = min([aic(r, n) for n in SINGLE if valid(r, n)] or [np.inf])
    tb = min([aic(r, n) for n in TWOB if valid(r, n)] or [np.inf])
    th = min([aic(r, n) for n in THERM if valid(r, n)] or [np.inf])
    cv = min(tb, th)
    if not (np.isfinite(cv) and np.isfinite(s)) or s - cv <= THR:
        continue
    d = tb - th
    if abs(d) < 4: n_dg += 1
    elif d < 0:    n_2b += 1
    else:          n_th += 1
tot = n_th + n_dg + n_2b
fig, ax = plt.subplots(figsize=(7, 5))
labels = [f'thermal-proxy\npreferred\n({n_th})',
          f'DEGENERATE\n2brk≈thermal\n({n_dg})',
          f'two-break\npreferred\n({n_2b})']
ax.bar([0, 1, 2], [n_th, n_dg, n_2b],
       color=['#ee6677', '#bbbbbb', '#ccbb44'], edgecolor='k')
ax.set_xticks([0, 1, 2]); ax.set_xticklabels(labels)
ax.set_ylabel('blocks'); _style(ax)
ax.set_title(f'Curvature beyond a single break: interpretation\n'
             f'{tot} blocks require curvature (ΔAIC>{THR:.0f} vs single); '
             f'{100*(n_th+n_dg)/tot:.0f}% thermal-or-degenerate')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig_curvature_split.png'), dpi=300)
plt.close(fig)

# ---------- Fig 3: alpha distribution (Band, VALID) ----------
al = np.array([float(r['BAND_ALPHA']) for r in am
               if valid(r, 'Band') and np.isfinite(r['BAND_ALPHA'])])
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(al, bins=np.arange(-2.0, 1.5, 0.15), color='#4477aa', edgecolor='k', alpha=0.85)
ax.axvline(-2/3, ls='--', color='k', label='slow-cooling sync (−2/3)')
ax.axvline(-1.0, ls=':', color='r', label='line of death (−1)')
ax.axvline(-3/2, ls='-.', color='purple', label='fast-cooling sync (−3/2)')
ax.set_xlabel(r'Band $\alpha$ (low-energy photon index)')
ax.set_ylabel('VALID blocks'); _style(ax)
ax.set_title(f'Low-energy index distribution ({len(al)} VALID Band blocks)')
ax.legend(framealpha=0.9, edgecolor='0.6')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig_alpha_dist.png'), dpi=300)
plt.close(fig)

# ---------- Fig 4: Ep vs kT (Band+BB VALID) ----------
ep, kt = [], []
for r in am:
    if valid(r, 'Band+BB') and np.isfinite(r['BANDBB_EP']) and np.isfinite(r['BANDBB_KT']):
        ep.append(float(r['BANDBB_EP'])); kt.append(float(r['BANDBB_KT']))
ep = np.array(ep); kt = np.array(kt)
fig, ax = plt.subplots(figsize=(7, 6))
if len(ep) >= 2:
    ax.scatter(kt, ep, c='k', s=18, alpha=0.6)
    m = np.isfinite(np.log10(kt)) & np.isfinite(np.log10(ep))
    if m.sum() >= 3:
        sl, ic = np.polyfit(np.log10(kt[m]), np.log10(ep[m]), 1)
        from scipy.stats import spearmanr
        rho, p = spearmanr(kt[m], ep[m])
        xx = np.logspace(np.log10(kt[m].min()), np.log10(kt[m].max()), 30)
        ax.plot(xx, 10**(ic+sl*np.log10(xx)), 'b--',
                label=f'slope={sl:.2f}\nρ={rho:.2f}, p={p:.1e}\nN={m.sum()}')
        ax.legend(framealpha=0.9, edgecolor='0.6')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('kT [keV]'); ax.set_ylabel('Ep [keV]'); _style(ax)
ax.set_title('Ep vs kT — Band+BB VALID blocks (Burgess+2014 style)')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig_ep_kt.png'), dpi=300)
plt.close(fig)

# ---------- Fig 5: DSBPL-vs-SBPL LRT ----------
if 'LRT_DSBPL_SBPL' in am.colnames:
    lrt = np.array([float(r['LRT_DSBPL_SBPL']) for r in am
                    if valid(r, 'DSBPL') and np.isfinite(r['LRT_DSBPL_SBPL'])])
    fig, ax = plt.subplots(figsize=(8, 5))
    lc = np.clip(lrt, -5, 60)
    ax.hist(lc, bins=np.arange(-5, 62, 2.5), color='#ccbb44', edgecolor='k', alpha=0.85)
    ax.axvline(9.2, ls='--', color='k', label='99% (2 dof)')
    ax.axvline(13.8, ls=':', color='r', label='~3σ (2 dof)')
    ax.set_xlabel('LRT  2·Δln L  (DSBPL vs SBPL)')
    ax.set_ylabel('VALID DSBPL blocks'); _style(ax)
    ax.set_title(f'Second-break significance ({len(lrt)} VALID DSBPL blocks; '
                 f'{(lrt>9.2).sum()} at 99%, {(lrt>13.8).sum()} at ~3σ)')
    ax.legend(framealpha=0.9, edgecolor='0.6')
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig_dsbpl_lrt.png'), dpi=300)
    plt.close(fig)

print('wrote figures to', FIG)
for f in sorted(os.listdir(FIG)):
    print('  ', f)
