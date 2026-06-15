#!/usr/bin/env python
"""
Burgess+2014 reproduction on Burgess-FAITHFUL Bayesian blocks.

Compares two binnings for the 6 common bursts:
  PROD     = our production blocks (event-mode BB, 8-900 keV)  -> results/per_burst
  REBLOCK  = Burgess-faithful blocks (count-rate BB, 8-300 keV) -> results/burgess_repro/per_burst

For 130427A we reuse the production fit (88 blocks already match Burgess's ~81;
alpha=0.66 baryonic already reproduces). All others are re-fit on REBLOCK.

Ep is the nuFnu peak per model (Band+BB -> Band xp; CPL+BB -> (2+index)*xc).
A block contributes an (Ep,kT) pair when the +BB composite is physically valid
and the blackbody is genuinely detected (Wilks LRT vs non-thermal parent).
"""
import warnings; warnings.filterwarnings('ignore')
import os, json
import numpy as np
from astropy.table import Table
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = os.path.join(BASE, 'results', 'per_burst')
REBL = os.path.join(BASE, 'results', 'burgess_repro', 'per_burst')
FIG = os.path.join(BASE, 'results', 'figures')

BURGESS = {
    'GRB 081224A': ('bn081224887', 1.01, 0.14, 'baryonic'),
    'GRB 090719A': ('bn090719063', 2.33, 0.27, 'magnetic'),
    'GRB 100707A': ('bn100707032', 1.77, 0.07, 'magnetic'),
    'GRB 110721A': ('bn110721200', 1.24, 0.11, 'baryonic'),
    'GRB 110920A': ('bn110920546', 1.97, 0.11, 'magnetic'),
    'GRB 130427A': ('bn130427324', 1.02, 0.05, 'baryonic'),
}
# which source to read each burst from in the REBLOCK column
REBLOCK_SRC = {  # 130427A reuses production (already Burgess-like)
    'bn081224887': REBL, 'bn090719063': REBL, 'bn100707032': REBL,
    'bn110721200': REBL, 'bn110920546': REBL, 'bn130427324': PROD,
}

EP_BOUNDS = (30.0, 5000.0); KT_BOUNDS = (1.0, 200.0)
LRT_BB_MIN = 9.2


def _cpl_peak(index, xc):
    out = (2.0 + index) * xc
    return np.where(index > -2.0, out, np.nan)


def valid_pairs(t, require_bb_sig=True):
    rows = t[t['BLOCK'] >= 0]
    kt_out, ep_out = [], []
    for r in rows:
        cands = []
        if 'BANDBB_VALID' in rows.colnames and bool(r['BANDBB_VALID']):
            lrt = float(r['LRT_BANDBB_BAND']) if np.isfinite(r['LRT_BANDBB_BAND']) else -np.inf
            kt = float(r['BANDBB_KT']); ep = float(r['BANDBB_EP'])
            railed = (kt <= KT_BOUNDS[0]*1.02 or kt >= KT_BOUNDS[1]*0.98
                      or ep <= EP_BOUNDS[0]*1.02)
            if (np.isfinite(kt) and np.isfinite(ep) and kt > 0 and ep > 0
                    and not railed and (lrt >= LRT_BB_MIN or not require_bb_sig)):
                cands.append((float(r['BANDBB_AIC']), kt, ep))
        if 'CPLBB_VALID' in rows.colnames and bool(r['CPLBB_VALID']):
            lrt = float(r['LRT_CPLBB_CPL']) if np.isfinite(r['LRT_CPLBB_CPL']) else -np.inf
            kt = float(r['CPLBB_KT']); idx = float(r['CPLBB_INDEX']); xc = float(r['CPLBB_XC'])
            ep = float(_cpl_peak(idx, xc)) if (np.isfinite(idx) and np.isfinite(xc)) else np.nan
            railed = (kt <= KT_BOUNDS[0]*1.02 or kt >= KT_BOUNDS[1]*0.98)
            if (np.isfinite(kt) and np.isfinite(ep) and kt > 0 and ep > 0
                    and not railed and (lrt >= LRT_BB_MIN or not require_bb_sig)):
                cands.append((float(r['CPLBB_AIC']), kt, ep))
        if cands:
            cands.sort(key=lambda c: c[0])
            kt_out.append(cands[0][1]); ep_out.append(cands[0][2])
    return np.array(kt_out), np.array(ep_out)


def fit_alpha(kt, ep):
    if len(kt) < 3:
        return np.nan, np.nan, np.nan, np.nan, len(kt)
    lx, ly = np.log10(kt), np.log10(ep)
    coef, cov = np.polyfit(lx, ly, 1, cov=True)
    alpha = float(coef[0])
    aerr = float(np.sqrt(cov[0, 0])) if np.all(np.isfinite(cov)) else np.nan
    rho, p = spearmanr(kt, ep)
    return alpha, aerr, float(rho), float(p), len(kt)


def classify(a):
    if not np.isfinite(a):
        return 'undetermined'
    return 'baryonic' if a < 1.5 else 'magnetic'


def analyse(path):
    if not os.path.exists(path):
        return None
    t = Table.read(path, format='ascii.ecsv')
    kt, ep = valid_pairs(t, require_bb_sig=True)
    a, ae, rho, p, n = fit_alpha(kt, ep)
    return dict(kt=kt, ep=ep, alpha=a, alpha_err=ae, rho=rho, p=p, N=n,
               jet=classify(a))


results = {}
pooled = {'prod': ([], []), 'rebl': ([], [])}
for g, (trig, a_pub, ae_pub, jet_pub) in BURGESS.items():
    prod = analyse(os.path.join(PROD, trig, 'spectral_fits.ecsv'))
    rebl = analyse(os.path.join(REBLOCK_SRC[trig], trig, 'spectral_fits.ecsv'))
    results[g] = dict(trig=trig, a_pub=a_pub, ae_pub=ae_pub, jet_pub=jet_pub,
                      prod=prod, rebl=rebl)
    if prod:
        pooled['prod'][0].extend(prod['kt']); pooled['prod'][1].extend(prod['ep'])
    if rebl:
        pooled['rebl'][0].extend(rebl['kt']); pooled['rebl'][1].extend(rebl['ep'])

comb = {}
for k, (kts, eps) in pooled.items():
    kts, eps = np.array(kts), np.array(eps)
    if len(kts) >= 3:
        r, p = spearmanr(kts, eps)
        comb[k] = dict(rho=float(r), p=float(p), N=int(len(kts)))
    else:
        comb[k] = dict(rho=np.nan, p=np.nan, N=int(len(kts)))

# ---------- report ----------
L = []
L.append('BURGESS+2014 REPRODUCTION: production blocks vs Burgess-faithful re-blocking')
L.append(f'{"GRB":12s} {"pubA":>10s} {"pubJet":>9s} | '
         f'{"PROD N":>6s} {"PROD a":>11s} {"PROD jet":>9s} | '
         f'{"REBL N":>6s} {"REBL a":>11s} {"REBL jet":>9s} {"match":>5s}')
for g, (trig, a_pub, ae_pub, jet_pub) in BURGESS.items():
    r = results[g]; pr = r['prod'] or {}; rb = r['rebl'] or {}
    def fa(d):
        return (f'{d.get("alpha",float("nan")):.2f}+/-{d.get("alpha_err",float("nan")):.2f}'
                if d and np.isfinite(d.get('alpha', np.nan)) else 'n/a')
    match = ('YES' if (rb and np.isfinite(rb.get('alpha', np.nan))
                       and classify(rb['alpha']) == jet_pub) else
             ('no' if (rb and np.isfinite(rb.get('alpha', np.nan))) else '-'))
    note = ' (PROD reused)' if trig == 'bn130427324' else ''
    L.append(f'{g:12s} {a_pub:>6.2f}+/-{ae_pub:<3.2f} {jet_pub:>9s} | '
             f'{pr.get("N",0):>6d} {fa(pr):>11s} {classify(pr.get("alpha",np.nan)):>9s} | '
             f'{rb.get("N",0):>6d} {fa(rb):>11s} {classify(rb.get("alpha",np.nan)):>9s} {match:>5s}{note}')
L.append('')
L.append(f'COMBINED  PROD: N={comb["prod"]["N"]} rho={comb["prod"]["rho"]:.3f} p={comb["prod"]["p"]:.2e}')
L.append(f'COMBINED  REBL: N={comb["rebl"]["N"]} rho={comb["rebl"]["rho"]:.3f} p={comb["rebl"]["p"]:.2e}')
L.append(f'Burgess+2014:   rho=0.81 p=4.35e-20')
report = '\n'.join(L)
open('/tmp/burgess_repro_reblock.txt', 'w').write(report + '\n')
print(report)
json.dump({'per_burst': {g: {'a_pub': results[g]['a_pub'],
           'prod': {k: (v.tolist() if hasattr(v, 'tolist') else v)
                    for k, v in (results[g]['prod'] or {}).items()},
           'rebl': {k: (v.tolist() if hasattr(v, 'tolist') else v)
                    for k, v in (results[g]['rebl'] or {}).items()}}
           for g in BURGESS}, 'combined': comb},
          open('/tmp/burgess_repro_reblock.json', 'w'), indent=1, default=float)

# ---------- figure: per-burst panels, PROD (grey) vs REBL (black+fit) ----------
fig, axes = plt.subplots(2, 3, figsize=(14, 9))
for ax, (g, (trig, a_pub, ae_pub, jet_pub)) in zip(axes.flat, BURGESS.items()):
    r = results[g]; pr = r['prod']; rb = r['rebl']
    if pr and len(pr['kt']):
        ax.scatter(pr['kt'], pr['ep'], s=26, facecolors='none',
                   edgecolors='0.6', label=f'production (N={pr["N"]})')
    if rb and len(rb['kt']):
        ax.scatter(rb['kt'], rb['ep'], c='k', s=30, zorder=3,
                   label=f're-blocked (N={rb["N"]})')
    if rb and rb['N'] >= 3 and np.isfinite(rb['alpha']):
        xx = np.logspace(np.log10(rb['kt'].min()), np.log10(rb['kt'].max()), 20)
        c = np.polyfit(np.log10(rb['kt']), np.log10(rb['ep']), 1)
        ax.plot(xx, 10**(c[1]+c[0]*np.log10(xx)), 'b--',
                label=f'our α={rb["alpha"]:.2f}±{rb["alpha_err"]:.2f}')
    ax.plot([], [], ' ', label=f'Burgess α={a_pub:.2f}')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('kT [keV]'); ax.set_ylabel('Ep [keV]')
    ax.set_title(f'{g}')
    ax.legend(fontsize=7, framealpha=0.9, edgecolor='0.6')
    ax.tick_params(direction='in', which='both', top=True, right=True)
    ax.minorticks_on()
fig.suptitle('Burgess+2014 reproduction — Burgess-faithful re-blocking (black) '
             'vs production (grey)')
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'fig_burgess_reblock.png'), dpi=200, bbox_inches='tight')
plt.close(fig)
print('\nwrote results/figures/fig_burgess_reblock.png')
