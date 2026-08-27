#!/usr/bin/env python3
"""Preference vs best-AIC (PI ruling 2026-08-26): a model is TRACKED in a
burst when it wins >=1 bin with margin dAIC>6 over the runner-up (>=2 bins =
strict tier). Reads stored AICs only; never refits."""
import os, glob, json
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows=[]
for fam in sorted(glob.glob(f'{ROOT}/results/campaign20_fam/*_highe/spectral_fits.ecsv')):
    trig = os.path.basename(os.path.dirname(fam)).replace('_highe','')
    prom = f'{ROOT}/results/convention_check/{trig}/spectral_fits.ecsv'
    src = prom if os.path.exists(prom) else fam
    t = Table.read(src)
    models = sorted({c[:-4] for c in t.colnames if c.endswith('_AIC')})
    stats={m:{'w':0,'w6':0,'w10':0,'bins6':[],'best_margin':0.0} for m in models}
    for r in t:
        blk = int(r['BLOCK'])
        aics = {m: float(r[f'{m}_AIC']) for m in models if np.isfinite(r[f'{m}_AIC'])}
        if len(aics) < 2: continue
        order = sorted(aics, key=aics.get)
        win, run = order[0], order[1]
        margin = aics[run]-aics[win]
        s=stats[win]; s['w']+=1
        s['best_margin']=max(s['best_margin'], margin)
        if margin>6 and blk!=-1: s['w6']+=1; s['bins6'].append(blk)
        if margin>10 and blk!=-1: s['w10']+=1
    for m,s in stats.items():
        if s['w']==0: continue
        rows.append(dict(TRIGGER=trig, MODEL=m, BINS_WON=s['w'],
            BINS_MARGIN6=s['w6'], BINS_MARGIN10=s['w10'],
            BEST_MARGIN=round(s['best_margin'],2),
            TRACKED=s['w6']>=1, TRACKED_STRICT=s['w6']>=2,
            BINS6=','.join(map(str,s['bins6'])) or '-',
            SRC=('promoted' if src==prom else 'fam')))
out=Table(rows=rows)
out.write(f'{ROOT}/results/campaign/model_preference.ecsv', format='ascii.ecsv', overwrite=True)
tr=out[out['TRACKED']]; st=out[out['TRACKED_STRICT']]
print(f'{len(set(out["TRIGGER"]))} bursts, {len(out)} burst-model argmin rows')
print(f'TRACKED (>=1 bin margin>6): {len(tr)} burst-model tracks in {len(set(tr["TRIGGER"]))} bursts')
print(f'TRACKED_STRICT (>=2 bins):  {len(st)} tracks in {len(set(st["TRIGGER"]))} bursts')
import collections
print('\nmost-tracked models (>=1-bin tier):')
for m,c in collections.Counter(tr['MODEL']).most_common(12): print(f'  {m:12} {c} bursts')
