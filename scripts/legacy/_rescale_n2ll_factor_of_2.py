"""
One-time fix for the factor-of-2 bug in older spectral_fits.ecsv files.

Pre-2026-05-24: script 10 stored n2ll = jl.current_minimum (which is -log L).
Standard convention: -2 log L. So all N2LL, AIC, BIC, and LRT columns
were off by exactly a factor of 2 in the likelihood term.

This script reads each per-burst spectral_fits.ecsv, applies the correction
in place (writes a .pre_n2ll_fix.bak backup), and writes back. After this,
the columns match the -2 log L convention and Wilks Δχ² thresholds apply.

Per-model prefixes processed: BAND, CPL, SBPL, DSBPL, BANDBB, CPLBB.
Conversion (per model prefix P):
    new_P_N2LL = 2 * old_P_N2LL
    new_P_AIC  = old_P_AIC + old_P_N2LL     # = 2·N2LL + 2k
    new_P_BIC  = old_P_BIC + old_P_N2LL     # = 2·N2LL + k·ln(N)
    new_LRT_BANDBB_BAND = 2 * old_LRT_BANDBB_BAND
    new_LRT_CPLBB_CPL   = 2 * old_LRT_CPLBB_CPL
BEST_AIC_MODEL / BEST_BIC_MODEL unchanged (argmin invariant under ×2 rescale).

A metadata flag `N2LL_CONVENTION = '-2logL'` is added to the ECSV header.
Idempotent: refuses to rescale if the flag is already present.

Usage:
    python _rescale_n2ll_factor_of_2.py            # rescale all 84
    python _rescale_n2ll_factor_of_2.py --dry-run  # show what would change
"""
import os, glob, shutil, argparse
import numpy as np
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PER_BURST = os.path.join(BASE, 'results', 'per_burst')

PREFIXES = ['BAND', 'CPL', 'SBPL', 'DSBPL', 'BANDBB', 'CPLBB']
LRT_COLS = ['LRT_BANDBB_BAND', 'LRT_CPLBB_CPL']


def rescale_table(t):
    if t.meta.get('N2LL_CONVENTION') == '-2logL':
        return False, 'already rescaled'

    # Per-model rescale
    for p in PREFIXES:
        n2ll_col = f'{p}_N2LL'
        aic_col  = f'{p}_AIC'
        bic_col  = f'{p}_BIC'
        if n2ll_col not in t.colnames:
            continue
        old_n2ll = np.asarray(t[n2ll_col], dtype=float).copy()
        if aic_col in t.colnames:
            old_aic = np.asarray(t[aic_col], dtype=float)
            t[aic_col] = old_aic + old_n2ll   # = 2·N2LL_old + 2k
        if bic_col in t.colnames:
            old_bic = np.asarray(t[bic_col], dtype=float)
            t[bic_col] = old_bic + old_n2ll   # = 2·N2LL_old + k·ln(N)
        t[n2ll_col] = 2.0 * old_n2ll

    # LRTs
    for c in LRT_COLS:
        if c in t.colnames:
            t[c] = 2.0 * np.asarray(t[c], dtype=float)

    t.meta['N2LL_CONVENTION'] = '-2logL'
    t.meta['N2LL_FIX_APPLIED'] = '2026-05-24 rescale_n2ll_factor_of_2'
    return True, 'rescaled'


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    paths = sorted(glob.glob(os.path.join(PER_BURST, '*', 'spectral_fits.ecsv')))
    print(f'Found {len(paths)} per-burst spectral_fits.ecsv files')

    n_rescaled = n_skip = 0
    for path in paths:
        trigger = os.path.basename(os.path.dirname(path))
        try:
            t = Table.read(path, format='ascii.ecsv')
            changed, msg = rescale_table(t)
            if not changed:
                n_skip += 1
                print(f'  {trigger}: skip ({msg})')
                continue
            if args.dry_run:
                print(f'  {trigger}: would rescale (sample N2LL '
                      f'{t["BAND_N2LL"][0]:.1f} after ×2 = {2*t["BAND_N2LL"][0]/2:.1f})')
                n_rescaled += 1
                continue
            bak = path + '.pre_n2ll_fix.bak'
            if not os.path.exists(bak):
                shutil.copy2(path, bak)
            t.write(path, format='ascii.ecsv', overwrite=True)
            n_rescaled += 1
            print(f'  {trigger}: rescaled, bak={os.path.basename(bak)}')
        except Exception as exc:
            print(f'  {trigger}: ERROR {type(exc).__name__}: {exc}')
            n_skip += 1

    action = 'would rescale' if args.dry_run else 'rescaled'
    print(f'\nDone. {action} {n_rescaled}, skipped {n_skip}.')


if __name__ == '__main__':
    main()
