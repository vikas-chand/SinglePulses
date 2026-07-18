#!/usr/bin/env python
"""
Phase 0b: full-sample re-fit driver. For every burst with a Bayesian-block ECSV,
run scripts/10 with an EXPLICIT background catalogue + block dir + out-root:
  --blocks-file <blocks-dir>/bb_blocks_spectral_<trig>.ecsv
  --bkg-file    <bkg-file>          (REQUIRED; the authoritative bkg catalogue)
  --out-dir     <out-root>/<trig>
  --include-bgo (NaI+BGO+LLE; BB + DSBPL multi-start are built into scripts/10)

The background file and out-root are CLI arguments, NOT hardcoded: the
human-reviewed catalogue (results/background_intervals.ecsv) drives the
AUTHORITATIVE run to a FRESH out-root, e.g.
  python scripts/29_refit_clean.py \\
      --bkg-file results/background_intervals.ecsv \\
      --out-root results/clean_per_burst_human

Resumable (skips bursts whose spectral_fits.ecsv exists); the subprocess return
code is checked (a nonzero exit -> FAIL, not a silent skip). Interpreter + Fermi
paths come from the environment (sys.executable / FERMI_DIR) so it is portable.
"""
import os, glob, sys, time, argparse, subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, 'scripts'); RES = os.path.join(BASE, 'results')
S10 = os.path.join(SCRIPTS, '10_spectral_fit_burst.py')
DEF_BLK = os.path.join(RES, 'clean_blocks')
DEF_OUT = os.path.join(RES, 'clean_per_burst')

# Portable interpreter + Fermi/CALDB env: prefer this process's own interpreter
# (which IS the threeML env when launched from it) and FERMI_DIR from the env.
PY = os.environ.get('THREEML_PY', sys.executable)
_FD = os.environ.get('FERMI_DIR',
                     '/Users/salim/anaconda3/envs/threeML/share/fermitools')
ENV = {**os.environ, 'PYTHONUNBUFFERED': '1', 'MPLBACKEND': 'Agg',
       'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'FERMI_DIR': _FD,
       'CALDB': _FD + '/data/caldb',
       'CALDBALIAS': _FD + '/data/caldb/software/tools/alias_config.fits',
       'CALDBCONFIG': _FD + '/data/caldb/software/tools/caldb.config',
       'CALDBROOT': _FD + '/data/caldb', 'EXTFILESSYS': _FD + '/refdata/fermi'}


def run(trig, bkg_file, blk_dir, out_root, timeout, extra=()):
    out = os.path.join(out_root, trig); os.makedirs(out, exist_ok=True)
    done = os.path.join(out, 'spectral_fits.ecsv')
    if os.path.exists(done):
        return (trig, 'skip', 0)
    blk = os.path.join(blk_dir, f'bb_blocks_spectral_{trig}.ecsv')
    log = os.path.join(out, 'refit.log')
    cmd = [PY, S10, '--trigger', trig, '--include-bgo', '--no-log',
           '--blocks-file', blk, '--bkg-file', bkg_file, '--out-dir', out]
    cmd += list(extra)                     # --models/--include-lat pass-through
    t0 = time.time()
    try:
        with open(log, 'w') as lf:
            cp = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT,
                                env=ENV, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return (trig, 'TIMEOUT', time.time() - t0)
    # Check BOTH the return code AND the expected output (M5: no silent failures).
    if cp.returncode != 0:
        return (trig, f'FAIL(rc={cp.returncode})', time.time() - t0)
    if not os.path.exists(done):
        return (trig, 'FAIL(no-output)', time.time() - t0)
    return (trig, 'ok', time.time() - t0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    # H2 (finished 2026-07-16): REQUIRED, no silent default — the old default was the
    # PROVISIONAL background_intervals_clean.ecsv, an easy way to silently fit the
    # wrong catalog. State the catalog explicitly every run.
    ap.add_argument('--bkg-file', required=True,
                    help='background-intervals ECSV (authoritative run: the '
                         'approved results/background_intervals.ecsv)')
    ap.add_argument('--blocks-dir', default=DEF_BLK, help='dir of bb_blocks_spectral_*.ecsv')
    ap.add_argument('--out-root', default=DEF_OUT, help='per-burst output root (use a FRESH dir for the authoritative run)')
    ap.add_argument('--nproc', type=int, default=int(os.environ.get('NPROC', '8')))
    ap.add_argument('--timeout', type=int, default=7200, help='per-burst timeout (s)')
    ap.add_argument('--models', choices=['default', 'shape', 'highe', 'threecomp'], default=None,
                    help='forwarded to scripts/10 (model-set selection)')
    ap.add_argument('--include-lat', action='store_true',
                    help='forwarded to scripts/10 (per-block LAT >100 MeV plugin)')
    args = ap.parse_args()
    extra = []
    if args.models:
        extra += ['--models', args.models]
    if args.include_lat:
        extra += ['--include-lat']

    if not os.path.exists(args.bkg_file):
        sys.exit(f'bkg file not found: {args.bkg_file}')
    os.makedirs(args.out_root, exist_ok=True)
    trigs = sorted(os.path.basename(f).split('bb_blocks_spectral_')[1].split('.ecsv')[0]
                   for f in glob.glob(f'{args.blocks_dir}/bb_blocks_spectral_*.ecsv'))
    todo = [t for t in trigs
            if not os.path.exists(os.path.join(args.out_root, t, 'spectral_fits.ecsv'))]
    print(f'bkg={os.path.basename(args.bkg_file)} blocks={args.blocks_dir} out={args.out_root}', flush=True)
    print(f'{len(trigs)} bursts, {len(todo)} to fit ({len(trigs)-len(todo)} done), {args.nproc} workers', flush=True)
    n_ok = n_fail = 0
    with ProcessPoolExecutor(max_workers=args.nproc) as ex:
        futs = {ex.submit(run, t, args.bkg_file, args.blocks_dir, args.out_root, args.timeout, tuple(extra)): t
                for t in trigs}
        for fu in as_completed(futs):
            trig, st, dt = fu.result()
            if st in ('ok', 'skip'):
                n_ok += 1
            else:
                n_fail += 1
            print(f'[{n_ok+n_fail}/{len(trigs)}] {trig}: {st} ({dt:.0f}s)', flush=True)
    print(f'\nDONE: {n_ok} ok/skip, {n_fail} failed. -> {args.out_root}', flush=True)
    if n_fail:
        sys.exit(1)                 # batch failures must not exit 0 (audit #32)


if __name__ == '__main__':
    main()
