"""Quick characterization of DSBPL (two-break) wins in the combined sample."""
import warnings; warnings.filterwarnings('ignore')
import numpy as np
from astropy.table import Table

am = Table.read('results/sample_all_models.ecsv', format='ascii.ecsv')
t  = Table.read('results/sample_best_per_block.ecsv', format='ascii.ecsv')

ds = t[[str(m) == 'DSBPL' for m in t['BEST_MODEL']]]
strong = marg = weak = 0
rows = []
for r in ds:
    trg, blk = r['TRIGGER_NAME'], int(r['BLOCK'])
    m = am[(am['TRIGGER_NAME'] == trg) & (am['BLOCK'] == blk)]
    if len(m) == 0:
        continue
    m = m[0]
    dsa = float(m['DSBPL_AIC'])
    onebr = [float(m[c]) for c in ['BAND_AIC', 'CPL_AIC', 'SBPL_AIC']
             if np.isfinite(m[c])]
    if not onebr:
        continue
    d = min(onebr) - dsa            # positive => DSBPL preferred
    strong += d > 10
    marg   += 4 < d <= 10
    weak   += d <= 4
    rows.append((trg, blk, dsa, min(onebr), d,
                 float(m['DSBPL_XB']) if 'DSBPL_XB' in m.colnames else np.nan,
                 float(m['DSBPL_XP']) if 'DSBPL_XP' in m.colnames else np.nan))

print(f"DSBPL wins: {len(ds)}/{len(t)} blocks ({100*len(ds)/len(t):.0f}%), "
      f"{len(set(ds['TRIGGER_NAME']))} bursts")
print(f"  strong  (dAIC>10): {strong}")
print(f"  marginal(4-10):    {marg}")
print(f"  weak    (<4):      {weak}")
print()
print("Top two-break detections (dAIC over best single-break):")
print(f"  {'TRIGGER':14s} {'BLK':>3s} {'dAIC':>6s} {'E_b1[keV]':>9s} {'E_b2/Ep':>9s}")
for trg, blk, dsa, b1, d, xb, xp in sorted(rows, key=lambda x: -x[4])[:12]:
    print(f"  {trg:14s} {blk:>3d} {d:>6.1f} {xb:>9.1f} {xp:>9.1f}")
