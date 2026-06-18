#!/usr/bin/env python
"""
Reproduce Burgess+2014 (ApJL 784 L43): per-burst Ep-kT correlation Ep ~ T^alpha
on the 6 bursts of that paper, all present in our 106-burst sample.

Burgess method (verified from the PDF):
  - PER-BURST: fit log10(Ep) vs log10(kT) across that GRB's time-resolved bins.
  - Pairs come from a 2-component (non-thermal + blackbody) fit in EVERY bin
    where both components are present -- NOT only bins where BB "wins" selection.
    Our analog: the Band+BB fit's Ep (Band xp) and kT (BB), validity-gated.
  - alpha ~ 1 => baryonic jet; alpha ~ 2 => magnetic jet.
  - Combined-sample Spearman rho = 0.81, p = 4.35e-20 (his Fig 4).

Burgess Table 1 (published):
  081224A 1.01+/-0.14 baryonic | 090719A 2.33+/-0.27 magnetic
  100707A 1.77+/-0.07 magnetic | 110721A 1.24+/-0.11 baryonic
  110920A 1.97+/-0.11 magnetic | 130427A 1.02+/-0.05 baryonic

Writes /tmp/burgess_repro.json + a readable report; figure to results/figures/.
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
PB = os.path.join(BASE, 'results', 'per_burst')
FIG = os.path.join(BASE, 'results', 'figures')

# Burgess GRB -> our trigger, with his published alpha + jet type
BURGESS = {
    'GRB 081224A': ('bn081224887', 1.01, 0.14, 'baryonic'),
    'GRB 090719A': ('bn090719063', 2.33, 0.27, 'magnetic'),
    'GRB 100707A': ('bn100707032', 1.77, 0.07, 'magnetic'),
    'GRB 110721A': ('bn110721200', 1.24, 0.11, 'baryonic'),
    'GRB 110920A': ('bn110920546', 1.97, 0.11, 'magnetic'),
    'GRB 130427A': ('bn130427324', 1.02, 0.05, 'baryonic'),
}

# Bounds (mirror script 10) for rail rejection
EP_BOUNDS = (30.0, 5000.0)
KT_BOUNDS = (1.0, 200.0)


# BB-significance threshold: a block contributes an (Ep,kT) pair only if the
# blackbody is GENUINELY detected — i.e. the +BB composite beats its non-thermal
# parent by a Wilks LRT on 2 extra dof. >9.2 = 99%; Burgess only used bins where
# the thermal component is present, which is what makes his correlation tight.
LRT_BB_MIN = 9.2


def _cpl_peak(index, xc):
    """nuFnu peak of a cutoff power law: Ep = (2 + index) * xc.
    (Returns nan if index <= -2, i.e. no peak — rising spectrum.)"""
    out = (2.0 + index) * xc
    return np.where(index > -2.0, out, np.nan)


def valid_pairs(t, require_bb_sig=True):
    """Per time-resolved block, return (kT, Ep) where a +BB composite has BB
    GENUINELY detected and is physically valid. Ep is the nuFnu PEAK, correctly
    parameterized per model: Band+BB -> Band xp; CPL+BB -> (2+index)*xc.
    When both composites qualify in a block, take the lower-AIC one.
    excludes BLOCK=-1 (time-integrated); Burgess uses time bins.
    """
    rows = t[t['BLOCK'] >= 0]
    kt_out, ep_out = [], []
    for r in rows:
        cands = []   # (aic, kT, Ep)
        # --- Band+BB ---
        if 'BANDBB_VALID' in rows.colnames and bool(r['BANDBB_VALID']):
            lrt = float(r['LRT_BANDBB_BAND']) if np.isfinite(r['LRT_BANDBB_BAND']) else -np.inf
            kt = float(r['BANDBB_KT']); ep = float(r['BANDBB_EP'])
            railed = (kt <= KT_BOUNDS[0]*1.02 or kt >= KT_BOUNDS[1]*0.98
                      or ep <= EP_BOUNDS[0]*1.02)
            if (np.isfinite(kt) and np.isfinite(ep) and kt > 0 and ep > 0
                    and not railed and (lrt >= LRT_BB_MIN or not require_bb_sig)):
                cands.append((float(r['BANDBB_AIC']), kt, ep))
        # --- CPL+BB (Ep = (2+index)*xc) ---
        if 'CPLBB_VALID' in rows.colnames and bool(r['CPLBB_VALID']):
            lrt = float(r['LRT_CPLBB_CPL']) if np.isfinite(r['LRT_CPLBB_CPL']) else -np.inf
            kt = float(r['CPLBB_KT']); idx = float(r['CPLBB_INDEX']); xc = float(r['CPLBB_XC'])
            ep = float(_cpl_peak(idx, xc)) if (np.isfinite(idx) and np.isfinite(xc)) else np.nan
            railed = (kt <= KT_BOUNDS[0]*1.02 or kt >= KT_BOUNDS[1]*0.98)
            if (np.isfinite(kt) and np.isfinite(ep) and kt > 0 and ep > 0
                    and not railed and (lrt >= LRT_BB_MIN or not require_bb_sig)):
                cands.append((float(r['CPLBB_AIC']), kt, ep))
        if cands:
            cands.sort(key=lambda c: c[0])   # lowest AIC wins the block
            kt_out.append(cands[0][1]); ep_out.append(cands[0][2])
    return np.array(kt_out), np.array(ep_out), np.full(len(kt_out), np.nan), np.full(len(ep_out), np.nan)


def fit_alpha(kt, ep):
    """log10(Ep) = alpha*log10(kT) + c. Return alpha, alpha_err, rho, p, N."""
    if len(kt) < 3:
        return np.nan, np.nan, np.nan, np.nan, len(kt)
    lx, ly = np.log10(kt), np.log10(ep)
    coef, cov = np.polyfit(lx, ly, 1, cov=True)
    alpha = coef[0]
    aerr = float(np.sqrt(cov[0, 0])) if np.all(np.isfinite(cov)) else np.nan
    rho, p = spearmanr(kt, ep)
    return float(alpha), aerr, float(rho), float(p), len(kt)


def classify(alpha):
    if not np.isfinite(alpha): return 'undetermined'
    if alpha < 1.5: return 'baryonic'
    return 'magnetic'


results = {}
all_kt, all_ep = [], []      # combined-sample pooled pairs (his Fig 4)
for gname, (trig, a_pub, ae_pub, jet_pub) in BURGESS.items():
    p = os.path.join(PB, trig, 'spectral_fits.ecsv')
    if not os.path.exists(p):
        results[gname] = {'trigger': trig, 'error': 'no spectral_fits'}
        continue
    t = Table.read(p, format='ascii.ecsv')
    rec = {'trigger': trig, 'alpha_pub': a_pub, 'alpha_pub_err': ae_pub,
           'jet_pub': jet_pub}
    # BB-significant pairs (Burgess-faithful) AND all-valid pairs (diagnostic)
    for tag, req in (('sig', True), ('all', False)):
        kt, ep, _, _ = valid_pairs(t, require_bb_sig=req)
        a, ae, rho, pp, n = fit_alpha(kt, ep)
        rec[tag] = {'alpha': a, 'alpha_err': ae, 'rho': rho, 'p': pp, 'N': n,
                    'jet': classify(a),
                    'jet_match': classify(a) == jet_pub if np.isfinite(a) else None}
    # combined sample uses the BB-significant pairs (Burgess Fig 4 analog)
    kts, eps, _, _ = valid_pairs(t, require_bb_sig=True)
    if len(kts) >= 1:
        all_kt.extend(kts.tolist()); all_ep.extend(eps.tolist())
    results[gname] = rec

# Combined-sample Spearman (Burgess Fig 4: rho=0.81, p=4.35e-20)
all_kt, all_ep = np.array(all_kt), np.array(all_ep)
if len(all_kt) >= 3:
    crho, cp = spearmanr(all_kt, all_ep)
    combined = {'rho': float(crho), 'p': float(cp), 'N': int(len(all_kt)),
                'rho_pub': 0.81, 'p_pub': 4.35e-20}
else:
    combined = {'rho': np.nan, 'p': np.nan, 'N': int(len(all_kt))}

out = {'per_burst': results, 'combined': combined}
json.dump(out, open('/tmp/burgess_repro.json', 'w'), indent=1, default=float)

# ---- readable report ----
L = []
L.append('BURGESS+2014 REPRODUCTION — per-burst Ep-kT, BB-significant blocks '
         f'(LRT>{LRT_BB_MIN}), Ep=nuFnu peak per model')
L.append(f'{"GRB":12s} {"N":>3s} {"our_alpha":>14s} {"pub_alpha":>12s} '
         f'{"our_jet":>9s} {"pub_jet":>9s} {"match":>5s} {"rho":>6s}  [all-valid: N,alpha]')
for g, (trig, a_pub, ae_pub, jet_pub) in BURGESS.items():
    r = results.get(g, {})
    bb = r.get('sig', {}); al = r.get('all', {})
    a, ae, n = bb.get('alpha', np.nan), bb.get('alpha_err', np.nan), bb.get('N', 0)
    our = f'{a:.2f}+/-{ae:.2f}' if np.isfinite(a) else 'n/a'
    mt = ('YES' if bb.get('jet_match') else 'no') if bb.get('jet_match') is not None else '-'
    alstr = f'{al.get("N",0)},{al.get("alpha",float("nan")):.2f}'
    L.append(f'{g:12s} {n:>3d} {our:>14s} {a_pub:.2f}+/-{ae_pub:<4.2f}  '
             f'{bb.get("jet","-"):>9s} {jet_pub:>9s} {mt:>5s} {bb.get("rho",float("nan")):>6.2f}  [{alstr}]')
L.append('')
L.append(f'COMBINED SAMPLE (pooled Band+BB pairs): N={combined["N"]}  '
         f'rho={combined.get("rho",float("nan")):.3f} p={combined.get("p",float("nan")):.2e}  '
         f'|  Burgess: rho=0.81 p=4.35e-20')
open('/tmp/burgess_repro.txt', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))

# ---- figure: per-burst panels ----
fig, axes = plt.subplots(2, 3, figsize=(14, 9))
for ax, (g, (trig, a_pub, ae_pub, jet_pub)) in zip(axes.flat, BURGESS.items()):
    t = Table.read(os.path.join(PB, trig, 'spectral_fits.ecsv'), format='ascii.ecsv')
    kt, ep, kte, epe = valid_pairs(t, require_bb_sig=True)
    r = results[g].get('sig', {})
    if len(kt) >= 1:
        ax.scatter(kt, ep, c='k', s=30, zorder=3)
    if r.get('N', 0) >= 3 and np.isfinite(r.get('alpha', np.nan)):
        xx = np.logspace(np.log10(kt.min()), np.log10(kt.max()), 20)
        lx = np.log10(kt); c = np.polyfit(lx, np.log10(ep), 1)
        ax.plot(xx, 10**(c[1] + c[0]*np.log10(xx)), 'b--',
                label=f'our α={r["alpha"]:.2f}±{r["alpha_err"]:.2f}')
        ax.plot([], [], ' ', label=f'Burgess α={a_pub:.2f}±{ae_pub:.2f}')
        ax.legend(fontsize=8, framealpha=0.9, edgecolor='0.6')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('kT [keV]'); ax.set_ylabel('Ep [keV]')
    ax.set_title(f'{g}  (N={r.get("N",0)})')
    ax.tick_params(direction='in', which='both', top=True, right=True)
    ax.minorticks_on()
fig.suptitle('Burgess+2014 reproduction — per-burst Ep–kT (Band+BB, validity-gated)')
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'fig_burgess_reproduction.png'), dpi=200,
            bbox_inches='tight')
plt.close(fig)
print('\nwrote results/figures/fig_burgess_reproduction.png')
