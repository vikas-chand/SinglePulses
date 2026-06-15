#!/usr/bin/env python
"""
Phase 0: Interactive per-detector background-interval selector.

For each GRB × each detector with TTE, plots binned LC with T90 shaded and
lets the user click two pre-burst bounds and two post-burst bounds. UX
mirrors fermitools/GtBurst/interactivePlots.py:71-445 — left-click+release
within 2 pixels places a vertical dashed line, two clicks define one
interval, intervals fill yellow, bin snapping via np.searchsorted, transient
dashed cursor line via motion_notify_event, matplotlib default toolbar for
zoom/pan with isNormalMode() guard silencing click-selection while zoom
active. Text buttons Clear / Accept / Skip GRB / Quit use picker=20.

Output: results/background_intervals.ecsv with one row per (trigger, det),
columns TRIGGER_NAME, DETECTOR, BKG_NEG_START, BKG_NEG_STOP,
BKG_POS_START, BKG_POS_STOP. Consumed by 04_bayesian_blocks.py and
05_replot_bb.py.

Usage:
    python 00_select_backgrounds.py                   # prompt only for missing (trigger,det)
    python 00_select_backgrounds.py --redo            # revisit every pair
    python 00_select_backgrounds.py --redo-grb bn200607921
    python 00_select_backgrounds.py --limit 3         # stop after 3 GRBs

Run in the threeML env so GBM TTE/RSP loading works for the overlay:
    /Users/salim/anaconda3/envs/threeML/bin/python scripts/00_select_backgrounds.py
"""

import os
import sys
import glob
import argparse
import warnings

import numpy as np
from astropy.io import fits
from astropy.table import Table

os.environ['OMP_NUM_THREADS'] = '1'
warnings.filterwarnings('ignore')

import matplotlib
# Prefer macOS's native Cocoa backend — it gives each figure its own window
# and doesn't die when one figure is closed (TkAgg's plt.close destroys the
# Tk root, which broke multi-detector iteration on the first run).
try:
    matplotlib.use('macosx')
except Exception:
    matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
OUT_PATH = os.path.join(RESULTS_DIR, 'background_intervals.ecsv')
SAMPLE_PATH = os.path.join(RESULTS_DIR, 'grb_sample.ecsv')

# gtburst-style 2-pixel tolerance: distinguishes click from drag (zoom).
CLICK_TOL_PIXELS = 2

# NaI angular-side grouping for BGO pairing (matches 02_download_data.py).
LOW_SIDE = {'n0', 'n1', 'n2', 'n3', 'n4', 'n5'}


# ============================================================================
# Interactive selector
# ============================================================================

class BackgroundSelector(object):
    """One detector's interactive figure. Returns ('accept'|'skip'|'quit', pre, post)."""

    def __init__(self, trigger, det, tte_file, t90_start, t90,
                 prev_pre=None, prev_post=None):
        self.trigger = trigger
        self.det = det
        self.t90_start = t90_start
        self.t90_stop = t90_start + t90

        # Build coarse binned LC from TTE
        with fits.open(tte_file) as hdul:
            times = hdul['EVENTS'].data['TIME']
            trigtime = hdul['PRIMARY'].header.get('TRIGTIME', 0.0)
            t_rel = times - trigtime

        # Plot window: generous around T90 but bounded by event range
        pad = max(120.0, 5.0 * t90)
        t_min = max(float(t_rel.min()), self.t90_start - pad)
        t_max = min(float(t_rel.max()), self.t90_stop + 2.0 * pad)

        # Bin width adapts to T90
        if t90 < 5:    dt = 0.064
        elif t90 < 30: dt = 0.128
        elif t90 < 100: dt = 0.256
        elif t90 < 300: dt = 0.5
        else:          dt = 1.0

        self.bins = np.arange(t_min, t_max + dt, dt)
        counts, _ = np.histogram(t_rel, bins=self.bins)
        self.bin_centers = 0.5 * (self.bins[:-1] + self.bins[1:])
        self.rates = counts / dt

        # State
        self.pending_clicks = []        # list of x-coords waiting to be paired
        self.pre_interval = prev_pre    # (start, stop) or None
        self.post_interval = prev_post
        self.fill_artists = []
        self.line_artists = []
        self.transient_line = None
        self.bkg_overlay_artist = None
        self.result = None              # 'accept' | 'skip' | 'quit'

        # Click-vs-drag detection (gtburst-style 2-pixel tolerance)
        self._press_x_pixel = None

        self._build_figure()

    def _build_figure(self):
        self.fig, self.ax = plt.subplots(figsize=(12, 6.5))
        self.fig.subplots_adjust(left=0.07, right=0.85, top=0.92, bottom=0.10)

        self.ax.step(self.bin_centers, self.rates, where='mid',
                     color='gray', lw=0.8, alpha=0.75)
        self.ax.axvspan(self.t90_start, self.t90_stop,
                        color='orange', alpha=0.12, zorder=0)
        self.ax.axvline(self.t90_start, color='orange', ls=':', lw=0.9)
        self.ax.axvline(self.t90_stop, color='orange', ls=':', lw=0.9)
        self.ax.set_xlabel('Time since trigger (s)', fontsize=11)
        self.ax.set_ylabel(r'Counts s$^{-1}$', fontsize=11)
        self.ax.set_title(
            f'{self.trigger}  ({self.det})  —  click 2 pre-burst + 2 post-burst bounds',
            fontsize=12,
        )

        # gtburst-style figure-text buttons with picker
        self.btn_clear = self.fig.text(
            0.87, 0.82, 'Clear', backgroundcolor='red', color='white',
            weight='bold', picker=20, fontsize=11, ha='left', va='center',
        )
        self.btn_accept = self.fig.text(
            0.87, 0.72, 'Accept', backgroundcolor='green', color='white',
            weight='bold', picker=20, fontsize=11, ha='left', va='center',
        )
        self.btn_skip = self.fig.text(
            0.87, 0.62, 'Skip GRB', backgroundcolor='#cc8800', color='white',
            weight='bold', picker=20, fontsize=10, ha='left', va='center',
        )
        self.btn_quit = self.fig.text(
            0.87, 0.52, 'Quit', backgroundcolor='gray', color='white',
            weight='bold', picker=20, fontsize=10, ha='left', va='center',
        )

        self.status_text = self.fig.text(
            0.07, 0.02, '', ha='left', va='bottom', fontsize=9, color='steelblue',
        )

        # If pre-populated from earlier detector, render and overlay immediately
        if self.pre_interval or self.post_interval:
            self._refresh_intervals()
            self._refresh_overlay()
            self._set_status(
                'Pre-populated from prior detector. Adjust if needed, then Accept.'
            )
        else:
            self._set_status('Click 4 times: 2 in pre-burst, 2 in post-burst.')

        self.cids = [
            self.fig.canvas.mpl_connect('button_press_event', self._on_press),
            self.fig.canvas.mpl_connect('button_release_event', self._on_release),
            self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion),
            self.fig.canvas.mpl_connect('pick_event', self._on_pick),
        ]

    # ---- gtburst's isNormalMode() guard ----
    def _is_normal_mode(self):
        toolbar = getattr(self.fig.canvas, 'toolbar', None)
        if toolbar is None:
            return True
        mode = getattr(toolbar, 'mode', '')
        # Empty string ⇒ idle; 'zoom rect'/'pan/zoom' ⇒ active
        return not mode

    # ---- Mouse events ----
    def _on_press(self, event):
        if not self._is_normal_mode():
            self._press_x_pixel = None
            return
        if event.x is None:
            self._press_x_pixel = None
        else:
            self._press_x_pixel = event.x

    def _on_release(self, event):
        if not self._is_normal_mode():
            return
        if event.button != 1 or self._press_x_pixel is None:
            return
        if event.x is None or event.xdata is None:
            return
        # Click-vs-drag tolerance: mirror gtburst's 2-pixel rule
        if abs(event.x - self._press_x_pixel) > CLICK_TOL_PIXELS:
            return
        x_snapped = self._snap_to_bin(event.xdata)
        self._add_click(x_snapped)

    def _on_motion(self, event):
        if self.transient_line is not None:
            try:
                self.transient_line.remove()
            except Exception:
                pass
            self.transient_line = None
        if not self._is_normal_mode() or event.xdata is None:
            self.fig.canvas.draw_idle()
            return
        self.transient_line = self.ax.axvline(
            event.xdata, color='black', ls=':', lw=0.5, alpha=0.45,
        )
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

    # ---- Bound-management ----
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
        midpoint = 0.5 * (a + b)

        if midpoint < self.t90_start:
            # Replaces any existing pre-burst interval
            self.pre_interval = (a, b)
            self._set_status(f'Pre-burst set: [{a:.2f}, {b:.2f}].')
        elif midpoint > self.t90_stop:
            self.post_interval = (a, b)
            self._set_status(f'Post-burst set: [{a:.2f}, {b:.2f}].')
        else:
            self._set_status(
                f'Discarded: interval midpoint {midpoint:.2f}s falls inside T90 '
                f'[{self.t90_start:.2f}, {self.t90_stop:.2f}].'
            )
            self._refresh_intervals()
            self.fig.canvas.draw_idle()
            return

        self._refresh_intervals()
        self._refresh_overlay()
        self.fig.canvas.draw_idle()

    def _clear_all(self):
        self.pending_clicks = []
        self.pre_interval = None
        self.post_interval = None
        self._refresh_intervals()
        if self.bkg_overlay_artist is not None:
            try:
                self.bkg_overlay_artist.remove()
            except Exception:
                pass
            self.bkg_overlay_artist = None
        self._set_status('Cleared. Click 4 times to redo.')
        self.fig.canvas.draw_idle()

    def _refresh_intervals(self):
        for art in self.fill_artists:
            try: art.remove()
            except Exception: pass
        self.fill_artists = []
        for art in self.line_artists:
            try: art.remove()
            except Exception: pass
        self.line_artists = []

        for interval in (self.pre_interval, self.post_interval):
            if interval is None:
                continue
            a, b = interval
            fill = self.ax.axvspan(a, b, color='gold', alpha=0.30, zorder=1)
            self.fill_artists.append(fill)
            for x in (a, b):
                self.line_artists.append(
                    self.ax.axvline(x, color='goldenrod', lw=1.0, alpha=0.85)
                )
        for x in self.pending_clicks:
            self.line_artists.append(
                self.ax.axvline(x, color='black', ls='--', lw=0.8, alpha=0.7)
            )

    def _refresh_overlay(self):
        """
        Polynomial-bkg visual overlay. Uses numpy.polyfit deg=2 on the binned
        rates inside the two user-selected intervals. This approximates 3ML's
        polyfit closely enough for human visual sanity-check. Scripts 04/05/06
        still use 3ML's own polyfit on the same boundaries downstream.
        """
        if self.bkg_overlay_artist is not None:
            try:
                self.bkg_overlay_artist.remove()
            except Exception:
                pass
            self.bkg_overlay_artist = None

        if self.pre_interval is None or self.post_interval is None:
            return

        mask_pre = (
            (self.bin_centers >= self.pre_interval[0])
            & (self.bin_centers <= self.pre_interval[1])
        )
        mask_post = (
            (self.bin_centers >= self.post_interval[0])
            & (self.bin_centers <= self.post_interval[1])
        )
        mask = mask_pre | mask_post
        if mask.sum() < 5:
            self._set_status('Too few LC bins inside intervals for polyfit overlay.')
            return

        x = self.bin_centers[mask]
        y = self.rates[mask]
        try:
            coeffs = np.polyfit(x, y, deg=2)
        except Exception:
            return
        bkg_curve = np.polyval(coeffs, self.bin_centers)
        self.bkg_overlay_artist, = self.ax.plot(
            self.bin_centers, bkg_curve, color='red', lw=1.3, alpha=0.85,
            zorder=3,
        )

    def _set_status(self, msg):
        self.status_text.set_text(msg)

    def run(self):
        plt.show(block=True)
        return self.result, self.pre_interval, self.post_interval


# ============================================================================
# Persistence
# ============================================================================

def load_existing(out_path):
    """Return dict[(trigger, det)] -> ((pre_start, pre_stop), (post_start, post_stop))."""
    if not os.path.exists(out_path):
        return {}
    t = Table.read(out_path, format='ascii.ecsv')
    out = {}
    for r in t:
        key = (str(r['TRIGGER_NAME']).strip(), str(r['DETECTOR']).strip())
        out[key] = (
            (float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])),
            (float(r['BKG_POS_START']), float(r['BKG_POS_STOP'])),
        )
    return out


def save_one_row(out_path, trigger, det, pre, post):
    """Append or replace one (trigger, det) row."""
    new_cols = {
        'TRIGGER_NAME': trigger,
        'DETECTOR': det,
        'BKG_NEG_START': float(pre[0]),
        'BKG_NEG_STOP': float(pre[1]),
        'BKG_POS_START': float(post[0]),
        'BKG_POS_STOP': float(post[1]),
    }
    if os.path.exists(out_path):
        t = Table.read(out_path, format='ascii.ecsv')
        mask = ~((t['TRIGGER_NAME'] == trigger) & (t['DETECTOR'] == det))
        t = t[mask]
        t.add_row(new_cols)
    else:
        t = Table(
            [[trigger], [det],
             [new_cols['BKG_NEG_START']], [new_cols['BKG_NEG_STOP']],
             [new_cols['BKG_POS_START']], [new_cols['BKG_POS_STOP']]],
            names=list(new_cols.keys()),
        )
    t.write(out_path, format='ascii.ecsv', overwrite=True)


# ============================================================================
# Detector enumeration
# ============================================================================

def get_detectors_for_grb(row, data_dir):
    """Return [(det, tte_file)] for this GRB — NaI angle-sorted first, then BGO."""
    trigger = str(row['TRIGGER_NAME']).strip()
    grb_dir = os.path.join(data_dir, trigger)
    nai_str = str(row['NAI_DETECTORS']).strip()
    nai_list = [d.strip() for d in nai_str.split(',') if d.strip()]
    if not nai_list:
        return []
    n_low = sum(1 for d in nai_list if d in LOW_SIDE)
    bgo = 'b0' if n_low >= len(nai_list) - n_low else 'b1'
    all_dets = nai_list + [bgo]

    out = []
    for det in all_dets:
        tte = glob.glob(os.path.join(grb_dir, f'glg_tte_{det}_*.fit.gz'))
        if tte:
            out.append((det, tte[0]))
    return out


# ============================================================================
# Main loop
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--redo', action='store_true',
                        help='Revisit every (trigger, det) pair')
    parser.add_argument('--redo-grb', type=str, default=None,
                        help='Revisit one trigger across all detectors')
    parser.add_argument('--limit', type=int, default=None,
                        help='Stop after this many GRBs')
    args = parser.parse_args()

    sample = Table.read(SAMPLE_PATH, format='ascii.ecsv')
    existing = load_existing(OUT_PATH)
    print(f'Sample: {len(sample)} GRBs. Existing (trigger, det) rows: {len(existing)}.')

    n_grbs_done = 0
    for i, row in enumerate(sample):
        trigger = str(row['TRIGGER_NAME']).strip()
        if args.redo_grb and trigger != args.redo_grb:
            continue

        t90 = float(row['T90'])
        t90_start = float(row['T90_START'])

        dets = get_detectors_for_grb(row, DATA_DIR)
        if not dets:
            continue

        # Skip if every detector already done and not in --redo mode
        if not args.redo and args.redo_grb is None:
            if all(((trigger, d) in existing) for d, _ in dets):
                continue

        print(f'\n[{i + 1}/{len(sample)}] {trigger} '
              f'(T90={t90:.1f}s, T90_start={t90_start:.2f}s): {len(dets)} detectors')

        # Seed-from-prior: pick the first already-done detector of this GRB,
        # if any, so the first un-done detector starts with a sensible default.
        prev_pre = None
        prev_post = None
        for d, _ in dets:
            if (trigger, d) in existing:
                prev_pre, prev_post = existing[(trigger, d)]
                break

        quit_flag = False
        skip_grb = False
        for det, tte in dets:
            key = (trigger, det)
            if not args.redo and args.redo_grb is None and key in existing:
                prev_pre, prev_post = existing[key]
                print(f'  {det}: already done — using as seed for next detector')
                continue

            print(f'  {det}: launching selector...')
            try:
                sel = BackgroundSelector(
                    trigger, det, tte, t90_start, t90,
                    prev_pre=prev_pre, prev_post=prev_post,
                )
                result, pre, post = sel.run()
            except Exception as exc:
                print(f'    selector raised {type(exc).__name__}: {exc}')
                continue

            if result == 'accept':
                save_one_row(OUT_PATH, trigger, det, pre, post)
                existing[key] = (pre, post)
                prev_pre, prev_post = pre, post
                print(f'    accepted: pre={pre}, post={post}')
            elif result == 'skip':
                print('    user skipped GRB')
                skip_grb = True
                break
            elif result == 'quit':
                print('    user quit')
                quit_flag = True
                break
            else:
                print('    closed without action — treating as skip')
                skip_grb = True
                break

        if quit_flag:
            break
        if not skip_grb:
            n_grbs_done += 1
            if args.limit is not None and n_grbs_done >= args.limit:
                print(f'\nReached --limit {args.limit}; stopping.')
                break

    print(f'\nDone. Output: {OUT_PATH}')


if __name__ == '__main__':
    main()
