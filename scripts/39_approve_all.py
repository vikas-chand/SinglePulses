#!/usr/bin/env python
"""
39_approve_all.py -- UNIFIED, GATED approval of detectors + background + source.

This is Stage 1 of the authoritative pipeline (see AGENTS.md / dev/AUTHORITATIVE_
PIPELINE.md). It produces ONE stamped catalog, results/background_intervals.ecsv,
in which every approved (trigger, detector) row carries:
  - the approved DETECTOR (only approved detectors get rows),
  - the BACKGROUND windows (pre/post),
  - the per-burst SOURCE / emission window (SRC_START, SRC_STOP),
  - a GATE STAMP: APPROVED_BY, APPROVED_UTC, APPROVAL_MODE, WINDOW_SOURCE,
so "what was approved, by whom, and how" is answerable from the file itself.

Approval may be made by a HUMAN (interactive GUI) or by an AI (vision on the
rendered light-curve PNGs). The gate records which. The AI never fabricates an
approval silently -- it stamps APPROVAL_MODE=ai_vision and APPROVED_BY="<agent>".

Three modes, mirroring the proven 00_prototype 3-phase pattern, scaled to all bursts:

  1) render   (light deps; downloads TTE/POSHIST on demand if absent) -- per burst:
     compute detector angles (POSHIST),
     render an LC PNG per candidate detector, and write a candidate manifest
     results/approval/<trigger>_pending.json (candidate detectors + suggested
     background + suggested source) for an agent/human to judge.

  2) AI-vision step (the agent: Codex or Claude) -- read <trigger>_pending.json and
     the PNGs, decide the approved detectors, per-detector bkg windows, and the
     per-burst source window, and WRITE results/approval/<trigger>_decision.json
     (schema below). No script runs here; the agent uses its own judgement.

  3) ingest   (light) -- read the <trigger>_decision.json files, validate, and write
     the stamped results/background_intervals.ecsv. Mode-agnostic: it stamps whatever
     approver/mode the decision file declares.

  gui         (needs a display) -- the human path: detector picker -> background
     selector per detector -> source marker, all reused from 00_prototype; writes a
     decision.json (mode=human_gui) then ingests it. Use when a person clicks.

decision.json schema (what the agent OR the gui writes):
  {
    "trigger": "bn110721200",
    "approver": "Claude (AI)" | "Khushboo Sharma",
    "mode": "ai_vision" | "human_gui" | "ai_auto",
    "detectors": ["n6", "n7", "b1"],                 # approved SET (NaI + BGO[+lle])
    "source": {"t1": <float>, "t2": <float>},        # per-burst emission window
    "windows": {                                      # one per approved detector
        "n6": {"pre": [t1, t2], "post": [t3, t4], "window_source": "adjusted"},
        ...
    },
    "angles": {"n6": 12.3, ...},   # OPTIONAL: per-det angle in deg; if omitted, ingest
                                   # falls back to the angles already in <trig>_pending.json
    "reasoning": "optional free text"
  }
window_source in {accepted_suggestion, adjusted, drawn_fresh} (audit only; validated).
Validation also requires the source window to lie within every approved detector's
background gap (pre_stop <= t1 < t2 <= post_start).

Examples:
  python scripts/39_approve_all.py render --all                 # render every burst
  python scripts/39_approve_all.py render --trigger bn110721200
  # (agent writes results/approval/<trigger>_decision.json)
  python scripts/39_approve_all.py ingest --all                 # -> background_intervals.ecsv
  python scripts/39_approve_all.py gui --trigger bn110721200 --approver "Khushboo Sharma"

render/gui need data/<trigger>/ TTE (+ POSHIST). render is dependency-light (numpy/
astropy/matplotlib) BUT will download a TTE/POSHIST on demand if absent -- pre-fetch
with handoff_background_approval/fetch_tte.py to keep it network/threeML-free. ingest
needs only the decision JSONs. Run from the repo root.
"""
import os
import sys
import glob
import json
import argparse
import datetime
import importlib.util

import numpy as np
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
RESULTS = os.path.join(BASE, 'results')
APPROVAL_DIR = os.path.join(RESULTS, 'approval')          # pending/decision JSONs
PNG_DIR = os.path.join(BASE, 'plots', 'approval_lc')      # rendered LC PNGs
OUT_CATALOG = os.path.join(RESULTS, 'background_intervals.ecsv')
SAMPLE_PATH = os.path.join(RESULTS, 'single_pulse_grbs.ecsv')
STARTING_PATH = os.path.join(RESULTS, 'background_starting_points.ecsv')

SCHEMA = ['TRIGGER_NAME', 'DETECTOR', 'BKG_NEG_START', 'BKG_NEG_STOP',
          'BKG_POS_START', 'BKG_POS_STOP', 'SRC_START', 'SRC_STOP', 'DET_ANGLE',
          'APPROVED_BY', 'APPROVED_UTC', 'APPROVAL_MODE', 'WINDOW_SOURCE']
# Explicit dtypes so an EMPTY catalog (no decisions yet) is not silently written
# as all-float64 (which would make string columns un-mergeable on the next ingest).
DTYPES = ['U32', 'U8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8',
          'U80', 'U24', 'U16', 'U24']
_STR_COLS = {'APPROVED_BY', 'APPROVED_UTC', 'APPROVAL_MODE', 'WINDOW_SOURCE'}
WINDOW_SOURCE_ENUM = {'accepted_suggestion', 'adjusted', 'drawn_fresh', 'unknown'}

# 00_prototype.py holds the proven detector-angle math, detector picker, LC render,
# and BackgroundSelector. Import it LAZILY (it pulls matplotlib + a GUI backend) so
# `ingest` -- pure file I/O -- never needs a display.
_P0 = None


def p0():
    global _P0
    if _P0 is None:
        path = os.path.join(BASE, 'scripts', '00_prototype_one_burst.py')
        spec = importlib.util.spec_from_file_location('proto0', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _P0 = mod
    return _P0


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def all_triggers():
    return sorted({os.path.basename(os.path.dirname(p))
                   for p in glob.glob(f'{DATA}/bn*/')})


def load_starting(trigger):
    """Suggested per-detector bkg windows for this trigger (from scripts/28 output)."""
    if not os.path.exists(STARTING_PATH):
        return {}
    t = Table.read(STARTING_PATH, format='ascii.ecsv')
    t = t[t['TRIGGER_NAME'] == trigger]
    return {str(r['DETECTOR']).strip(): {
        'pre': [float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])],
        'post': [float(r['BKG_POS_START']), float(r['BKG_POS_STOP'])]} for r in t}


# ============================================================================
# render -- candidates + LC PNGs + pending.json
# ============================================================================

def compute_candidates(trigger):
    """Detector angles (POSHIST), pre-ticked NaI<=50deg + matching BGO, suggested
    bkg (from starting_points) and a suggested per-burst source window."""
    P = p0()
    sample = Table.read(os.path.join(RESULTS, 'grb_sample.ecsv'), format='ascii.ecsv') \
        if os.path.exists(os.path.join(RESULTS, 'grb_sample.ecsv')) else None
    # Source RA/DEC + bcat mask come from grb_sample. get_grb_row raises SystemExit
    # (BaseException) when the trigger is absent — guard so one missing burst can't
    # abort an --all run.
    row = None
    if sample is not None and trigger in set(str(t) for t in sample['TRIGGER_NAME']):
        try:
            row = P.get_grb_row(trigger, sample)
        except SystemExit:
            row = None
    if row is None:
        # LOUD, never silent (R-GL-3): without this row there is no source RA/DEC,
        # so no detector angles, no BCAT mask, and no detector picker in gui mode.
        why = ('results/grb_sample.ecsv is MISSING'
               if sample is None else
               f'{trigger} is not in results/grb_sample.ecsv')
        print('  ' + '=' * 66)
        print(f'  WARNING [{trigger}]: {why}.')
        print('  -> no source RA/DEC: detector angles, BCAT mask and the detector')
        print('     picker are unavailable for this burst.')
        print('  -> remedy: `git pull` (the catalog is tracked in the repo), or')
        print('     regenerate with scripts/01_build_sample.py (NOTE: re-queries')
        print('     live HEASARC; may drift from the frozen benchmark sample).')
        print('  ' + '=' * 66)
    src_ra = float(row['RA']) if row is not None else None
    src_dec = float(row['DEC']) if row is not None else None
    bcat = set()
    if row is not None and 'NAI_DETECTORS' in row.colnames:
        bcat = {d.strip() for d in str(row['NAI_DETECTORS']).split(',') if d.strip()}

    angles = {}
    if src_ra is not None:
        try:
            try:
                trigtime = P.get_trigtime_met(trigger)
            except RuntimeError:
                boot = next(iter(bcat), None)
                trigtime = (P.get_trigtime_met(trigger)
                            if (boot and P.ensure_tte_for_detector(trigger, boot))
                            else None)
            if trigtime is not None:
                poshist = P.download_poshist(trigger, os.path.join(DATA, trigger))
                ra_scx, dec_scx, ra_scz, dec_scz = P.get_pointing_at_trigger(poshist, trigtime)
                angles = {d: float(P.get_detector_angle(ra_scx, dec_scx, ra_scz, dec_scz,
                                  src_ra, src_dec, d)) for d in P.ALL_DETECTORS}
        except (RuntimeError, OSError) as exc:
            print(f'  {trigger}: angle computation failed ({type(exc).__name__}: {exc}); '
                  'falling back to BCAT/starting-points pre-ticking')
            angles = {}

    suggested_bkg = load_starting(trigger)
    # pre-ticked detectors: NaI <= threshold (+ BCAT rescue + closest-BCAT fallback,
    # mirroring 00_prototype), matching BGO; else the detectors with a suggested bkg.
    pre_ticked = set()
    if angles:
        thr = getattr(P, 'ANGLE_THRESHOLD_DEG', 50.0)
        resc = getattr(P, 'ANGLE_RESCUE_DEG', 60.0)
        pre_ticked = {d for d in angles if d.startswith('n') and angles[d] <= thr}
        pre_ticked |= {d for d in bcat if d.startswith('n') and angles.get(d, 999) <= resc}
        if not any(d.startswith('n') for d in pre_ticked):
            # final fallback: the single closest BCAT NaI (it triggered; geometry borderline)
            bcat_nai = [(d, angles.get(d, 999)) for d in bcat if d.startswith('n')]
            if bcat_nai:
                pre_ticked.add(min(bcat_nai, key=lambda x: x[1])[0])
        low = getattr(P, 'LOW_SIDE_NAI', {'n0', 'n1', 'n2', 'n3', 'n4', 'n5'})
        if any(d in low for d in pre_ticked):
            pre_ticked.add('b0')
        if any(d.startswith('n') and d not in low for d in pre_ticked):
            pre_ticked.add('b1')
    if not pre_ticked:
        pre_ticked = set(suggested_bkg)

    # Suggested source: a real EMISSION estimate (peak-find tightened within the bkg
    # gap of the brightest pre-ticked NaI), NOT the full quiet gap — a wide gap as the
    # source would defeat 27b's tightening. Falls back to the gap only if estimation fails.
    src = None
    nai_ticked = sorted([d for d in pre_ticked if d.startswith('n')],
                        key=lambda d: angles.get(d, 999))
    for d in nai_ticked:
        if d not in suggested_bkg:
            continue
        gap_lo, gap_hi = suggested_bkg[d]['pre'][1], suggested_bkg[d]['post'][0]
        s_lo, s_hi = _emission_estimate(trigger, d, suggested_bkg[d], gap_lo, gap_hi)
        src = {'t1': s_lo, 't2': s_hi}
        break
    return {'angles': angles, 'pre_ticked': sorted(pre_ticked), 'bcat': sorted(bcat),
            'suggested_bkg': suggested_bkg, 'suggested_source': src,
            'src_ra': src_ra, 'src_dec': src_dec}


def _emission_estimate(trigger, det, bkg, gap_lo, gap_hi):
    """Tighten [gap_lo, gap_hi] to the burst emission by reusing 27b's emission_window
    (pure numpy; lazy import keeps render light). Returns the gap unchanged on failure."""
    try:
        spec = importlib.util.spec_from_file_location(
            'reblock27b', os.path.join(BASE, 'scripts', '27b_reblock_3ml.py'))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        tt = m.load_nai(trigger, det)
        if tt is None or tt.size < 30:
            return gap_lo, gap_hi
        pre, post = bkg['pre'], bkg['post']
        bt = (pre[1] - pre[0]) + (post[1] - post[0])
        bc = int(((tt >= pre[0]) & (tt < pre[1])).sum()
                 + ((tt >= post[0]) & (tt < post[1])).sum())
        brate = bc / bt if bt > 0 else 0.0
        lo, hi = m.emission_window(tt, float(gap_lo), float(gap_hi), brate)
        return float(lo), float(hi)
    except Exception:
        return gap_lo, gap_hi


def render_one(trigger, overwrite=False):
    P = p0()
    os.makedirs(APPROVAL_DIR, exist_ok=True)
    os.makedirs(PNG_DIR, exist_ok=True)
    pending_path = os.path.join(APPROVAL_DIR, f'{trigger}_pending.json')
    if os.path.exists(pending_path) and not overwrite:
        return trigger, 'exists', 0
    if overwrite:                          # clear stale PNGs so re-render is clean
        for p in glob.glob(os.path.join(PNG_DIR, f'{trigger}_*.png')):
            try:
                os.remove(p)
            except OSError:
                pass
    cand = compute_candidates(trigger)
    dets = cand['pre_ticked'] or sorted(cand['suggested_bkg'])
    rendered = []
    for det in dets:
        if not P.ensure_tte_for_detector(trigger, det):
            continue
        outpath = os.path.join(PNG_DIR, f'{trigger}_{det}.png')
        try:
            meta = P.render_lc_png(trigger, det, None, None, outpath)
        except Exception as exc:
            print(f'  {trigger} {det}: render failed ({type(exc).__name__}: {exc})')
            continue
        meta.update({'detector': det, 'png_path': outpath,
                     'angle_deg': cand['angles'].get(det),
                     'in_bcat': det in cand['bcat'],
                     'suggested_bkg': cand['suggested_bkg'].get(det)})
        rendered.append(meta)
    if not rendered:                       # don't record a failed render as complete
        return trigger, 'empty (no PNGs)', 0
    manifest = {
        'trigger': trigger,
        'src_ra': cand['src_ra'], 'src_dec': cand['src_dec'],
        'pre_ticked': cand['pre_ticked'],
        'suggested_source': cand['suggested_source'],
        'detectors': rendered,
        'instructions': ('Judge from the PNGs. Write '
                         f'results/approval/{trigger}_decision.json per the schema '
                         'in scripts/39_approve_all.py (detectors, source, windows, '
                         'approver, mode). Only list detectors you approve.'),
    }
    with open(pending_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    return trigger, 'rendered', len(rendered)


# ============================================================================
# ingest -- decision.json -> stamped catalog
# ============================================================================

def _pair(x):
    """Coerce x to [t1, t2] floats, or None if it is not a 2-element numeric list."""
    if not isinstance(x, (list, tuple)) or len(x) != 2:
        return None
    try:
        return [float(x[0]), float(x[1])]
    except (TypeError, ValueError):
        return None


def _validate_decision(d):
    """Return (ok, msg). Defensive: agent/human-authored JSON may be malformed, so
    every shape/type is checked and a clear INVALID message returned (never a crash)."""
    for k in ('trigger', 'approver', 'mode', 'detectors', 'source', 'windows'):
        if k not in d:
            return False, f'missing key "{k}"'
    if not isinstance(d['detectors'], list) or not d['detectors']:
        return False, 'no approved detectors'
    if not isinstance(d['windows'], dict):
        return False, 'windows must be a {detector: {pre, post}} map'
    s = d['source']
    if not isinstance(s, dict) or 't1' not in s or 't2' not in s:
        return False, 'source must have t1 and t2'
    try:
        s1, s2 = float(s['t1']), float(s['t2'])
    except (TypeError, ValueError):
        return False, 'source t1/t2 must be numbers'
    if not (s2 > s1):
        return False, 'source must have t1 < t2'
    ang = d.get('angles')
    if ang is not None and not isinstance(ang, dict):
        return False, 'angles must be a {detector: degrees} map'
    ws_seen = set()
    for det in d['detectors']:
        w = d['windows'].get(det)
        if not isinstance(w, dict) or 'pre' not in w or 'post' not in w:
            return False, f'{det}: missing pre/post window'
        pre, post = _pair(w['pre']), _pair(w['post'])
        if pre is None or post is None:
            return False, f'{det}: pre/post must each be [t1, t2] numbers'
        if not (pre[1] > pre[0] and post[1] > post[0]):
            return False, f'{det}: pre/post must be increasing'
        if not (post[0] >= pre[1]):
            return False, f'{det}: post must start at/after pre ends'
        if not (pre[1] <= s1 and s2 <= post[0]):
            return False, (f'{det}: source [{s1:g},{s2:g}] must lie within the '
                           f'background gap [{pre[1]:g},{post[0]:g}]')
        ws = w.get('window_source')
        if ws is not None:
            ws_seen.add(ws)
    bad = ws_seen - WINDOW_SOURCE_ENUM
    if bad:
        return False, f'window_source must be in {sorted(WINDOW_SOURCE_ENUM)}; got {sorted(bad)}'
    return True, 'ok'


def _load_pending_angles(trigger):
    """{det: angle_deg} from <trigger>_pending.json (render already computed these);
    the angle fallback for AI-vision decisions that omit a top-level `angles` map."""
    p = os.path.join(APPROVAL_DIR, f'{trigger}_pending.json')
    if not os.path.exists(p):
        return {}
    try:
        m = json.load(open(p))
    except (ValueError, OSError):
        return {}
    out = {}
    for e in m.get('detectors', []):
        det, a = e.get('detector'), e.get('angle_deg')
        if det is not None and a is not None:
            try:
                out[det] = float(a)
            except (TypeError, ValueError):
                pass
    return out


def ingest_one(trigger, rows_accum):
    path = os.path.join(APPROVAL_DIR, f'{trigger}_decision.json')
    if not os.path.exists(path):
        return trigger, 'no decision', 0
    try:
        with open(path) as f:
            d = json.load(f)
    except ValueError as exc:
        return trigger, f'INVALID: unreadable JSON ({exc})', 0
    ok, msg = _validate_decision(d)
    if not ok:
        return trigger, f'INVALID: {msg}', 0
    src1, src2 = float(d['source']['t1']), float(d['source']['t2'])
    stamp_utc = _utcnow()
    dec_ang = d.get('angles') if isinstance(d.get('angles'), dict) else {}
    pend_ang = _load_pending_angles(trigger)   # fallback for the AI-vision path

    def _ang(det):
        v = dec_ang.get(det, pend_ang.get(det))
        try:
            return float(v) if v is not None else np.nan
        except (TypeError, ValueError):
            return np.nan

    n = 0
    for det in d['detectors']:
        w = d['windows'][det]
        pre, post = _pair(w['pre']), _pair(w['post'])
        rows_accum.append({
            'TRIGGER_NAME': trigger, 'DETECTOR': det,
            'BKG_NEG_START': pre[0], 'BKG_NEG_STOP': pre[1],
            'BKG_POS_START': post[0], 'BKG_POS_STOP': post[1],
            'SRC_START': src1, 'SRC_STOP': src2,
            'DET_ANGLE': _ang(det),
            'APPROVED_BY': str(d['approver']), 'APPROVED_UTC': stamp_utc,
            'APPROVAL_MODE': str(d['mode']),
            'WINDOW_SOURCE': str(w.get('window_source', 'unknown')),
        })
        n += 1
    return trigger, 'ingested', n


def write_catalog(rows, merge=True):
    """Write/merge rows into OUT_CATALOG (replace any existing (trigger,det)).
    Never writes a degenerate all-float64 empty table (which would poison later
    merges): an empty result with no existing file is a no-op."""
    if not rows and not (merge and os.path.exists(OUT_CATALOG)):
        return 0
    # Always construct with explicit dtypes (works for the empty case too).
    new = Table(names=SCHEMA, dtype=DTYPES)
    for r in rows:
        new.add_row([r[c] for c in SCHEMA])
    if merge and os.path.exists(OUT_CATALOG):
        old = Table.read(OUT_CATALOG, format='ascii.ecsv')
        for c in SCHEMA:                       # migrate older/narrower files
            if c not in old.colnames:
                old[c] = ['unknown' if c in _STR_COLS else np.nan] * len(old)
        keys = {(r['TRIGGER_NAME'], r['DETECTOR']) for r in rows}
        keep = [i for i, r in enumerate(old)
                if (str(r['TRIGGER_NAME']), str(r['DETECTOR'])) not in keys]
        old = old[keep][list(SCHEMA)]          # column order + drop strays
        for r in rows:
            old.add_row([r[c] for c in SCHEMA])
        new = old
    tmp = OUT_CATALOG + '.tmp'
    new.write(tmp, format='ascii.ecsv', overwrite=True)
    os.replace(tmp, OUT_CATALOG)
    return len(new)


# ============================================================================
# gui -- human path (detector picker -> bkg selector -> source marker)
# ============================================================================

def source_marker_gui(trigger, ref_det, suggested=None):
    """Minimal 2-click source/emission marker on the brightest-detector LC.
    Returns (t1, t2). Reuses the same LC the picker draws."""
    P = p0()
    import matplotlib.pyplot as plt
    P._ensure_keepalive()   # persistent Tk root (multi-window fix); idempotent
    from astropy.io import fits
    tte = P.find_tte(trigger, ref_det)
    band_lo, band_hi = P._band_for_det(ref_det)
    with fits.open(tte) as h:
        ev = h['EVENTS'].data
        t0 = h['PRIMARY'].header.get('TRIGTIME', 0.0)
        eb = h['EBOUNDS'].data
        emid = 0.5 * (np.asarray(eb['E_MIN']) + np.asarray(eb['E_MAX']))
        m = (emid[np.clip(ev['PHA'], 0, len(emid) - 1)] >= band_lo) & \
            (emid[np.clip(ev['PHA'], 0, len(emid) - 1)] <= band_hi)
        tr = ev['TIME'][m] - t0
    lo = suggested['t1'] - 50 if suggested else (tr.min() if len(tr) else -50)
    hi = suggested['t2'] + 50 if suggested else (tr.max() if len(tr) else 100)
    bins = np.arange(lo, hi, 0.256)
    cnt, _ = np.histogram(tr, bins=bins)
    ctr = 0.5 * (bins[:-1] + bins[1:])
    picks = []
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.step(ctr, cnt / 0.256, where='mid', color='black', lw=0.7)
    ax.set_title(f'{trigger} [{ref_det}] — click SOURCE start then stop, then close')
    ax.set_xlabel('Time since trigger (s)'); ax.set_ylabel('Counts/s')
    if suggested:
        ax.axvspan(suggested['t1'], suggested['t2'], color='gold', alpha=0.2,
                   label='suggested')
        ax.legend()
    vlines = []

    def on_click(ev):
        if ev.inaxes != ax or ev.button != 1 or ev.xdata is None:
            return
        if len(picks) >= 2:
            return
        picks.append(float(ev.xdata))
        vlines.append(ax.axvline(ev.xdata, color='red', lw=1.2))
        fig.canvas.draw_idle()
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show(block=True)
    if len(picks) == 2:
        return min(picks), max(picks)
    if suggested:
        # R-GL-3 visibility: adopting the suggestion must never be silent.
        # (Phase-3 rebuild per GUI_REQUIREMENTS R-SM-2..5 will make adoption an
        # explicit Accept instead of a window-close side effect.)
        print(f'  {trigger}: source window closed with {len(picks)} click(s) — '
              f"ADOPTING the suggested source [{suggested['t1']:.3f}, "
              f"{suggested['t2']:.3f}] s")
        return suggested['t1'], suggested['t2']
    raise SystemExit(f'{trigger}: source not marked')


def gui_one(trigger, approver):
    """Full human approval for one burst -> writes decision.json (mode=human_gui)."""
    P = p0()
    cand = compute_candidates(trigger)
    angles = cand['angles'] or {d: 999.0 for d in cand['pre_ticked']}
    # The GUI approval path is review-seeded: default ticks should have a
    # suggested background interval to Accept/adjust. Angle-qualified detectors
    # without a seed remain visible in the picker and can still be manually
    # selected, but then their background must be drawn fresh.
    seeded = set(cand['suggested_bkg'])
    pre_ticked_for_gui = set(cand['pre_ticked']) & seeded
    low_side = getattr(P, 'LOW_SIDE_NAI', {'n0', 'n1', 'n2', 'n3', 'n4', 'n5'})
    seeded_nai = {d for d in pre_ticked_for_gui if d.startswith('n')}
    if 'b0' in pre_ticked_for_gui and not any(d in low_side for d in seeded_nai):
        pre_ticked_for_gui.remove('b0')
    if 'b1' in pre_ticked_for_gui and not any(
            d.startswith('n') and d not in low_side for d in seeded_nai):
        pre_ticked_for_gui.remove('b1')
    dropped_defaults = sorted(set(cand['pre_ticked']) - pre_ticked_for_gui)
    if dropped_defaults:
        print(f'  {trigger}: not pre-ticking unseeded/unpaired defaults: '
              f'{", ".join(dropped_defaults)}')
    if cand['src_ra'] is None:
        # HARD STOP (R-GL-4, decided 2026-07-03): in gui mode the picker IS the
        # rater's detector-selection judgement; silently substituting seeded
        # pre-ticks would change the benchmark task. main() catches SystemExit
        # per-trigger, so an --all run continues with the next burst.
        raise SystemExit(
            f'{trigger}: no source RA/DEC (results/grb_sample.ecsv missing or '
            f'lacks this trigger) — the detector picker cannot run. '
            f'`git pull` to get the tracked catalog, then retry. '
            f'Refusing to approve without the picker.')
    if angles:
        selected = P.pick_detectors_with_angles_gui(
            trigger, angles, pre_ticked_for_gui, set(cand['bcat']),
            cand['src_ra'], cand['src_dec'])
    else:
        # R-GL-5: angle computation failed (POSHIST/network) with RA/DEC known.
        # Offline != stale clone, so continue — but LOUDLY, never silently.
        print('  ' + '!' * 66)
        print(f'  {trigger}: DETECTOR PICKER SKIPPED — angle computation failed '
              '(see message above).')
        print(f'  Proceeding with seeded pre-ticked detectors: '
              f'{", ".join(sorted(pre_ticked_for_gui)) or "(none)"}')
        print('  ' + '!' * 66)
        selected = list(pre_ticked_for_gui)
    if not selected:
        return trigger, 'no detectors', 0
    # Ubuntu/TkAgg: finish tearing down the picker window before the first detector
    # window opens (same deferred-destroy zombie fix as between detectors).
    if hasattr(P, '_drain_gui_events'):
        P._drain_gui_events()
    windows = {}
    for det in selected:
        if not P.ensure_tte_for_detector(trigger, det):
            continue
        seed = cand['suggested_bkg'].get(det, {})
        if not seed:
            print(f'  {trigger} {det}: no pre-selected background; draw fresh or skip')
        res, pre, post = P.review_one_detector(trigger, det, seed, None, None)
        if res == 'quit':                  # honour Quit -> abort the burst (not skip)
            raise SystemExit(f'{trigger}: user quit at {det}')
        if res != 'accept':                # 'skip' / closed-without-action
            print(f'  {det}: {res} — skipping')
            continue
        same = (seed and list(pre) == seed.get('pre') and list(post) == seed.get('post'))
        windows[det] = {'pre': list(pre), 'post': list(post),
                        'window_source': 'accepted_suggestion' if same else 'adjusted'}
    if not windows:
        return trigger, 'no windows accepted', 0
    # source is marked on a NaI LC; if only BGO windows were accepted, we cannot.
    nai_ref = sorted([d for d in windows if d.startswith('n')],
                     key=lambda d: angles.get(d, 999))
    if not nai_ref:
        return trigger, 'no NaI approved (cannot mark source on BGO)', 0
    s1, s2 = source_marker_gui(trigger, nai_ref[0], cand['suggested_source'])
    decision = {'trigger': trigger, 'approver': approver, 'mode': 'human_gui',
                'detectors': list(windows), 'source': {'t1': s1, 't2': s2},
                'windows': windows,
                'angles': {d: angles.get(d) for d in windows}}
    os.makedirs(APPROVAL_DIR, exist_ok=True)
    with open(os.path.join(APPROVAL_DIR, f'{trigger}_decision.json'), 'w') as f:
        json.dump(decision, f, indent=2)
    return trigger, 'decided', len(windows)


# ============================================================================
# main
# ============================================================================

def _select_triggers(args):
    if args.trigger:
        return [args.trigger]
    if getattr(args, 'all', False):
        return all_triggers()
    raise SystemExit('Specify --trigger <bn...> or --all')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='mode', required=True)

    # --approval-dir / --out isolate a rater's run (decision JSONs + output catalog),
    # so multiple experts and the AI each produce a separate catalog for the benchmark.
    pr = sub.add_parser('render', help='render LC PNGs + candidate manifest')
    pr.add_argument('--trigger'); pr.add_argument('--all', action='store_true')
    pr.add_argument('--overwrite', action='store_true')
    pr.add_argument('--approval-dir', default=None)

    ing = sub.add_parser('ingest', help='decision JSONs -> stamped catalog')
    ing.add_argument('--trigger'); ing.add_argument('--all', action='store_true')
    ing.add_argument('--approval-dir', default=None)
    ing.add_argument('--out', default=None, help='output catalog path (per-rater)')

    g = sub.add_parser('gui', help='human approval (detector+bkg+source)')
    g.add_argument('--trigger'); g.add_argument('--all', action='store_true')
    g.add_argument('--approver', required=True)
    g.add_argument('--approval-dir', default=None)
    g.add_argument('--out', default=None, help='output catalog path (per-rater)')

    args = ap.parse_args()
    global APPROVAL_DIR, OUT_CATALOG
    if getattr(args, 'approval_dir', None):
        APPROVAL_DIR = args.approval_dir
    if getattr(args, 'out', None):
        OUT_CATALOG = args.out

    if args.mode == 'render':
        for trig in _select_triggers(args):
            try:
                r = render_one(trig, overwrite=args.overwrite)
            except Exception as exc:
                r = (trig, f'FAIL {type(exc).__name__}: {exc}', 0)
            print(f'{r[0]:13s} {r[1]:24s} {r[2]} PNGs')

    elif args.mode == 'ingest':
        rows = []
        for trig in _select_triggers(args):
            try:
                r = ingest_one(trig, rows)
            except Exception as exc:
                r = (trig, f'FAIL {type(exc).__name__}: {exc}', 0)
            print(f'{r[0]:13s} {r[1]:24s} {r[2]} rows')
        total = write_catalog(rows, merge=True)
        print(f'\n-> {OUT_CATALOG}: +{len(rows)} rows this run, {total} total')

    elif args.mode == 'gui':
        rows = []
        for trig in _select_triggers(args):
            try:
                r = gui_one(trig, args.approver)
                if r[1] == 'decided':
                    # surface the ingest outcome — an INVALID decision must not
                    # be reported as a success (silent-reject found in the first
                    # Expert1 pilot run: source window overlapped a post window)
                    r = ingest_one(trig, rows)
            except SystemExit as exc:
                r = (trig, f'stop: {exc}', 0)
            print(f'{r[0]:13s} {r[1]:24s} {r[2]}')
        if rows:
            total = write_catalog(rows, merge=True)
            print(f'\n-> {OUT_CATALOG}: +{len(rows)} rows, {total} total')


if __name__ == '__main__':
    main()
