#!/usr/bin/env python
"""
Combine per-burst spectral_fits.ecsv files into sample-level outputs.

Reads:  results/per_burst/<trigger>/spectral_fits.ecsv  (per-burst, 151 cols)
Writes (under results/):
  sample_all_models.ecsv      — every model's params kept (long-form, 152 cols)
                                One row per (trigger, block).
  sample_best_per_block.ecsv  — winning model only per (trigger, block),
                                with canonical names (alpha, Ep, beta, kT, ...).
                                Selection by lowest AIC across OK fits.

Quality filters available on best_per_block:
  --require-minos      drop rows where the winning model's MINOS failed
  --drop-railed FRAC   drop rows where any winning param is within FRAC of a bound
                       (default off; pass e.g. 0.01 for Burgess-style 1% filter)

Usage:
  python 12_combine_sample_results.py
  python 12_combine_sample_results.py --require-minos --drop-railed 0.01
"""
import os, glob, argparse
import numpy as np
from astropy.table import Table, vstack

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(BASE, 'results')
PER_BURST = os.path.join(RESULTS, 'per_burst')

# Map BEST_AIC_MODEL string → (prefix, canonical_param_map)
# canonical_param_map: {canonical_col_name: source_col_suffix_in_ECSV}
MODEL_CANONICAL = {
    'Band': ('BAND', {
        'ALPHA': 'ALPHA', 'EP': 'EP', 'BETA': 'BETA', 'K': 'K',
    }),
    'CPL': ('CPL', {
        'INDEX': 'INDEX', 'EC': 'XC', 'K': 'K',
    }),
    'SBPL': ('SBPL', {
        'ALPHA': 'ALPHA', 'EBREAK': 'EBREAK', 'BETA': 'BETA', 'K': 'K',
    }),
    'DSBPL': ('DSBPL', {
        'ALPHA1': 'ALPHA1', 'XB': 'XB', 'ALPHA2': 'ALPHA2',
        'XP': 'XP', 'BETA': 'BETA', 'K': 'K',
    }),
    'Band+BB': ('BANDBB', {
        'ALPHA': 'ALPHA', 'EP': 'EP', 'BETA': 'BETA', 'K_BAND': 'K_BAND',
        'KT': 'KT', 'K_BB': 'K_BB',
    }),
    'CPL+BB': ('CPLBB', {
        'INDEX': 'INDEX', 'EC': 'XC', 'K_CPL': 'K_CPL',
        'KT': 'KT', 'K_BB': 'K_BB',
    }),
}


def load_per_burst():
    """Glob all per-burst spectral_fits.ecsv, return list of (trigger, Table)."""
    paths = sorted(glob.glob(os.path.join(PER_BURST, '*', 'spectral_fits.ecsv')))
    out = []
    for p in paths:
        trigger = os.path.basename(os.path.dirname(p))
        try:
            t = Table.read(p, format='ascii.ecsv')
            t['TRIGGER_NAME'] = trigger
            out.append((trigger, t))
        except Exception as exc:
            print(f'  skip {trigger}: read failed ({exc})')
    return out


def combine_all_models(per_burst):
    """Long-form: stack all per-burst tables; missing cols filled with NaN."""
    tabs = [t for _, t in per_burst]
    if not tabs:
        return Table()
    stacked = vstack(tabs, join_type='outer', metadata_conflicts='silent')
    # Move TRIGGER_NAME to front
    cols = ['TRIGGER_NAME'] + [c for c in stacked.colnames if c != 'TRIGGER_NAME']
    return stacked[cols]


def _winning_row(row, model_name):
    """Extract canonical params from `row` for the winning `model_name`."""
    if model_name not in MODEL_CANONICAL:
        return None
    prefix, pmap = MODEL_CANONICAL[model_name]
    status = row.get(f'{prefix}_STATUS', 'NA')
    if status != 'OK':
        return None
    out = {
        'BEST_MODEL': model_name,
        'BEST_PREFIX': prefix,
        'N2LL': float(row.get(f'{prefix}_N2LL', np.nan)),
        'AIC': float(row.get(f'{prefix}_AIC', np.nan)),
        'BIC': float(row.get(f'{prefix}_BIC', np.nan)),
        'MINOS_OK': bool(row.get(f'{prefix}_MINOS_OK', False)),
    }
    for canon, src in pmap.items():
        for suf in ('', '_ERR', '_NEG_ERR', '_POS_ERR'):
            src_col = f'{prefix}_{src}{suf}'
            out_col = f'{canon}{suf}'
            v = row.get(src_col, np.nan)
            try:
                out[out_col] = float(v)
            except (TypeError, ValueError):
                out[out_col] = np.nan
    return out


def _row_get(row, key, default=np.nan):
    """Safe Table-row .get equivalent."""
    if key in row.colnames:
        v = row[key]
        # Treat masked as NaN
        if hasattr(v, 'mask') and bool(v.mask):
            return default
        return v
    return default


def build_best_per_block(per_burst, require_minos=False, drop_railed=None):
    """Pick BEST_AIC_MODEL's params per row; emit canonical-name table."""
    rows = []
    for trigger, t in per_burst:
        for r in t:
            best = _row_get(r, 'BEST_AIC_MODEL', 'INCONCLUSIVE')
            row_dict = {k: _row_get(r, k) for k in r.colnames}
            winning = _winning_row(row_dict, str(best).strip())
            if winning is None:
                continue
            if require_minos and not winning['MINOS_OK']:
                continue
            # Compose output row
            out = {
                'TRIGGER_NAME': trigger,
                'BLOCK': int(_row_get(r, 'BLOCK', -99)),
                'T_START': float(_row_get(r, 'T_START', np.nan)),
                'T_STOP': float(_row_get(r, 'T_STOP', np.nan)),
                'T_MID': float(_row_get(r, 'T_MID', np.nan)),
                'N_DETS': int(_row_get(r, 'N_DETS', 0)),
                **winning,
                # Companion model cross-check
                'BEST_BIC_MODEL': str(_row_get(r, 'BEST_BIC_MODEL', '')),
                'LRT_BANDBB_BAND': float(_row_get(r, 'LRT_BANDBB_BAND', np.nan)),
                'LRT_CPLBB_CPL':   float(_row_get(r, 'LRT_CPLBB_CPL', np.nan)),
            }
            rows.append(out)

    if not rows:
        return Table()

    keys = list(rows[0].keys())
    # Make sure every row has all keys
    for r in rows:
        for k in keys:
            r.setdefault(k, np.nan)
        for k in r:
            if k not in keys:
                keys.append(k)
    tab = Table(rows=[[r.get(k, np.nan) for k in keys] for r in rows],
                names=keys)

    if drop_railed is not None and drop_railed > 0:
        tab = _filter_railed(tab, frac=drop_railed)
    return tab


def _filter_railed(tab, frac=0.01):
    """Drop rows where a key winning param is within `frac` of a model bound.
    Conservative; only checks the canonical params (alpha, Ep, beta, kT, index, xc).
    Bounds from script 10 setup functions.
    """
    BOUNDS = {
        'ALPHA':  (-1.9, 1.9),
        'EP':     (30.0, 5000.0),
        'BETA':   (-5.0, -1.6),
        'INDEX':  (-2.0, 1.0),
        'EC':     (10.0, 5e4),
        'EBREAK': (10.0, 5000.0),
        'XP':     (10.0, 5000.0),
        'XB':     (5.0, 1000.0),
        'KT':     (1.0, 200.0),
    }
    keep = np.ones(len(tab), dtype=bool)
    for col, (lo, hi) in BOUNDS.items():
        if col not in tab.colnames:
            continue
        v = np.asarray(tab[col], dtype=float)
        span = hi - lo
        railed = ((v - lo) < frac * span) | ((hi - v) < frac * span)
        finite = np.isfinite(v)
        keep &= ~(railed & finite)
    n_drop = (~keep).sum()
    if n_drop:
        print(f'  filtered {n_drop} rows for railed params (frac={frac})')
    return tab[keep]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--require-minos', action='store_true',
                   help='Drop best-per-block rows where winning model MINOS failed')
    p.add_argument('--drop-railed', type=float, default=None,
                   help='Drop best-per-block rows where any param is within FRAC '
                        'of a bound (e.g. 0.01 = 1%%)')
    args = p.parse_args()

    per_burst = load_per_burst()
    print(f'Loaded {len(per_burst)} per-burst tables '
          f'({sum(len(t) for _,t in per_burst)} total fit rows)')

    all_path = os.path.join(RESULTS, 'sample_all_models.ecsv')
    all_models = combine_all_models(per_burst)
    if len(all_models):
        all_models.write(all_path, format='ascii.ecsv', overwrite=True)
        print(f'  wrote {all_path}  ({len(all_models)} rows × {len(all_models.colnames)} cols)')

    best_path = os.path.join(RESULTS, 'sample_best_per_block.ecsv')
    best = build_best_per_block(per_burst,
                                require_minos=args.require_minos,
                                drop_railed=args.drop_railed)
    if len(best):
        best.write(best_path, format='ascii.ecsv', overwrite=True)
        print(f'  wrote {best_path}  ({len(best)} rows × {len(best.colnames)} cols)')

        # Winner tally
        from collections import Counter
        c = Counter(str(m) for m in best['BEST_MODEL'])
        print('\nWinner tally (lowest AIC across all models):')
        for k, n in c.most_common():
            print(f'  {k:10s}: {n}')


if __name__ == '__main__':
    main()
