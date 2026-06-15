#!/usr/bin/env python
"""
Time-integrated window review GUI.

For one burst (default: brightest NaI from single_pulse_grbs.ecsv), reads
the derived T_INT window (computed by scripts/08_plot_multiband_bb.py
following our 2σ-start / 1.5σ-x3-stop convention), opens a 2-panel review
window:

  TOP: 8-900 keV LC step (1.024 s bins) for the brightest NaI
       + 3ML polyfit bkg model (red dashed)
       + gold-shaded T_INT region
       + dashed vertical lines at T_INT_START and T_INT_STOP

  BOTTOM: per-bin residuals (sigma units, gtburst formula) for the
          polyfit — sanity check that bkg model is good

Buttons (right side, gtburst-style picker=20 figure text):
  Accept   — save the AI/auto-derived T_INT as-is
  Override — user clicks 2 times to define a new (start, stop) pair;
             gold shading + vlines update; press Accept to commit
  Skip     — don't save anything; go to next
  Quit     — exit

Output: results/time_integrated_windows_reviewed.ecsv with
   TRIGGER_NAME, DETECTOR, T_INT_START, T_INT_STOP, T_INT_WIDTH,
   T_PEAK, REVIEWED (bool), OVERRIDDEN (bool), TIMESTAMP

Run in threeML env. matplotlib uses macosx backend (not TkAgg).
"""
import os
import sys
import glob
import argparse
import warnings
from datetime import datetime
import numpy as np
from astropy.io import fits
from astropy.table import Table

os.environ.setdefault('OMP_NUM_THREADS', '1')
warnings.filterwarnings('ignore')

_FD_DEFAULT = '/Users/salim/anaconda3/envs/threeML/share/fermitools'
if not os.environ.get('CALDB'):
    os.environ['FERMI_DIR'] = _FD_DEFAULT
    os.environ['CALDB'] = _FD_DEFAULT + '/data/caldb'
    os.environ['CALDBALIAS'] = _FD_DEFAULT + '/data/caldb/software/tools/alias_config.fits'
    os.environ['CALDBCONFIG'] = _FD_DEFAULT + '/data/caldb/software/tools/caldb.config'
    os.environ['CALDBROOT'] = _FD_DEFAULT + '/data/caldb'
    os.environ['EXTFILESSYS'] = _FD_DEFAULT + '/refdata/fermi'

import matplotlib
try:
    matplotlib.use('macosx')
except Exception:
    try:
        matplotlib.use('TkAgg')
    except Exception:
        # Headless fallback — GUI won't actually open but at least import works
        matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

BASE = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE, 'data')
RESULTS_DIR = os.path.join(BASE, 'results')
SAMPLE_PATH = os.path.join(RESULTS_DIR, 'grb_sample.ecsv')
SINGLE_PATH = os.path.join(RESULTS_DIR, 'single_pulse_grbs.ecsv')
BKG_PROTO_PATH = os.path.join(RESULTS_DIR, 'background_intervals_prototype.ecsv')
BKG_MAIN_PATH = os.path.join(RESULTS_DIR, 'background_intervals.ecsv')
TINT_AUTO_PATH = os.path.join(RESULTS_DIR, 'time_integrated_windows.ecsv')
TINT_REVIEW_PATH = os.path.join(RESULTS_DIR, 'time_integrated_windows_reviewed.ecsv')

NAI_BAND = (8.0, 900.0)
LC_BIN_S = 0.064          # 64 ms — fine enough for burst-edge transitions to be sharp
P0 = 0.01
# NB: NO Phase-A sub-3σ merge here — that belongs to the spectral-analysis
# step. T_INT determination uses raw Scargle BB output.
TINT_START_THRESH = 2.0
TINT_STOP_THRESH = 1.5
TINT_STOP_RUN_N = (3, 2, 1)


# ============================================================================
# Helpers
# ============================================================================

def find_tte(trigger, det):
    m = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_tte_{det}_*.fit.gz'))
    return m[0] if m else None


def find_rsp(trigger, det):
    m = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_cspec_{det}_*.rsp*'))
    return m[0] if m else None


def load_bkg_for(trigger, det, bkg_proto, bkg_main):
    """Per-detector bkg lookup — required, no legacy fallback."""
    for tab in (bkg_proto, bkg_main):
        if tab is None:
            continue
        m = (tab['TRIGGER_NAME'] == trigger) & (tab['DETECTOR'] == det)
        if m.any():
            r = tab[m][0]
            return (float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP']),
                    float(r['BKG_POS_START']), float(r['BKG_POS_STOP']))
    raise KeyError(
        f'No per-detector bkg for ({trigger}, {det}). '
        f'Run scripts/00_prototype_one_burst.py --trigger {trigger} first.')


def compute_t_int_cumsum_saturation(bin_edges, counts_per_bin, bkg_counts_per_bin,
                                    n_mc=1000, seed=42,
                                    smooth_window=16, frac=0.03,
                                    min_consec_below=32, **kwargs):
    """Smoothed-rate-threshold T_INT with min_consec_below to skip brief
    inter-pulse gaps. See scripts/08_plot_multiband_bb.py."""
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
        n = len(net_smooth)
        ext_thr = 2.0 * thr  # safety margin: new peak must be 2x stop-threshold
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
        # Fermi-trigger-style 4.5σ noise floor (von Kienlin+ 2014)
        bkg_mean_per_bin = float(np.mean(bkg_counts_per_bin)) if len(bkg_counts_per_bin) else 0.0
        sigma_smoothed = (np.sqrt(max(bkg_mean_per_bin, 1.0)) /
                          np.sqrt(max(smooth_window, 1)))
        thr = max(frac * peak_s, 4.5 * sigma_smoothed)
        i_stop = min(_walk_to_threshold(net_smooth, ipk, 'forward', thr), n_bins - 1)
        i_start = max(_walk_to_threshold(net_smooth, ipk, 'backward', thr), 0)
        return (float(bin_edges[i_start]),
                float(bin_edges[i_stop + 1]),
                float(bin_centres[ipk]))

    net_obs = counts_per_bin - bkg_counts_per_bin
    t_start, t_stop, t_peak = _one(net_obs)
    if t_start is None:
        return dict(t_start=None, t_stop=None, t_peak=None,
                    t_start_err=0.0, t_stop_err=0.0, n_mc=0)

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
    """2σ start, 3-consecutive-<1.5σ stop after peak. Copied from 08."""
    bb_starts = np.asarray(bb_starts, dtype=float)
    bb_sigs = np.asarray(bb_sigs, dtype=float)
    n = len(bb_sigs)
    if n == 0:
        return None, None, None, None
    above = np.where(bb_sigs >= start_thresh)[0]
    if len(above) == 0:
        return None, None, None, None
    i_start = int(above[0])
    t_start = float(bb_starts[i_start])
    i_peak = i_start + int(np.argmax(bb_sigs[i_start:]))
    t_peak = float(bb_starts[i_peak])
    t_stop = float(post_start)
    for k in run_lengths:
        for j in range(i_peak + 1, n - k + 1):
            if all(bb_sigs[j + m] < stop_thresh for m in range(k)):
                t_stop = float(bb_starts[j])
                break
        else:
            continue
        break
    return t_start, t_stop, i_peak, t_peak


# ============================================================================
# Review GUI
# ============================================================================

class TIntReviewer(object):
    """2-panel LC + residuals review window. Returns
    ('accept'|'skip'|'quit', t_int_start, t_int_stop, overridden)."""

    def __init__(self, trigger, det, tte_file, rsp_file, pre, post,
                 t_int_start_init, t_int_stop_init, t_peak):
        self.trigger = trigger
        self.det = det
        self.tte_file = tte_file
        self.rsp_file = rsp_file
        self.pre_a, self.pre_b = pre
        self.post_a, self.post_b = post
        self.t_int_start = t_int_start_init
        self.t_int_stop = t_int_stop_init
        self.t_peak = t_peak

        # Bin TTE events in NaI 8-900 keV + matching channel mask for bkg
        with fits.open(tte_file) as hdul:
            evts = hdul['EVENTS'].data
            trigtime = hdul['PRIMARY'].header.get('TRIGTIME', 0.0)
            ebounds = hdul['EBOUNDS'].data
            chan_emin = ebounds['E_MIN']; chan_emax = ebounds['E_MAX']
            n_chan = len(chan_emin)
            pha = evts['PHA']; times = evts['TIME']
            valid = pha < n_chan
            e_lo = chan_emin[np.clip(pha, 0, n_chan - 1)]
            e_hi = chan_emax[np.clip(pha, 0, n_chan - 1)]
            in_band = valid & (e_lo >= NAI_BAND[0]) & (e_hi <= NAI_BAND[1])
            t_rel = times[in_band] - trigtime
            # Channel mask: True for channels fully within NaI_BAND.
            # Must match the energy band of the LC, else residuals get
            # biased negative because polyfit integrates over ALL channels
            # while LC histogram only sees 8-900 keV.
            self.chan_mask = ((chan_emin >= NAI_BAND[0])
                              & (chan_emax <= NAI_BAND[1]))

        # Plot window: bkg windows + buffer
        t_min = self.pre_a - 5.0
        t_max = self.post_b + 5.0
        self.bin_width = LC_BIN_S
        self.bins = np.arange(t_min, t_max + LC_BIN_S, LC_BIN_S)
        counts, _ = np.histogram(t_rel, bins=self.bins)
        self.bin_centers = 0.5 * (self.bins[:-1] + self.bins[1:])
        self.counts_per_bin = counts.astype(float)
        self.rates = self.counts_per_bin / LC_BIN_S

        # State
        self.overridden = False         # set True by arrow-key adjust
        self.result = None
        self.fill_artist = None
        self.tint_line_artists = []
        self.bkg_overlay_artist = None
        self.resid_artists = []
        self._tsb = None
        # Micro-adjust state: None | 'start' | 'stop'
        self._adjust_mode = None
        # Remember auto values so Reset works
        self._auto_start = self.t_int_start
        self._auto_stop = self.t_int_stop

        self._build_figure()

    def _build_figure(self):
        self.fig = plt.figure(figsize=(12, 7.5))
        gs = self.fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.0,
                                   left=0.07, right=0.85, top=0.93, bottom=0.10)
        self.ax = self.fig.add_subplot(gs[0])
        self.ax_res = self.fig.add_subplot(gs[1], sharex=self.ax)

        self.ax.step(self.bin_centers, self.rates, where='mid',
                     color='0.45', lw=0.8, alpha=0.85)
        # Bkg windows shaded faintly
        self.ax.axvspan(self.pre_a, self.pre_b, color='0.85', alpha=0.4, zorder=0)
        self.ax.axvspan(self.post_a, self.post_b, color='0.85', alpha=0.4, zorder=0)

        self.ax.set_ylabel(r'Counts s$^{-1}$ (NaI 8-900 keV)', fontsize=11)
        self.ax.set_title(
            f'{self.trigger}  ({self.det})  —  review T_INT '
            f'(approve, Override to redraw, or Skip/Quit)',
            fontsize=12)
        plt.setp(self.ax.get_xticklabels(), visible=False)

        # Residuals panel skeleton
        self.ax_res.axhline(0, color='red', ls='--', lw=1.0, zorder=1)
        self.ax_res.axhline(1, color='gray', ls=':', lw=0.5, alpha=0.6)
        self.ax_res.axhline(-1, color='gray', ls=':', lw=0.5, alpha=0.6)
        self.ax_res.axhline(3, color='gray', ls=':', lw=0.4, alpha=0.5)
        self.ax_res.axhline(-3, color='gray', ls=':', lw=0.4, alpha=0.5)
        self.ax_res.set_ylabel(r'Residuals ($\sigma$)', fontsize=10)
        self.ax_res.set_xlabel('Time since trigger (s)', fontsize=11)
        self.ax_res.set_xlim(self.bins[0], self.bins[-1])
        self.ax_res.set_ylim(-5, 12)
        self.ax_res.grid(alpha=0.25, lw=0.3)

        # Buttons (gtburst-style figure text + picker)
        self.btn_accept = self.fig.text(0.87, 0.85, 'Accept',
                                        backgroundcolor='green', color='white',
                                        weight='bold', picker=20, fontsize=12,
                                        ha='left', va='center')
        self.btn_adj_start = self.fig.text(0.87, 0.75, 'Adj START',
                                           backgroundcolor='#cc8800', color='white',
                                           weight='bold', picker=20, fontsize=11,
                                           ha='left', va='center')
        self.btn_adj_stop = self.fig.text(0.87, 0.66, 'Adj STOP',
                                          backgroundcolor='#cc8800', color='white',
                                          weight='bold', picker=20, fontsize=11,
                                          ha='left', va='center')
        self.btn_reset = self.fig.text(0.87, 0.57, 'Reset',
                                       backgroundcolor='steelblue', color='white',
                                       weight='bold', picker=20, fontsize=11,
                                       ha='left', va='center')
        self.btn_skip = self.fig.text(0.87, 0.48, 'Skip',
                                      backgroundcolor='gray', color='white',
                                      weight='bold', picker=20, fontsize=11,
                                      ha='left', va='center')
        self.btn_quit = self.fig.text(0.87, 0.39, 'Quit',
                                      backgroundcolor='black', color='white',
                                      weight='bold', picker=20, fontsize=11,
                                      ha='left', va='center')
        self.help_text = self.fig.text(
            0.87, 0.29,
            'micro-adjust:\n  ←/→ ± 1 bin (64 ms)\n  shift+←/→ ± 16 bins (~1 s)\n'
            '  keys s/e = start/stop\n  esc = exit adjust',
            ha='left', va='top', fontsize=8, color='0.30',
            family='monospace')
        self.status_text = self.fig.text(0.07, 0.02, '',
                                         ha='left', va='bottom',
                                         fontsize=9, color='steelblue')

        # Initial T_INT shading + lines + polyfit residuals
        self._refresh_tint()
        self._refresh_overlay()

        if self.t_int_start is not None:
            self._set_status(
                f'Auto T_INT = [{self.t_int_start:.2f}, {self.t_int_stop:.2f}] s '
                f'(width {self.t_int_stop - self.t_int_start:.2f}s). '
                f'Accept, Adj START / Adj STOP (arrow keys), Reset, Skip, or Quit.')
        else:
            self._set_status(
                'No auto T_INT (no positive net). Use Adj START / Adj STOP '
                '(arrow keys) to set manually, then Accept.')

        self.cids = [
            self.fig.canvas.mpl_connect('pick_event', self._on_pick),
            self.fig.canvas.mpl_connect('key_press_event', self._on_key),
        ]

    def _on_pick(self, event):
        if event.mouseevent.button != 1:
            return
        if event.artist is self.btn_accept:
            if self.t_int_start is None or self.t_int_stop is None:
                self._set_status('No T_INT to accept.')
                self.fig.canvas.draw_idle()
                return
            self.result = 'accept'
            plt.close(self.fig)
        elif event.artist is self.btn_adj_start:
            # If no auto T_INT (no positive net), seed at peak so adjust works
            if self.t_int_start is None:
                self.t_int_start = self.t_peak if self.t_peak is not None else 0.0
                self.t_int_stop = self.t_int_start + self.bin_width
                self.overridden = True
                self._refresh_tint()
            self._adjust_mode = 'start'
            self._set_status(
                f'Adjusting START — current {self.t_int_start:.3f}s. '
                f'Use ←/→ (±{self.bin_width:.3f}s), shift+←/→ (±{16*self.bin_width:.3f}s), '
                f'esc to exit adjust.')
            self.fig.canvas.draw_idle()
        elif event.artist is self.btn_adj_stop:
            if self.t_int_stop is None:
                self.t_int_stop = self.t_peak if self.t_peak is not None else 0.0
                self.t_int_start = self.t_int_stop - self.bin_width
                self.overridden = True
                self._refresh_tint()
            self._adjust_mode = 'stop'
            self._set_status(
                f'Adjusting STOP — current {self.t_int_stop:.3f}s. '
                f'Use ←/→ (±{self.bin_width:.3f}s), shift+←/→ (±{16*self.bin_width:.3f}s), '
                f'esc to exit adjust.')
            self.fig.canvas.draw_idle()
        elif event.artist is self.btn_reset:
            self.t_int_start = self._auto_start
            self.t_int_stop = self._auto_stop
            self.overridden = False
            self._adjust_mode = None
            self._refresh_tint()
            self._set_status(
                f'Reset to auto: [{self.t_int_start}, {self.t_int_stop}] s.'
                if self.t_int_start is not None
                else 'Reset to auto: no positive net.')
            self.fig.canvas.draw_idle()
        elif event.artist is self.btn_skip:
            self.result = 'skip'
            plt.close(self.fig)
        elif event.artist is self.btn_quit:
            self.result = 'quit'
            plt.close(self.fig)

    def _on_key(self, event):
        """Arrow-key micro-adjust of selected endpoint."""
        if self._adjust_mode is None:
            return
        if event.key in ('escape',):
            self._adjust_mode = None
            self._set_status(
                f'Adjust mode exited. Current T_INT = '
                f'[{self.t_int_start:.3f}, {self.t_int_stop:.3f}] s.')
            self.fig.canvas.draw_idle()
            return
        step = 0
        if event.key == 'left':       step = -1
        elif event.key == 'right':    step = +1
        elif event.key == 'shift+left':  step = -16   # ~1 s at 64 ms bins
        elif event.key == 'shift+right': step = +16
        elif event.key in ('s',):  # switch to start
            self._adjust_mode = 'start'
            self._set_status(f'Adjusting START — current {self.t_int_start:.3f}s.')
            self.fig.canvas.draw_idle()
            return
        elif event.key in ('e',):  # switch to stop
            self._adjust_mode = 'stop'
            self._set_status(f'Adjusting STOP — current {self.t_int_stop:.3f}s.')
            self.fig.canvas.draw_idle()
            return
        else:
            return
        delta = step * self.bin_width
        if self._adjust_mode == 'start':
            self.t_int_start += delta
            self.overridden = True
            label = 'START'
            cur = self.t_int_start
        else:
            self.t_int_stop += delta
            self.overridden = True
            label = 'STOP'
            cur = self.t_int_stop
        self._refresh_tint()
        self._set_status(
            f'Adjusted {label} → {cur:.3f}s '
            f'(T_INT = [{self.t_int_start:.3f}, {self.t_int_stop:.3f}] s, '
            f'Δ={self.t_int_stop - self.t_int_start:.3f}s)')
        self.fig.canvas.draw_idle()

    def _refresh_tint(self):
        if self.fill_artist is not None:
            try: self.fill_artist.remove()
            except Exception: pass
            self.fill_artist = None
        for art in self.tint_line_artists:
            try: art.remove()
            except Exception: pass
        self.tint_line_artists = []
        if self.t_int_start is None or self.t_int_stop is None:
            return
        self.fill_artist = self.ax.axvspan(
            self.t_int_start, self.t_int_stop,
            color='gold', alpha=0.30, zorder=1,
            label='T_INT' if not self.overridden else 'T_INT (override)')
        for x in (self.t_int_start, self.t_int_stop):
            self.tint_line_artists.append(
                self.ax.axvline(x, color='goldenrod', ls='--', lw=1.2,
                                alpha=0.85, zorder=2))
            self.tint_line_artists.append(
                self.ax_res.axvline(x, color='goldenrod', ls='--', lw=1.0,
                                    alpha=0.7, zorder=1))

    def _ensure_tsb(self):
        if self._tsb is not None:
            return
        from threeML import TimeSeriesBuilder
        self._tsb = TimeSeriesBuilder.from_gbm_tte(
            self.det, self.tte_file, rsp_file=self.rsp_file, verbose=False)

    def _refresh_overlay(self):
        # Run 3ML polyfit + draw bkg-rate curve + residuals
        try:
            self._ensure_tsb()
            self._tsb.set_background_interval(
                f'{self.pre_a:.3f}-{self.pre_b:.3f}',
                f'{self.post_a:.3f}-{self.post_b:.3f}')
        except Exception as exc:
            self._set_status(f'3ML polyfit failed: {type(exc).__name__}: {exc}')
            return
        ts = self._tsb._time_series
        n = len(self.bin_centers)
        bkg_counts = np.zeros(n); bkg_err = np.zeros(n)
        for k in range(n):
            try:
                bkg_counts[k] = float(ts.get_total_poly_count(
                    self.bins[k], self.bins[k + 1], mask=self.chan_mask))
                bkg_err[k] = float(ts.get_total_poly_error(
                    self.bins[k], self.bins[k + 1], mask=self.chan_mask))
            except TypeError as exc:
                # Refuse to silently fall back to broadband (would
                # re-introduce the energy-mismatch bug we just fixed).
                raise RuntimeError(
                    'Installed 3ML does not support mask= in '
                    'get_total_poly_count. Upgrade 3ML or implement a manual '
                    'masked sum over ts._polynomials[chan_mask].') from exc
            except Exception:
                bkg_counts[k] = np.nan; bkg_err[k] = np.nan
        bkg_rate = bkg_counts / self.bin_width
        denom = np.sqrt(np.maximum(bkg_counts + bkg_err ** 2, 1.0))
        residuals = (self.counts_per_bin - bkg_counts) / denom

        if self.bkg_overlay_artist is not None:
            try: self.bkg_overlay_artist.remove()
            except Exception: pass
        self.bkg_overlay_artist, = self.ax.plot(
            self.bin_centers, bkg_rate, color='red', lw=1.3, alpha=0.85,
            zorder=3, label='3ML polyfit bkg')

        for art in self.resid_artists:
            try: art.remove()
            except Exception: pass
        self.resid_artists = []
        try:
            cont = self.ax_res.errorbar(
                self.bin_centers, residuals,
                yerr=np.ones_like(residuals),
                color='black', ecolor='black', elinewidth=0.5, zorder=2)
            self.resid_artists.append(cont[0])
            for art in cont[1]: self.resid_artists.append(art)
            for art in cont[2]: self.resid_artists.append(art)
        except Exception:
            pass
        finite = residuals[np.isfinite(residuals)]
        if len(finite):
            ymin = float(np.min(finite))
            ymax = float(min(np.max(finite), 10.0))
            self.ax_res.set_ylim(ymin - 1.0, ymax + 0.5)

    def _set_status(self, msg):
        self.status_text.set_text(msg)

    def run(self):
        plt.show(block=True)
        return (self.result, self.t_int_start, self.t_int_stop, self.overridden)


# ============================================================================
# Save reviewed row
# ============================================================================

def save_reviewed_row(trigger, det, t_int_start, t_int_stop, t_peak,
                      overridden, target_path):
    row = {
        'TRIGGER_NAME': trigger,
        'DETECTOR': det,
        'T_INT_START': float(t_int_start),
        'T_INT_STOP': float(t_int_stop),
        'T_INT_WIDTH': float(t_int_stop - t_int_start),
        'T_PEAK': float(t_peak) if t_peak is not None else float('nan'),
        'REVIEWED': True,
        'OVERRIDDEN': bool(overridden),
        'TIMESTAMP': datetime.now().isoformat(timespec='seconds'),
    }
    if os.path.exists(target_path):
        t = Table.read(target_path, format='ascii.ecsv')
        mask = ~((t['TRIGGER_NAME'] == trigger) & (t['DETECTOR'] == det))
        t = t[mask]
        t.add_row(row)
    else:
        t = Table([[row[k]] for k in row], names=list(row.keys()))
    t.write(target_path, format='ascii.ecsv', overwrite=True)


# ============================================================================
# Driver
# ============================================================================

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--trigger', default='bn200607921')
    p.add_argument('--det', default=None,
                   help='detector (default: brightest from single_pulse_grbs.ecsv)')
    args = p.parse_args()

    sample = Table.read(SAMPLE_PATH, format='ascii.ecsv')
    bkg_proto = (Table.read(BKG_PROTO_PATH, format='ascii.ecsv')
                 if os.path.exists(BKG_PROTO_PATH) else None)
    bkg_main = (Table.read(BKG_MAIN_PATH, format='ascii.ecsv')
                if os.path.exists(BKG_MAIN_PATH) else None)

    # Pick brightest detector
    if args.det:
        det = args.det
    else:
        single = Table.read(SINGLE_PATH, format='ascii.ecsv')
        m = single['TRIGGER_NAME'] == args.trigger
        if not m.any():
            raise SystemExit(f'{args.trigger} not in single_pulse_grbs.ecsv. Pass --det.')
        det = str(single[m][0]['DETECTOR']).strip()

    trigger = args.trigger
    tte = find_tte(trigger, det)
    rsp = find_rsp(trigger, det)
    if tte is None or rsp is None:
        raise SystemExit(f'TTE/RSP missing for {trigger} {det}')

    pre_a, pre_b, post_a, post_b = load_bkg_for(trigger, det, bkg_proto, bkg_main)

    # Run 3ML BB + Phase-A to get blocks, then compute T_INT
    from threeML import TimeSeriesBuilder
    print(f'Running 3ML BB on {trigger} {det} ...')
    tsb = TimeSeriesBuilder.from_gbm_tte(det, tte, rsp_file=rsp, verbose=False)
    tsb.set_background_interval(f'{pre_a:.3f}-{pre_b:.3f}',
                                f'{post_a:.3f}-{post_b:.3f}')
    tsb.set_active_time_interval(f'{pre_b:.3f}-{post_a:.3f}')
    tsb.create_time_bins(pre_b, post_a, method='bayesblocks',
                         p0=P0, use_background=True)

    # RAW Scargle BB (Phase-A merge belongs to spectral analysis, not here).
    bb_starts = np.array(tsb.bins.starts).copy()
    bb_sigs = np.array(tsb.significance_per_interval).copy()

    # T_INT via cumsum-saturation from peak (Maccary/Salim algorithm,
    # Fermi_lightcurve_autoselect.ipynb cells 16+18). Replaces the
    # old BB-threshold approach which mis-fired when pre-burst Scargle
    # blocks were narrow but ≥ 2σ from polyfit residuals.
    ts = tsb._time_series
    tint_bins = np.arange(pre_b, post_a + LC_BIN_S, LC_BIN_S)
    tint_centres = 0.5 * (tint_bins[:-1] + tint_bins[1:])
    with fits.open(tte) as hdul:
        evts = hdul['EVENTS'].data
        ebounds = hdul['EBOUNDS'].data
        chan_emin = ebounds['E_MIN']; chan_emax = ebounds['E_MAX']
        n_chan = len(chan_emin)
        pha = evts['PHA']; times = evts['TIME']
        valid = pha < n_chan
        e_lo = chan_emin[np.clip(pha, 0, n_chan-1)]
        e_hi = chan_emax[np.clip(pha, 0, n_chan-1)]
        in_band = valid & (e_lo >= NAI_BAND[0]) & (e_hi <= NAI_BAND[1])
        t_rel_8_900 = times[in_band] - hdul['PRIMARY'].header.get('TRIGTIME', 0.0)
        chan_mask = (chan_emin >= NAI_BAND[0]) & (chan_emax <= NAI_BAND[1])
    tint_counts, _ = np.histogram(t_rel_8_900, bins=tint_bins)
    def _bkg_in_band(t1, t2):
        return float(ts.get_total_poly_count(t1, t2, mask=chan_mask))
    try:
        _bkg_in_band(tint_bins[0], tint_bins[1])
    except TypeError as exc:
        raise RuntimeError(
            'Installed 3ML does not support mask= in get_total_poly_count. '
            'Upgrade 3ML or implement a manual masked sum.') from exc
    tint_bkg = np.array([_bkg_in_band(tint_bins[k], tint_bins[k+1])
                         for k in range(len(tint_centres))])
    tint = compute_t_int_cumsum_saturation(
        tint_bins, tint_counts.astype(float), tint_bkg,
        n_mc=1000)
    t_start = tint['t_start']; t_stop = tint['t_stop']
    t_peak = tint['t_peak']
    t_start_err = tint['t_start_err']; t_stop_err = tint['t_stop_err']
    if t_start is None:
        print(f'  No positive-net-rate bin found → no auto T_INT '
              f'(GUI will open in manual-override mode).')
    else:
        print(f'  T_INT_START = {t_start:.2f} ± {t_start_err:.2f} s')
        print(f'  T_INT_STOP  = {t_stop:.2f} ± {t_stop_err:.2f} s')
        print(f'  T_PEAK      = {t_peak:.2f} s')
        print(f'  → BB: {len(bb_starts)} blocks, '
              f'T_INT = [{t_start:.2f}, {t_stop:.2f}] s')

    # Open review GUI
    reviewer = TIntReviewer(
        trigger, det, tte, rsp, (pre_a, pre_b), (post_a, post_b),
        t_start, t_stop, t_peak)
    result, final_start, final_stop, overridden = reviewer.run()
    if result == 'accept':
        save_reviewed_row(trigger, det, final_start, final_stop, t_peak,
                          overridden, TINT_REVIEW_PATH)
        flag = '(overridden)' if overridden else '(auto)'
        print(f'\nSaved T_INT = [{final_start:.2f}, {final_stop:.2f}] s {flag}'
              f'\n  → {TINT_REVIEW_PATH}')
    elif result == 'skip':
        print('\nSkipped — no row written.')
    elif result == 'quit':
        print('\nQuit.')


if __name__ == '__main__':
    main()
