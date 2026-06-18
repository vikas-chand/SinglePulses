"""
Trustworthy two-break-vs-thermal tally on the vision-background sample.
Applies: (1) physical-validity gate (winning model's *_VALID), (2) decision
rule ΔAIC>=10 over 2nd-best else INCONCLUSIVE, (3) curvature classification
(single-break vs DSBPL two-break vs BB thermal-proxy), (4) DSBPL-vs-SBPL LRT.
Writes a clean report to /tmp/final_tally.txt.
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np
from astropy.table import Table
from collections import Counter

am = Table.read('results/sample_all_models.ecsv', format='ascii.ecsv')
best = Table.read('results/sample_best_per_block.ecsv', format='ascii.ecsv')
N = len(am)

PREFIX = {'Band': 'BAND', 'CPL': 'CPL', 'SBPL': 'SBPL', 'DSBPL': 'DSBPL',
          'Band+BB': 'BANDBB', 'CPL+BB': 'CPLBB'}
SINGLE = ['Band', 'CPL', 'SBPL']
TWOBREAK = ['DSBPL']
THERMAL = ['Band+BB', 'CPL+BB']


def aic(row, name):
    c = f'{PREFIX[name]}_AIC'
    return float(row[c]) if (c in row.colnames and np.isfinite(row[c])) else np.inf


def valid(row, name):
    c = f'{PREFIX[name]}_VALID'
    if c not in row.colnames:
        return np.isfinite(aic(row, name))   # backstop if VALID missing
    v = row[c]
    return bool(v) and np.isfinite(aic(row, name))


out = []
out.append(f'Sample: {N} blocks from {len(set(str(x) for x in am["TRIGGER_NAME"]))} bursts '
           f'(vision backgrounds, NaI+BGO+LLE, validity-gated engine)')
out.append('')

# --- (A) raw winner (lowest AIC, physical-gated by the engine already) ---
raw = Counter(str(m) for m in best['BEST_MODEL'])
out.append('(A) BEST_AIC_MODEL winner tally (engine already physical-gated):')
for k, n in raw.most_common():
    out.append(f'    {k:10s}: {n:4d}  ({100*n/len(best):.0f}%)')
out.append('')

# --- (B) decision-rule winner: require dAIC>=10 over 2nd-best VALID model ---
DEC = 10.0
dec = Counter()
for r in am:
    cand = {nm: aic(r, nm) for nm in PREFIX if valid(r, nm)}
    if not cand:
        dec['NO_VALID_FIT'] += 1; continue
    ordered = sorted(cand.items(), key=lambda x: x[1])
    if len(ordered) == 1 or (ordered[1][1] - ordered[0][1]) >= DEC:
        dec[ordered[0][0]] += 1
    else:
        dec['INCONCLUSIVE'] += 1
out.append(f'(B) Decision-rule winner (dAIC>={DEC:.0f} over 2nd-best VALID model, else INCONCLUSIVE):')
for k, n in dec.most_common():
    out.append(f'    {k:14s}: {n:4d}  ({100*n/N:.0f}%)')
out.append('')

# --- (C) curvature analysis: is curvature beyond a single break required, and
#         is it a 2SBPL break or a thermal bump (the central degeneracy) ---
THR = 6.0
n_curv = n_degen = n_2b = n_th = 0
strong2b = []
for r in am:
    s = min([aic(r, n) for n in SINGLE if valid(r, n)] or [np.inf])
    tb = min([aic(r, n) for n in TWOBREAK if valid(r, n)] or [np.inf])
    th = min([aic(r, n) for n in THERMAL if valid(r, n)] or [np.inf])
    curv = min(tb, th)
    if not (np.isfinite(curv) and np.isfinite(s)):
        continue
    if s - curv > THR:                     # curvature required
        n_curv += 1
        d = tb - th
        if abs(d) < 4:   n_degen += 1
        elif d < 0:      n_2b += 1; strong2b.append((str(r['TRIGGER_NAME']), int(r['BLOCK']), s-curv, -d))
        else:            n_th += 1
out.append(f'(C) Curvature beyond a single break (dAIC>{THR:.0f} vs best single, VALID only): {n_curv} blocks')
out.append(f'    of those:  thermal-proxy preferred: {n_th}   DEGENERATE(2brk~thermal): {n_degen}   two-break preferred: {n_2b}')
out.append('')

# --- (D) DSBPL-vs-SBPL nested LRT (the project central comparison) ---
if 'LRT_DSBPL_SBPL' in am.colnames:
    lrt = np.asarray(am['LRT_DSBPL_SBPL'], dtype=float)
    dval = np.asarray(am['DSBPL_VALID'], dtype=bool) if 'DSBPL_VALID' in am.colnames else np.isfinite(lrt)
    fin = np.isfinite(lrt) & dval
    # Wilks 2 dof: >9.2 = 99%, >13.8 = 3sigma-ish
    out.append('(D) DSBPL-vs-SBPL nested LRT (2 extra params; VALID DSBPL only):')
    out.append(f'    blocks with finite valid LRT: {fin.sum()}')
    out.append(f'    LRT>9.2  (99%):   {(lrt[fin]>9.2).sum()}')
    out.append(f'    LRT>13.8 (~3sig): {(lrt[fin]>13.8).sum()}')
out.append('')

# --- (E) strongest genuine two-break detections ---
out.append('(E) Strongest VALID two-break-preferred blocks (dAIC over best single | over thermal):')
for trg, blk, dc, dth in sorted(strong2b, key=lambda x: -x[2])[:12]:
    out.append(f'    {trg:14s} blk{blk:>3d}  dAIC_vs_single={dc:6.1f}  dAIC_vs_thermal={dth:6.1f}')

open('/tmp/final_tally.txt', 'w').write('\n'.join(out) + '\n')
print('done -> /tmp/final_tally.txt')
