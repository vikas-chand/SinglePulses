#!/usr/bin/env python
"""
Phase 3: Bayesian blocks time binning (Burgess 2019 method).

For each single-pulse GRB (from Phase 2 classification):
1. Load TTE data via 3ML TimeSeriesBuilder for brightest NaI
2. Fit polynomial background using GBM catalog background intervals
3. Run Bayesian blocks binning (p0=0.01) with background model
4. Filter bins by significance (>3σ)
5. Apply same time bins to additional NaI detectors + BGO
6. Export PHA files for all detectors
7. Save diagnostic plots with background model + Bayesian blocks overlay

Multi-detector approach follows Burgess et al. (2014).
Reference: Burgess 2019
"""

import os
import sys
import glob
import warnings
import numpy as np
from astropy.io import fits
from astropy.table import Table

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
warnings.filterwarnings('ignore')

from threeML import TimeSeriesBuilder

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')
PHA_DIR = os.path.join(BASE_DIR, 'data', 'pha')
os.makedirs(PHA_DIR, exist_ok=True)
os.makedirs(os.path.join(PLOTS_DIR, 'bayesian_blocks'), exist_ok=True)

# Parameters
P0 = 0.01               # Bayesian blocks false-positive rate
SIG_THRESHOLD = 3.0      # minimum significance per bin (σ)

# NaI detectors on each side of the spacecraft
LOW_SIDE = {'n0', 'n1', 'n2', 'n3', 'n4', 'n5'}   # -> BGO b0
HIGH_SIDE = {'n6', 'n7', 'n8', 'n9', 'na', 'nb'}   # -> BGO b1


def select_detectors(det_str, brightest):
    """Select additional NaI detectors (beyond brightest) + BGO.

    Parameters
    ----------
    det_str : str
        Comma-separated NaI detector names from catalog.
    brightest : str
        The brightest NaI detector (already used for BB).

    Returns
    -------
    additional_nai : list of str
        Up to 2 additional NaI detectors.
    bgo : str
        'b0' or 'b1' based on majority side.
    all_nai : list of str
        All NaI detectors (brightest + additional).
    """
    nai_dets = [d.strip() for d in det_str.split(',')][:3]

    # Determine BGO: b0 if majority NaI are on n0-n5 side, else b1
    n_low = sum(1 for d in nai_dets if d in LOW_SIDE)
    bgo = 'b0' if n_low >= len(nai_dets) - n_low else 'b1'

    # Additional NaI = all except brightest
    additional_nai = [d for d in nai_dets if d != brightest]

    return additional_nai, bgo, nai_dets


def run_bayesian_blocks(trigger, det, t90, t90_start,
                        bkg_neg_start, bkg_neg_stop,
                        bkg_pos_start, bkg_pos_stop,
                        data_dir):
    """
    Run Bayesian blocks binning on the brightest NaI detector.

    Uses the GBM catalog background intervals for polynomial fitting.

    Returns dict with results, or raises on failure.
    """
    grb_dir = os.path.join(data_dir, trigger)

    # Find TTE and RSP files
    tte_files = glob.glob(os.path.join(grb_dir, f'glg_tte_{det}_*.fit.gz'))
    rsp_files = glob.glob(os.path.join(grb_dir, f'glg_cspec_{det}_*.rsp*'))

    if not tte_files or not rsp_files:
        raise FileNotFoundError(f"Missing TTE or RSP for {trigger} det {det}")

    tte_file = tte_files[0]
    rsp_file = rsp_files[0]

    # Create TimeSeriesBuilder
    tsb = TimeSeriesBuilder.from_gbm_tte(
        det, tte_file, rsp_file=rsp_file, verbose=False
    )

    # Background intervals from GBM catalog
    burst_start = t90_start
    burst_stop = t90_start + t90

    bkg_str_neg = f'{bkg_neg_start:.3f}-{bkg_neg_stop:.3f}'
    bkg_str_pos = f'{bkg_pos_start:.3f}-{bkg_pos_stop:.3f}'

    tsb.set_background_interval(bkg_str_neg, bkg_str_pos)

    # Set active interval to T90
    tsb.set_active_time_interval(f'{burst_start:.3f}-{burst_stop:.3f}')

    # Run Bayesian blocks
    tsb.create_time_bins(
        burst_start, burst_stop,
        method='bayesblocks',
        p0=P0,
        use_background=True
    )

    bins = tsb.bins
    all_starts = np.array(bins.starts)
    all_stops = np.array(bins.stops)
    n_bins_total = len(all_starts)

    # Get significance and counts per bin
    sigs = np.array(tsb.significance_per_interval)
    counts = np.array(tsb.total_counts_per_interval)
    bkg_counts = np.array(tsb.background_counts_per_interval)

    # Filter by significance
    mask_sig = sigs >= SIG_THRESHOLD
    n_bins_sig = int(np.sum(mask_sig))

    # Export PHA files for brightest detector
    pha_outdir = os.path.join(PHA_DIR, trigger)
    os.makedirs(pha_outdir, exist_ok=True)
    pha_written = False
    try:
        tsb.write_pha_from_binner(
            os.path.join(pha_outdir, f'{trigger}_{det}'),
            overwrite=True
        )
        pha_written = True
    except Exception:
        pass

    return {
        'tsb': tsb,
        'all_starts': all_starts,
        'all_stops': all_stops,
        'sigs': sigs,
        'counts': counts,
        'bkg_counts': bkg_counts,
        'n_bins_total': n_bins_total,
        'n_bins_sig': n_bins_sig,
        'pha_written': pha_written,
        'bkg_poly_order': tsb.background_poly_order,
    }


def export_additional_detector(trigger, other_det, tsb_brightest,
                               t90_start, t90,
                               bkg_neg_start, bkg_neg_stop,
                               bkg_pos_start, bkg_pos_stop,
                               data_dir):
    """Apply the brightest detector's time bins to another detector and export PHA.

    Parameters
    ----------
    trigger : str
    other_det : str
        Detector name (NaI or BGO).
    tsb_brightest : TimeSeriesBuilder
        The brightest detector's TSB with Bayesian blocks already computed.
    t90_start, t90 : float
    bkg_neg_start, bkg_neg_stop, bkg_pos_start, bkg_pos_stop : float
    data_dir : str

    Returns
    -------
    success : bool
    """
    grb_dir = os.path.join(data_dir, trigger)

    tte_files = glob.glob(os.path.join(grb_dir, f'glg_tte_{other_det}_*.fit.gz'))
    rsp_files = glob.glob(os.path.join(grb_dir, f'glg_cspec_{other_det}_*.rsp*'))

    if not tte_files or not rsp_files:
        return False

    tte_file = tte_files[0]
    rsp_file = rsp_files[0]

    burst_start = t90_start
    burst_stop = t90_start + t90

    bkg_str_neg = f'{bkg_neg_start:.3f}-{bkg_neg_stop:.3f}'
    bkg_str_pos = f'{bkg_pos_start:.3f}-{bkg_pos_stop:.3f}'

    tsb_other = TimeSeriesBuilder.from_gbm_tte(
        other_det, tte_file, rsp_file=rsp_file, verbose=False
    )
    tsb_other.set_background_interval(bkg_str_neg, bkg_str_pos)
    tsb_other.set_active_time_interval(f'{burst_start:.3f}-{burst_stop:.3f}')

    # Copy time bins from brightest detector
    tsb_other.read_bins(tsb_brightest)

    # Export PHA
    pha_outdir = os.path.join(PHA_DIR, trigger)
    os.makedirs(pha_outdir, exist_ok=True)
    tsb_other.write_pha_from_binner(
        os.path.join(pha_outdir, f'{trigger}_{other_det}'),
        overwrite=True
    )
    return True


def plot_bayesian_blocks(trigger, det, res, t90_start, t90,
                         bkg_neg_start, bkg_neg_stop,
                         bkg_pos_start, bkg_pos_stop, outpath):
    """
    Diagnostic plot with:
    - Top: light curve with background model and Bayesian block bins
    - Bottom: significance per bin
    """
    all_starts = res['all_starts']
    all_stops = res['all_stops']
    sigs = res['sigs']
    counts = res['counts']
    bkg_counts = res['bkg_counts']
    widths = all_stops - all_starts

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8),
                                    gridspec_kw={'height_ratios': [3, 1]},
                                    sharex=True)

    # --- Top panel: light curve + background model + BB bins ---
    # Total count rate per bin
    rate = counts / widths
    bkg_rate = bkg_counts / widths
    net_rate = rate - bkg_rate
    centers = 0.5 * (all_starts + all_stops)

    # Plot net rate as bars colored by significance
    for j in range(len(all_starts)):
        color = 'steelblue' if sigs[j] >= SIG_THRESHOLD else 'lightgray'
        ax1.bar(all_starts[j], net_rate[j], width=widths[j], align='edge',
                color=color, edgecolor='black', linewidth=0.5, alpha=0.8)

    # Overplot background rate as a step line
    ax1.step(np.append(all_starts, all_stops[-1]),
             np.append(bkg_rate, bkg_rate[-1]),
             where='post', color='red', lw=1.5, ls='--', label='Background model')

    # Mark T90 interval
    ax1.axvline(t90_start, color='orange', ls=':', lw=1, alpha=0.7)
    ax1.axvline(t90_start + t90, color='orange', ls=':', lw=1, alpha=0.7)

    # Mark background intervals
    ax1.axvspan(bkg_neg_start, bkg_neg_stop, alpha=0.05, color='red',
                label='Bkg intervals')
    ax1.axvspan(bkg_pos_start, bkg_pos_stop, alpha=0.05, color='red')

    ax1.set_ylabel('Count rate (cts/s)')
    ax1.set_title(f'{trigger} ({det}) — Bayesian Blocks: '
                   f'{res["n_bins_total"]} total, {res["n_bins_sig"]} sig (>{SIG_THRESHOLD}σ)  |  '
                   f'bkg poly order={res["bkg_poly_order"]}')
    ax1.legend(fontsize=8, loc='upper right')

    # --- Bottom panel: significance ---
    colors = ['green' if s >= SIG_THRESHOLD else 'red' for s in sigs]
    ax2.bar(all_starts, sigs, width=widths, align='edge',
            color=colors, edgecolor='black', linewidth=0.5, alpha=0.8)
    ax2.axhline(SIG_THRESHOLD, color='red', ls='--', lw=1,
                label=f'{SIG_THRESHOLD}σ threshold')
    ax2.set_ylabel('Significance (σ)')
    ax2.set_xlabel('Time since trigger (s)')
    ax2.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


# ==========================================================================
# Main
# ==========================================================================
if __name__ == '__main__':
    # Load horizontal line results — focus on single-pulse GRBs
    hl_path = os.path.join(RESULTS_DIR, 'horizontal_line_results.ecsv')
    if not os.path.exists(hl_path):
        print("ERROR: Run 03_horizontal_line.py first")
        sys.exit(1)

    hl_results = Table.read(hl_path, format='ascii.ecsv')
    single_pulse = hl_results[hl_results['CLASSIFICATION'] == 'single']
    print(f"Single-pulse GRBs to process: {len(single_pulse)}")

    # Load full sample for T90_START, background intervals, and NAI_DETECTORS
    sample = Table.read(os.path.join(RESULTS_DIR, 'grb_sample.ecsv'),
                        format='ascii.ecsv')

    results = []
    n_processed = 0
    n_failed = 0

    for i, row in enumerate(single_pulse):
        trigger = str(row['TRIGGER_NAME']).strip()
        det = str(row['DETECTOR']).strip()  # brightest NaI
        t90 = float(row['T90'])

        # Get T90_START, background intervals, and detector list from main sample
        match = sample[sample['TRIGGER_NAME'] == trigger]
        if len(match) == 0:
            print(f"[SKIP] {trigger}: not found in sample table")
            n_failed += 1
            continue

        t90_start = float(match['T90_START'][0])
        bkg_neg_start = float(match['BKG_NEG_START'][0])
        bkg_neg_stop = float(match['BKG_NEG_STOP'][0])
        bkg_pos_start = float(match['BKG_POS_START'][0])
        bkg_pos_stop = float(match['BKG_POS_STOP'][0])
        det_str = str(match['NAI_DETECTORS'][0]).strip()

        # Determine additional detectors + BGO
        additional_nai, bgo, all_nai = select_detectors(det_str, det)
        additional_dets = additional_nai + [bgo]

        print(f"[{i+1}/{len(single_pulse)}] {trigger} (det={det}, "
              f"additional={','.join(additional_dets)}, T90={t90:.1f}s)...",
              end=' ', flush=True)

        try:
            # Step 1: Run BB on brightest NaI (unchanged)
            res = run_bayesian_blocks(
                trigger, det, t90, t90_start,
                bkg_neg_start, bkg_neg_stop,
                bkg_pos_start, bkg_pos_stop,
                DATA_DIR
            )

            # Step 2: Apply same time bins to additional detectors
            dets_with_pha = [det] if res['pha_written'] else []

            for other_det in additional_dets:
                try:
                    ok = export_additional_detector(
                        trigger, other_det, res['tsb'],
                        t90_start, t90,
                        bkg_neg_start, bkg_neg_stop,
                        bkg_pos_start, bkg_pos_stop,
                        DATA_DIR
                    )
                    if ok:
                        dets_with_pha.append(other_det)
                except Exception as e:
                    print(f"\n    [WARN] {other_det}: {e}", end='')

            results.append({
                'NAME': str(row['NAME']),
                'TRIGGER_NAME': trigger,
                'T90': t90,
                'DETECTOR': det,
                'HL_SCORE': float(row['SCORE']),
                'BB_BINS_TOTAL': res['n_bins_total'],
                'BB_BINS_SIG': res['n_bins_sig'],
                'MEAN_SIGNIFICANCE': float(np.mean(res['sigs'])),
                'BKG_POLY_ORDER': res['bkg_poly_order'],
                'PHA_WRITTEN': res['pha_written'],
                'DETECTORS_PHA': ','.join(dets_with_pha),
                'BGO_DETECTOR': bgo,
            })

            # Diagnostic plot (brightest detector only)
            plot_outpath = os.path.join(PLOTS_DIR, 'bayesian_blocks',
                                        f'{trigger}_bb.png')
            plot_bayesian_blocks(trigger, det, res, t90_start, t90,
                                 bkg_neg_start, bkg_neg_stop,
                                 bkg_pos_start, bkg_pos_stop, plot_outpath)

            n_processed += 1
            print(f"{res['n_bins_total']} bins ({res['n_bins_sig']} sig), "
                  f"poly_order={res['bkg_poly_order']}, "
                  f"PHA: {','.join(dets_with_pha)} ({len(dets_with_pha)} dets)")

        except Exception as e:
            print(f"FAILED: {e}")
            n_failed += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Processed: {n_processed}, Failed: {n_failed}")

    if results:
        res_table = Table(results)
        print(f"\nBayesian blocks statistics for single-pulse GRBs:")
        print(f"  Total bins:  mean={np.mean(res_table['BB_BINS_TOTAL']):.1f}, "
              f"median={np.median(res_table['BB_BINS_TOTAL']):.0f}, "
              f"range={res_table['BB_BINS_TOTAL'].min()}-{res_table['BB_BINS_TOTAL'].max()}")
        print(f"  Sig bins:    mean={np.mean(res_table['BB_BINS_SIG']):.1f}, "
              f"median={np.median(res_table['BB_BINS_SIG']):.0f}, "
              f"range={res_table['BB_BINS_SIG'].min()}-{res_table['BB_BINS_SIG'].max()}")

        # Detector count summary
        det_counts = [len(r['DETECTORS_PHA'].split(',')) for r in results
                      if r['DETECTORS_PHA']]
        if det_counts:
            print(f"\n  Detectors with PHA: mean={np.mean(det_counts):.1f}, "
                  f"median={np.median(det_counts):.0f}, "
                  f"range={min(det_counts)}-{max(det_counts)}")

        # Per-GRB summary
        print(f"\nPer-GRB results:")
        for r in res_table:
            print(f"  {r['TRIGGER_NAME']:15s}  T90={r['T90']:7.1f}s  "
                  f"BB_total={r['BB_BINS_TOTAL']:3d}  BB_sig={r['BB_BINS_SIG']:3d}  "
                  f"mean_sig={r['MEAN_SIGNIFICANCE']:6.1f}σ  "
                  f"dets={r['DETECTORS_PHA']}")

        # Save
        outpath = os.path.join(RESULTS_DIR, 'bayesian_blocks_results.ecsv')
        res_table.write(outpath, format='ascii.ecsv', overwrite=True)
        print(f"\nResults saved to {outpath}")

    print(f"{'='*60}")
