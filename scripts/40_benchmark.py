#!/usr/bin/env python
"""
40_benchmark.py -- score AI-vs-human Stage-1 selections, with human-vs-human as the
denominator (see dev/BENCHMARK_PLAN.md).

Each rater (>=2 human experts + the AI) approves the SAME benchmark bursts via
scripts/39 (run with --out/--approval-dir so each writes a SEPARATE catalog in the
scripts/39 schema, distinguished by APPROVED_BY + APPROVAL_MODE). This script loads
all those catalogs and computes, for every rater PAIR on their common bursts:
  - detector approved-set Jaccard (task 1),
  - background pre/post edge deltas + window IoU (task 2),
  - source edge deltas + IoU + fractional-duration error (task 3).
Pairs are split into HUMAN-vs-HUMAN (the inter-expert baseline = the denominator) and
AI-vs-HUMAN. The headline per metric: does AI-vs-human agreement fall WITHIN the
human-vs-human band? If yes, the agent matches experts as well as experts match
each other. (QC-flagging, task 4, is scored separately once flag files exist; and the
downstream parameter-impact test runs on the fit outputs -- stub at the end.)

Usage:
  python scripts/40_benchmark.py --catalog-dir results/benchmark            # *.ecsv there
  python scripts/40_benchmark.py --catalogs a.ecsv b.ecsv ai.ecsv [--csv out.csv]
Light deps (numpy/astropy). Read-only. Run from repo root.
"""
import os
import glob
import argparse
import itertools
import numpy as np
from astropy.table import Table

AI_MODES = {'ai_vision', 'ai_auto', 'ai'}


def _iou(a, b):
    """Intersection-over-union of two intervals [a0,a1],[b0,b1]."""
    inter = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union > 0 else 0.0


def load_catalog(path):
    """-> dict(rater, mode, detectors{trig:set}, bkg{(trig,det):(4)}, source{trig:(2)})."""
    t = Table.read(path, format='ascii.ecsv')
    rater = (str(t['APPROVED_BY'][0]) if 'APPROVED_BY' in t.colnames and len(t)
             else os.path.splitext(os.path.basename(path))[0])
    mode = (str(t['APPROVAL_MODE'][0]) if 'APPROVAL_MODE' in t.colnames and len(t)
            else 'unknown')
    detectors, bkg, source = {}, {}, {}
    for r in t:
        trig, det = str(r['TRIGGER_NAME']), str(r['DETECTOR'])
        detectors.setdefault(trig, set()).add(det)
        bkg[(trig, det)] = (float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP']),
                            float(r['BKG_POS_START']), float(r['BKG_POS_STOP']))
        if 'SRC_START' in t.colnames:
            s1, s2 = float(r['SRC_START']), float(r['SRC_STOP'])
            if np.isfinite(s1) and np.isfinite(s2):
                source[trig] = (s1, s2)
    return {'rater': rater, 'mode': mode, 'path': path,
            'detectors': detectors, 'bkg': bkg, 'source': source}


def pair_metrics(A, B):
    """Per-item agreement metrics between two raters on their common bursts."""
    rows = []
    common = set(A['detectors']) & set(B['detectors'])
    for trig in sorted(common):
        da, db = A['detectors'][trig], B['detectors'][trig]
        jac = len(da & db) / len(da | db) if (da | db) else 1.0
        rows.append({'trig': trig, 'metric': 'det_jaccard', 'det': '', 'value': jac})
        for det in sorted(da & db):
            a, b = A['bkg'][(trig, det)], B['bkg'][(trig, det)]
            for k, name in enumerate(('neg_start', 'neg_stop', 'pos_start', 'pos_stop')):
                rows.append({'trig': trig, 'metric': f'bkg_d_{name}', 'det': det,
                             'value': abs(a[k] - b[k])})
            rows.append({'trig': trig, 'metric': 'bkg_pre_iou', 'det': det,
                         'value': _iou(a[0:2], b[0:2])})
            rows.append({'trig': trig, 'metric': 'bkg_post_iou', 'det': det,
                         'value': _iou(a[2:4], b[2:4])})
        if trig in A['source'] and trig in B['source']:
            sa, sb = A['source'][trig], B['source'][trig]
            rows.append({'trig': trig, 'metric': 'src_d_start', 'det': '',
                         'value': abs(sa[0] - sb[0])})
            rows.append({'trig': trig, 'metric': 'src_d_stop', 'det': '',
                         'value': abs(sa[1] - sb[1])})
            rows.append({'trig': trig, 'metric': 'src_iou', 'det': '',
                         'value': _iou(sa, sb)})
            da_dur, db_dur = sa[1] - sa[0], sb[1] - sb[0]
            if da_dur > 0:
                rows.append({'trig': trig, 'metric': 'src_frac_dur_err', 'det': '',
                             'value': abs(db_dur - da_dur) / da_dur})
    return rows


def _summ(vals):
    v = np.asarray(vals, float)
    if not len(v):
        return (np.nan, np.nan, np.nan, 0)
    return (np.median(v), np.percentile(v, 25), np.percentile(v, 75), len(v))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--catalog-dir', default=None, help='dir of per-rater *.ecsv')
    ap.add_argument('--catalogs', nargs='*', default=None, help='explicit catalog paths')
    ap.add_argument('--csv', default=None, help='write per-pair-per-item metrics here')
    args = ap.parse_args()

    paths = args.catalogs or (sorted(glob.glob(os.path.join(args.catalog_dir, '*.ecsv')))
                              if args.catalog_dir else None)
    if not paths or len(paths) < 2:
        raise SystemExit('Need >=2 per-rater catalogs (--catalog-dir or --catalogs).')
    cats = [load_catalog(p) for p in paths]
    print('Raters:')
    for c in cats:
        kind = 'AI' if c['mode'] in AI_MODES else 'human'
        print(f'  {c["rater"]:24s} [{kind:5s} / {c["mode"]}] '
              f'{len(c["detectors"])} bursts  ({os.path.basename(c["path"])})')

    # all rater pairs, classified
    by_type = {'H-H': [], 'AI-H': [], 'AI-AI': []}
    all_rows = []
    for A, B in itertools.combinations(cats, 2):
        ai_a, ai_b = A['mode'] in AI_MODES, B['mode'] in AI_MODES
        ptype = 'AI-AI' if (ai_a and ai_b) else ('H-H' if not (ai_a or ai_b) else 'AI-H')
        rows = pair_metrics(A, B)
        for r in rows:
            r['pair'] = f'{A["rater"]}|{B["rater"]}'; r['ptype'] = ptype
        by_type[ptype].extend(rows)
        all_rows.extend(rows)

    metrics = ['det_jaccard', 'bkg_pre_iou', 'bkg_post_iou', 'bkg_d_neg_start',
               'bkg_d_neg_stop', 'bkg_d_pos_start', 'bkg_d_pos_stop',
               'src_iou', 'src_d_start', 'src_d_stop', 'src_frac_dur_err']
    higher_better = {'det_jaccard', 'bkg_pre_iou', 'bkg_post_iou', 'src_iou'}

    print('\n=== Agreement: AI-vs-human vs the human-vs-human band (median [IQR]) ===')
    print(f'{"metric":18s} {"H-H (baseline)":22s} {"AI-H":22s}  verdict')
    for m in metrics:
        hh = _summ([r['value'] for r in by_type['H-H'] if r['metric'] == m])
        ah = _summ([r['value'] for r in by_type['AI-H'] if r['metric'] == m])
        if hh[3] == 0 or ah[3] == 0:
            verdict = '(need both H-H and AI-H pairs)'
        elif m in higher_better:
            verdict = 'AI within human band' if ah[0] >= hh[1] else 'AI WORSE than experts'
        else:  # lower better (edge deltas)
            verdict = 'AI within human band' if ah[0] <= hh[2] else 'AI WORSE than experts'
        print(f'{m:18s} {hh[0]:6.3f} [{hh[1]:.3f},{hh[2]:.3f}] n={hh[3]:<4d} '
              f'{ah[0]:6.3f} [{ah[1]:.3f},{ah[2]:.3f}] n={ah[3]:<4d}  {verdict}')

    if not by_type['H-H']:
        print('\nNOTE: no human-vs-human pairs found -> no inter-expert denominator. '
              'Add a 2nd human rater for the rigorous benchmark (BENCHMARK_PLAN.md).')

    if args.csv:
        Table(rows=[{k: r.get(k) for k in ('ptype', 'pair', 'trig', 'det', 'metric', 'value')}
                    for r in all_rows]).write(args.csv, format='csv', overwrite=True)
        print(f'\nper-item metrics -> {args.csv}')

    # ---- downstream parameter-impact (STUB) -------------------------------------
    # Needs the two fit catalogs (clean_per_burst from each rater's run). To be filled
    # once the dual-mode Stage 2-3 has run: match (trigger, block) and compare Ep,
    # alpha, kT, and the model classification AI-vs-human against the human-vs-human band.
    print('\n[downstream parameter-impact: run after the dual-mode fits exist]')


if __name__ == '__main__':
    main()
