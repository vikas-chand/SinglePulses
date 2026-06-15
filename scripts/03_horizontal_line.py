#!/usr/bin/env python
"""
Phase 2: Busby & Lazzati (2024) horizontal line algorithm.

For each GRB with downloaded TTE data:
1. Build a light curve (120 bins) — NOT background-subtracted
2. Apply the horizontal line algorithm to classify single vs multi-pulse
3. Save classifications and diagnostic plots

Reference: Busby & Lazzati 2024, ApJ, 972, 83

Algorithm details (Section 2.2):
- 16 equally-spaced horizontal lines between:
    - Lowest: 2σ above the background count rate
    - Highest: 2σ below the peak count rate
- The lowest line is excluded from scoring → 15 scoring lines
- For each scoring line:
    - Find points ≥ 1σ above the line
    - Identify first and last such crossing
    - Count "failure points" between crossings that fall ≥ 1σ below the line
- Score = 1 - total_failures / (15 × 120)
- Threshold: 0.9983 (≤ 3 unnormalized failures)
"""

import os
import sys
import glob
import warnings
import numpy as np
from astropy.io import fits
from astropy.table import Table

warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(os.path.join(PLOTS_DIR, 'lightcurves'), exist_ok=True)

# Algorithm parameters (from Busby & Lazzati 2024, Section 2.2)
N_BINS = 120           # number of uniform bins in the ROI
N_LINES = 16           # total horizontal lines placed
N_SCORING = 15         # lines used for scoring (lowest excluded)
E_MIN_KEV = 8.0        # energy range lower bound (keV)
E_MAX_KEV = 900.0      # energy range upper bound (keV)
THRESHOLD = 0.9983     # single-pulse threshold (≤3 failures out of 1800)


def load_tte_lightcurve(tte_file, t90_start, t90):
    """
    Load TTE data and build a uniformly-binned light curve (counts, NOT rates).

    Region of interest per Eq. 1 of Busby & Lazzati:
        t_start = max(T90_start - 0.5 * T90, Tdstart)
        t_stop  = min(T90_start + 2 * T90, Tend)

    Also estimates background from the median counts in the T90 interval
    as described in the paper: "The average background count was determined
    by taking the median of all counts outside the region defined by
    T90start < t < T90start + T90."

    Returns:
        bin_centers: array of bin center times (s, relative to trigger)
        counts: raw counts per bin (NOT background-subtracted)
        bkg_level: estimated background counts per bin
        sigma_bkg: sqrt(bkg_level) — Poisson uncertainty on background
    """
    hdu = fits.open(tte_file)
    trigger_time = hdu['PRIMARY'].header.get('TRIGTIME', 0)

    events = hdu['EVENTS'].data
    times = events['TIME'] - trigger_time  # relative to trigger
    pha = events['PHA']

    # Energy selection via EBOUNDS
    ebounds = hdu['EBOUNDS'].data
    e_lo = ebounds['E_MIN']
    e_hi = ebounds['E_MAX']
    good_chan = np.where((e_hi >= E_MIN_KEV) & (e_lo <= E_MAX_KEV))[0]
    mask_energy = np.isin(pha, good_chan)
    times = times[mask_energy]

    hdu.close()

    # Region of interest per Eq. 1:
    # max(T90start - 0.5*T90, Tdstart) <= t <= min(T90start + 2*T90, Tend)
    data_start = times.min()
    data_stop = times.max()
    roi_start = max(t90_start - 0.5 * t90, data_start + 0.1)
    roi_stop = min(t90_start + 2.0 * t90, data_stop - 0.1)

    # Bin duration = T90/48 (paper Section 2.1)
    bin_width = t90 / 48.0
    bin_edges = np.arange(roi_start, roi_stop + bin_width * 0.5, bin_width)
    # Trim last edge to not exceed roi_stop
    bin_edges = bin_edges[bin_edges <= roi_stop + bin_width * 0.01]
    if len(bin_edges) < 3:
        # Fallback to fixed 120 bins if T90 is too short
        bin_edges = np.linspace(roi_start, roi_stop, N_BINS + 1)
        bin_width = bin_edges[1] - bin_edges[0]
    counts, _ = np.histogram(times, bins=bin_edges)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    # Background estimation:
    # "The average background count was determined by taking the median
    #  of all counts outside the region defined by T90start < t < T90start + T90"
    # We estimate background from bins outside the T90 interval but inside ROI
    mask_outside_t90 = (bin_centers < t90_start) | (bin_centers > t90_start + t90)
    if np.sum(mask_outside_t90) >= 3:
        bkg_level = float(np.median(counts[mask_outside_t90]))
    else:
        # Fallback: use the lowest 10% of bins
        sorted_counts = np.sort(counts)
        bkg_level = float(np.median(sorted_counts[:max(3, N_BINS // 10)]))

    sigma_bkg = np.sqrt(max(bkg_level, 1.0))  # Poisson: σ = √N

    return bin_centers, counts.astype(float), bkg_level, sigma_bkg, bin_width


def horizontal_line_score(counts, bkg_level, sigma_bkg):
    """
    Busby & Lazzati (2024) horizontal line algorithm (Section 2.2).

    Works on RAW counts (not background-subtracted).

    1. Place 16 equally-spaced horizontal lines between:
       - Lowest: bkg_level + 2σ  (2σ above background)
       - Highest: peak - 2σ      (2σ below peak)
    2. Exclude the lowest line from scoring → 15 scoring lines
    3. For each scoring line at height h:
       - Find bins with counts ≥ h + σ(h)  ["above the line by 1σ"]
         where σ(h) = √h (Poisson)
       - Identify the first and last such bin (the "outermost crossings")
       - Between those crossings, count bins with counts ≤ h - σ(h)
         ["failure points": bins that fall 1σ below the line]
    4. Score = 1 - total_failures / (N_SCORING × n_bins)

    Returns:
        score: float, higher = more single-pulse-like
        total_failures: int, total failure points across all scoring lines
        line_heights: array of the 16 line heights used
    """
    peak = counts.max()

    # Line placement bounds
    lowest = bkg_level + 2.0 * sigma_bkg
    highest = peak - 2.0 * np.sqrt(max(peak, 1.0))

    if highest <= lowest:
        # Not enough dynamic range — can't run the test meaningfully
        return np.nan, -1, np.array([])

    line_heights = np.linspace(lowest, highest, N_LINES)

    total_failures = 0

    # Skip the lowest line (index 0), score lines 1..15
    for line_idx in range(1, N_LINES):
        h = line_heights[line_idx]
        sigma_h = np.sqrt(max(h, 1.0))  # Poisson σ for this count level

        # Bins that are ≥ 1σ above the line
        above = counts >= (h + sigma_h)

        if not np.any(above):
            # No bins above this line — no crossings, no failures
            continue

        # First and last crossing
        above_indices = np.where(above)[0]
        first_cross = above_indices[0]
        last_cross = above_indices[-1]

        if first_cross >= last_cross:
            # Only one crossing point — no interior to check
            continue

        # Between crossings: count failure points (bins ≤ 1σ below the line)
        interior = counts[first_cross:last_cross + 1]
        failures = np.sum(interior <= (h - sigma_h))
        total_failures += failures

    n_bins = len(counts)
    score = 1.0 - total_failures / (N_SCORING * n_bins)

    return score, total_failures, line_heights


def plot_diagnostic(bin_centers, counts, bkg_level, sigma_bkg, line_heights,
                    score, total_failures, trigger, det, t90_start, t90, outpath):
    """Save a diagnostic plot showing the light curve and horizontal lines."""
    fig, ax = plt.subplots(figsize=(12, 5))

    # Light curve
    ax.step(bin_centers, counts, where='mid', color='black', lw=0.8, label='Light curve')

    # Background level
    ax.axhline(bkg_level, color='blue', ls=':', lw=1, alpha=0.7, label=f'Background ({bkg_level:.0f})')

    # T90 interval
    ax.axvspan(t90_start, t90_start + t90, alpha=0.08, color='orange', label='T90')

    # Horizontal lines (colored by whether they contribute failures)
    if len(line_heights) > 0:
        for idx, h in enumerate(line_heights):
            if idx == 0:
                # Excluded line
                ax.axhline(h, color='gray', ls='--', lw=0.4, alpha=0.5)
            else:
                sigma_h = np.sqrt(max(h, 1.0))
                above = counts >= (h + sigma_h)
                if np.any(above):
                    above_idx = np.where(above)[0]
                    interior = counts[above_idx[0]:above_idx[-1] + 1]
                    has_failures = np.any(interior <= (h - sigma_h))
                else:
                    has_failures = False
                color = 'red' if has_failures else 'green'
                ax.axhline(h, color=color, ls='-', lw=0.6, alpha=0.4)

    ax.set_xlabel('Time since trigger (s)')
    ax.set_ylabel('Counts per bin')
    tag = 'SINGLE' if score >= THRESHOLD else 'MULTI'
    ax.set_title(f'{trigger} ({det})  |  Score = {score:.4f}  |  Failures = {total_failures}  |  {tag}')
    ax.legend(fontsize=8, loc='upper right')
    fig.tight_layout()
    fig.savefig(outpath, dpi=100)
    plt.close(fig)


# ==========================================================================
# Main
# ==========================================================================
if __name__ == '__main__':
    sample = Table.read(os.path.join(RESULTS_DIR, 'grb_sample.ecsv'), format='ascii.ecsv')
    print(f"Sample: {len(sample)} GRBs")

    results = []
    n_processed = 0
    n_skipped = 0
    n_nodata = 0

    for i, row in enumerate(sample):
        trigger = str(row['TRIGGER_NAME']).strip()
        name = str(row['NAME']).strip()
        t90 = float(row['T90'])
        t90_start = float(row['T90_START'])
        det_str = str(row['NAI_DETECTORS']).strip()

        if not det_str:
            n_skipped += 1
            continue

        det = det_str.split(',')[0]

        # Find TTE file
        grb_dir = os.path.join(DATA_DIR, trigger)
        tte_files = glob.glob(os.path.join(grb_dir, f'glg_tte_{det}_*.fit.gz'))
        if not tte_files:
            tte_files = glob.glob(os.path.join(DATA_DIR, f'glg_tte_{det}_{trigger}*.fit.gz'))
        if not tte_files:
            n_nodata += 1
            continue

        tte_file = tte_files[0]

        try:
            bin_centers, counts, bkg_level, sigma_bkg, bin_width = \
                load_tte_lightcurve(tte_file, t90_start, t90)

            score, total_failures, line_heights = \
                horizontal_line_score(counts, bkg_level, sigma_bkg)

            if np.isnan(score):
                classification = 'insufficient_snr'
            elif score >= THRESHOLD:
                classification = 'single'
            else:
                classification = 'multi'

            results.append({
                'NAME': name,
                'TRIGGER_NAME': trigger,
                'T90': t90,
                'FLUENCE': float(row['FLUENCE']),
                'DETECTOR': det,
                'SCORE': round(score, 6) if not np.isnan(score) else -1.0,
                'FAILURES': total_failures,
                'CLASSIFICATION': classification,
                'HAS_LAT': bool(row['HAS_LAT']),
            })

            # Diagnostic plot
            plot_outpath = os.path.join(PLOTS_DIR, 'lightcurves', f'{trigger}_lc.png')
            plot_diagnostic(
                bin_centers, counts, bkg_level, sigma_bkg, line_heights,
                score if not np.isnan(score) else 0.0,
                total_failures, trigger, det, t90_start, t90, plot_outpath
            )

            n_processed += 1
            tag = classification[0].upper()
            if n_processed % 50 == 0 or n_processed <= 5:
                print(f"[{n_processed:4d}] {trigger}: score={score:.4f}, "
                      f"failures={total_failures}, [{tag}]")

        except Exception as e:
            print(f"[ERROR] {trigger}: {e}")
            n_skipped += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Processed: {n_processed}")
    print(f"Skipped (errors): {n_skipped}")
    print(f"No data available: {n_nodata}")

    if results:
        res_table = Table(results)
        n_single = np.sum(res_table['CLASSIFICATION'] == 'single')
        n_multi = np.sum(res_table['CLASSIFICATION'] == 'multi')
        n_insuf = np.sum(res_table['CLASSIFICATION'] == 'insufficient_snr')
        print(f"\nClassification results:")
        print(f"  Single-pulse:     {n_single}")
        print(f"  Multi-pulse:      {n_multi}")
        print(f"  Insufficient SNR: {n_insuf}")

        valid = res_table[res_table['SCORE'] >= 0]
        if len(valid) > 0:
            print(f"\nScore distribution (valid only):")
            print(f"  min={valid['SCORE'].min():.4f}, "
                  f"median={np.median(valid['SCORE']):.4f}, "
                  f"max={valid['SCORE'].max():.4f}")

        # Save all results
        outpath = os.path.join(RESULTS_DIR, 'horizontal_line_results.ecsv')
        res_table.write(outpath, format='ascii.ecsv', overwrite=True)
        print(f"\nAll results saved to {outpath}")

        # Save single and multi lists separately
        single = res_table[res_table['CLASSIFICATION'] == 'single']
        multi = res_table[res_table['CLASSIFICATION'] == 'multi']
        single.write(os.path.join(RESULTS_DIR, 'single_pulse_grbs.ecsv'),
                      format='ascii.ecsv', overwrite=True)
        multi.write(os.path.join(RESULTS_DIR, 'multi_pulse_grbs.ecsv'),
                     format='ascii.ecsv', overwrite=True)
        print(f"Single-pulse list: {len(single)} GRBs")
        print(f"Multi-pulse list:  {len(multi)} GRBs")

        # Score histogram
        if len(valid) > 0:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(valid['SCORE'], bins=40, edgecolor='black', alpha=0.7, color='steelblue')
            ax.axvline(THRESHOLD, color='red', ls='--', lw=2,
                       label=f'Threshold = {THRESHOLD}')
            ax.set_xlabel('Horizontal Line Score')
            ax.set_ylabel('Count')
            ax.set_title(f'Busby & Lazzati Score Distribution (N={len(valid)})')
            ax.legend()
            fig.tight_layout()
            fig.savefig(os.path.join(PLOTS_DIR, 'score_histogram.png'), dpi=150)
            plt.close(fig)

        # Failures histogram
        valid_failures = res_table[res_table['FAILURES'] >= 0]
        if len(valid_failures) > 0:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(valid_failures['FAILURES'], bins=50, edgecolor='black',
                    alpha=0.7, color='steelblue')
            ax.axvline(3, color='red', ls='--', lw=2, label='Threshold = 3 failures')
            ax.set_xlabel('Total Failure Points')
            ax.set_ylabel('Count')
            ax.set_title(f'Failure Point Distribution (N={len(valid_failures)})')
            ax.legend()
            fig.tight_layout()
            fig.savefig(os.path.join(PLOTS_DIR, 'failures_histogram.png'), dpi=150)
            plt.close(fig)

    print(f"{'='*60}")
