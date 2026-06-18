"""
Two-break vs thermal-proxy degeneracy analysis (the central Two_Breaks question).

Physics: the low-energy break of a 2SBPL (synchrotron cooling break) produces
spectral curvature that a blackbody bump on a single-break SBPL/CPL can mimic.
So {DSBPL} and {Band+BB, CPL+BB} are alternative descriptions of the SAME
"curvature beyond a single break". Single-break models {Band, CPL, SBPL} lack it.

This script:
  1. Regroups winners into  SINGLE-BREAK  vs  CURVATURE  classes.
  2. For each block, computes best-AIC within each class.
  3. Flags blocks where curvature is *required* (curvature class beats single
     by ΔAIC>thr) and, among those, whether the two-break and thermal-proxy
     interpretations are DEGENERATE (|AIC_2break - AIC_thermal| < 4) or whether
     one is clearly preferred.
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np
from astropy.table import Table

am = Table.read('results/sample_all_models.ecsv', format='ascii.ecsv')

SINGLE  = {'Band': 'BAND', 'CPL': 'CPL', 'SBPL': 'SBPL'}
TWOBREAK = {'DSBPL': 'DSBPL'}                       # genuine second break
THERMAL  = {'Band+BB': 'BANDBB', 'CPL+BB': 'CPLBB'} # BB proxy for the break


def aic(row, prefix):
    c = f'{prefix}_AIC'
    if c in row.colnames and np.isfinite(row[c]):
        return float(row[c])
    return np.inf


def best_of(row, group):
    vals = {name: aic(row, pre) for name, pre in group.items()}
    name = min(vals, key=vals.get)
    return name, vals[name]


n_total = 0
n_curv_required = 0          # curvature class beats single by >THR
n_degenerate = 0            # within this, 2break ~ thermal (|dAIC|<4)
n_twobreak_pref = 0         # 2break clearly better than thermal proxy
n_thermal_pref = 0          # thermal proxy clearly better than 2break
THR = 6.0                    # AIC threshold for "required"
rows_curv = []

for r in am:
    n_total += 1
    s_name, s_aic = best_of(r, SINGLE)
    tb_name, tb_aic = best_of(r, TWOBREAK)
    th_name, th_aic = best_of(r, THERMAL)
    curv_aic = min(tb_aic, th_aic)
    if not np.isfinite(curv_aic) or not np.isfinite(s_aic):
        continue
    if (s_aic - curv_aic) > THR:        # curvature required
        n_curv_required += 1
        d = tb_aic - th_aic             # +ve => thermal better; -ve => 2break better
        if abs(d) < 4:
            verdict = 'DEGENERATE'
            n_degenerate += 1
        elif d < 0:
            verdict = '2break>thermal'
            n_twobreak_pref += 1
        else:
            verdict = 'thermal>2break'
            n_thermal_pref += 1
        rows_curv.append((str(r['TRIGGER_NAME']), int(r['BLOCK']),
                          s_aic - curv_aic, tb_aic, th_aic, d, verdict))

print(f"Total fit blocks:                 {n_total}")
print(f"Curvature REQUIRED (ΔAIC>{THR:.0f} vs single-break): {n_curv_required} "
      f"({100*n_curv_required/n_total:.0f}%)")
print()
print("Within the curvature-required blocks, which interpretation wins?")
print(f"  DEGENERATE (2break ≈ thermal, |ΔAIC|<4): {n_degenerate}"
      f"   ← the core Two_Breaks ambiguity")
print(f"  two-break clearly preferred:             {n_twobreak_pref}")
print(f"  thermal-proxy clearly preferred:         {n_thermal_pref}")
print()
print("Strongest curvature blocks (sorted by ΔAIC over single-break):")
print(f"  {'TRIGGER':14s} {'BLK':>3s} {'dAIC_curv':>9s} "
      f"{'2brk_AIC':>9s} {'therm_AIC':>9s} {'verdict':>14s}")
for trg, blk, dcurv, tbA, thA, d, v in sorted(rows_curv, key=lambda x: -x[2])[:20]:
    print(f"  {trg:14s} {blk:>3d} {dcurv:>9.1f} {tbA:>9.1f} {thA:>9.1f} {v:>14s}")
