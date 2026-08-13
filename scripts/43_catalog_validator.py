#!/usr/bin/env python3
"""Adjudication-aware validator for the approved selections catalog.

Born 2026-08-12 from flag F-2 (Khushboo, GRB 200524A walkthrough): the rule
`pre_stop <= t1 < t2 <= post_start` (source_selection.md) is a Stage-1 GUI
WARNING, overridable by the human gate; overrides live in
results/human_review_qc_flags.txt. TWO operators (Claude, then Khushboo) have
now independently re-flagged already-adjudicated rows because they validated
against the written rule without joining the decisions ledger — per campaign
doctrine, twice-by-two-operators = a SKILL bug, so the ledger join now lives
in code. A violation is reported ONLY if it is NOT covered by an accepted
adjudication. Exit 1 on any unadjudicated violation.
"""
import os, sys
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, 'results', 'background_intervals.ecsv')
LEDGER = os.path.join(ROOT, 'results', 'human_review_qc_flags.txt')


def load_ledger():
    acc = set()          # (trigger, detector) pairs with accepted overrun
    if os.path.exists(LEDGER):
        for line in open(LEDGER):
            p = line.split('\t')
            if len(p) >= 3 and 'overruns_bkg_gap' in p[1]:
                trig = p[0].strip()
                for tok in p[2].split(','):
                    det = tok.split('[')[0].strip()
                    if det:
                        acc.add((trig, det))
    return acc


def main():
    t = Table.read(CAT)
    acc = load_ledger()
    new = []
    for r in t:
        trig, det = str(r['TRIGGER_NAME']), str(r['DETECTOR'])
        pre_stop, post_start = float(r['BKG_NEG_STOP']), float(r['BKG_POS_START'])
        t1, t2 = float(r['SRC_START']), float(r['SRC_STOP'])
        ok_rule = (pre_stop <= t1 < t2 <= post_start)
        if not ok_rule and (trig, det) not in acc:
            over = max(pre_stop - t1, t2 - post_start)
            new.append((trig, det, round(over, 2)))
    n_adj = sum(1 for r in t
                if (str(r['TRIGGER_NAME']), str(r['DETECTOR'])) in acc)
    print(f'catalog rows: {len(t)}; adjudicated-accepted overruns on file: {n_adj}')
    if new:
        print(f'UNADJUDICATED violations: {len(new)}')
        for v in new:
            print('  ', *v)
        sys.exit(1)
    print('UNADJUDICATED violations: 0 — catalog consistent with rule + ledger')


if __name__ == '__main__':
    main()
