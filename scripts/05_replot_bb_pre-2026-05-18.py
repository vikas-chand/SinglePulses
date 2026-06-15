#!/usr/bin/env python
"""
Replot Bayesian Blocks — independent BB per energy band from TTE data.

For each GRB, multi-panel plot:
  - Multiple NaI energy bands (8-50, 50-300, 300-900 keV)
  - Each panel: gray step TTE histogram + black step BB (independent per band)
  - Bottom panel: broadband significance per BB bin (from 3ML)
  - Shared x-axis, hspace=0

Uses astropy.stats.bayesian_blocks (fitness='events') per band,
same approach as GRB110721A notebook.
"""

import os
import sys
import glob
import warnings
import multiprocessing as mp
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.stats import bayesian_blocks

GRB_TIMEOUT = 180  # seconds per GRB

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')
os.makedirs(os.path.join(PLOTS_DIR, 'bayesian_blocks'), exist_ok=True)

P0 = 0.01
SIG_THRESHOLD = 3.0

# Energy bands for NaI (keV)
ENERGY_BANDS = [
    (300, 900),   # hard
    (50, 300),    # medium
    (8, 50),      # soft
]
BROADBAND = (8, 900)


def read_tte_events_by_band(tte_file):
    """
    Read TTE FITS and return dict of event times per energy band.
    """
    with fits.open(tte_file) as hdul:
        times = hdul['EVENTS'].data['TIME']
        pha   = hdul['EVENTS'].data['PHA']
        trigtime = hdul['PRIMARY'].header.get('TRIGTIME', 0.0)

        ebounds = hdul['EBOUNDS'].data
        chan_emin = ebounds['E_MIN']
        n_chan = len(chan_emin)

        valid = pha < n_chan
        energies = np.where(valid,
                            chan_emin[np.clip(pha, 0, n_chan - 1)],
                            0.0)
        t_rel = times - trigtime

        result = {}
        for (elo, ehi) in ENERGY_BANDS:
            mask = valid & (energies >= elo) & (energies < ehi)
            result[(elo, ehi)] = t_rel[mask]

        mask_bb = valid & (energies >= BROADBAND[0]) & (energies < BROADBAND[1])
        result['broadband'] = t_rel[mask_bb]

        return result


def _run_3ml_worker(args, result_dict):
    """Worker function for 3ML BB — runs in subprocess for timeout."""
    det, tte_file, rsp_file = args[:3]
    burst_start, burst_stop = args[3], args[4]
    bkg_neg_start, bkg_neg_stop = args[5], args[6]
    bkg_pos_start, bkg_pos_stop = args[7], args[8]

    warnings.filterwarnings('ignore')
    from threeML import TimeSeriesBuilder

    tsb = TimeSeriesBuilder.from_gbm_tte(
        det, tte_file, rsp_file=rsp_file, verbose=False
    )
    tsb.set_background_interval(
        f'{bkg_neg_start:.3f}-{bkg_neg_stop:.3f}',
        f'{bkg_pos_start:.3f}-{bkg_pos_stop:.3f}'
    )
    tsb.set_active_time_interval(f'{burst_start:.3f}-{burst_stop:.3f}')
    tsb.create_time_bins(burst_start, burst_stop,
                         method='bayesblocks', p0=P0, use_background=True)

    result_dict['bb_starts'] = np.array(tsb.bins.starts).tolist()
    result_dict['bb_stops'] = np.array(tsb.bins.stops).tolist()
    result_dict['sigs'] = np.array(tsb.significance_per_interval).tolist()
    result_dict['poly_order'] = tsb.background_poly_order


def run_3ml_with_timeout(det, tte_file, rsp_file,
                         burst_start, burst_stop,
                         bkg_neg_start, bkg_neg_stop,
                         bkg_pos_start, bkg_pos_stop,
                         timeout=GRB_TIMEOUT):
    """Run 3ML BB in a subprocess with real timeout."""
    manager = mp.Manager()
    result_dict = manager.dict()

    args = (det, tte_file, rsp_file,
            burst_start, burst_stop,
            bkg_neg_start, bkg_neg_stop,
            bkg_pos_start, bkg_pos_stop)

    proc = mp.Process(target=_run_3ml_worker, args=(args, result_dict))
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=5)
        return None

    if 'bb_starts' not in result_dict:
        return None

    return {
        'bb_starts': np.array(result_dict['bb_starts']),
        'bb_stops': np.array(result_dict['bb_stops']),
        'sigs': np.array(result_dict['sigs']),
        'poly_order': result_dict['poly_order'],
    }


def plot_bb_multiband(trigger, det, t90, t90_start,
                      bkg_neg_start, bkg_neg_stop,
                      bkg_pos_start, bkg_pos_stop,
                      data_dir, outpath):
    """
    Multi-panel BB plot with independent BB per energy band.
    """
    grb_dir = os.path.join(data_dir, trigger)

    tte_files = glob.glob(os.path.join(grb_dir, f'glg_tte_{det}_*.fit.gz'))
    rsp_files = glob.glob(os.path.join(grb_dir, f'glg_cspec_{det}_*.rsp*'))
    if not tte_files or not rsp_files:
        raise FileNotFoundError(f"Missing TTE or RSP for {trigger}")

    # --- 1. Read TTE events per energy band ---
    events_by_band = read_tte_events_by_band(tte_files[0])

    # --- 2. 3ML: background + BB (broadband, for significance) ---
    burst_start = t90_start
    burst_stop  = t90_start + t90

    ml_result = run_3ml_with_timeout(
        det, tte_files[0], rsp_files[0],
        burst_start, burst_stop,
        bkg_neg_start, bkg_neg_stop,
        bkg_pos_start, bkg_pos_stop
    )

    has_sig = ml_result is not None
    if has_sig:
        bb_starts = ml_result['bb_starts']
        bb_stops  = ml_result['bb_stops']
        sigs      = ml_result['sigs']
        bb_widths = bb_stops - bb_starts
        n_total   = len(bb_starts)
        n_sig     = int(np.sum(sigs >= SIG_THRESHOLD))
        poly_order = ml_result['poly_order']

    # --- 3. Time range and fine bins ---
    # Wide enough to include background intervals
    plot_tmin = min(bkg_neg_start - 2.0, burst_start - max(0.15 * t90, 2.0))
    plot_tmax = max(bkg_pos_stop + 2.0, burst_stop + max(0.15 * t90, 2.0))

    if t90 < 5:
        dt = 0.064
    elif t90 < 30:
        dt = 0.128
    elif t90 < 100:
        dt = 0.256
    elif t90 < 300:
        dt = 0.5
    else:
        dt = 1.0

    fine_bins = np.arange(plot_tmin, plot_tmax + dt, dt)

    # --- 4. Independent BB per energy band ---
    # BB on burst region + margin (not full bkg range — too many events)
    bb_margin = max(0.2 * t90, 5.0)
    bb_tmin = burst_start - bb_margin
    bb_tmax = burst_stop + bb_margin

    band_bb_edges = {}
    for band_key in ENERGY_BANDS:
        evts = events_by_band[band_key]
        evts_filt = evts[(evts >= bb_tmin) & (evts <= bb_tmax)]
        if len(evts_filt) > 10:
            try:
                edges = bayesian_blocks(evts_filt, fitness='events', p0=P0)
                band_bb_edges[band_key] = edges
            except Exception:
                band_bb_edges[band_key] = None
        else:
            band_bb_edges[band_key] = None

    # =====================================================================
    # PLOT
    # =====================================================================
    n_bands = len(ENERGY_BANDS)
    n_panels = n_bands + (1 if has_sig else 0)

    fig = plt.figure(figsize=(10, 2.5 * n_panels))
    height_ratios = [1] * n_bands + ([0.6] if has_sig else [])
    gs = GridSpec(n_panels, 1, figure=fig, hspace=0.0,
                  height_ratios=height_ratios)

    axes = [fig.add_subplot(gs[k, 0]) for k in range(n_panels)]
    for ax in axes[1:]:
        ax.sharex(axes[0])

    # --- Energy band panels ---
    for idx, (elo, ehi) in enumerate(ENERGY_BANDS):
        ax = axes[idx]
        evts = events_by_band[(elo, ehi)]

        # Gray step: fine TTE histogram
        fine_counts, _ = np.histogram(evts, bins=fine_bins)
        fine_rates = fine_counts / dt
        ax.step(fine_bins[:-1], fine_rates, where='post',
                color='gray', linewidth=0.8, alpha=0.5)

        # Black step: independent BB for this band (full range)
        bb_edges = band_bb_edges[(elo, ehi)]
        if bb_edges is not None and len(bb_edges) > 1:
            bb_counts, _ = np.histogram(evts, bins=bb_edges)
            bb_widths_band = np.diff(bb_edges)
            bb_rates_band = bb_counts / bb_widths_band

            # Use full edges array so the step extends to the last bin's right edge
            plot_x = np.append(bb_edges[:-1], bb_edges[-1])
            plot_y = np.append(bb_rates_band, bb_rates_band[-1])
            ax.step(plot_x, plot_y, where='post',
                    color='black', linewidth=2, label='Bayesian Blocks')

        # T90 markers
        if idx == 0:
            ax.axvline(burst_start, color='blue', ls='--', lw=0.8, alpha=0.6,
                       label='T90')
            ax.axvline(burst_stop, color='blue', ls='--', lw=0.8, alpha=0.6)
        else:
            ax.axvline(burst_start, color='blue', ls='--', lw=0.8, alpha=0.6)
            ax.axvline(burst_stop, color='blue', ls='--', lw=0.8, alpha=0.6)

        # Label
        if elo >= 300:
            band_label = '0.3-0.9 MeV'
        else:
            band_label = f'{elo}-{ehi} keV'

        # Build legend manually
        handles, labels = ax.get_legend_handles_labels()
        band_handle = Line2D([0], [0], color='gray', lw=0.8, alpha=0.5)
        legend_handles = [band_handle] + handles
        legend_labels = [band_label] + labels
        ax.legend(legend_handles, legend_labels, loc='upper right', fontsize=8)
        ax.set_ylabel('Counts s$^{-1}$', fontsize=10)
        ax.set_xlim(plot_tmin, plot_tmax)
        ymax = fine_rates.max() * 1.15 if fine_rates.max() > 0 else 1
        ax.set_ylim(0, ymax)
        ax.minorticks_on()
        ax.tick_params(axis='both', which='major', length=5, labelsize=9)
        ax.tick_params(axis='both', which='minor', length=3)
        ax.tick_params(labelbottom=False)

    # --- Bottom panel: broadband significance (from 3ML) ---
    if has_sig:
        ax_sig = axes[-1]
        colors_sig = ['#2ca02c' if s >= SIG_THRESHOLD else '#d62728' for s in sigs]
        ax_sig.bar(bb_starts, sigs, width=bb_widths, align='edge',
                   color=colors_sig, edgecolor='black', linewidth=0.5, alpha=0.85)
        ax_sig.axhline(SIG_THRESHOLD, color='red', ls='--', lw=1,
                       label=f'{SIG_THRESHOLD:.0f}σ')

        # Background intervals shaded in salmon
        ax_sig.axvspan(bkg_neg_start, bkg_neg_stop,
                       color='salmon', alpha=0.25, label='Bkg intervals')
        ax_sig.axvspan(bkg_pos_start, bkg_pos_stop,
                       color='salmon', alpha=0.25)

        ax_sig.set_ylabel('Sig (σ)', fontsize=10)
        ax_sig.set_xlabel('Time since trigger (s)', fontsize=11)
        ax_sig.legend(loc='upper right', fontsize=8)
        ax_sig.minorticks_on()
        ax_sig.tick_params(axis='both', which='major', length=5, labelsize=9)
        ax_sig.tick_params(axis='both', which='minor', length=3)
        sig_max = max(np.max(np.abs(sigs)) * 1.15, SIG_THRESHOLD * 2)
        sig_min = min(0, np.min(sigs) * 1.15) if np.any(sigs < 0) else 0
        ax_sig.set_ylim(sig_min, sig_max)
    else:
        axes[-1].set_xlabel('Time since trigger (s)', fontsize=11)
        axes[-1].tick_params(labelbottom=True)

    # Title
    if has_sig:
        title = (f'{trigger}  ({det})  —  BB: {n_total} bins (broadband), '
                 f'{n_sig} sig (>{SIG_THRESHOLD:.0f}σ)  |  bkg poly order {poly_order}')
    else:
        title = f'{trigger}  ({det})  —  3ML timed out, energy-band BB only'

    fig.suptitle(title, fontsize=12, fontweight='bold', y=0.98)

    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close(fig)

    if has_sig:
        return {'n_bins_total': n_total, 'n_bins_sig': n_sig, 'poly_order': poly_order}
    else:
        return {'n_bins_total': 0, 'n_bins_sig': 0, 'poly_order': -1}


# ===========================================================================
if __name__ == '__main__':
    mp.set_start_method('fork', force=True)

    bb = Table.read(os.path.join(RESULTS_DIR, 'bayesian_blocks_results.ecsv'),
                    format='ascii.ecsv')
    sample = Table.read(os.path.join(RESULTS_DIR, 'grb_sample.ecsv'),
                        format='ascii.ecsv')

    print(f"Replotting {len(bb)} GRBs with independent BB per energy band...")

    n_ok = 0
    n_fail = 0
    n_timeout = 0

    for i, row in enumerate(bb):
        trigger = str(row['TRIGGER_NAME']).strip()
        det = str(row['DETECTOR']).strip()
        t90 = float(row['T90'])

        match = sample[sample['TRIGGER_NAME'] == trigger]
        if len(match) == 0:
            n_fail += 1
            continue

        t90_start     = float(match['T90_START'][0])
        bkg_neg_start = float(match['BKG_NEG_START'][0])
        bkg_neg_stop  = float(match['BKG_NEG_STOP'][0])
        bkg_pos_start = float(match['BKG_POS_START'][0])
        bkg_pos_stop  = float(match['BKG_POS_STOP'][0])

        outpath = os.path.join(PLOTS_DIR, 'bayesian_blocks', f'{trigger}_bb.png')
        print(f"  [{i+1}/{len(bb)}] {trigger} (T90={t90:.1f}s)...", end=' ', flush=True)

        try:
            res = plot_bb_multiband(
                trigger, det, t90, t90_start,
                bkg_neg_start, bkg_neg_stop,
                bkg_pos_start, bkg_pos_stop,
                DATA_DIR, outpath
            )
            if res['poly_order'] < 0:
                n_timeout += 1
                print(f"OK (3ML timeout, BB per band only)")
            else:
                n_ok += 1
                print(f"OK ({res['n_bins_sig']} sig bins)")
        except Exception as e:
            n_fail += 1
            print(f"FAILED: {e}")

    print(f"\nDone: {n_ok} OK, {n_timeout} timeout (partial), {n_fail} failed")
