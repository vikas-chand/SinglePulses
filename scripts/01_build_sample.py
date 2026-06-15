#!/usr/bin/env python
"""
Phase 1, Step 1.1: Build the GRB sample.

Query the Fermi GBM burst catalog, apply fluence cut (>1e-5 erg/cm²),
and cross-match with the Fermi LAT GRB catalog to flag LAT/LLE detections.
Save the final sample table.
"""

import os
import numpy as np
from astroquery.heasarc import Heasarc
from astropy.table import Table, join

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

FLUENCE_CUT = 1.0e-5  # erg/cm^2
T90_CUT = 2.0          # seconds — long GRBs only (Busby & Lazzati criterion)

# ---------------------------------------------------------------------------
# 1. Query Fermi GBM burst catalog
# ---------------------------------------------------------------------------
print("Querying Fermi GBM burst catalog (fermigbrst)...")
h = Heasarc()

gbm_fields = (
    'NAME, TRIGGER_NAME, TRIGGER_TIME, RA, DEC, '
    'T90, T90_ERROR, T90_START, '
    'FLUENCE, FLUENCE_ERROR, '
    'FLUX_1024, FLUX_1024_ERROR, '
    'BCAT_DETECTOR_MASK, SCAT_DETECTOR_MASK'
)

gbm = h.query_object(
    '*',
    mission='fermigbrst',
    fields=gbm_fields,
    resultmax=10000,
)
print(f"  Total GBM bursts retrieved: {len(gbm)}")

# ---------------------------------------------------------------------------
# 2. Apply quality + selection cuts
# ---------------------------------------------------------------------------
# Remove rows with missing T90 or fluence (stored as NaN, not masked)
mask_valid = np.isfinite(gbm['T90']) & np.isfinite(gbm['FLUENCE'])
gbm_valid = gbm[mask_valid]
print(f"  After removing missing T90/fluence: {len(gbm_valid)}")

# T90 > 2 s (long GRBs)
mask_t90 = gbm_valid['T90'] > T90_CUT
gbm_long = gbm_valid[mask_t90]
print(f"  After T90 > {T90_CUT} s cut: {len(gbm_long)}")

# Fluence > 1e-5 erg/cm^2
mask_fluence = gbm_long['FLUENCE'] > FLUENCE_CUT
sample = gbm_long[mask_fluence]
print(f"  After fluence > {FLUENCE_CUT} cut: {len(sample)}")

# ---------------------------------------------------------------------------
# 3. Query Fermi LAT GRB catalog and cross-match
# ---------------------------------------------------------------------------
print("\nQuerying Fermi LAT GRB catalog (fermilgrb)...")
lat_fields = 'NAME, GBM_CAT_NAME, LLE_BBBD_SIG, LLE_T90'
lat = h.query_object(
    '*',
    mission='fermilgrb',
    fields=lat_fields,
    resultmax=10000,
)
print(f"  LAT GRBs retrieved: {len(lat)}")

# Flag which GBM bursts have LAT/LLE detections
# The LAT catalog GBM_CAT_NAME matches the GBM NAME column
lat_names = set(str(n).strip() for n in lat['GBM_CAT_NAME'] if str(n).strip())
sample['HAS_LAT'] = [str(n).strip() in lat_names for n in sample['NAME']]
n_lat = np.sum(sample['HAS_LAT'])
print(f"  GRBs in sample with LAT/LLE detection: {n_lat}")

# ---------------------------------------------------------------------------
# 4. Parse detector mask to find brightest NaI detectors
# ---------------------------------------------------------------------------
NaI_LABELS = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5',
              'n6', 'n7', 'n8', 'n9', 'na', 'nb']

def parse_detector_mask(mask_str):
    """Parse the 14-char detector mask (12 NaI + 2 BGO).
    '1' means the detector was triggered / selected.
    Returns list of selected NaI detector names.
    """
    mask_str = str(mask_str).strip()
    if len(mask_str) < 12:
        return []
    selected = []
    for i, ch in enumerate(mask_str[:12]):
        if ch == '1':
            selected.append(NaI_LABELS[i])
    return selected

sample['NAI_DETECTORS'] = [parse_detector_mask(m) for m in sample['BCAT_DETECTOR_MASK']]
sample['N_NAI'] = [len(d) for d in sample['NAI_DETECTORS']]

# ---------------------------------------------------------------------------
# 5. Print summary and save
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"FINAL SAMPLE: {len(sample)} GRBs")
print(f"  With LAT/LLE: {n_lat}")
print(f"  T90 range: {sample['T90'].min():.1f} – {sample['T90'].max():.1f} s")
print(f"  Fluence range: {sample['FLUENCE'].min():.2e} – {sample['FLUENCE'].max():.2e} erg/cm²")
print(f"{'='*60}")

# Print the sample
print(f"\n{'NAME':<25s} {'TRIGGER':<15s} {'T90':>8s} {'FLUENCE':>12s} {'LAT':>5s} {'NaI dets':>10s}")
print('-' * 80)
for row in sample:
    print(f"{str(row['NAME']):<25s} {str(row['TRIGGER_NAME']):<15s} "
          f"{row['T90']:8.2f} {row['FLUENCE']:12.2e} "
          f"{'Y' if row['HAS_LAT'] else 'N':>5s} "
          f"{','.join(row['NAI_DETECTORS']):>10s}")

# Save
outpath = os.path.join(RESULTS_DIR, 'grb_sample.ecsv')
# Convert list columns to strings for serialization
sample_out = sample.copy()
sample_out['NAI_DETECTORS'] = [','.join(d) for d in sample_out['NAI_DETECTORS']]
sample_out.write(outpath, format='ascii.ecsv', overwrite=True)
print(f"\nSample saved to {outpath}")
