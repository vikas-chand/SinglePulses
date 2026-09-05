#!/usr/bin/env python3
"""Skeleton §1: derive every burst's STATE from evidence on disk (never from
memory or logs of intent). Writes results/campaign/burst_state/<trig>.json
and prints the campaign board. Read-only w.r.t. science products."""
import os, json, glob, datetime
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SB = os.path.join(ROOT, 'results', 'campaign', 'burst_state')
os.makedirs(SB, exist_ok=True)
STRUCTURAL = {'bn100130729': 'RESPONSE_UNCOVERED: DRMs cover +139..+475 s; source 62-81 s'}

def state_of(trig):
    ev = {}
    def E(k, v): ev[k] = v; return bool(v)
    # S2 blocks
    if not E('blocks', os.path.exists(f'{ROOT}/results/sweep106/{trig}/blocks/bb_blocks_spectral_{trig}.ecsv')):
        return 'S1_STAGE1_APPROVED', ev
    if trig in STRUCTURAL:
        ev['reason'] = STRUCTURAL[trig]; return 'SX_STRUCTURAL_EXCLUSION', ev
    # S3 fit + 24-model census
    fam = f'{ROOT}/results/campaign20_fam/{trig}_highe/spectral_fits.ecsv'
    prom = f'{ROOT}/results/convention_check/{trig}/spectral_fits.ecsv'
    src = prom if os.path.exists(prom) else (fam if os.path.exists(fam) else None)
    if not E('fit_table', src): return 'S2_BINNED', ev
    t = Table.read(src)
    nm = len({c[:-4] for c in t.colnames if c.endswith('_AIC')})
    if not E('census24', nm >= 24): return 'S2_BINNED', ev   # F-CONTRACT if a table exists but census fails
    # S4 retry: eligible iff literal FAILs in highe family
    fails = sum(1 for r in t for c in t.colnames
                if c.endswith('_STATUS') and str(r[c]).strip() == 'FAIL')
    ev['fail_cells'] = fails
    retry_ok = (fails == 0) or os.path.exists(
        f'{ROOT}/results/convention_check/{trig}/family_runs/highe_retry/spectral_fits.ecsv') \
        or os.path.exists(f'{ROOT}/results/campaign20_fam/{trig}_highe_retry/spectral_fits.ecsv')
    if not E('retry_terminal', retry_ok): return 'S3_FIT', ev
    # S5 promoted with receipt
    rec = glob.glob(f'{ROOT}/results/convention_check/{trig}/promotion_receipts/*.json')
    if not E('receipt', bool(rec)): return 'S4_RETRIED', ev
    ev['currency'] = 'UNVERIFIED (NR-22)'
    # S6 temporal
    if not E('p2_summary', os.path.exists(f'{ROOT}/results/sweep106/{trig}/p2_temporal_summary.json')):
        return 'S5_PROMOTED', ev
    # S7 products
    grids = len(glob.glob(f'{ROOT}/results/convention_check/sed_grid_{trig}/*.png'))
    mont = len(glob.glob(f'{ROOT}/results/convention_check/sed_grid_{trig}/montage/*.png'))
    ev['grids'], ev['montages'] = grids, mont
    if not (grids and mont): return 'S6_TEMPORAL_DONE', ev
    # S8 assembled at campaign commit (R1: staging manifest required)
    man = glob.glob(f'{ROOT}/paper/GRB*/staging_manifest.json')
    mine = [m for m in man if trig[2:8] in os.path.basename(os.path.dirname(m))]
    if not E('assembled_manifest', bool(mine)): return 'S7_PRODUCTS_DONE', ev
    # S9 gated — three sha-bound verdicts (approximated: NR-24 entry in VISION_QC)
    vq = f'{ROOT}/results/sweep106/{trig}/VISION_QC.md'
    gated = os.path.exists(vq) and 'NR-24' in open(vq).read()
    if not E('gated', gated): return 'S8_ASSEMBLED', ev
    ap = f'{ROOT}/results/sweep106/{trig}/APPROVALS.json'
    st = json.load(open(ap)) if os.path.exists(ap) else {}
    if any(v.get('status') == 'APPROVED' for v in st.values()): return 'S11_APPROVED', ev
    if any(v.get('status') == 'PRESENTED' for v in st.values()): return 'S10_PRESENTED', ev
    return 'S9_GATED', ev

cat = Table.read(f'{ROOT}/results/background_intervals.ecsv')
trigs = sorted({str(x).strip() for x in cat['TRIGGER_NAME']})
board = {}
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
for trig in trigs:
    s, ev = state_of(trig)
    board.setdefault(s, []).append(trig)
    json.dump({'trig': trig, 'state': s, 'derived_utc': now, 'evidence': ev},
              open(f'{SB}/{trig}.json', 'w'), indent=1, default=str)
print(f'CAMPAIGN BOARD — {len(trigs)} bursts — {now}')
for s in sorted(board):
    print(f'  {s:24} {len(board[s]):3}  {" ".join(board[s][:6])}{" ..." if len(board[s])>6 else ""}')
