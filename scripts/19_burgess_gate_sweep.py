#!/usr/bin/env python
"""
Gate sweep: how the recovered Burgess Ep-kT correlation depends on the
BB-detection threshold and the time-binning. For each LRT gate we report,
per binning (PROD vs Burgess-faithful REBLOCK), the combined Spearman rho and
the number of (Ep,kT) pairs. Isolates 'binning fixed' from 'BB-detectability'.
"""
import warnings; warnings.filterwarnings('ignore')
import os
import numpy as np
from astropy.table import Table
from scipy.stats import spearmanr

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = os.path.join(BASE, 'results', 'per_burst')
REBL = os.path.join(BASE, 'results', 'burgess_repro', 'per_burst')

BURG = ['bn081224887', 'bn090719063', 'bn100707032',
        'bn110721200', 'bn110920546', 'bn130427324']
REBLOCK_SRC = {t: REBL for t in BURG}; REBLOCK_SRC['bn130427324'] = PROD

EP = (30, 5000); KT = (1, 200)
GATES = [9.2, 6.0, 4.6, 2.7, 0.0]   # 99%, 95%, 90%, ~84%, none(all-valid)


def cpl_peak(i, xc):
    return (2 + i) * xc if i > -2 else np.nan


def pairs(t, lrt_min):
    rows = t[t['BLOCK'] >= 0]; ko = []; eo = []
    for r in rows:
        c = []
        if bool(r['BANDBB_VALID']):
            l = r['LRT_BANDBB_BAND']; l = l if np.isfinite(l) else -1e9
            kt = float(r['BANDBB_KT']); ep = float(r['BANDBB_EP'])
            rail = (kt <= KT[0]*1.02 or kt >= KT[1]*0.98 or ep <= EP[0]*1.02)
            if (np.isfinite(kt) and np.isfinite(ep) and kt > 0 and ep > 0
                    and not rail and l >= lrt_min):
                c.append((float(r['BANDBB_AIC']), kt, ep))
        if bool(r['CPLBB_VALID']):
            l = r['LRT_CPLBB_CPL']; l = l if np.isfinite(l) else -1e9
            kt = float(r['CPLBB_KT']); idx = float(r['CPLBB_INDEX']); xc = float(r['CPLBB_XC'])
            ep = cpl_peak(idx, xc) if (np.isfinite(idx) and np.isfinite(xc)) else np.nan
            rail = (kt <= KT[0]*1.02 or kt >= KT[1]*0.98)
            if (np.isfinite(kt) and np.isfinite(ep) and kt > 0 and ep > 0
                    and not rail and l >= lrt_min):
                c.append((float(r['CPLBB_AIC']), kt, ep))
        if c:
            c.sort(); ko.append(c[0][1]); eo.append(c[0][2])
    return np.array(ko), np.array(eo)


def load(src, trig):
    p = os.path.join(src, trig, 'spectral_fits.ecsv')
    return Table.read(p, format='ascii.ecsv') if os.path.exists(p) else None

prod_t = {t: load(PROD, t) for t in BURG}
rebl_t = {t: load(REBLOCK_SRC[t], t) for t in BURG}

print(f'{"gate(LRT)":>9s} | {"PROD N":>6s} {"PROD rho":>8s} {"PROD p":>9s} '
      f'| {"REBL N":>6s} {"REBL rho":>8s} {"REBL p":>9s}')
print('-'*64)
for g in GATES:
    pk, pe, rk, re = [], [], [], []
    for t in BURG:
        if prod_t[t] is not None:
            a, b = pairs(prod_t[t], g); pk.extend(a); pe.extend(b)
        if rebl_t[t] is not None:
            a, b = pairs(rebl_t[t], g); rk.extend(a); re.extend(b)
    def sp(k, e):
        k, e = np.array(k), np.array(e)
        if len(k) >= 3:
            r, p = spearmanr(k, e); return len(k), r, p
        return len(k), np.nan, np.nan
    pn, pr, pp = sp(pk, pe); rn, rr, rp = sp(rk, re)
    glab = f'{g:.1f}' if g > 0 else 'none'
    print(f'{glab:>9s} | {pn:>6d} {pr:>8.3f} {pp:>9.1e} '
          f'| {rn:>6d} {rr:>8.3f} {rp:>9.1e}')
print('\nBurgess+2014: rho=0.81, p=4.35e-20 (his Bayesian synchrotron+BB, all bins)')

# per-burst alpha at a moderate gate, REBLOCK
print('\nPer-burst alpha (REBLOCK) at LRT>4.6 (90%) and all-valid:')
print(f'{"trig":13s} {"pubA":>5s} | {"N(4.6)":>6s} {"a(4.6)":>7s} | {"N(all)":>6s} {"a(all)":>7s}')
PUB = {'bn081224887':1.01,'bn090719063':2.33,'bn100707032':1.77,
       'bn110721200':1.24,'bn110920546':1.97,'bn130427324':1.02}
for t in BURG:
    if rebl_t[t] is None:
        continue
    def al(gate):
        k, e = pairs(rebl_t[t], gate)
        if len(k) >= 3:
            return len(k), float(np.polyfit(np.log10(k), np.log10(e), 1)[0])
        return len(k), np.nan
    n46, a46 = al(4.6); na, aa = al(0.0)
    print(f'{t:13s} {PUB[t]:>5.2f} | {n46:>6d} {a46:>7.2f} | {na:>6d} {aa:>7.2f}')
