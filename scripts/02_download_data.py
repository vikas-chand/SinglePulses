#!/usr/bin/env python
"""
Phase 1, Step 1.2: Download TTE + CSPEC + RSP data for each GRB.

For each GRB in the sample, download data for up to 3 NaI detectors
(from the NAI_DETECTORS column, angle-sorted) plus the corresponding
BGO detector (b0 for n0-n5 side, b1 for n6-nb side).

Multi-detector approach follows Burgess et al. (2014).
"""

import os
import sys
import time
import glob
import numpy as np
from astropy.table import Table

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from threeML import download_GBM_trigger_data

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(DATA_DIR, exist_ok=True)

# NaI detectors on each side of the spacecraft
LOW_SIDE = {'n0', 'n1', 'n2', 'n3', 'n4', 'n5'}   # -> BGO b0
HIGH_SIDE = {'n6', 'n7', 'n8', 'n9', 'na', 'nb'}   # -> BGO b1


def select_detectors(det_str):
    """Select up to 3 NaI detectors + corresponding BGO.

    Parameters
    ----------
    det_str : str
        Comma-separated NaI detector names (angle-sorted, brightest first).

    Returns
    -------
    nai_dets : list of str
        Up to 3 NaI detectors.
    bgo : str
        'b0' or 'b1' based on majority side of NaI detectors.
    all_dets : list of str
        nai_dets + [bgo].
    """
    nai_dets = [d.strip() for d in det_str.split(',')][:3]

    # Determine BGO: b0 if majority NaI are on n0-n5 side, else b1
    n_low = sum(1 for d in nai_dets if d in LOW_SIDE)
    bgo = 'b0' if n_low >= len(nai_dets) - n_low else 'b1'

    all_dets = nai_dets + [bgo]
    return nai_dets, bgo, all_dets


def check_existing_files(grb_dir, all_dets):
    """Check if all needed detector files already exist.

    For each detector we need at least a TTE (.fit.gz) and RSP (.rsp/.rsp2).

    Returns
    -------
    missing : list of str
        Detectors that are missing files.
    """
    missing = []
    for det in all_dets:
        tte = glob.glob(os.path.join(grb_dir, f'glg_tte_{det}_*.fit.gz'))
        rsp = glob.glob(os.path.join(grb_dir, f'glg_cspec_{det}_*.rsp*'))
        if not tte or not rsp:
            missing.append(det)
    return missing


# Load sample
sample = Table.read(os.path.join(RESULTS_DIR, 'grb_sample.ecsv'), format='ascii.ecsv')
print(f"Sample size: {len(sample)} GRBs")

# Track successes and failures
success = []
failed = []

for i, row in enumerate(sample):
    trigger = str(row['TRIGGER_NAME']).strip()
    det_str = str(row['NAI_DETECTORS']).strip()

    if not det_str:
        print(f"[{i+1}/{len(sample)}] {trigger}: no detectors listed, skipping")
        failed.append((trigger, 'no detectors'))
        continue

    nai_dets, bgo, all_dets = select_detectors(det_str)

    grb_dir = os.path.join(DATA_DIR, trigger)
    os.makedirs(grb_dir, exist_ok=True)

    # Check which detectors still need downloading
    missing = check_existing_files(grb_dir, all_dets)

    if not missing:
        print(f"[{i+1}/{len(sample)}] {trigger}: all {len(all_dets)} detectors present, skipping")
        success.append(trigger)
        continue

    print(f"[{i+1}/{len(sample)}] {trigger}: downloading {len(missing)} detectors "
          f"({','.join(missing)}) of {len(all_dets)} total...", end=' ', flush=True)
    try:
        result = download_GBM_trigger_data(
            trigger,
            detectors=missing,
            destination_directory=grb_dir,
            compress_tte=True
        )
        print("OK")
        success.append(trigger)
    except Exception as e:
        print(f"FAILED: {e}")
        failed.append((trigger, str(e)))

    # Brief pause to be polite to HEASARC
    time.sleep(0.5)

print(f"\n{'='*60}")
print(f"Downloads complete: {len(success)} succeeded, {len(failed)} failed")
if failed:
    print(f"\nFailed triggers:")
    for t, reason in failed[:20]:
        print(f"  {t}: {reason}")
    if len(failed) > 20:
        print(f"  ... and {len(failed)-20} more")
print(f"{'='*60}")

# Save download status
status_path = os.path.join(RESULTS_DIR, 'download_status.txt')
with open(status_path, 'w') as f:
    f.write(f"Success: {len(success)}\n")
    f.write(f"Failed: {len(failed)}\n\n")
    f.write("Failed triggers:\n")
    for t, reason in failed:
        f.write(f"  {t}: {reason}\n")
print(f"Status saved to {status_path}")
