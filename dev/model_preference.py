#!/usr/bin/env python3
"""Preference vs best-AIC (PI ruling 2026-08-26): a model is TRACKED in a
burst when it wins >=1 bin with margin dAIC>6 over the RUNNER-UP (>=2 bins =
strict tier). Reads stored AICs only; never refits.

NR-26 GATE-BEFORE-ARGMIN (fixed 2026-08-30, first fresh session): the argmin
runs ONLY over models the engine marked valid (<M>_VALID true and <M>_STATUS
not FAIL/ERROR) -- the same gate behind the engine's BEST_AIC_MODEL column,
which this tool cross-checks row by row; a burst whose gated winner disagrees
with the engine's column is NOT written (loud refusal, exit 3). Figure-name ->
column-prefix mapping is read from the ENGINE spec tables in scripts/10 via
ast (NR-10 name-canon authority) -- never a regex canon.

PI ruling 2026-08-30 (verbatim): 'dAIC reference: BOTH constructs stay, with
mandatory labels -- "DECISIVE" = chain-gate vs best simpler ancestor (structure
claims, dAIC>=10); "TRACKED" = vs runner-up (preference, dAIC>6 in 1-2 bins).
Never print either word without its reference.'  This tool computes the
TRACKED construct ONLY. It does not compute DECISIVE.

  model_preference.py                # all bursts -> results/campaign/model_preference.ecsv
  model_preference.py --trig bnXXX   # one burst  -> results/campaign/model_preference_bnXXX.ecsv
                                     #   (the no-sweep ruling: per-burst use never rewrites the campaign file)
"""
import os, sys, ast, glob, argparse, datetime, subprocess, collections
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, 'scripts', '10_spectral_fit_burst.py')
MARGIN_REFERENCE = ('runner-up = TRACKED construct (PI 2026-08-26, 2026-08-30); '
                    'NOT the DECISIVE chain-gate margin vs best simpler ancestor')
VALIDITY_GATE = 'engine <M>_VALID true and <M>_STATUS not FAIL/ERROR (NR-26); cross-checked vs BEST_AIC_MODEL'


def engine_name_map():
    """{figure name -> column prefix} from every spec dict in scripts/10 (NR-10)."""
    tree = ast.parse(open(ENGINE).read(), ENGINE)
    m = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        d = {}
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
                    and k.value in ('name', 'prefix') and isinstance(v.value, str)):
                d[k.value] = v.value
        if 'name' in d and 'prefix' in d:
            m[d['name']] = d['prefix']
    if not m:
        sys.exit('ERROR: no name/prefix spec pairs found in scripts/10')
    return m


def model_valid(row, m, cols):
    a = row[f'{m}_AIC']
    if a is None or not np.isfinite(a):
        return False
    if f'{m}_VALID' in cols and not bool(row[f'{m}_VALID']):
        return False
    if f'{m}_STATUS' in cols and str(row[f'{m}_STATUS']).upper() in ('FAIL', 'ERROR'):
        return False
    return True


def preference(trig, src, name2prefix):
    t = Table.read(src)
    cols = t.colnames
    models = sorted({c[:-4] for c in cols if c.endswith('_AIC')})
    stats = {m: {'w': 0, 'w6': 0, 'w10': 0, 'bins6': [], 'best_margin': 0.0} for m in models}
    mismatches = []
    for r in t:
        blk = int(r['BLOCK'])
        aics = {m: float(r[f'{m}_AIC']) for m in models if model_valid(r, m, cols)}
        if len(aics) < 2:
            continue
        order = sorted(aics, key=aics.get)
        win, run = order[0], order[1]
        if 'BEST_AIC_MODEL' in cols:
            eng = name2prefix.get(str(r['BEST_AIC_MODEL']), f'?{r["BEST_AIC_MODEL"]}')
            if eng != win:
                mismatches.append((blk, str(r['BEST_AIC_MODEL']), win))
        margin = aics[run] - aics[win]
        s = stats[win]; s['w'] += 1
        s['best_margin'] = max(s['best_margin'], margin)
        if margin > 6 and blk != -1: s['w6'] += 1; s['bins6'].append(blk)
        if margin > 10 and blk != -1: s['w10'] += 1
    rows = []
    for m, s in stats.items():
        if s['w'] == 0:
            continue
        rows.append(dict(TRIGGER=trig, MODEL=m, BINS_WON=s['w'],
                         BINS_MARGIN6=s['w6'], BINS_MARGIN10=s['w10'],
                         BEST_MARGIN=round(s['best_margin'], 2),
                         TRACKED=s['w6'] >= 1, TRACKED_STRICT=s['w6'] >= 2,
                         BINS6=','.join(map(str, s['bins6'])) or '-',
                         MARGIN_REF='runner-up', VALIDITY_GATE='engine VALID+STATUS'))
    return rows, mismatches


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--trig', help='one burst only -> results/campaign/model_preference_<trig>.ecsv')
    a = ap.parse_args()
    name2prefix = engine_name_map()
    rows, bad, srcs = [], {}, {}
    for fam in sorted(glob.glob(f'{ROOT}/results/campaign20_fam/*_highe/spectral_fits.ecsv')):
        trig = os.path.basename(os.path.dirname(fam)).replace('_highe', '')
        if a.trig and trig != a.trig:
            continue
        prom = f'{ROOT}/results/convention_check/{trig}/spectral_fits.ecsv'
        src = prom if os.path.exists(prom) else fam
        rr, mm = preference(trig, src, name2prefix)
        if mm:                       # gate != engine: refuse to write this burst (NR-26)
            bad[trig] = mm
            continue
        for r in rr:
            r['SRC'] = 'promoted' if src == prom else 'fam'
        rows += rr
        srcs[trig] = os.path.relpath(src, ROOT)
    if not rows:
        for t_, mm in bad.items():
            print(f'!! {t_}: gated winner != engine BEST_AIC_MODEL in {mm}')
        sys.exit(f'ERROR: nothing written ({"no table for " + a.trig if a.trig and a.trig not in bad else "all bursts refused"})')
    out = Table(rows=rows)
    try:
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    except Exception:
        head = 'unknown'
    out.meta.update(MARGIN_REFERENCE=MARGIN_REFERENCE, VALIDITY_GATE=VALIDITY_GATE,
                    NR26='gate-before-argmin applied 2026-08-30',
                    argv=sys.argv, git_head=head,
                    generated_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    sources=srcs)
    dest = f'{ROOT}/results/campaign/model_preference' + (f'_{a.trig}' if a.trig else '') + '.ecsv'
    out.write(dest, format='ascii.ecsv', overwrite=True)
    tr = out[out['TRACKED']]; st = out[out['TRACKED_STRICT']]
    print(f'WROTE {os.path.relpath(dest, ROOT)}')
    print(f'{len(set(out["TRIGGER"]))} bursts, {len(out)} burst-model gated-argmin rows  [margin ref: runner-up; gate: {VALIDITY_GATE}]')
    print(f'TRACKED (>=1 bin margin>6 vs runner-up): {len(tr)} burst-model tracks in {len(set(tr["TRIGGER"]))} bursts')
    print(f'TRACKED_STRICT (>=2 bins):               {len(st)} tracks in {len(set(st["TRIGGER"]))} bursts')
    print('\nmost-tracked models (>=1-bin tier):')
    for m, c in collections.Counter(tr['MODEL']).most_common(12):
        print(f'  {m:12} {c} bursts')
    if bad:
        print('\n!! GATE MISMATCH vs engine BEST_AIC_MODEL -- rows NOT written for:')
        for t_, mm in bad.items():
            print(f'  {t_}: {mm}')
        sys.exit(3)
