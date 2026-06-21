#!/usr/bin/env python
"""
Phase 0 end-to-end prototype on ONE burst.

Default trigger: bn200607921 (single-pulse, we have its data + a human-clicked
baseline from yesterday for sanity-checking the AI's selections).

Three-phase invocation so the AI-vision step is clean:

    Phase 1 — detector picker + LC PNG generation:
        python 00_prototype_one_burst.py [--trigger bn200607921]
        → opens detector-selection GUI (gtburst-style)
        → renders 1.024-s LC PNG per approved detector to plots/lc_for_ai/
        → writes manifest plots/lc_for_ai/<trigger>_pending.json
        → exits, prints "AI vision step needed"

    Phase 2 — AI vision:
        Claude (in this session) reads each PNG via Read, emits per-detector
        {pre, post, confidence, reasoning, flags} and writes them to
        plots/lc_for_ai/<trigger>_ai_selections.json. No script runs.

    Phase 3 — bkg-approval GUI + BB:
        python 00_prototype_one_burst.py --resume [--trigger bn200607921]
        → opens gtburst-style bkg picker per detector, pre-populated with
          AI's intervals (user Accept/Clear-redo/Skip/Quit)
        → saves approved intervals to results/background_intervals_prototype.ecsv
        → runs BB with use_background=True per detector
        → saves blocks to results/bb_blocks_prototype_<trigger>.ecsv

Run in the threeML env with CALDB env vars exported so 3ML can load.
"""

import os
import sys
import glob
import json
import re
import argparse
import warnings
import urllib.request

import numpy as np
from astropy.io import fits
from astropy.table import Table

os.environ.setdefault('OMP_NUM_THREADS', '1')
warnings.filterwarnings('ignore')

import matplotlib
try:
    matplotlib.use('macosx')
except Exception:
    matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')
LC_FOR_AI_DIR = os.path.join(PLOTS_DIR, 'lc_for_ai')

os.makedirs(LC_FOR_AI_DIR, exist_ok=True)

# BackgroundSelector is inlined below (same UI as scripts/00_select_backgrounds.py).
# Inlined rather than imported because the Bash sandbox blocks reading sibling
# script files via Python's import machinery in this Claude Code session.

CLICK_TOL_PIXELS = 2


class BackgroundSelector(object):
    """One detector's interactive figure — gtburst-mirror UX. Returns
    ('accept'|'skip'|'quit', pre, post) from .run().

    Two-panel layout (LC on top, residuals on bottom) modelled after gtburst's
    makeLightCurveWithResiduals (dataHandling.py:2835-2911). Residuals come
    from 3ML's gtburst-style two-stage polyfit, computed lazily once both
    intervals are set."""

    def __init__(self, trigger, det, tte_file, rsp_file=None,
                 t90_start=None, t90=None,
                 prev_pre=None, prev_post=None):
        self.trigger = trigger
        self.det = det
        self.tte_file = tte_file
        self.rsp_file = rsp_file
        self.has_t90 = (t90_start is not None and t90 is not None)
        self.t90_start = t90_start
        self.t90_stop = (t90_start + t90) if self.has_t90 else None

        with fits.open(tte_file) as hdul:
            times = hdul['EVENTS'].data['TIME']
            trigtime = hdul['PRIMARY'].header.get('TRIGTIME', 0.0)
            t_rel = times - trigtime

        if self.has_t90:
            pad = max(120.0, 5.0 * t90)
            t_min = max(float(t_rel.min()), self.t90_start - pad)
            t_max = min(float(t_rel.max()), self.t90_stop + 2.0 * pad)
            if t90 < 5:    dt = 0.064
            elif t90 < 30: dt = 0.128
            elif t90 < 100: dt = 0.256
            elif t90 < 300: dt = 0.5
            else:          dt = 1.0
        else:
            # No T90 — use full event-time range, 1-s binning
            t_min = float(t_rel.min())
            t_max = float(t_rel.max())
            dt = 1.0

        self.bin_width = float(dt)
        self.bins = np.arange(t_min, t_max + dt, dt)
        counts, _ = np.histogram(t_rel, bins=self.bins)
        self.bin_centers = 0.5 * (self.bins[:-1] + self.bins[1:])
        self.counts_per_bin = counts.astype(float)
        self.rates = self.counts_per_bin / dt

        self.pending_clicks = []
        self.pre_interval = prev_pre
        self.post_interval = prev_post
        self.fill_artists_top = []
        self.fill_artists_bot = []
        self.line_artists = []
        self.transient_line = None
        self.bkg_overlay_artist = None       # bkg rate curve on top panel
        self.resid_artists = []              # residual errorbar + line on bottom
        self.result = None
        self._press_x_pixel = None
        self._tsb = None                      # lazy 3ML TimeSeriesBuilder
        self._adjust_edge = None              # keyboard micro-adjust: (win, idx)

        self._build_figure()

    def _build_figure(self):
        self.fig = plt.figure(figsize=(12, 8.0))
        # hspace=0 matches gtburst (dataHandling.py:2847)
        gs = self.fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.0,
                                   left=0.07, right=0.85, top=0.93, bottom=0.10)
        self.ax = self.fig.add_subplot(gs[0])        # LC panel
        self.ax_res = self.fig.add_subplot(gs[1], sharex=self.ax)  # residuals

        self.ax.step(self.bin_centers, self.rates, where='mid',
                     color='gray', lw=0.8, alpha=0.75)
        if self.has_t90:
            self.ax.axvspan(self.t90_start, self.t90_stop,
                            color='orange', alpha=0.12, zorder=0)
            self.ax.axvline(self.t90_start, color='orange', ls=':', lw=0.9)
            self.ax.axvline(self.t90_stop, color='orange', ls=':', lw=0.9)
        self.ax.set_ylabel(r'Counts s$^{-1}$', fontsize=11)
        self.ax.set_title(
            f'{self.trigger}  ({self.det})  —  pre-populated from AI; '
            f'adjust or Accept   (residuals via 3ML polyfit below)',
            fontsize=12,
        )
        plt.setp(self.ax.get_xticklabels(), visible=False)

        # Bottom (residuals) panel — initial empty state with 0-line
        self.ax_res.axhline(0, color='red', ls='--', lw=1.0, zorder=1)
        self.ax_res.axhline( 1, color='gray', ls=':', lw=0.6, alpha=0.7)
        self.ax_res.axhline(-1, color='gray', ls=':', lw=0.6, alpha=0.7)
        self.ax_res.axhline( 3, color='gray', ls=':', lw=0.4, alpha=0.5)
        self.ax_res.axhline(-3, color='gray', ls=':', lw=0.4, alpha=0.5)
        self.ax_res.set_ylabel(r'Residuals ($\sigma$)', fontsize=10)
        self.ax_res.set_xlabel('Time since trigger (s)', fontsize=11)
        self.ax_res.set_ylim(-5, 5)
        self.ax_res.set_xlim(self.bins[0], self.bins[-1])
        self.ax_res.grid(alpha=0.25, lw=0.3)

        self.btn_clear = self.fig.text(0.87, 0.82, 'Clear',
                                       backgroundcolor='red', color='white',
                                       weight='bold', picker=20, fontsize=11,
                                       ha='left', va='center')
        self.btn_accept = self.fig.text(0.87, 0.72, 'Accept',
                                        backgroundcolor='green', color='white',
                                        weight='bold', picker=20, fontsize=11,
                                        ha='left', va='center')
        self.btn_skip = self.fig.text(0.87, 0.62, 'Skip GRB',
                                      backgroundcolor='#cc8800', color='white',
                                      weight='bold', picker=20, fontsize=10,
                                      ha='left', va='center')
        self.btn_quit = self.fig.text(0.87, 0.52, 'Quit',
                                      backgroundcolor='gray', color='white',
                                      weight='bold', picker=20, fontsize=10,
                                      ha='left', va='center')
        self.status_text = self.fig.text(0.07, 0.02, '', ha='left',
                                         va='bottom', fontsize=9,
                                         color='steelblue')

        if self.pre_interval or self.post_interval:
            self._refresh_intervals()
            self._refresh_overlay()
            self._set_status('AI pre-populated. Adjust if needed, then Accept.')
        else:
            self._set_status('Click 4 times: 2 pre-burst, 2 post-burst.')

        # Keyboard micro-adjust (from 09_review_time_integrated.py): pick an edge
        # with a/s/d/f, nudge with arrows. Free the arrow keys from matplotlib's
        # pan-history keymap so they reach our handler.
        import matplotlib as _mpl
        for _k in ('keymap.back', 'keymap.forward'):
            try:
                _mpl.rcParams[_k] = [x for x in _mpl.rcParams[_k]
                                     if x not in ('left', 'right')]
            except Exception:
                pass
        self.fig.text(0.87, 0.40,
                      'micro-adjust:\n a / s  pre L/R\n d / f  post L/R\n'
                      ' ←/→  ±1 bin\n shift  ±16 bin\n esc  exit',
                      ha='left', va='top', fontsize=8, color='0.30',
                      family='monospace')
        self.cids = [
            self.fig.canvas.mpl_connect('button_press_event', self._on_press),
            self.fig.canvas.mpl_connect('button_release_event', self._on_release),
            self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion),
            self.fig.canvas.mpl_connect('pick_event', self._on_pick),
            self.fig.canvas.mpl_connect('key_press_event', self._on_key),
        ]

    def _is_normal_mode(self):
        toolbar = getattr(self.fig.canvas, 'toolbar', None)
        if toolbar is None:
            return True
        mode = getattr(toolbar, 'mode', '')
        return not mode

    def _on_press(self, event):
        if not self._is_normal_mode():
            self._press_x_pixel = None
            return
        self._press_x_pixel = event.x

    def _on_release(self, event):
        if not self._is_normal_mode():
            return
        if event.button != 1 or self._press_x_pixel is None:
            return
        if event.x is None or event.xdata is None:
            return
        if abs(event.x - self._press_x_pixel) > CLICK_TOL_PIXELS:
            return
        self._add_click(self._snap_to_bin(event.xdata))

    def _on_motion(self, event):
        if self.transient_line is not None:
            try: self.transient_line.remove()
            except Exception: pass
            self.transient_line = None
        if not self._is_normal_mode() or event.xdata is None:
            self.fig.canvas.draw_idle()
            return
        self.transient_line = self.ax.axvline(
            event.xdata, color='black', ls=':', lw=0.5, alpha=0.45)
        self.fig.canvas.draw_idle()

    def _on_pick(self, event):
        if event.mouseevent.button != 1:
            return
        if event.artist is self.btn_clear:
            self._clear_all()
        elif event.artist is self.btn_accept:
            if self.pre_interval is None or self.post_interval is None:
                self._set_status('Need both pre + post intervals before Accept.')
                self.fig.canvas.draw_idle()
                return
            self.result = 'accept'
            plt.close(self.fig)
        elif event.artist is self.btn_skip:
            self.result = 'skip'
            plt.close(self.fig)
        elif event.artist is self.btn_quit:
            self.result = 'quit'
            plt.close(self.fig)

    def _snap_to_bin(self, x):
        idx = int(np.searchsorted(self.bins, x))
        idx = max(0, min(idx, len(self.bins) - 1))
        return float(self.bins[idx])

    def _add_click(self, x):
        self.pending_clicks.append(x)
        if len(self.pending_clicks) < 2:
            self._set_status('1 click pending. Click again to close the interval.')
            self._refresh_intervals()
            self.fig.canvas.draw_idle()
            return
        a, b = sorted(self.pending_clicks[:2])
        self.pending_clicks = []

        # If we know T90, use it as a sanity guard ONLY (no routing).
        if self.has_t90:
            midpoint = 0.5 * (a + b)
            if self.t90_start <= midpoint <= self.t90_stop:
                self._set_status(
                    f'Discarded: midpoint {midpoint:.2f}s inside T90.')
                self._refresh_intervals()
                self.fig.canvas.draw_idle()
                return

        # Assign by time order, not by T90 — works for any burst.
        # First completed interval → pre. Second → post. Subsequent: time-sorted.
        new_interval = (a, b)
        intervals = [iv for iv in (self.pre_interval, self.post_interval, new_interval)
                     if iv is not None]
        # Sort by start time. Earliest = pre, latest = post (keep just 2).
        intervals.sort(key=lambda iv: iv[0])
        if len(intervals) >= 2:
            self.pre_interval = intervals[0]
            self.post_interval = intervals[-1]
        else:
            self.pre_interval = intervals[0]
            self.post_interval = None
        slot = ('pre' if new_interval is self.pre_interval
                else 'post' if new_interval is self.post_interval
                else 'replaced')
        self._set_status(
            f'Interval [{a:.2f}, {b:.2f}] assigned to {slot} (time-order rule).')
        self._refresh_intervals()
        self._refresh_overlay()
        self.fig.canvas.draw_idle()

    def _clear_all(self):
        self.pending_clicks = []
        self.pre_interval = None
        self.post_interval = None
        self._refresh_intervals()
        if self.bkg_overlay_artist is not None:
            try: self.bkg_overlay_artist.remove()
            except Exception: pass
            self.bkg_overlay_artist = None
        self._set_status('Cleared. Click 4 times to redo.')
        self.fig.canvas.draw_idle()

    def _refresh_intervals(self):
        for art in self.fill_artists_top + self.fill_artists_bot:
            try: art.remove()
            except Exception: pass
        self.fill_artists_top = []
        self.fill_artists_bot = []
        for art in self.line_artists:
            try: art.remove()
            except Exception: pass
        self.line_artists = []
        for interval in (self.pre_interval, self.post_interval):
            if interval is None:
                continue
            a, b = interval
            self.fill_artists_top.append(
                self.ax.axvspan(a, b, color='gold', alpha=0.30, zorder=1))
            self.fill_artists_bot.append(
                self.ax_res.axvspan(a, b, color='gold', alpha=0.25, zorder=0))
            for x in (a, b):
                self.line_artists.append(
                    self.ax.axvline(x, color='goldenrod', lw=1.0, alpha=0.85))
        for x in self.pending_clicks:
            self.line_artists.append(self.ax.axvline(
                x, color='black', ls='--', lw=0.8, alpha=0.7))

    def _ensure_tsb(self):
        """Lazy-load 3ML TimeSeriesBuilder once per detector."""
        if self._tsb is not None:
            return
        from threeML import TimeSeriesBuilder
        rsp = self.rsp_file
        if rsp is None:
            cand = glob.glob(
                self.tte_file.replace('glg_tte_', 'glg_cspec_')
                .replace('.fit.gz', '.rsp*'))
            rsp = cand[0] if cand else None
        self._tsb = TimeSeriesBuilder.from_gbm_tte(
            self.det, self.tte_file, rsp_file=rsp, verbose=False)

    def _compute_3ml_polyfit_residuals(self):
        """Run 3ML's two-stage polyfit on current intervals; integrate
        per-channel polynomials over each LC bin; return (bkg_rate, residuals).
        Mirrors gtburst's makeLightCurveWithResiduals (dataHandling.py:2835).
        Returns (None, None) on failure."""
        try:
            self._ensure_tsb()
            pre_str = f'{self.pre_interval[0]:.3f}-{self.pre_interval[1]:.3f}'
            post_str = f'{self.post_interval[0]:.3f}-{self.post_interval[1]:.3f}'
            self._tsb.set_background_interval(pre_str, post_str)
        except Exception as exc:
            self._set_status(
                f'3ML polyfit failed: {type(exc).__name__}: {str(exc)[:80]}')
            return None, None
        ts = self._tsb._time_series
        n = len(self.bin_centers)
        bkg_counts = np.zeros(n)
        bkg_err = np.zeros(n)
        for k in range(n):
            t1, t2 = self.bins[k], self.bins[k + 1]
            try:
                bkg_counts[k] = float(ts.get_total_poly_count(t1, t2))
                bkg_err[k]    = float(ts.get_total_poly_error(t1, t2))
            except Exception:
                bkg_counts[k] = np.nan
                bkg_err[k]    = np.nan
        # gtburst residual formula (dataHandling.py:2882-2883):
        #   residual = (obs - bkg*liveFrac) / sqrt(bkg*liveFrac + (bkg_err*liveFrac)^2)
        # We bin events from TTE with no dead-time correction, so liveFrac = 1.
        # Denominator uses BKG counts (bkg-only hypothesis), not observed.
        obs = self.counts_per_bin
        denom = np.sqrt(np.maximum(bkg_counts + bkg_err**2, 1.0))
        residuals = (obs - bkg_counts) / denom
        bkg_rate = bkg_counts / self.bin_width
        return bkg_rate, residuals

    def _refresh_overlay(self):
        """Run 3ML polyfit → overlay bkg-rate curve on top + errorbar
        residuals on bottom (gtburst style)."""
        # Clear previous
        if self.bkg_overlay_artist is not None:
            try: self.bkg_overlay_artist.remove()
            except Exception: pass
            self.bkg_overlay_artist = None
        for art in self.resid_artists:
            try: art.remove()
            except Exception: pass
        self.resid_artists = []

        if self.pre_interval is None or self.post_interval is None:
            return

        self._set_status('Computing 3ML polyfit + residuals (~3-5 s)...')
        self.fig.canvas.draw()
        try: self.fig.canvas.flush_events()
        except Exception: pass

        bkg_rate, residuals = self._compute_3ml_polyfit_residuals()
        if bkg_rate is None:
            return

        # Top: bkg rate curve
        self.bkg_overlay_artist, = self.ax.plot(
            self.bin_centers, bkg_rate, color='red', lw=1.3, alpha=0.9,
            zorder=3, label='3ML polyfit bkg')

        # Bottom: residual errorbars — matplotlib default style (no fmt),
        # matches gtburst (dataHandling.py:2889 `errorbar(tmean, residuals,
        # yerr=[1 for x in tmean])`).
        try:
            cont = self.ax_res.errorbar(
                self.bin_centers, residuals,
                yerr=np.ones_like(residuals),
                color='black', ecolor='black', elinewidth=0.6, zorder=2,
            )
            self.resid_artists.append(cont[0])
            for art in cont[1]: self.resid_artists.append(art)
            for art in cont[2]: self.resid_artists.append(art)
        except Exception:
            pass

        # gtburst y-limits: ylim(min(residuals), min(max(residuals), 10))
        # i.e. let the bottom be whatever, cap the top at 10σ so the burst
        # spike doesn't crush the bkg-region scatter. (dataHandling.py:2890)
        finite = residuals[np.isfinite(residuals)]
        if len(finite):
            ymin = float(np.min(finite))
            ymax = float(min(np.max(finite), 10.0))
            # Pad a bit so error bars don't clip
            self.ax_res.set_ylim(ymin - 1.0, ymax + 0.5)

        # Summary: fraction of bkg-region bins within ±1σ
        mask_pre = ((self.bin_centers >= self.pre_interval[0])
                    & (self.bin_centers <= self.pre_interval[1]))
        mask_post = ((self.bin_centers >= self.post_interval[0])
                     & (self.bin_centers <= self.post_interval[1]))
        bkg_mask = mask_pre | mask_post
        bres = residuals[bkg_mask]
        bres = bres[np.isfinite(bres)]
        if len(bres):
            frac = np.mean(np.abs(bres) < 1.0)
            self._set_status(
                f'3ML polyfit done. Bkg residuals: '
                f'{100*frac:.0f}% within ±1σ over {len(bres)} bins. '
                f'Burst should rise above zero in residuals.')

    def _set_status(self, msg):
        self.status_text.set_text(msg)

    def _on_key(self, event):
        """Arrow-key micro-adjust of a background edge (09 UX, 4 edges).
        a/s = pre start/stop, d/f = post start/stop; ←/→ = ±1 bin,
        shift+←/→ = ±16 bins; esc exits. Residuals refit after each nudge."""
        EDGES = {'a': ('pre', 0), 's': ('pre', 1), 'd': ('post', 0), 'f': ('post', 1)}
        if event.key in EDGES:
            self._adjust_edge = EDGES[event.key]
            win, i = self._adjust_edge
            iv = self.pre_interval if win == 'pre' else self.post_interval
            cur = f'{iv[i]:.2f}s' if iv else '(unset — place window first)'
            self._set_status(
                f'Adjusting {win}-{"start" if i == 0 else "stop"} = {cur}.  '
                f'arrows ±{self.bin_width:.2f}s, shift ±{16 * self.bin_width:.2f}s, '
                f'esc to exit.')
            self.fig.canvas.draw_idle()
            return
        if event.key == 'escape':
            self._adjust_edge = None
            self._set_status('Adjust mode off.')
            self.fig.canvas.draw_idle()
            return
        if self._adjust_edge is None:
            return
        step = {'left': -1, 'right': 1,
                'shift+left': -16, 'shift+right': 16}.get(event.key)
        if step is None:
            return
        win, i = self._adjust_edge
        iv = self.pre_interval if win == 'pre' else self.post_interval
        if iv is None:
            self._set_status(f'{win} window not set — place it first or seed it.')
            self.fig.canvas.draw_idle()
            return
        iv = list(iv)
        newv = self._snap_to_bin(iv[i] + step * self.bin_width)
        if i == 0:
            newv = min(newv, iv[1] - self.bin_width)     # start stays left of stop
        else:
            newv = max(newv, iv[0] + self.bin_width)     # stop stays right of start
        iv[i] = newv
        if win == 'pre':
            self.pre_interval = tuple(iv)
        else:
            self.post_interval = tuple(iv)
        self._refresh_intervals()
        self._refresh_overlay()      # refit 3ML polyfit + residuals (~3-5 s)
        self.fig.canvas.draw_idle()

    def run(self):
        plt.show(block=True)
        return self.result, self.pre_interval, self.post_interval

# Constants matching gtburst conventions
NAI_LOW_BAND = (8.0, 900.0)        # keV, the standard NaI display band
BGO_LOW_BAND = (250.0, 40000.0)    # keV, BGO display band
LC_BIN_S = 1.024                   # gtburst CSPEC native cadence (asymptotic)

LOW_SIDE_NAI = {'n0', 'n1', 'n2', 'n3', 'n4', 'n5'}
ALL_DETECTORS = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5',
                 'n6', 'n7', 'n8', 'n9', 'na', 'nb', 'b0', 'b1']
ANGLE_THRESHOLD_DEG = 50.0  # NaI ≤ 50° pre-ticked (Goldstein+ 2012 conservative cut)
ANGLE_RESCUE_DEG = 60.0     # BCAT NaI ≤ 60° also kept (it triggered; borderline geometry)
# Bayesian Blocks event-mode is ~O(N^2) and OOMs/segfaults the native layer with
# NO Python traceback above ~1.4M events. Above this, bin first. 500k is well
# below the ~1.3M known-good ceiling. See project_bb_oom_extreme_bursts.
MAX_BB_EVENTS = 500_000

# Meegan+ 2009 NaI/BGO pointing directions in spacecraft (zenith, azimuth) degrees.
# Copied from fermitools/GtBurst/angularDistance.py:7-22.
DET_DIR = {
    'n0': (20.58,  45.89),  'n6': (20.43, 224.93),
    'n1': (45.31,  45.11),  'n7': (46.18, 224.62),
    'n2': (90.21,  58.44),  'n8': (89.97, 236.61),
    'n3': (45.24, 314.87),  'n9': (45.55, 135.19),
    'n4': (90.27, 303.15),  'na': (90.42, 123.73),
    'n5': (89.79,   3.35),  'nb': (90.32, 183.74),
    'b0': (90.0,    0.00),  'b1': (90.0,  180.00),
}


# ============================================================================
# Helpers
# ============================================================================

def _detector_kind(det):
    if det.startswith('n'):
        return 'nai'
    if det.startswith('b'):
        return 'bgo'
    return 'unknown'


def _band_for_det(det):
    return NAI_LOW_BAND if _detector_kind(det) == 'nai' else BGO_LOW_BAND


def get_grb_row(trigger, sample):
    rows = sample[sample['TRIGGER_NAME'] == trigger]
    if len(rows) == 0:
        raise SystemExit(f"{trigger} not in results/grb_sample.ecsv")
    return rows[0]


def default_detector_list(row):
    """All NaIs in BCAT mask + corresponding BGO. Pre-ticked in the GUI."""
    nai = [d.strip() for d in str(row['NAI_DETECTORS']).split(',') if d.strip()]
    if not nai:
        return [], None
    n_low = sum(1 for d in nai if d in LOW_SIDE_NAI)
    bgo = 'b0' if n_low >= len(nai) - n_low else 'b1'
    return nai, bgo


def find_tte(trigger, det):
    matches = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_tte_{det}_*.fit.gz'))
    return matches[0] if matches else None


def find_rsp(trigger, det):
    matches = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_cspec_{det}_*.rsp*'))
    return matches[0] if matches else None


# ============================================================================
# Spacecraft pointing + detector-angle math (port of gtburst's angularDistance)
# ============================================================================

def _vec_from_radec(ra_deg, dec_deg):
    r = np.deg2rad(ra_deg)
    d = np.deg2rad(dec_deg)
    cd = np.cos(d)
    return np.array([cd * np.cos(r), cd * np.sin(r), np.sin(d)])


def _radec_from_vec(v):
    v = v / np.linalg.norm(v)
    ra = np.rad2deg(np.arctan2(v[1], v[0]))
    if ra < 0: ra += 360.0
    dec = np.rad2deg(np.arcsin(np.clip(v[2], -1.0, 1.0)))
    return float(ra), float(dec)


def _angular_distance(ra1, dec1, ra2, dec2):
    """Vincenty formula (gtburst's getAngularDistance)."""
    lon1, lat1, lon2, lat2 = map(np.deg2rad, (ra1, dec1, ra2, dec2))
    sdlon = np.sin(lon2 - lon1); cdlon = np.cos(lon2 - lon1)
    slat1 = np.sin(lat1); slat2 = np.sin(lat2)
    clat1 = np.cos(lat1); clat2 = np.cos(lat2)
    num1 = clat2 * sdlon
    num2 = clat1 * slat2 - slat1 * clat2 * cdlon
    denom = slat1 * slat2 + clat1 * clat2 * cdlon
    return float(np.rad2deg(np.arctan2(np.sqrt(num1**2 + num2**2), denom)))


def _rodrigues(axis_vec, angle_deg):
    """Rotation matrix for rotation by angle_deg around unit axis vector."""
    a = np.deg2rad(angle_deg)
    ax = axis_vec / np.linalg.norm(axis_vec)
    K = np.array([[0,     -ax[2],  ax[1]],
                  [ax[2],  0,     -ax[0]],
                  [-ax[1], ax[0],  0    ]])
    return np.eye(3) + np.sin(a) * K + (1.0 - np.cos(a)) * (K @ K)


def _detector_radec(ra_scx, dec_scx, ra_scz, dec_scz, theta_det, phi_det):
    """Where the detector points in J2000 (gtburst's getRaDec).
    Rotate SCX around SCZ by phi_det, then rotate SCZ around the new Y by theta_det.
    """
    vx = _vec_from_radec(ra_scx, dec_scx)
    vz = _vec_from_radec(ra_scz, dec_scz)
    vxx = _rodrigues(vz, phi_det) @ vx
    vy = np.cross(vz, vxx)
    vzz = _rodrigues(vy, theta_det) @ vz
    return _radec_from_vec(vzz)


def get_detector_angle(ra_scx, dec_scx, ra_scz, dec_scz, src_ra, src_dec, det):
    """Angular separation (deg) between detector pointing and source."""
    theta_det, phi_det = DET_DIR[det]
    det_ra, det_dec = _detector_radec(ra_scx, dec_scx, ra_scz, dec_scz,
                                      theta_det, phi_det)
    return _angular_distance(src_ra, src_dec, det_ra, det_dec)


def _quaternion_axis_to_radec(q, body_axis):
    """Quaternion (q1, q2, q3, q4) with q4 scalar (POSHIST convention).
    Return (RA, DEC) in J2000 of a body-frame axis vector."""
    q1, q2, q3, q4 = q
    R = np.array([
        [1 - 2 * (q2 * q2 + q3 * q3), 2 * (q1 * q2 - q3 * q4),     2 * (q1 * q3 + q2 * q4)],
        [2 * (q1 * q2 + q3 * q4),     1 - 2 * (q1 * q1 + q3 * q3), 2 * (q2 * q3 - q1 * q4)],
        [2 * (q1 * q3 - q2 * q4),     2 * (q2 * q3 + q1 * q4),     1 - 2 * (q1 * q1 + q2 * q2)],
    ])
    return _radec_from_vec(R @ np.asarray(body_axis, dtype=float))


def _trigger_date_parts(trigger):
    """bn200607921 → ('2020', '06', '07', '200607')."""
    m = re.match(r'bn(\d{2})(\d{2})(\d{2})\d{3}$', trigger)
    if not m:
        raise ValueError(f"Cannot parse trigger {trigger}")
    yy, mm, dd = m.groups()
    yyyy = '20' + yy if int(yy) < 80 else '19' + yy
    return yyyy, mm, dd, yy + mm + dd


def download_poshist(trigger, dest_dir):
    """Fetch glg_poshist_all_<YYMMDD>_v*.fit from FSSC for this trigger's day."""
    yyyy, mm, dd, yymmdd = _trigger_date_parts(trigger)
    os.makedirs(dest_dir, exist_ok=True)
    existing = sorted(glob.glob(os.path.join(dest_dir, f'glg_poshist_all_{yymmdd}_v*.fit')))
    if existing:
        return existing[-1]
    base = f'https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/daily/{yyyy}/{mm}/{dd}/current'
    for v in ['v01', 'v00', 'v02']:
        fn = f'glg_poshist_all_{yymmdd}_{v}.fit'
        url = f'{base}/{fn}'
        out = os.path.join(dest_dir, fn)
        print(f'  fetching POSHIST {fn} ...', end=' ', flush=True)
        try:
            urllib.request.urlretrieve(url, out)
            print('OK')
            return out
        except Exception as exc:
            print(f'fail ({type(exc).__name__})')
            try: os.remove(out)
            except FileNotFoundError: pass
    raise RuntimeError(f'Could not download POSHIST for {trigger}')


def get_pointing_at_trigger(poshist_file, trigtime_met):
    """Open POSHIST, find rows bracketing trigtime_met, return interpolated
    (ra_scx, dec_scx, ra_scz, dec_scz). Handles both direct RA_SCX/Z columns
    and quaternion-only formats."""
    with fits.open(poshist_file) as hdul:
        ext = None
        for hdu in hdul:
            if hdu.name in ('GLAST POS HIST', 'SC_DATA'):
                ext = hdu
                break
        if ext is None:
            raise RuntimeError(f'No POSHIST extension in {poshist_file}')
        data = ext.data
        cols = data.dtype.names
        time_col = 'SCLK_UTC' if 'SCLK_UTC' in cols else 'TIME'
        time = np.array(data[time_col])
        idx_after = int(np.searchsorted(time, trigtime_met))
        idx_before = idx_after - 1
        if idx_after >= len(time) or idx_before < 0:
            raise RuntimeError(f'POSHIST does not cover trigtime {trigtime_met}')

        if all(c in cols for c in ('RA_SCX', 'DEC_SCX', 'RA_SCZ', 'DEC_SCZ')):
            def interp(col):
                return float(np.interp(trigtime_met,
                                       [time[idx_before], time[idx_after]],
                                       [data[col][idx_before], data[col][idx_after]]))
            return interp('RA_SCX'), interp('DEC_SCX'), interp('RA_SCZ'), interp('DEC_SCZ')

        if 'QSJ_1' in cols:
            q_b = np.array([data['QSJ_1'][idx_before], data['QSJ_2'][idx_before],
                            data['QSJ_3'][idx_before], data['QSJ_4'][idx_before]], dtype=float)
            q_a = np.array([data['QSJ_1'][idx_after], data['QSJ_2'][idx_after],
                            data['QSJ_3'][idx_after], data['QSJ_4'][idx_after]], dtype=float)
            frac = (trigtime_met - time[idx_before]) / max(time[idx_after] - time[idx_before], 1e-9)
            q = (1.0 - frac) * q_b + frac * q_a
            q = q / np.linalg.norm(q)
            ra_scx, dec_scx = _quaternion_axis_to_radec(q, [1.0, 0.0, 0.0])
            ra_scz, dec_scz = _quaternion_axis_to_radec(q, [0.0, 0.0, 1.0])
            return ra_scx, dec_scx, ra_scz, dec_scz

        raise RuntimeError(f'POSHIST has neither RA_SCX/Z nor QSJ_n columns. Got {cols}')


def get_trigtime_met(trigger):
    """Read TRIGTIME (MET) from any existing TTE primary header."""
    grb_dir = os.path.join(DATA_DIR, trigger)
    for tte in glob.glob(os.path.join(grb_dir, 'glg_tte_*_*.fit.gz')):
        with fits.open(tte) as hdul:
            tt = hdul[0].header.get('TRIGTIME')
            if tt is not None:
                return float(tt)
    raise RuntimeError(f'No TTE with TRIGTIME for {trigger} — '
                       'download at least one detector first.')


def ensure_tte_for_detector(trigger, det):
    """If TTE+RSP for this det already exist, return True. Else fetch via 3ML."""
    if find_tte(trigger, det) and find_rsp(trigger, det):
        return True
    from threeML import download_GBM_trigger_data
    grb_dir = os.path.join(DATA_DIR, trigger)
    os.makedirs(grb_dir, exist_ok=True)
    print(f'  downloading TTE/RSP for {det} ...', end=' ', flush=True)
    try:
        download_GBM_trigger_data(trigger, detectors=[det],
                                  destination_directory=grb_dir,
                                  compress_tte=True)
        ok = (find_tte(trigger, det) is not None
              and find_rsp(trigger, det) is not None)
        print('OK' if ok else 'fail (files missing after download)')
        return ok
    except Exception as exc:
        print(f'fail ({type(exc).__name__}: {exc})')
        return False


# ============================================================================
# Step 1 — Detector picker GUI
# ============================================================================

def pick_detectors_with_angles_gui(trigger, angles, pre_ticked, bcat_mask,
                                   src_ra, src_dec):
    """
    Show all 14 GBM detectors sorted by angle ascending. Labels include
    angle and BCAT-mask indicator. Returns list of user-OK'd detectors.
    """
    sorted_dets = sorted(angles.keys(), key=lambda d: angles[d])

    fig = plt.figure(figsize=(11.0, 0.36 * len(sorted_dets) + 3.0))
    # Use suptitle for the main heading and fig.text for the long
    # instruction so they don't overflow the axes width.
    fig.suptitle(
        f'{trigger}    source = ({src_ra:.2f}, {src_dec:.2f})',
        fontsize=13, weight='bold', y=0.97,
    )
    fig.text(
        0.5, 0.93,
        f'All 14 GBM detectors, sorted by angle to source.   '
        f'Pre-ticked: NaI θ ≤ {ANGLE_THRESHOLD_DEG:.0f}° + matching BGO.',
        fontsize=10, ha='center', va='top',
    )
    fig.text(
        0.5, 0.905,
        '(Tick / untick as desired. Detectors without TTE on disk will be '
        'downloaded on Accept.)',
        fontsize=9, ha='center', va='top', style='italic', color='0.35',
    )

    labels = []
    for d in sorted_dets:
        kind = 'BGO' if _detector_kind(d) == 'bgo' else 'NaI'
        bcat = '✓ BCAT' if d in bcat_mask else '      '
        labels.append(f'{d}   θ = {angles[d]:6.1f}°   ({kind})   {bcat}')

    init_state = [d in pre_ticked for d in sorted_dets]
    # Leave generous top margin for the suptitle / instruction lines.
    check_ax = fig.add_axes([0.18, 0.05, 0.52, 0.82])
    checks = CheckButtons(check_ax, labels, init_state)

    result = {'quit': False}
    btn_accept = fig.text(0.80, 0.55, 'Accept', backgroundcolor='green',
                          color='white', weight='bold', picker=20,
                          fontsize=13, ha='left', va='center')
    btn_quit = fig.text(0.80, 0.42, 'Quit', backgroundcolor='gray',
                        color='white', weight='bold', picker=20,
                        fontsize=11, ha='left', va='center')

    def on_pick(event):
        if event.mouseevent.button != 1:
            return
        if event.artist is btn_accept:
            plt.close(fig)
        elif event.artist is btn_quit:
            result['quit'] = True
            plt.close(fig)

    fig.canvas.mpl_connect('pick_event', on_pick)
    plt.show(block=True)

    if result['quit']:
        raise SystemExit('User quit detector selection.')

    states = checks.get_status()
    return [sorted_dets[i] for i, s in enumerate(states) if s]


# ============================================================================
# Step 2 — Render raw 1.024-s LC PNG (no T90 annotation)
# ============================================================================

def render_lc_png(trigger, det, t90_start, t90, outpath):
    """
    1.024-s binned LC PNG for one detector.
    NaI: 8-900 keV. BGO: 250-40000 keV. Linear y-axis. No T90 shading
    (AI should identify burst region from the data alone).
    """
    tte = find_tte(trigger, det)
    if tte is None:
        raise FileNotFoundError(f"No TTE for {trigger} {det}")

    band_lo, band_hi = _band_for_det(det)

    with fits.open(tte) as hdul:
        evts = hdul['EVENTS'].data
        trigtime = hdul['PRIMARY'].header.get('TRIGTIME', 0.0)
        ebounds = hdul['EBOUNDS'].data
        chan_emin = ebounds['E_MIN']
        chan_emax = ebounds['E_MAX']
        n_chan = len(chan_emin)

        pha = evts['PHA']
        times = evts['TIME']
        valid = pha < n_chan

        e_lo = chan_emin[np.clip(pha, 0, n_chan - 1)]
        e_hi = chan_emax[np.clip(pha, 0, n_chan - 1)]
        in_band = valid & (e_lo >= band_lo) & (e_hi <= band_hi)

        t_rel = times[in_band] - trigtime

    # Plot window
    if t90 is not None and t90_start is not None:
        burst_stop = t90_start + t90
        pad = max(150.0, 6.0 * t90)
        tmin = max(t_rel.min() if len(t_rel) else -100.0, t90_start - pad)
        tmax = min(t_rel.max() if len(t_rel) else 200.0, burst_stop + 2.0 * pad)
    else:
        # No T90 — use full event-time extent (clipped to a sane width)
        tmin = float(t_rel.min()) if len(t_rel) else -150.0
        tmax = float(t_rel.max()) if len(t_rel) else 500.0
        # Clip to ±1000 s to keep the PNG readable
        tmin = max(tmin, -1000.0)
        tmax = min(tmax,  1500.0)

    bins = np.arange(tmin, tmax + LC_BIN_S, LC_BIN_S)
    counts, _ = np.histogram(t_rel, bins=bins)
    centers = 0.5 * (bins[:-1] + bins[1:])
    rate = counts / LC_BIN_S

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.step(centers, rate, where='mid', color='black', lw=0.7)
    ax.set_xlabel('Time since trigger (s)', fontsize=11)
    ax.set_ylabel(r'Counts s$^{-1}$', fontsize=11)
    ax.set_title(
        f'{trigger}  ({det})  —  {LC_BIN_S}-s bins, {band_lo:.0f}-{band_hi:.0f} keV',
        fontsize=11,
    )
    ax.set_xlim(tmin, tmax)
    ax.grid(alpha=0.25, lw=0.4)
    fig.tight_layout()
    fig.savefig(outpath, dpi=120, bbox_inches='tight')
    plt.close(fig)

    return {
        't_min': float(tmin),
        't_max': float(tmax),
        'n_bins': int(len(centers)),
        'band_lo_kev': float(band_lo),
        'band_hi_kev': float(band_hi),
        'bin_s': float(LC_BIN_S),
    }


# ============================================================================
# Step 5 — Bkg approval GUI (uses existing BackgroundSelector)
# ============================================================================

def review_one_detector(trigger, det, ai_intervals, t90_start, t90):
    """
    Open the existing gtburst-style picker pre-populated with AI's intervals.
    Returns (result, pre, post) where result is 'accept'|'skip'|'quit'.

    NOTE: t90_start/t90 are explicitly NOT passed through to the picker.
    The GUI shows only the LC and the bkg windows — no T90 shading, no
    midpoint-discard guard. Click routing uses time-order rule.
    """
    tte = find_tte(trigger, det)
    rsp = find_rsp(trigger, det)
    if tte is None:
        return 'skip', None, None
    pre_seed = tuple(ai_intervals['pre']) if 'pre' in ai_intervals else None
    post_seed = tuple(ai_intervals['post']) if 'post' in ai_intervals else None
    sel = BackgroundSelector(
        trigger, det, tte, rsp_file=rsp,
        t90_start=None, t90=None,    # T90-free GUI
        prev_pre=pre_seed, prev_post=post_seed,
    )
    return sel.run()


# ============================================================================
# Step 6 — Bayesian blocks on approved intervals
# ============================================================================

def _merge_subthreshold_blocks(tsb, threshold=3.0, max_iter=200):
    """
    Phase-A merge: walk blocks left-to-right; for each block with
    significance < threshold, merge with the lower-significance flanking
    neighbor (forced right at i=0, left at i=N-1, tie→right). Recompute
    significance via 3ML by reinstalling custom bins. Iterate until all
    blocks pass or only one remains.

    Returns dict with starts, stops, sigs, is_merged (bool per final block),
    constituent_count (int per final block).
    """
    starts = list(np.array(tsb.bins.starts))
    stops = list(np.array(tsb.bins.stops))
    sigs = list(np.array(tsb.significance_per_interval))
    is_merged = [False] * len(starts)
    constituent_count = [1] * len(starts)

    iters = 0
    while iters < max_iter:
        iters += 1
        if len(sigs) <= 1:
            break
        if all(s >= threshold for s in sigs):
            break
        # First (leftmost) sub-threshold block
        i = next((k for k, s in enumerate(sigs) if s < threshold), None)
        if i is None:
            break
        # Pick lower-sig flanking neighbor (forced at edges, tie→right)
        if i == 0:
            partner = 1
        elif i == len(sigs) - 1:
            partner = i - 1
        else:
            partner = (i - 1) if sigs[i - 1] < sigs[i + 1] else (i + 1)
        a, b = sorted([i, partner])
        new_start = min(starts[a], starts[b])
        new_stop = max(stops[a], stops[b])
        merged_const = constituent_count[a] + constituent_count[b]

        # Build new bin list with the merged block in slot a, drop b
        starts[a] = new_start
        stops[a] = new_stop
        is_merged[a] = True
        constituent_count[a] = merged_const
        del starts[b]; del stops[b]; del is_merged[b]; del constituent_count[b]

        # Reinstall custom bins; recompute significances
        tsb.create_time_bins(method='custom', start=list(starts), stop=list(stops))
        sigs = list(np.array(tsb.significance_per_interval))

    return {
        'starts': starts, 'stops': stops, 'sigs': sigs,
        'is_merged': is_merged, 'constituent_count': constituent_count,
        'n_merge_iters': iters,
    }


def run_bb_for_detector(trigger, det, t90_start, t90,
                        pre_interval, post_interval, p0=0.01,
                        merge_threshold=3.0):
    """
    TimeSeriesBuilder.set_background_interval(...) → create_time_bins
    (method='bayesblocks', use_background=True) over the T90 window →
    Phase-A merge of sub-3σ blocks. Returns merged block boundaries +
    per-block significance, is_merged flags, and constituent counts.
    """
    from threeML import TimeSeriesBuilder

    tte = find_tte(trigger, det)
    rsp = find_rsp(trigger, det)
    if tte is None or rsp is None:
        raise FileNotFoundError(f"Missing TTE or RSP for {trigger} {det}")

    burst_start = float(pre_interval[1])
    burst_stop = float(post_interval[0])

    # OOM guard: this broadband BB is VISUALIZATION-ONLY (plot panel d). 3ML's
    # native bayesblocks segfaults/OOMs (no catchable traceback) on extreme-count
    # bursts, so PRE-CHECK and skip — the SCIENCE BB (run_bb_for_detector_8_900,
    # binned for high counts) still runs. See project_bb_oom_extreme_bursts.
    with fits.open(tte) as _h:
        _t0 = _h['PRIMARY'].header.get('TRIGTIME', 0.0)
        _tt = np.asarray(_h['EVENTS'].data['TIME']) - _t0
    _nev = int(np.count_nonzero((_tt >= burst_start) & (_tt <= burst_stop)))
    if _nev > MAX_BB_EVENTS:
        print(f'  [BB-guard] {det}: {_nev:,} events in window > {MAX_BB_EVENTS:,} '
              f'-> SKIP broadband (viz) BB; spectral BB still runs')
        return {'starts': [], 'stops': [], 'sigs': [], 'is_merged': [],
                'constituent_count': [], 'n_merge_iters': 0,
                'raw_starts': [], 'raw_stops': [], 'raw_sigs': [],
                'poly_order': -1, 'pre_interval': list(pre_interval),
                'post_interval': list(post_interval)}

    tsb = TimeSeriesBuilder.from_gbm_tte(det, tte, rsp_file=rsp, verbose=False)
    pre_str = f'{pre_interval[0]:.3f}-{pre_interval[1]:.3f}'
    post_str = f'{post_interval[0]:.3f}-{post_interval[1]:.3f}'
    tsb.set_background_interval(pre_str, post_str)

    # BB search window = between user-clicked bkg windows (pre_stop, post_start).
    # NO catalog T90 used here — works identically for unpublished bursts.
    # See memory feedback_no_catalog_t90_in_gui.md.
    tsb.set_active_time_interval(f'{burst_start:.3f}-{burst_stop:.3f}')
    tsb.create_time_bins(burst_start, burst_stop,
                         method='bayesblocks', p0=p0, use_background=True)

    pre_starts = list(np.array(tsb.bins.starts))
    pre_stops = list(np.array(tsb.bins.stops))
    pre_sigs = list(np.array(tsb.significance_per_interval))

    merged = _merge_subthreshold_blocks(tsb, threshold=merge_threshold)

    return {
        # final (post-merge) blocks
        'starts': merged['starts'],
        'stops': merged['stops'],
        'sigs': merged['sigs'],
        'is_merged': merged['is_merged'],
        'constituent_count': merged['constituent_count'],
        'n_merge_iters': merged['n_merge_iters'],
        # raw (pre-merge) for diagnostic
        'raw_starts': pre_starts,
        'raw_stops': pre_stops,
        'raw_sigs': pre_sigs,
        'poly_order': int(getattr(tsb, 'background_poly_order', -1)),
        'pre_interval': list(pre_interval),
        'post_interval': list(post_interval),
    }


def _compute_t_int_for_burst(t_band, ts, chan_mask, burst_start, burst_stop,
                             lc_bin_s=0.064, smooth_window=16,
                             frac=0.03, min_consec_below=32):
    """Smoothed-rate-threshold T_INT (Fermi 4.5σ noise floor variant);
    see scripts/09_review_time_integrated.py for full algorithm doc.
    Returns (t_int_start, t_int_stop) or (None, None) if no positive net."""
    bins = np.arange(burst_start, burst_stop + lc_bin_s, lc_bin_s)
    counts, _ = np.histogram(t_band, bins=bins)
    bkg = np.array([float(ts.get_total_poly_count(bins[k], bins[k+1], mask=chan_mask))
                    for k in range(len(bins) - 1)])
    net = counts.astype(float) - bkg
    if not np.any(net > 0):
        return None, None
    # Smooth
    w = max(int(smooth_window), 1)
    kernel = np.ones(w) / float(w)
    pad = w // 2
    padded = np.concatenate([net[pad-1::-1], net, net[:-pad-1:-1]])
    ns = np.convolve(padded, kernel, mode='valid')
    extra = len(ns) - len(net); lo = extra // 2
    ns = ns[lo:lo + len(net)]

    ipk = int(np.argmax(ns))
    peak_s = float(ns[ipk])
    if peak_s <= 0:
        return None, None
    bkg_mean_per_bin = float(np.mean(bkg)) if len(bkg) else 0.0
    sigma_smoothed = np.sqrt(max(bkg_mean_per_bin, 1.0)) / np.sqrt(w)
    thr = max(frac * peak_s, 4.5 * sigma_smoothed)

    def _walk_one(walk):
        run = 0; last_above = 0
        for i in range(1, len(walk)):
            if walk[i] < thr:
                run += 1
                if run >= min_consec_below:
                    return last_above
            else:
                run = 0
                last_above = i
        return len(walk) - 1

    def _walk(direction):
        ext_thr = 2.0 * thr
        n = len(ns)
        if direction == 'forward':
            edge = ipk + _walk_one(ns[ipk:])
            for _ in range(20):
                lo_i = edge + 1
                if lo_i >= n: break
                if ns[lo_i:].max() < ext_thr: break
                new_ipk = lo_i + int(np.argmax(ns[lo_i:]))
                new_edge = new_ipk + _walk_one(ns[new_ipk:])
                if new_edge <= edge: break
                edge = new_edge
            return edge
        else:
            edge = ipk - _walk_one(ns[ipk::-1])
            for _ in range(20):
                hi = edge - 1
                if hi < 0: break
                if ns[:hi + 1].max() < ext_thr: break
                new_ipk = int(np.argmax(ns[:hi + 1]))
                new_edge = new_ipk - _walk_one(ns[new_ipk::-1])
                if new_edge >= edge: break
                edge = new_edge
            return edge

    i_stop = min(_walk('forward'), len(bins) - 2)
    i_start = max(_walk('backward'), 0)
    return float(bins[i_start]), float(bins[i_stop + 1])


def run_bb_for_detector_8_900(trigger, det, pre_interval, post_interval,
                              p0=0.01, merge_threshold=3.0,
                              band=(8.0, 900.0)):
    """
    BB on events restricted to the 8-900 keV NaI spectral band
    (= the channels used by downstream spectral fitting). Block edges
    here drive per-block PHA extraction, so they should reflect rate
    changes IN the spectral-fit band, not broadband (which can include
    out-of-band channels with their own structure).

    Uses astropy.stats.bayesian_blocks (event mode) on the energy-filtered
    arrival times. Per-block significance is computed manually via the
    polyfit bkg integrated with a CHANNEL MASK matching the band, so
    the significance is also in 8-900 keV.

    Phase-A sub-merge_threshold merge is applied identically.

    Returns same dict shape as run_bb_for_detector(), with an extra
    'band' field documenting the energy restriction.
    """
    from threeML import TimeSeriesBuilder
    import astropy.stats as astats

    tte = find_tte(trigger, det)
    rsp = find_rsp(trigger, det)
    if tte is None or rsp is None:
        raise FileNotFoundError(f"Missing TTE or RSP for {trigger} {det}")

    # 3ML TSB for the polyfit + per-block bkg integration
    tsb = TimeSeriesBuilder.from_gbm_tte(det, tte, rsp_file=rsp, verbose=False)
    pre_str = f'{pre_interval[0]:.3f}-{pre_interval[1]:.3f}'
    post_str = f'{post_interval[0]:.3f}-{post_interval[1]:.3f}'
    tsb.set_background_interval(pre_str, post_str)
    ts = tsb._time_series

    # Read raw events + build channel mask for the band
    with fits.open(tte) as hdul:
        evts = hdul['EVENTS'].data
        trigtime = hdul['PRIMARY'].header.get('TRIGTIME', 0.0)
        eb = hdul['EBOUNDS'].data
        cmin = eb['E_MIN']; cmax = eb['E_MAX']
        n_chan = len(cmin)
        pha = evts['PHA']; times = evts['TIME']
        valid = pha < n_chan
        e_lo = cmin[np.clip(pha, 0, n_chan - 1)]
        e_hi = cmax[np.clip(pha, 0, n_chan - 1)]
        in_band = valid & (e_lo >= band[0]) & (e_hi <= band[1])
        t_band = times[in_band] - trigtime
        chan_mask = (cmin >= band[0]) & (cmax <= band[1])

    burst_start = float(pre_interval[1])
    burst_stop = float(post_interval[0])
    t_in_search = t_band[(t_band >= burst_start) & (t_band <= burst_stop)]
    if len(t_in_search) < 20:
        raise RuntimeError(
            f'Too few {band[0]}-{band[1]} keV events ({len(t_in_search)}) '
            f'in search window [{burst_start:.2f}, {burst_stop:.2f}] '
            f'for BB on {trigger} {det}')

    # Astropy BB on event arrival times across FULL search window.
    # BB sees the bkg+burst+bkg context (constrains edge change-points).
    # OOM guard: event-mode BB scales ~O(N^2) and segfaults the native layer
    # (no traceback) above ~1.4M events (bn130427324, bn230802285). Above
    # MAX_BB_EVENTS, run BB on a finely-binned light curve via fitness='measures'
    # (Gaussian per-bin; valid at high counts/bin). Validated to reproduce
    # event-mode block structure (pulse onset within ~1 bin). See
    # project_bb_oom_extreme_bursts.
    if t_in_search.size > MAX_BB_EVENTS:
        _dt = 0.064
        _edges = np.arange(burst_start, burst_stop + _dt, _dt)
        _cnt, _ = np.histogram(t_in_search, bins=_edges)
        _ctr = 0.5 * (_edges[:-1] + _edges[1:])
        _rate = _cnt / _dt
        _err = np.sqrt(np.maximum(_cnt, 1)) / _dt
        print(f'  [BB-guard] {det}: {t_in_search.size:,} events > {MAX_BB_EVENTS:,} '
              f'-> binned BB (fitness=measures) at {_dt*1e3:.0f} ms')
        edges = astats.bayesian_blocks(_ctr, _rate, _err,
                                       fitness='measures', p0=p0)
    else:
        edges = astats.bayesian_blocks(t_in_search, fitness='events', p0=p0)
    starts_full = list(np.asarray(edges[:-1], dtype=float))
    stops_full  = list(np.asarray(edges[1:], dtype=float))

    # Determine T_INT (burst extent) via smoothed-rate threshold.
    # Filter BB blocks to those overlapping T_INT; clip the edge blocks
    # to T_INT boundaries. Outside-T_INT blocks (pre/post bkg tails) get
    # dropped here so spectral fits only see the actual burst signal.
    t_int_start, t_int_stop = _compute_t_int_for_burst(
        t_band, ts, chan_mask, burst_start, burst_stop)
    if t_int_start is None:
        # No positive net detected — fall back to full search window
        t_int_start, t_int_stop = burst_start, burst_stop

    starts, stops = [], []
    for s, e in zip(starts_full, stops_full):
        if e <= t_int_start or s >= t_int_stop:
            continue  # entirely outside T_INT — drop
        starts.append(max(s, t_int_start))
        stops.append(min(e, t_int_stop))

    def _sig_for_block(t1, t2):
        obs = float(np.sum((t_band >= t1) & (t_band < t2)))
        try:
            bkg = float(ts.get_total_poly_count(t1, t2, mask=chan_mask))
            bkg_err = float(ts.get_total_poly_error(t1, t2, mask=chan_mask))
        except TypeError as exc:
            raise RuntimeError(
                'Installed 3ML does not support mask= in '
                'get_total_poly_count. Upgrade 3ML or implement a manual '
                'masked sum.') from exc
        denom = np.sqrt(max(bkg + bkg_err ** 2, 1.0))
        return (obs - bkg) / denom

    # Sigs of RAW (unfiltered) blocks for diagnostic; filtered sigs for merge
    raw_sigs_full = [_sig_for_block(a, b)
                     for a, b in zip(starts_full, stops_full)]
    pre_sigs = [_sig_for_block(a, b) for a, b in zip(starts, stops)]

    # Phase-A merge: sub-3σ blocks → merge with lower-sig flanking neighbor.
    # Inline port of _merge_subthreshold_blocks since we don't have a 3ML
    # tsb.create_time_bins handle here (we're not pushing edges back into 3ML).
    is_merged = [False] * len(starts)
    cnt = [1] * len(starts)
    sigs = list(pre_sigs)
    n_iter = 0
    while n_iter < 200:
        n_iter += 1
        if len(sigs) <= 1 or all(s >= merge_threshold for s in sigs):
            break
        i = next((k for k, s in enumerate(sigs) if s < merge_threshold), None)
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
        stops[a]  = max(stops[a], stops[b])
        is_merged[a] = True
        cnt[a] = cnt[a] + cnt[b]
        del starts[b]; del stops[b]; del is_merged[b]; del cnt[b]
        # Recompute sigs for merged block + neighbors (others unchanged)
        sigs = [_sig_for_block(starts[k], stops[k]) for k in range(len(starts))]

    return {
        # FINAL spectral-fit blocks: BB → filter to T_INT → clip edges → merge
        'starts': starts, 'stops': stops, 'sigs': sigs,
        'is_merged': is_merged, 'constituent_count': cnt,
        'n_merge_iters': n_iter,
        # Raw BB output over the FULL search window (pre-filter, pre-merge)
        'raw_starts': starts_full,
        'raw_stops':  stops_full,
        'raw_sigs':   raw_sigs_full,
        # T_INT used as the filter window
        't_int_start': t_int_start,
        't_int_stop':  t_int_stop,
        'poly_order': int(getattr(tsb, 'background_poly_order', -1)),
        'pre_interval': list(pre_interval),
        'post_interval': list(post_interval),
        'band': band,
    }


# ============================================================================
# Persistence
# ============================================================================

def save_pending_manifest(trigger, dets_with_meta, path):
    t90s = dets_with_meta['t90']
    t90_start = dets_with_meta['t90_start']
    t90_stop = (t90_start + t90s
                if (t90s is not None and t90_start is not None) else None)
    manifest = {
        'trigger': trigger,
        't90_start_s': t90_start,
        't90_s': t90s,
        't90_stop_s': t90_stop,
        'detectors': dets_with_meta['detectors'],
    }
    with open(path, 'w') as f:
        json.dump(manifest, f, indent=2)


def load_ai_selections(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_bkg_row(trigger, det, pre, post, target_path):
    """Append/replace one (trigger, det) row in the prototype's ECSV.
    Uses fcntl exclusive lock so concurrent workers (script 11) can't
    corrupt the shared ECSV via read-modify-write races."""
    import fcntl
    new = {
        'TRIGGER_NAME': trigger,
        'DETECTOR': det,
        'BKG_NEG_START': float(pre[0]),
        'BKG_NEG_STOP': float(pre[1]),
        'BKG_POS_START': float(post[0]),
        'BKG_POS_STOP': float(post[1]),
    }
    lock_path = target_path + '.lock'
    with open(lock_path, 'w') as lock_fp:
        fcntl.flock(lock_fp, fcntl.LOCK_EX)
        try:
            if os.path.exists(target_path):
                t = Table.read(target_path, format='ascii.ecsv')
                mask = ~((t['TRIGGER_NAME'] == trigger) & (t['DETECTOR'] == det))
                t = t[mask]
                t.add_row(new)
            else:
                t = Table([[new[k]] for k in new], names=list(new.keys()))
            # Atomic rename to prevent half-written file races.
            tmp = target_path + '.tmp'
            t.write(tmp, format='ascii.ecsv', overwrite=True)
            os.replace(tmp, target_path)
        finally:
            fcntl.flock(lock_fp, fcntl.LOCK_UN)


def save_bb_blocks(trigger, all_blocks, target_path):
    """Write one row per (det, block) to bb_blocks_prototype_<trigger>.ecsv.
    Includes IS_MERGED + CONSTITUENT_COUNT columns from Phase-A merge."""
    rows = []
    for det, bb in all_blocks.items():
        for k in range(len(bb['starts'])):
            rows.append({
                'TRIGGER_NAME': trigger,
                'DETECTOR': det,
                'BLOCK_INDEX': k,
                'T_START': float(bb['starts'][k]),
                'T_STOP': float(bb['stops'][k]),
                'SIGNIFICANCE': float(bb['sigs'][k]),
                'IS_MERGED': bool(bb['is_merged'][k]),
                'CONSTITUENT_COUNT': int(bb['constituent_count'][k]),
                'POLY_ORDER': int(bb['poly_order']),
            })
    if not rows:
        return
    t = Table(rows)
    t.write(target_path, format='ascii.ecsv', overwrite=True)


# ============================================================================
# Phase orchestrator
# ============================================================================

def phase1_pre_ai(trigger, ignore_catalog_t90=False):
    """Detector picker (all 14, with angles) → on-the-fly TTE download →
    render LC PNGs → write pending manifest.

    If ignore_catalog_t90 is True (or catalog values are missing/masked),
    T90 is not used anywhere — neither for plot framing nor as GUI guide.
    """
    sample = Table.read(os.path.join(RESULTS_DIR, 'grb_sample.ecsv'),
                        format='ascii.ecsv')
    row = get_grb_row(trigger, sample)

    src_ra = float(row['RA'])
    src_dec = float(row['DEC'])

    # T90 is OPTIONAL. Treat masked / non-finite as missing.
    def _opt_float(val):
        try:
            v = float(val)
            return v if np.isfinite(v) else None
        except (TypeError, ValueError):
            return None
    if ignore_catalog_t90:
        t90, t90_start = None, None
    else:
        t90 = _opt_float(row['T90']) if 'T90' in row.colnames else None
        t90_start = _opt_float(row['T90_START']) if 'T90_START' in row.colnames else None
        if t90 is None or t90_start is None:
            t90, t90_start = None, None  # both-or-neither
    if t90 is None:
        print('  (catalog T90 unavailable or ignored — proceeding T90-free)')

    bcat_mask = set([d.strip() for d in str(row['NAI_DETECTORS']).split(',')
                     if d.strip()])

    # ---- Compute angles for all 14 detectors via POSHIST + gtburst math ----
    print(f'Computing detector angles for {trigger} ...')
    grb_data_dir = os.path.join(DATA_DIR, trigger)
    try:
        trigtime_met = get_trigtime_met(trigger)
    except RuntimeError:
        # No TTE yet on disk — bootstrap by downloading one BCAT detector first
        bootstrap = next(iter(bcat_mask), None)
        if bootstrap is None:
            raise SystemExit(f'{trigger}: no BCAT NaI detectors to bootstrap TRIGTIME')
        print(f'  no TTE on disk; bootstrap-downloading {bootstrap} for TRIGTIME ...')
        if not ensure_tte_for_detector(trigger, bootstrap):
            raise SystemExit(f'Could not bootstrap-download {bootstrap}')
        trigtime_met = get_trigtime_met(trigger)
    print(f'  TRIGTIME = {trigtime_met:.3f} MET')

    poshist = download_poshist(trigger, grb_data_dir)
    ra_scx, dec_scx, ra_scz, dec_scz = get_pointing_at_trigger(poshist, trigtime_met)
    print(f'  SCX = ({ra_scx:7.2f}, {dec_scx:7.2f})   '
          f'SCZ = ({ra_scz:7.2f}, {dec_scz:7.2f})   '
          f'source = ({src_ra:7.2f}, {src_dec:7.2f})')

    angles = {d: get_detector_angle(ra_scx, dec_scx, ra_scz, dec_scz,
                                    src_ra, src_dec, d) for d in ALL_DETECTORS}
    nais_keep = {d for d in ALL_DETECTORS
                 if d.startswith('n') and angles[d] <= ANGLE_THRESHOLD_DEG}
    # BCAT-rescue (BACKGROUND_SELECTION_PROCESS.md: "50°<θ≤60° AND in BCAT mask"
    # is a valid keep — the detector TRIGGERED, so the source was in its FoV).
    # Without this, bursts whose only on-source NaIs sit at 50-60° get
    # "no detectors selected". If STILL empty after the 60° band, fall back to
    # the single closest BCAT NaI (it triggered; geometry just borderline).
    nais_keep |= {d for d in bcat_mask
                  if d.startswith('n')
                  and angles.get(d, 999) <= ANGLE_RESCUE_DEG}
    if not nais_keep:
        bcat_nais = [(d, angles.get(d, 999)) for d in bcat_mask if d.startswith('n')]
        if bcat_nais:
            closest = min(bcat_nais, key=lambda x: x[1])
            nais_keep.add(closest[0])
            print(f'  BCAT-rescue: no NaI <= {ANGLE_RESCUE_DEG}°; keeping closest '
                  f'BCAT NaI {closest[0]} (θ={closest[1]:.1f}°)')
    bgo_keep = set()
    if any(d in LOW_SIDE_NAI for d in nais_keep):
        bgo_keep.add('b0')
    if any(d.startswith('n') and d not in LOW_SIDE_NAI for d in nais_keep):
        bgo_keep.add('b1')
    pre_ticked = nais_keep | bgo_keep
    print(f'  pre-ticked: {", ".join(sorted(pre_ticked))}')

    # ---- Detector picker: all 14 with angles ----
    selected = pick_detectors_with_angles_gui(trigger, angles, pre_ticked,
                                              bcat_mask, src_ra, src_dec)
    if not selected:
        raise SystemExit('No detectors selected; nothing to do.')
    print(f'User approved: {", ".join(sorted(selected))}')

    # ---- On-the-fly download for any selected detector without TTE ----
    final = []
    for det in selected:
        if not ensure_tte_for_detector(trigger, det):
            print(f'  WARN: skipping {det} (could not get TTE)')
            continue
        final.append(det)
    selected = final
    if not selected:
        raise SystemExit('No detectors with usable TTE after download attempts.')

    dets_meta = []
    for det in selected:
        outpath = os.path.join(LC_FOR_AI_DIR, f'{trigger}_{det}.png')
        meta = render_lc_png(trigger, det, t90_start, t90, outpath)
        meta['detector'] = det
        meta['png_path'] = outpath
        meta['kind'] = _detector_kind(det)
        meta['angle_deg'] = float(angles[det])
        meta['in_bcat'] = det in bcat_mask
        dets_meta.append(meta)
        print(f'  rendered {outpath}  (θ={angles[det]:.1f}°)')

    manifest_path = os.path.join(LC_FOR_AI_DIR, f'{trigger}_pending.json')
    save_pending_manifest(trigger, {
        't90_start': t90_start, 't90': t90, 'detectors': dets_meta,
    }, manifest_path)

    print()
    print('=' * 70)
    print('PHASE 1 done. AI vision step needed.')
    print()
    print('Either:')
    print(f'  (a) In this Claude session, ask: "look at the LC PNGs for {trigger}')
    print('      and write background intervals to'
          f' {LC_FOR_AI_DIR}/{trigger}_ai_selections.json"')
    print('  (b) Run an external vision call per PNG and write selections to')
    print(f'      {LC_FOR_AI_DIR}/{trigger}_ai_selections.json')
    print()
    print('Expected JSON format (one entry per detector):')
    print('  {')
    print('    "n6": {"pre": [t1, t2], "post": [t3, t4], '
          '"confidence": "high|medium|low",')
    print('           "reasoning": "...", "flags": []},')
    print('    ...')
    print('  }')
    print()
    print(f'When done, resume with:')
    print(f'  python {os.path.basename(sys.argv[0])} --resume --trigger {trigger}')
    print('=' * 70)


def phase3_post_ai(trigger, auto_approve=False, ignore_catalog_t90=False,
                   accept_low=False):
    """Read AI selections → bkg-picker GUI per detector → run BB → Phase A merge."""
    sample = Table.read(os.path.join(RESULTS_DIR, 'grb_sample.ecsv'),
                        format='ascii.ecsv')
    row = get_grb_row(trigger, sample)
    def _opt_float(val):
        try:
            v = float(val); return v if np.isfinite(v) else None
        except (TypeError, ValueError):
            return None
    # BB's active-time window comes from the user-clicked bkg edges
    # (pre_stop, post_start) — derived per-detector in run_bb_for_detector.
    # Catalog T90 is NOT required and not used here. We still optionally
    # read T90 only for the AI-selections JSON metadata field; it never
    # enters the BB numerical step. ignore_catalog_t90 forces None.
    if ignore_catalog_t90:
        t90, t90_start = None, None
    else:
        t90 = _opt_float(row['T90']) if 'T90' in row.colnames else None
        t90_start = _opt_float(row['T90_START']) if 'T90_START' in row.colnames else None
        if t90 is None or t90_start is None:
            t90, t90_start = None, None
    # No raise-SystemExit here: missing catalog T90 is fine. run_bb_for_detector
    # now defines the active interval from approved bkg edges.

    ai_path = os.path.join(LC_FOR_AI_DIR, f'{trigger}_ai_selections.json')
    ai = load_ai_selections(ai_path)
    if ai is None:
        raise SystemExit(
            f'No AI selections at {ai_path}. Run phase 1 first, then have the '
            f'AI write selections to that path.'
        )

    bkg_out = os.path.join(RESULTS_DIR, 'background_intervals_prototype.ecsv')
    bb_out = os.path.join(RESULTS_DIR, f'bb_blocks_prototype_{trigger}.ecsv')

    approved = {}
    for det, ai_pick in ai.items():
        if 'pre' not in ai_pick or 'post' not in ai_pick:
            print(f'  {det}: AI selection missing pre/post — skipping')
            continue

        _conf = ai_pick.get('confidence', 'high')
        if auto_approve and (_conf != 'low' or accept_low):
            _tag = ('auto-approved' if _conf != 'low'
                    else 'AUTO-ACCEPTED LOW-CONFIDENCE (--accept-low)')
            print(f'  {det}: {_tag} (confidence={_conf}, '
                  f'flags={ai_pick.get("flags", [])})')
            pre = tuple(ai_pick['pre'])
            post = tuple(ai_pick['post'])
        else:
            print(f'  {det}: opening review GUI...')
            result, pre, post = review_one_detector(
                trigger, det, ai_pick, t90_start, t90,
            )
            if result == 'quit':
                print('  user quit')
                break
            if result != 'accept':
                print(f'  {det}: not accepted ({result}) — skipping')
                continue

        save_bkg_row(trigger, det, pre, post, bkg_out)
        approved[det] = (pre, post)
        print(f'  {det}: accepted pre={pre}, post={post}')

    if not approved:
        print('No detectors accepted. No BB run.')
        return

    print()
    print(f'Running BB on {len(approved)} detector(s) with use_background=True...')
    all_blocks = {}            # broadband BB (3ML, all channels) — visualization
    all_blocks_8_900 = {}      # 8-900 keV BB — drives spectral analysis
    for det, (pre, post) in approved.items():
        try:
            bb = run_bb_for_detector(trigger, det, t90_start, t90, pre, post)
            all_blocks[det] = bb
            n_raw = len(bb['raw_starts'])
            n_final = len(bb['starts'])
            n_merged_blocks = sum(1 for m in bb['is_merged'] if m)
            print(f'  {det} [broadband]: raw {n_raw} → merged {n_final} blocks '
                  f'({n_merged_blocks} are merged); '
                  f'final sigs {[f"{s:.1f}" for s in bb["sigs"]]}; '
                  f'poly_order={bb["poly_order"]}')
        except Exception as exc:
            print(f'  {det} [broadband]: BB failed — {type(exc).__name__}: {exc}')

        # 8-900 keV BB for spectral analysis (skip BGOs — they cover 250-40000 keV
        # so the 8-900 mask is empty; spectral fit uses NaI 8-900 anyway)
        if det.startswith('n'):
            try:
                bb_sp = run_bb_for_detector_8_900(trigger, det, pre, post)
                all_blocks_8_900[det] = bb_sp
                n_raw = len(bb_sp['raw_starts'])
                n_final = len(bb_sp['starts'])
                n_merged_blocks = sum(1 for m in bb_sp['is_merged'] if m)
                print(f'  {det} [8-900 keV]: raw {n_raw} → merged {n_final} blocks '
                      f'({n_merged_blocks} are merged); '
                      f'final sigs {[f"{s:.1f}" for s in bb_sp["sigs"]]}')
            except Exception as exc:
                print(f'  {det} [8-900 keV]: BB failed — {type(exc).__name__}: {exc}')

    save_bb_blocks(trigger, all_blocks, bb_out)
    bb_sp_out = os.path.join(RESULTS_DIR, f'bb_blocks_spectral_{trigger}.ecsv')
    if all_blocks_8_900:
        save_bb_blocks(trigger, all_blocks_8_900, bb_sp_out)
    print()
    print('=' * 70)
    print('PHASE 3 done.')
    print(f'  Bkg intervals: {bkg_out}')
    print(f'  BB blocks (broadband, for plot panel d): {bb_out}')
    print(f'  BB blocks (8-900 keV, for spectral fits): {bb_sp_out}')
    print('  → BB blocks are the per-detector analysis time bins.')
    print('  → User-approved bkg intervals + per-channel polyfit (in 3ML TSB)')
    print('    are reusable for MEPSA pulse-finding on bkg-subtracted LC.')
    print('=' * 70)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--trigger', default='bn200607921',
                   help='trigger name (default: bn200607921)')
    p.add_argument('--resume', action='store_true',
                   help='Skip phase 1; read AI selections + run bkg picker + BB.')
    p.add_argument('--auto-approve', action='store_true',
                   help='Phase 3: accept AI selections without GUI '
                        '(low-confidence still goes to GUI).')
    p.add_argument('--no-t90', action='store_true',
                   help='Ignore catalog T90 — useful for unpublished bursts. '
                        'T90 is never used in numerical calcs; it only provides '
                        'a visual guide + sanity guard in the GUI.')
    p.add_argument('--accept-low', action='store_true',
                   help='Batch mode: auto-accept low-confidence AI selections '
                        '(loudly logged) instead of opening the blocking GUI. '
                        'Requires --auto-approve. Use only after the low-confidence '
                        'picks have been spot-checked.')
    args = p.parse_args()

    if args.resume:
        phase3_post_ai(args.trigger, auto_approve=args.auto_approve,
                       ignore_catalog_t90=args.no_t90,
                       accept_low=args.accept_low)
    else:
        phase1_pre_ai(args.trigger, ignore_catalog_t90=args.no_t90)


if __name__ == '__main__':
    main()
