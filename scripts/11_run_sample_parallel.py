#!/usr/bin/env python
"""
Fully automated sample-scale parallel runner for Two_Breaks.

For each burst in the single-pulse sample, runs the full pipeline:

  1. Phase 1 — `00_prototype_one_burst.py --trigger X`
       Generates lc_for_ai/ PNGs + pending manifest.
       Skipped if `lc_for_ai/<trigger>_pending.json` already exists.

  2. Phase 2 (heuristic) — write `<trigger>_ai_selections.json`
       Top-3 NaI detectors by angle (already chosen by Phase 1) +
       closest BGO; bkg windows pre=[-100,-20]s, post=[t90_stop+20,t90_stop+100]s,
       confidence='high'. Real Anthropic-vision Phase 2 can replace this
       function later as a quality upgrade.
       Skipped if `<trigger>_ai_selections.json` already exists.

  3. Phase 3 — `00_prototype_one_burst.py --resume --auto-approve --trigger X`
       Consumes ai_selections.json, runs BB blocks, writes
       background_intervals_prototype.ecsv + bb_blocks_spectral_<trigger>.ecsv.
       Skipped if bkg ECSV row + bb_blocks_spectral exist.

  4. Spectral fits — `10_spectral_fit_burst.py --trigger X`
       Runs all 6 GBM models, writes per_burst/<trigger>/spectral_fits.ecsv.
       Always run (cheap to re-run; updates per-burst log).

Dispatches across `--processes` worker processes (default 12). Each worker
writes its own per-burst log under `results/per_burst/<trigger>/logs/`.

Usage:
    python 11_run_sample_parallel.py                    # all 106 bursts, 12 cores
    python 11_run_sample_parallel.py --processes 4
    python 11_run_sample_parallel.py --triggers bn260105973,bn150902733
"""
import os, sys, glob, json, argparse, subprocess, time, traceback
from datetime import datetime
from multiprocessing import Pool, cpu_count

import numpy as np
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, 'scripts')
RESULTS = os.path.join(BASE, 'results')
DATA = os.path.join(BASE, 'data')
PER_BURST = os.path.join(RESULTS, 'per_burst')
LC_FOR_AI = os.path.join(BASE, 'plots', 'lc_for_ai')

PROTOTYPE = os.path.join(SCRIPTS, '00_prototype_one_burst.py')
SCRIPT_10 = os.path.join(SCRIPTS, '10_spectral_fit_burst.py')

PYTHON = '/Users/salim/anaconda3/envs/threeML/bin/python'

# CALDB env vars — required by fermitools/3ML in subprocess workers since the
# parent shell may not export them. Matches script 10's import-time setup.
_FD = '/Users/salim/anaconda3/envs/threeML/share/fermitools'
SUBPROC_ENV = {
    **os.environ,
    'PYTHONUNBUFFERED': '1',
    'MPLBACKEND': 'Agg',
    'FERMI_DIR': _FD,
    'CALDB': _FD + '/data/caldb',
    'CALDBALIAS': _FD + '/data/caldb/software/tools/alias_config.fits',
    'CALDBCONFIG': _FD + '/data/caldb/software/tools/caldb.config',
    'CALDBROOT': _FD + '/data/caldb',
    'EXTFILESSYS': _FD + '/refdata/fermi',
}


# ---------------- LLE auto-download (HAS_LAT bursts) ----------------
def _has_lle_locally(trigger):
    """True if all 3 LLE files are present on disk."""
    base = os.path.join(DATA, trigger)
    lle = glob.glob(os.path.join(base, 'gll_lle_*.fit*'))
    ft2 = (glob.glob(os.path.join(base, 'gll_ft2_*.fit*'))
           + glob.glob(os.path.join(base, 'gll_pt_*.fit*')))
    rsp = (glob.glob(os.path.join(base, 'gll_lle_*.rsp*'))
           + glob.glob(os.path.join(base, 'gll_cspec_*.rsp*')))
    return bool(lle and ft2 and rsp)


def _download_lle(trigger):
    """Fetch LLE event/FT2/RSP via 3ML's download_LLE_trigger_data.
    Trigger name format expected by 3ML: strip 'bn' prefix.
    Returns True on success, False on 404 / missing data.
    """
    if _has_lle_locally(trigger):
        return True
    try:
        from threeML import download_LLE_trigger_data
        dest = os.path.join(DATA, trigger)
        os.makedirs(dest, exist_ok=True)
        trig_num = trigger[2:] if trigger.startswith('bn') else trigger
        download_LLE_trigger_data(trigger_name=trig_num,
                                  destination_directory=dest)
        return _has_lle_locally(trigger)
    except Exception:
        return False


# ---------------- Phase 2 heuristic AI selections ----------------


# ---------------- Per-burst worker ----------------
def _run_subprocess(args, log_path):
    """Run a subprocess, capture stdout+stderr to log_path."""
    with open(log_path, 'a') as logf:
        logf.write(f'\n\n{"="*72}\n[runner] {datetime.now().isoformat()} '
                   f'CMD: {" ".join(args)}\n{"="*72}\n')
        logf.flush()
        try:
            proc = subprocess.run(args, stdout=logf, stderr=subprocess.STDOUT,
                                  timeout=7200, env=SUBPROC_ENV)
            return proc.returncode
        except subprocess.TimeoutExpired:
            logf.write('\n[runner] TIMEOUT after 7200 s\n')
            return -1


def _runner_log_path(trigger):
    log_dir = os.path.join(PER_BURST, trigger, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    return os.path.join(log_dir, f'11_runner_{stamp}.log')


def _has_lat_flag(trigger):
    """True if single_pulse_grbs.ecsv marks this trigger HAS_LAT=True."""
    try:
        sp = Table.read(os.path.join(RESULTS, 'single_pulse_grbs.ecsv'),
                        format='ascii.ecsv')
        m = sp['TRIGGER_NAME'] == trigger
        if m.any():
            return bool(sp[m][0]['HAS_LAT'])
    except Exception:
        pass
    return False


def worker(trigger):
    """Run all phases for one burst. Returns dict with per-phase status."""
    t0 = time.time()
    result = {'trigger': trigger, 'phases': {}, 'status': 'pending',
              'error': None, 'wall_s': 0.0}
    log_path = _runner_log_path(trigger)
    result['log'] = log_path

    try:
        # Phase 0 (new): LLE auto-download for HAS_LAT bursts
        if _has_lat_flag(trigger):
            ok = _download_lle(trigger)
            result['phases']['lle'] = 'ok' if ok else 'unavailable'
            with open(log_path, 'a') as lf:
                lf.write(f'\n[runner] LLE for {trigger}: '
                         f'{result["phases"]["lle"]}\n')
        else:
            result['phases']['lle'] = 'skip_no_lat'

        # Phase 1: light-curve PNGs + pending manifest
        pending_path = os.path.join(LC_FOR_AI, f'{trigger}_pending.json')
        if not os.path.exists(pending_path):
            rc = _run_subprocess([PYTHON, PROTOTYPE, '--trigger', trigger,
                                  '--no-t90'], log_path)
            result['phases']['p1'] = rc
            if rc != 0 or not os.path.exists(pending_path):
                result['status'] = 'fail_phase1'
                return result
        else:
            result['phases']['p1'] = 'skip'

        # Phase 2: REQUIRE a real AI-vision ai_selections.json. No heuristic
        # fallback (no shortcuts) — the vision step must have produced it.
        ai_path = os.path.join(LC_FOR_AI, f'{trigger}_ai_selections.json')
        if not os.path.exists(ai_path):
            with open(log_path, 'a') as lf:
                lf.write(f'\n[runner] Phase 2: MISSING {ai_path} '
                         f'- AI-vision selection not run for this burst.\n')
            result['phases']['p2'] = 'missing_ai_selection'
            result['status'] = 'fail_no_ai_selection'
            return result
        result['phases']['p2'] = 'ai_vision'

        # Phase 3: bkg picker + BB blocks (auto-approve)
        # Gate ONLY on the per-burst bb_spec (written atomically per trigger);
        # do NOT read the shared background_intervals ECSV here - concurrent
        # workers atomically replace it, so an unlocked read can race.
        bb_spec = os.path.join(RESULTS, f'bb_blocks_spectral_{trigger}.ecsv')
        needs_p3 = not os.path.exists(bb_spec)
        if needs_p3:
            rc = _run_subprocess([PYTHON, PROTOTYPE, '--resume',
                                  '--auto-approve', '--accept-low',
                                  '--trigger', trigger,
                                  '--no-t90'], log_path)
            result['phases']['p3'] = rc
            if rc != 0 or not os.path.exists(bb_spec):
                result['status'] = 'fail_phase3'
                return result
        else:
            result['phases']['p3'] = 'skip'

        # Phase 4: spectral fits (always run). BGO included by default
        # (user requirement: use all approved detectors). LLE auto-added
        # by script 10 if a glg_lle_*.fit and glg_lle_*.rsp pair exists
        # under data/<trigger>/.
        rc = _run_subprocess([PYTHON, SCRIPT_10, '--trigger', trigger,
                              '--include-bgo',
                              '--no-log'], log_path)
        # --no-log here because the runner is already capturing stdout
        # into the per-burst log via _run_subprocess; doubling it would
        # be redundant.
        result['phases']['fit'] = rc
        fit_ecsv = os.path.join(PER_BURST, trigger, 'spectral_fits.ecsv')
        if rc != 0 or not os.path.exists(fit_ecsv):
            result['status'] = 'fail_fit'
            return result

        result['status'] = 'ok'

    except Exception as exc:
        result['status'] = 'exception'
        result['error'] = f'{type(exc).__name__}: {exc}'
        with open(log_path, 'a') as lf:
            lf.write(f'\n[runner] EXCEPTION:\n{traceback.format_exc()}\n')

    result['wall_s'] = time.time() - t0
    return result


# ---------------- Driver ----------------
def list_triggers(spec=None):
    sp = Table.read(os.path.join(RESULTS, 'single_pulse_grbs.ecsv'),
                    format='ascii.ecsv')
    all_trigs = sorted(set(str(t).strip() for t in sp['TRIGGER_NAME']))
    if spec:
        wanted = [t.strip() for t in spec.split(',') if t.strip()]
        unknown = set(wanted) - set(all_trigs)
        if unknown:
            print(f'WARNING: unknown triggers (not in sample): {unknown}')
        return [t for t in wanted if t in all_trigs]
    return all_trigs


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--processes', type=int, default=12,
                   help='Worker pool size (default 12)')
    p.add_argument('--triggers', type=str, default=None,
                   help='Comma-separated trigger names (default: full sample)')
    p.add_argument('--limit', type=int, default=None,
                   help='Run only first N triggers from the list (testing)')
    args = p.parse_args()

    triggers = list_triggers(args.triggers)
    if args.limit:
        triggers = triggers[:args.limit]
    n_proc = min(args.processes, max(1, cpu_count() - 2), len(triggers))

    print(f'Triggers to process: {len(triggers)}')
    print(f'Worker pool:         {n_proc}')
    print(f'Available CPU cores: {cpu_count()}')
    print()

    t_start = time.time()
    summary_rows = []
    with Pool(processes=n_proc) as pool:
        for k, r in enumerate(pool.imap_unordered(worker, triggers, chunksize=1)):
            elapsed = time.time() - t_start
            print(f'[{k+1}/{len(triggers)}] {r["trigger"]:14s} '
                  f'status={r["status"]:14s} '
                  f'phases={r["phases"]} '
                  f'wall={r["wall_s"]:.0f}s  '
                  f'(total elapsed: {elapsed:.0f}s)')
            summary_rows.append({
                'TRIGGER_NAME': r['trigger'],
                'STATUS': r['status'],
                'PHASE1': str(r['phases'].get('p1', '')),
                'PHASE2': str(r['phases'].get('p2', '')),
                'PHASE3': str(r['phases'].get('p3', '')),
                'PHASE_FIT': str(r['phases'].get('fit', '')),
                'WALL_S': r['wall_s'],
                'LOG': r.get('log', ''),
                'ERROR': r.get('error', '') or '',
            })

    # Write summary ECSV
    sum_path = os.path.join(RESULTS,
        f'sample_run_summary_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.ecsv')
    if summary_rows:
        keys = list(summary_rows[0].keys())
        Table(rows=[[r[k] for k in keys] for r in summary_rows],
              names=keys).write(sum_path, format='ascii.ecsv', overwrite=True)
        print(f'\nSummary written: {sum_path}')

    # Tally
    by_status = {}
    for r in summary_rows:
        by_status[r['STATUS']] = by_status.get(r['STATUS'], 0) + 1
    print('\nFinal tally:')
    for s, n in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f'  {s:14s}: {n}')


if __name__ == '__main__':
    main()
