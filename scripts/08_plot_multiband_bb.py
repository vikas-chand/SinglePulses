#!/usr/bin/env python
"""
LATBright-Fig.6-style multi-band BB plot — generalized for batch over the
single-pulse GRB sample.

For each (trigger, brightest-NaI) pair, produces a 4-panel stacked figure:
  (a) 300-900 keV LC + per-band event-mode BB
  (b) 50-300 keV   LC + per-band event-mode BB
  (c) 8-50 keV     LC + per-band event-mode BB
  (d) per-block significance bars from broadband background-aware BB
      (3ML use_background=True + Phase-A sub-3σ merge)
T90 (catalog) shaded across all panels.

Style: LATBright/GRB260226A/plot_config.py:apply_pub_style() + PUB dict.

Usage:
  # One GRB (brightest NaI from single_pulse_grbs.ecsv, else specify --det):
  python 08_plot_multiband_bb.py --trigger bn200607921
  python 08_plot_multiband_bb.py --trigger bn200607921 --det n6

  # Full batch over all single-pulse GRBs:
  python 08_plot_multiband_bb.py --all-single-pulse
  python 08_plot_multiband_bb.py --all-single-pulse --limit 5     # first 5 only
  python 08_plot_multiband_bb.py --all-single-pulse --skip-existing

Outputs:
  plots/multiband_bb/<trigger>_<det>_multiband.png
  logs/multiband_bb_<DATE>.log
  results/multiband_bb_summary.ecsv

Run in the threeML env (or with CALDB env vars exported).
"""
import os
import sys
import glob
import argparse
import warnings
import traceback
from datetime import datetime

import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.stats import bayesian_blocks

os.environ.setdefault('OMP_NUM_THREADS', '1')
warnings.filterwarnings('ignore')

# ---- CALDB env fallback ----
_FD_DEFAULT = '/Users/salim/anaconda3/envs/threeML/share/fermitools'
if not os.environ.get('CALDB'):
    os.environ['FERMI_DIR'] = _FD_DEFAULT
    os.environ['CALDB'] = _FD_DEFAULT + '/data/caldb'
    os.environ['CALDBALIAS'] = _FD_DEFAULT + '/data/caldb/software/tools/alias_config.fits'
    os.environ['CALDBCONFIG'] = _FD_DEFAULT + '/data/caldb/software/tools/caldb.config'
    os.environ['CALDBROOT'] = _FD_DEFAULT + '/data/caldb'
    os.environ['EXTFILESSYS'] = _FD_DEFAULT + '/refdata/fermi'

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ---- LATBright publication style ----
_LATBRIGHT = '/Users/salim/Desktop/LATBright/GRB260226A'
if _LATBRIGHT not in sys.path:
    sys.path.insert(0, _LATBRIGHT)
from plot_config import apply_pub_style, PUB, step_from_bb  # noqa: E402
apply_pub_style()

# ---- Paths ----
BASE = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE, 'data')
RESULTS_DIR = os.path.join(BASE, 'results')
PLOTS_DIR = os.path.join(BASE, 'plots', 'multiband_bb')
LOGS_DIR = os.path.join(BASE, 'logs')
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

SAMPLE_PATH = os.path.join(RESULTS_DIR, 'grb_sample.ecsv')
SINGLE_PATH = os.path.join(RESULTS_DIR, 'single_pulse_grbs.ecsv')
BKG_PROTO_PATH = os.path.join(RESULTS_DIR, 'background_intervals_prototype.ecsv')
BKG_MAIN_PATH = os.path.join(RESULTS_DIR, 'background_intervals.ecsv')

# ---- Conventions ----
ENERGY_BANDS = [(300, 900), (50, 300), (8, 50)]
BAND_LABELS = ['300-900 keV', '50-300 keV', '8-50 keV']
PANEL_LETTERS = ['(a)', '(b)', '(c)']
LC_BIN_S = 0.256             # for the per-band LC display panels
TINT_BIN_S = 0.064           # 64 ms — finer bins for T_INT cumsum-saturation
P0 = 0.01
SIG_THRESHOLD = 3.0           # Phase-A merge threshold
TINT_START_THRESH = 2.0       # σ — first block ≥ this is T_INT_START
TINT_STOP_THRESH  = 1.5       # σ — run of N consecutive < this defines STOP
TINT_STOP_RUN_N   = (3, 2, 1) # fallback chain for the stop-run length
PLOT_TMIN, PLOT_TMAX = -100, 200


# ============================================================================
# Background interval loader — fallback chain
# ============================================================================

def load_bkg_for(trigger, det, sample_row, bkg_proto, bkg_main):
    """
    Returns (pre_a, pre_b, post_a, post_b, source).
    Requires a PER-DETECTOR bkg entry (no legacy fallback). Lookup order:
      1. results/background_intervals_prototype.ecsv (source='proto')
      2. results/background_intervals.ecsv          (source='main')

    Raises KeyError if neither contains a row for (trigger, det).
    This is by design: every GRB must go through Phase 0
    (scripts/00_prototype_one_burst.py) so its per-detector bkg windows
    are AI/human-reviewed before any BB/plotting runs. The legacy
    `BKG_*_START` columns in grb_sample.ecsv are NOT accepted (their
    provenance is out-of-tree gtburst clicks; same window shared across
    all detectors regardless of geometry).
    """
    for tab, src in [(bkg_proto, 'proto'), (bkg_main, 'main')]:
        if tab is None:
            continue
        m = (tab['TRIGGER_NAME'] == trigger) & (tab['DETECTOR'] == det)
        if m.any():
            r = tab[m][0]
            return (float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP']),
                    float(r['BKG_POS_START']), float(r['BKG_POS_STOP']), src)
    raise KeyError(
        f'No per-detector bkg for ({trigger}, {det}). '
        f'Run scripts/00_prototype_one_burst.py --trigger {trigger} first '
        f'(legacy grb_sample.ecsv BKG_*_START columns are NOT accepted).'
    )


# ============================================================================
# Phase-A merge — sub-3σ blocks → lower-sig flanking neighbor
# (copied from scripts/00_prototype_one_burst.py)
# ============================================================================

def merge_subthreshold_blocks(tsb, threshold=3.0, max_iter=200):
    starts = list(np.array(tsb.bins.starts))
    stops = list(np.array(tsb.bins.stops))
    sigs = list(np.array(tsb.significance_per_interval))
    is_merged = [False] * len(starts)
    cnt = [1] * len(starts)
    iters = 0
    while iters < max_iter:
        iters += 1
        if len(sigs) <= 1 or all(s >= threshold for s in sigs):
            break
        i = next((k for k, s in enumerate(sigs) if s < threshold), None)
        if i is None:
            break
        if i == 0:
            partner = 1
        elif i == len(sigs) - 1:
            partner = i - 1
        else:
            partner = (i - 1) if sigs[i - 1] < sigs[i + 1] else (i + 1)
        a, b = sorted([i, partner])
        starts[a] = min(starts[a], starts[b])
        stops[a] = max(stops[a], stops[b])
        is_merged[a] = True
        cnt[a] = cnt[a] + cnt[b]
        del starts[b]; del stops[b]; del is_merged[b]; del cnt[b]
        tsb.create_time_bins(method='custom', start=list(starts), stop=list(stops))
        sigs = list(np.array(tsb.significance_per_interval))
    return starts, stops, sigs, is_merged, cnt, iters


# ============================================================================
# Per-GRB plot
# ============================================================================

def compute_t_int_cumsum_saturation(bin_edges, counts_per_bin, bkg_counts_per_bin,
                                    n_mc=1000, seed=42,
                                    smooth_window=16, frac=0.03,
                                    min_consec_below=32, **kwargs):
    """
    Smoothed-rate-threshold T_INT (Salim, 2026-05-22).
    Walks outward from the peak of the smoothed bkg-subtracted LC; stops
    only after `min_consec_below` consecutive bins where smoothed rate <
    frac × peak rate (default 32 bins = 2 s at 64 ms, so brief inter-pulse
    gaps don't trigger STOP). Works on the cumsum DERIVATIVE so polyfit
    residual bias doesn't accumulate.
    """
    bin_edges = np.asarray(bin_edges, dtype=float)
    counts_per_bin = np.asarray(counts_per_bin, dtype=float)
    bkg_counts_per_bin = np.asarray(bkg_counts_per_bin, dtype=float)
    bin_centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    n_bins = len(bin_centres)
    if len(counts_per_bin) != n_bins or len(bkg_counts_per_bin) != n_bins:
        raise ValueError(
            f'bin_edges length {len(bin_edges)} inconsistent with '
            f'counts_per_bin length {len(counts_per_bin)}')

    def _smooth(x, window):
        if window <= 1:
            return x.astype(float)
        kernel = np.ones(window) / float(window)
        pad = window // 2
        padded = np.concatenate([x[pad-1::-1], x, x[:-pad-1:-1]])
        smoothed = np.convolve(padded, kernel, mode='valid')
        extra = len(smoothed) - len(x)
        lo = extra // 2
        return smoothed[lo:lo + len(x)]

    def _walk_one(walk, thr):
        """Single-sweep walk; stop after `min_consec_below` sub-threshold bins.
        Returns offset of last bin above threshold within `walk`."""
        run = 0
        last_above = 0
        for i in range(1, len(walk)):
            if walk[i] < thr:
                run += 1
                if run >= min_consec_below:
                    return last_above
            else:
                run = 0
                last_above = i
        return len(walk) - 1

    def _walk_to_threshold(net_smooth, ipk, direction, thr):
        """Walk to threshold + (only if a STRONG later/earlier peak exists)
        iteratively extend. Safety margin: a candidate "new peak" beyond
        the initial edge must reach >= 2 * thr (i.e. 2x the saturation
        threshold = 2*frac of main peak rate) before we extend. This
        prevents noise excursions at 1-1.5x thr from chaining T_INT
        out into pre/post-bkg regions."""
        n = len(net_smooth)
        ext_thr = 2.0 * thr   # extension requires stronger evidence
        if direction == 'forward':
            edge_idx = ipk + _walk_one(net_smooth[ipk:], thr)
            for _ in range(20):
                lo = edge_idx + 1
                if lo >= n: break
                if net_smooth[lo:].max() < ext_thr: break
                new_ipk = lo + int(np.argmax(net_smooth[lo:]))
                new_edge = new_ipk + _walk_one(net_smooth[new_ipk:], thr)
                if new_edge <= edge_idx: break
                edge_idx = new_edge
            return edge_idx
        else:
            edge_idx = ipk - _walk_one(net_smooth[ipk::-1], thr)
            for _ in range(20):
                hi = edge_idx - 1
                if hi < 0: break
                if net_smooth[:hi + 1].max() < ext_thr: break
                new_ipk = int(np.argmax(net_smooth[:hi + 1]))
                new_edge = new_ipk - _walk_one(net_smooth[new_ipk::-1], thr)
                if new_edge >= edge_idx: break
                edge_idx = new_edge
            return edge_idx

    def _one(net):
        if not np.any(net > 0):
            return None, None, None
        net_smooth = _smooth(net, smooth_window)
        ipk = int(np.argmax(net_smooth))
        peak_s = float(net_smooth[ipk])
        if peak_s <= 0:
            return None, None, None
        # Threshold = max(frac × peak, Fermi-style 4.5σ noise floor).
        # σ_smoothed = Poisson std of the smoothed bkg counts per bin.
        # 4.5σ matches the Fermi GBM trigger algorithm convention
        # (Paciesas+ 2012, von Kienlin+ 2014) — sufficiently low false-
        # alarm rate per bin to avoid triggering on noise excursions in
        # pre/post-burst regions while still catching weak burst edges.
        bkg_mean_per_bin = float(np.mean(bkg_counts_per_bin)) if len(bkg_counts_per_bin) else 0.0
        sigma_smoothed = (np.sqrt(max(bkg_mean_per_bin, 1.0)) /
                          np.sqrt(max(smooth_window, 1)))
        noise_floor = 4.5 * sigma_smoothed
        thr = max(frac * peak_s, noise_floor)
        i_stop = min(_walk_to_threshold(net_smooth, ipk, 'forward', thr), n_bins - 1)
        i_start = max(_walk_to_threshold(net_smooth, ipk, 'backward', thr), 0)
        return (float(bin_edges[i_start]),
                float(bin_edges[i_stop + 1]),
                float(bin_centres[ipk]))

    # Point estimate from the observed LC
    net_obs = counts_per_bin - bkg_counts_per_bin
    t_start, t_stop, t_peak = _one(net_obs)
    if t_start is None:
        return dict(t_start=None, t_stop=None, t_peak=None,
                    t_start_err=0.0, t_stop_err=0.0, n_mc=0)

    # MC uncertainty: Poisson-resample raw counts, re-subtract same bkg
    if n_mc >= 2:
        rng = np.random.default_rng(seed)
        starts = np.zeros(n_mc); stops = np.zeros(n_mc)
        valid = np.zeros(n_mc, dtype=bool)
        lam = np.maximum(counts_per_bin, 0)
        for i in range(n_mc):
            fake = rng.poisson(lam).astype(float)
            t_s, t_e, _ = _one(fake - bkg_counts_per_bin)
            if t_s is not None:
                starts[i], stops[i], valid[i] = t_s, t_e, True
        starts = starts[valid]; stops = stops[valid]
        t_start_err = float(np.std(starts)) if len(starts) else 0.0
        t_stop_err = float(np.std(stops)) if len(stops) else 0.0
    else:
        t_start_err = t_stop_err = 0.0

    return dict(t_start=t_start, t_stop=t_stop, t_peak=t_peak,
                t_start_err=t_start_err, t_stop_err=t_stop_err,
                n_mc=int(n_mc))


def compute_time_integrated_window(bb_starts, bb_sigs, post_start,
                                   start_thresh=TINT_START_THRESH,
                                   stop_thresh=TINT_STOP_THRESH,
                                   run_lengths=TINT_STOP_RUN_N):
    """
    Derive the time-integrated analysis window from BB blocks (sorted by
    T_START, all within the BB search window).

    START: T_START of the first block with sig ≥ start_thresh (default 2σ).
    PEAK:  index of the most-significant block AT OR AFTER i_start.
    STOP:  T_START of the first of N consecutive blocks all with
           sig < stop_thresh (default 1.5σ), searched FROM PEAK + 1
           onward (so a pre-peak dip cannot trigger an early stop).
           Try N in run_lengths order (default (3, 2, 1)). If no
           qualifying run exists before the search-window edge,
           STOP = post_start (burst stayed above threshold to the edge —
           captures EE tail).

    Returns (t_start, t_stop, n_blocks_inside, mean_sig_inside,
             i_peak, t_peak) or (None, ..., None, None) if no block
    ≥ start_thresh exists.
    """
    bb_starts = np.asarray(bb_starts, dtype=float)
    bb_sigs = np.asarray(bb_sigs, dtype=float)
    n = len(bb_sigs)
    if n == 0:
        return None, None, 0, 0.0, None, None
    above = np.where(bb_sigs >= start_thresh)[0]
    if len(above) == 0:
        return None, None, 0, 0.0, None, None
    i_start = int(above[0])
    t_start = float(bb_starts[i_start])

    # Peak block: argmax of significance at or after the start
    rel = int(np.argmax(bb_sigs[i_start:]))
    i_peak = i_start + rel
    t_peak = float(bb_starts[i_peak])

    # Search for stop-run starting AFTER the peak
    t_stop = float(post_start)
    for k in run_lengths:
        for j in range(i_peak + 1, n - k + 1):
            if all(bb_sigs[j + m] < stop_thresh for m in range(k)):
                t_stop = float(bb_starts[j])
                break
        else:
            continue
        break

    inside = (bb_starts >= t_start) & (bb_starts < t_stop)
    n_inside = int(inside.sum())
    mean_sig = float(bb_sigs[inside].mean()) if n_inside else 0.0
    return t_start, t_stop, n_inside, mean_sig, i_peak, t_peak


def find_tte(trigger, det):
    m = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_tte_{det}_*.fit.gz'))
    return m[0] if m else None


def find_rsp(trigger, det):
    m = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_cspec_{det}_*.rsp*'))
    return m[0] if m else None


def make_plot(trigger, det, sample_row, bkg_proto, bkg_main, outpath):
    """Render one PNG. Raises on failure. Returns summary dict."""
    tte = find_tte(trigger, det)
    rsp = find_rsp(trigger, det)
    if tte is None or rsp is None:
        raise FileNotFoundError(f'TTE or RSP missing for {trigger} {det}')

    pre_a, pre_b, post_a, post_b, src_tag = load_bkg_for(
        trigger, det, sample_row, bkg_proto, bkg_main)

    t90 = float(sample_row['T90'])
    t90_start = float(sample_row['T90_START'])
    t90_stop = t90_start + t90

    # ---- Read TTE events with per-bin energy ----
    with fits.open(tte) as hdul:
        evts = hdul['EVENTS'].data
        trigtime = hdul['PRIMARY'].header.get('TRIGTIME', 0.0)
        ebounds = hdul['EBOUNDS'].data
        chan_emin = ebounds['E_MIN']; chan_emax = ebounds['E_MAX']
        n_chan = len(chan_emin)
        pha = evts['PHA']; times = evts['TIME']
        valid = pha < n_chan
        e_lo = chan_emin[np.clip(pha, 0, n_chan - 1)]
        e_hi = chan_emax[np.clip(pha, 0, n_chan - 1)]
        t_rel = times - trigtime

    # ---- 3ML BB with use_background=True for the sig panel ----
    from threeML import TimeSeriesBuilder
    tsb = TimeSeriesBuilder.from_gbm_tte(det, tte, rsp_file=rsp, verbose=False)
    tsb.set_background_interval(f'{pre_a:.3f}-{pre_b:.3f}',
                                f'{post_a:.3f}-{post_b:.3f}')
    # BB search window from user-clicked bkg edges (pre_stop, post_start).
    # NO catalog T90 in any numerical step.
    burst_start = float(pre_b); burst_stop = float(post_a)
    tsb.set_active_time_interval(f'{burst_start:.3f}-{burst_stop:.3f}')
    tsb.create_time_bins(burst_start, burst_stop, method='bayesblocks',
                         p0=P0, use_background=True)

    # Use RAW Scargle BB output everywhere in this script — both for the
    # significance bar plot AND for the T_INT determination. Phase-A
    # sub-3σ merging belongs to the LATER spectral-analysis step, NOT
    # here (otherwise pre-burst sub-3σ blocks get absorbed into the first
    # burst block and the 2σ-START rule mis-fires at the BB search edge —
    # bug observed 2026-05-21 on bn200607921 n6).
    bb_starts = np.array(tsb.bins.starts).copy()
    bb_stops = np.array(tsb.bins.stops).copy()
    bb_sigs = np.array(tsb.significance_per_interval).copy()
    bb_widths = bb_stops - bb_starts
    bb_merged = np.zeros(len(bb_starts), dtype=bool)   # no merging here
    bb_cnt = np.ones(len(bb_starts), dtype=int)
    poly_order = int(getattr(tsb, 'background_poly_order', -1))

    # ---- Time-integrated analysis window (cumsum-saturation from peak) ----
    # Bin the 8-900 keV events at 1.024 s across the BB search window,
    # subtract the polyfit bkg model (per-bin integral), then run the
    # branched-cumsum-saturation algorithm.
    ts = tsb._time_series
    tint_bins = np.arange(burst_start, burst_stop + TINT_BIN_S, TINT_BIN_S)
    tint_centres = 0.5 * (tint_bins[:-1] + tint_bins[1:])
    in_8_900 = valid & (e_lo >= 8.0) & (e_hi <= 900.0)
    t_8_900 = t_rel[in_8_900]
    tint_counts, _ = np.histogram(t_8_900, bins=tint_bins)
    # Channel mask so bkg integral matches the LC's 8-900 keV band
    # (otherwise observed = 8-900 keV but bkg = broadband ⇒ negative-biased net).
    # We REQUIRE the masked polyfit integration; silently falling back to
    # broadband would re-introduce the energy-mismatch bug.
    chan_mask_8_900 = (chan_emin >= 8.0) & (chan_emax <= 900.0)
    def _bkg_in_band(t1, t2):
        return float(ts.get_total_poly_count(t1, t2, mask=chan_mask_8_900))
    try:
        _bkg_in_band(tint_bins[0], tint_bins[1])
    except TypeError as exc:
        raise RuntimeError(
            'Installed 3ML does not support mask= in get_total_poly_count. '
            'Upgrade 3ML or implement a manual masked sum over '
            'ts._polynomials[chan_mask] — silent broadband fallback would '
            'cause negatively-biased net counts.') from exc
    tint_bkg = np.array([_bkg_in_band(tint_bins[k], tint_bins[k+1])
                         for k in range(len(tint_centres))])
    tint = compute_t_int_cumsum_saturation(
        tint_bins, tint_counts.astype(float), tint_bkg,
        n_mc=1000)
    t_int_start = tint['t_start']
    t_int_stop = tint['t_stop']
    t_peak = tint['t_peak']
    t_int_start_err = tint['t_start_err']
    t_int_stop_err = tint['t_stop_err']
    n_int_blocks = int(np.sum((bb_starts >= (t_int_start or 0))
                              & (bb_starts < (t_int_stop or 0)))) if t_int_start else 0
    mean_int_sig = float(bb_sigs[(bb_starts >= (t_int_start or 0))
                                 & (bb_starts < (t_int_stop or 0))].mean()) \
                   if n_int_blocks else 0.0

    # ---- Figure ----
    fig = plt.figure(figsize=(PUB['figwidth'], 9.0))
    gs = GridSpec(4, 1, height_ratios=[1, 1, 1, 0.55], hspace=0.0,
                  left=0.11, right=0.97, top=0.96, bottom=0.07)
    axes_lc = [fig.add_subplot(gs[i]) for i in range(3)]
    ax_sig = fig.add_subplot(gs[3], sharex=axes_lc[0])
    for a in axes_lc[1:]:
        a.sharex(axes_lc[0])

    # Plot window adapts to T90 if huge bursts
    pad = max(60.0, 3.0 * t90)
    plot_tmin = max(PLOT_TMIN, t90_start - pad)
    plot_tmax = min(PLOT_TMAX, t90_stop + 2.0 * pad)
    # But keep at least the original window if catalog T90 fits inside it
    plot_tmin = min(plot_tmin, PLOT_TMIN)
    plot_tmax = max(plot_tmax, PLOT_TMAX)

    bins = np.arange(plot_tmin, plot_tmax + LC_BIN_S, LC_BIN_S)
    centers = 0.5 * (bins[:-1] + bins[1:])
    bb_event_window_min = max(plot_tmin, pre_a)
    bb_event_window_max = min(plot_tmax, post_b)

    for i, (band, label, letter) in enumerate(zip(ENERGY_BANDS, BAND_LABELS,
                                                  PANEL_LETTERS)):
        ax = axes_lc[i]
        band_lo, band_hi = band
        in_band = valid & (e_lo >= band_lo) & (e_hi <= band_hi)
        t_band = t_rel[in_band]
        counts, _ = np.histogram(t_band, bins=bins)
        rates = counts / LC_BIN_S
        ax.step(centers, rates, where='mid', color=PUB['color_fill'],
                lw=PUB['lw_reference'], alpha=0.9, zorder=2)

        t_for_bb = t_band[(t_band >= bb_event_window_min)
                          & (t_band <= bb_event_window_max)]
        if len(t_for_bb) > 20:
            try:
                edges = bayesian_blocks(t_for_bb, fitness='events', p0=P0)
                bc, _ = np.histogram(t_band, bins=edges)
                widths = np.diff(edges)
                rates_bb = bc / widths
                step_from_bb(ax, edges, rates_bb,
                             color=PUB['color_step'], lw=PUB['lw_primary'],
                             zorder=4)
            except Exception:
                pass

        # Mark derived time-integrated window with vertical dashed lines
        # (NO catalog T90 anywhere — pipeline is fully data-driven)
        if t_int_start is not None and t_int_stop is not None:
            ax.axvline(t_int_start, color=PUB['color_t90'],
                       ls='--', lw=PUB['lw_secondary'], alpha=0.8, zorder=1)
            ax.axvline(t_int_stop, color=PUB['color_t90'],
                       ls='--', lw=PUB['lw_secondary'], alpha=0.8, zorder=1)
        ax.text(0.015, 0.93, letter, transform=ax.transAxes,
                fontsize=PUB['panel_label_size'], weight='bold',
                va='top', ha='left')
        ax.text(0.985, 0.93, label, transform=ax.transAxes,
                fontsize=PUB['tick_size'], va='top', ha='right')
        ax.set_ylabel(r'Rate [cts s$^{-1}$]', fontsize=PUB['label_size'])
        ax.set_ylim(0, max(rates.max(), 1) * 1.10)
        if i < 2:
            plt.setp(ax.get_xticklabels(), visible=False)

    # ---- Sig panel ----
    sane = bb_widths >= 0.01
    colors = [PUB['color_nai_lo'] if (s >= SIG_THRESHOLD) and ok else '0.7'
              for s, ok in zip(bb_sigs, sane)]
    ax_sig.bar(bb_starts, bb_sigs, width=bb_widths, align='edge',
               color=colors, edgecolor='black', linewidth=0.5, alpha=0.85,
               zorder=2)
    ax_sig.axhline(SIG_THRESHOLD, color=PUB['color_hline'], ls='--',
                   lw=PUB['lw_secondary'], zorder=3)
    ax_sig.text(0.985, 0.92, r'$3\sigma$', transform=ax_sig.transAxes,
                fontsize=PUB['tick_size'], va='top', ha='right')
    ax_sig.text(0.015, 0.92, '(d)', transform=ax_sig.transAxes,
                fontsize=PUB['panel_label_size'], weight='bold',
                va='top', ha='left')
    if t_int_start is not None and t_int_stop is not None:
        ax_sig.axvline(t_int_start, color=PUB['color_t90'],
                       ls='--', lw=PUB['lw_secondary'], alpha=0.8, zorder=1)
        ax_sig.axvline(t_int_stop, color=PUB['color_t90'],
                       ls='--', lw=PUB['lw_secondary'], alpha=0.8, zorder=1)
    # Mark threshold lines used by the time-integrated rule
    ax_sig.axhline(TINT_START_THRESH, color='0.4', ls=':', lw=0.5,
                   alpha=0.5, zorder=1)
    ax_sig.axhline(TINT_STOP_THRESH, color='0.4', ls=':', lw=0.5,
                   alpha=0.5, zorder=1)
    ax_sig.set_ylabel(r'Sig [$\sigma$]', fontsize=PUB['label_size'])
    ax_sig.set_xlabel(r'Time since trigger $T_0$ [s]',
                      fontsize=PUB['label_size'])
    ax_sig.set_xlim(plot_tmin, plot_tmax)
    finite = bb_sigs[np.isfinite(bb_sigs)]
    ax_sig.set_ylim(0, max(finite.max() * 1.10 if len(finite) else 2 * SIG_THRESHOLD,
                           2 * SIG_THRESHOLD))

    # GRB title in figure top (no catalog T90 — derived T_INT shown instead)
    if t_int_start is not None:
        tint_tag = (f'T_INT = [{t_int_start:.2f}, {t_int_stop:.2f}] s '
                    f'(Δ={t_int_stop - t_int_start:.2f}s)')
    else:
        tint_tag = 'T_INT: no ≥2σ block found'
    fig.text(0.5, 0.985,
             f'{trigger}  ({det}, bkg={src_tag}, poly={poly_order})   {tint_tag}',
             ha='center', va='top', fontsize=PUB['tick_size'])

    fig.savefig(outpath, dpi=PUB['dpi'])
    plt.close(fig)

    return {
        'TRIGGER_NAME': trigger,
        'DETECTOR': det,
        'BKG_SOURCE': src_tag,
        'POLY_ORDER': poly_order,
        'N_BB_BLOCKS': int(len(bb_starts)),
        'N_BB_SIG_3SIGMA': int(np.sum(bb_sigs >= SIG_THRESHOLD)),
        'N_MERGED': int(np.sum(bb_merged)),
        'MEAN_SIG': float(np.mean(bb_sigs)) if len(bb_sigs) else 0.0,
        'T_INT_START': float(t_int_start) if t_int_start is not None else float('nan'),
        'T_INT_STOP': float(t_int_stop) if t_int_stop is not None else float('nan'),
        'T_INT_WIDTH': float(t_int_stop - t_int_start) if t_int_start is not None else float('nan'),
        # MC-derived counting-only 1σ (Poisson resampling of raw counts,
        # same fixed polyfit). Does NOT include polyfit-coefficient or
        # interval-selection uncertainty.
        'T_INT_START_ERR_COUNT': float(t_int_start_err),
        'T_INT_STOP_ERR_COUNT': float(t_int_stop_err),
        'T_PEAK': float(t_peak) if t_peak is not None else float('nan'),
        'N_BLOCKS_IN_T_INT': int(n_int_blocks),
        'MEAN_SIG_IN_T_INT': float(mean_int_sig),
    }


# ============================================================================
# Batch driver
# ============================================================================

def _try_read(path):
    if os.path.exists(path):
        try:
            return Table.read(path, format='ascii.ecsv')
        except Exception:
            return None
    return None


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--trigger', type=str, default=None,
                   help='single trigger (default: bn200607921 if no --all-single-pulse)')
    p.add_argument('--det', type=str, default=None,
                   help='detector name (default: brightest from single_pulse_grbs.ecsv)')
    p.add_argument('--all-single-pulse', action='store_true',
                   help='iterate over results/single_pulse_grbs.ecsv')
    p.add_argument('--limit', type=int, default=None,
                   help='stop after N GRBs (testing)')
    p.add_argument('--skip-existing', action='store_true',
                   help='skip GRBs whose PNG already exists')
    args = p.parse_args()

    sample = Table.read(SAMPLE_PATH, format='ascii.ecsv')
    bkg_proto = _try_read(BKG_PROTO_PATH)
    bkg_main = _try_read(BKG_MAIN_PATH)

    targets = []
    if args.all_single_pulse:
        single = Table.read(SINGLE_PATH, format='ascii.ecsv')
        for row in single:
            targets.append((str(row['TRIGGER_NAME']).strip(),
                            str(row['DETECTOR']).strip()))
    else:
        trig = args.trigger or 'bn200607921'
        if args.det:
            det = args.det
        else:
            try:
                single = Table.read(SINGLE_PATH, format='ascii.ecsv')
                m = single['TRIGGER_NAME'] == trig
                det = str(single[m][0]['DETECTOR']).strip() if m.any() else 'n9'
            except Exception:
                det = 'n9'
        targets.append((trig, det))

    if args.limit is not None:
        targets = targets[:args.limit]
    print(f'{len(targets)} (trigger, det) pairs to plot.')

    log_path = os.path.join(
        LOGS_DIR, f'multiband_bb_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    log_f = open(log_path, 'w')

    summary_rows = []
    n_ok = n_fail = n_skip = 0

    for i, (trigger, det) in enumerate(targets):
        outpath = os.path.join(PLOTS_DIR, f'{trigger}_{det}_multiband.png')
        if args.skip_existing and os.path.exists(outpath):
            print(f'[{i+1}/{len(targets)}] {trigger} {det}: SKIP (exists)')
            n_skip += 1
            continue

        m = sample['TRIGGER_NAME'] == trigger
        if not m.any():
            msg = f'{trigger} not in grb_sample.ecsv'
            print(f'[{i+1}/{len(targets)}] {trigger} {det}: FAIL — {msg}')
            log_f.write(f'FAIL\t{trigger}\t{det}\t{msg}\n')
            n_fail += 1
            continue
        sample_row = sample[m][0]

        print(f'[{i+1}/{len(targets)}] {trigger} {det}: ', end='', flush=True)
        try:
            info = make_plot(trigger, det, sample_row, bkg_proto, bkg_main,
                             outpath)
            print(f'OK ({info["N_BB_BLOCKS"]} blocks, '
                  f'{info["N_MERGED"]} merged, '
                  f'bkg={info["BKG_SOURCE"]}, poly={info["POLY_ORDER"]})')
            log_f.write(f'OK\t{trigger}\t{det}\t{info}\n')
            summary_rows.append(info)
            n_ok += 1
        except Exception as exc:
            tb = traceback.format_exc(limit=2).strip().replace('\n', ' | ')
            print(f'FAIL — {type(exc).__name__}: {str(exc)[:80]}')
            log_f.write(f'FAIL\t{trigger}\t{det}\t{type(exc).__name__}: {exc}\t{tb}\n')
            n_fail += 1

    log_f.close()

    if summary_rows:
        summary_path = os.path.join(RESULTS_DIR, 'multiband_bb_summary.ecsv')
        keys = list(summary_rows[0].keys())
        t = Table(rows=[[r[k] for k in keys] for r in summary_rows], names=keys)
        t.write(summary_path, format='ascii.ecsv', overwrite=True)
        print(f'\nSummary: {summary_path}')

        # Dedicated time-integrated windows table for downstream consumers
        tint_keys = ['TRIGGER_NAME', 'DETECTOR',
                     'T_INT_START', 'T_INT_START_ERR_COUNT',
                     'T_INT_STOP', 'T_INT_STOP_ERR_COUNT',
                     'T_INT_WIDTH', 'T_PEAK',
                     'N_BLOCKS_IN_T_INT', 'MEAN_SIG_IN_T_INT']
        tint_rows = [[r[k] for k in tint_keys] for r in summary_rows]
        tint_path = os.path.join(RESULTS_DIR, 'time_integrated_windows.ecsv')
        Table(rows=tint_rows, names=tint_keys).write(
            tint_path, format='ascii.ecsv', overwrite=True)
        print(f'T_INT:   {tint_path}')

    print(f'\n{"="*60}')
    print(f'OK:   {n_ok}')
    print(f'SKIP: {n_skip}')
    print(f'FAIL: {n_fail}')
    print(f'Log:  {log_path}')
    print(f'PNGs: {PLOTS_DIR}/')
    print(f'{"="*60}')


if __name__ == '__main__':
    main()
