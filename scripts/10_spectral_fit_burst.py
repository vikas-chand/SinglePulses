#!/usr/bin/env python
"""
End-to-end spectral analysis for ONE burst (Burgess+2014 / Guiriec+2015 style).

For each Bayesian-block bin (from bb_blocks_spectral_<trigger>.ecsv,
8-900 keV T_INT-filtered) AND for the time-integrated window, jointly fit
the following models on approved NaI (+ optional BGO) detectors:

  GBM-meaningful set (6 models):
    Band       (4)   — non-thermal baseline
    CPL        (3)   — cutoff PL; solves β-rails for short bursts
    SBPL       (4)   — smoothly broken PL
    DSBPL      (6)   — Ravasio+2018; THE Two_Breaks namesake model
    Band+BB    (6)   — Guiriec M2; Burgess+2014 thermal/non-thermal
    CPL+BB     (5)   — Guiriec M5; compact thermal + cutoff

  Note: Band+PL / Band+CPL / CPL+PL (Guiriec M3 / M4 / true B+C) and the
  high-E ×Cutoff variants need LLE/LAT data to constrain the extra
  high-energy component — deferred until LLE pipeline is wired up.

Uses the BRIGHTEST NaI's BB block edges as canonical time bins
(Burgess+ 2019 convention) and seeds all per-block fits from the T_INT
fit (Burgess+ 2014 convention; do NOT chain seed-from-previous-block).

MINOS asymmetric errors via jl.get_errors() after each fit; Hessian
fallback if MINOS fails. K-edge masked at 30-40 keV (Gruber+ 2014).
Cross-norm use_effective_area_correction(0.8, 1.2) on non-reference
detectors.

Outputs per burst (results/per_burst/<trigger>/):
  spectral_fits.ecsv   — one row per bin (BLOCK=-1 = T_INT) × 6 models
  spectral_fits.json   — metadata (canonical detector, time bins, etc.)
  ep_kt_correlation.png  — Ep vs kT scatter (Band+BB fit)
  spectral_evolution.png — Ep(t), kT(t), α(t)

Usage:
  python 10_spectral_fit_burst.py --trigger bn260105973
"""
import os, sys, glob, argparse, warnings, json
warnings.filterwarnings('ignore')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import numpy as np
from astropy.io import fits
from astropy.table import Table

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

# ---- Paths ----
BASE = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE, 'data')
RESULTS_DIR = os.path.join(BASE, 'results')
PER_BURST_DIR = os.path.join(RESULTS_DIR, 'per_burst')

# ---- Energy ranges ----
NAI_RANGES = ('8.1-33', '40-900')      # K-edge masked
BGO_RANGES = ('300-40000',)
LLE_RANGES = ('30000-100000',)         # 30 MeV - 100 MeV (LLE native band)
EFFAREA_BOUNDS = (0.8, 1.2)

DEFAULT_PARAMS = dict(
    alpha=-1.0, Ep=200.0, beta=-2.25, kT=30.0,
    K_band=0.01, K_bb=1e-4,
)


def find_tte(trigger, det):
    # newest version, deterministic (audit #19: was unsorted glob()[0])
    m = sorted(glob.glob(os.path.join(DATA_DIR, trigger, f'glg_tte_{det}_*.fit.gz')))
    return m[-1] if m else None

def find_rsp(trigger, det):
    # newest version, deterministic (audit #19: was unsorted glob()[0])
    m = sorted(glob.glob(os.path.join(DATA_DIR, trigger, f'glg_cspec_{det}_*.rsp*')))
    return m[-1] if m else None

def find_lat_files(trigger):
    """(ft1, ft2_lat, rsp_standin) for the >100 MeV LAT chain, or (None,)*3.

    FT1/FT2 come from data/<trigger>/LAT/ (astroquery FSSC naming L*_EV00/_SC00
    or gll_ft1/gll_ft2). The RSP is a gtburst LATData constructor requirement
    only (unused >100 MeV): the LLE gll_cspec rsp when present, else any local
    cspec rsp as a stand-in."""
    base = os.path.join(DATA_DIR, trigger)
    ft1 = (sorted(glob.glob(os.path.join(base, 'LAT', '*_EV*.fits')))
           or sorted(glob.glob(os.path.join(base, 'LAT', 'gll_ft1_*.fit*'))))
    ft2 = (sorted(glob.glob(os.path.join(base, 'LAT', '*_SC*.fits')))
           or sorted(glob.glob(os.path.join(base, 'LAT', 'gll_ft2_*.fit*')))
           or sorted(glob.glob(os.path.join(base, 'gll_pt_*.fit*'))))
    rsp = (sorted(glob.glob(os.path.join(base, 'gll_cspec_*.rsp*')))
           or sorted(glob.glob(os.path.join(base, 'glg_cspec_*.rsp2'))))
    if ft1 and ft2 and rsp:
        return ft1[-1], ft2[-1], rsp[-1]
    return None, None, None


# Real source coordinates — REQUIRED when a FermiLATLike plugin is present
# (the LAT likelihood evaluates exposure at the source position; for GBM-only
# fits the PointSource direction is irrelevant and stays at 0,0).
SRC_RA = 0.0
SRC_DEC = 0.0


def find_lle_files(trigger):
    """Return (lle_event_file, pointing_file, rsp_file) or (None, None, None).
    from_lat_lle REQUIRES the LLE POINTING file gll_pt_*.fit; the LAT FT2
    (gll_ft2_*) makes it FitFail (LATBright E2E audit C1-C3), so gll_pt is used
    STRICTLY and gll_ft2 is only a last resort with a warning. A common file
    version is preferred across the triplet to avoid mixed-version DRMs."""
    import re
    base = os.path.join(DATA_DIR, trigger)
    def _v(p):
        m = re.search(r'_v(\d+)\.', os.path.basename(p)); return m.group(1) if m else None
    lle = sorted(glob.glob(os.path.join(base, 'gll_lle_*.fit*')))
    pt = sorted(glob.glob(os.path.join(base, 'gll_pt_*.fit*')))
    ft2 = sorted(glob.glob(os.path.join(base, 'gll_ft2_*.fit*')))
    rsp = sorted(glob.glob(os.path.join(base, 'gll_lle_*.rsp*'))
               + glob.glob(os.path.join(base, 'gll_cspec_*.rsp*')))
    if not (lle and (pt or ft2) and rsp):
        return None, None, None
    L = lle[-1]; v = _v(L)
    if pt:
        P = next((p for p in pt if _v(p) == v), pt[-1])
    else:
        P = ft2[-1]
        print(f'    {trigger}: WARNING no gll_pt POINTING file — falling back to LAT '
              f'FT2 {os.path.basename(P)} (from_lat_lle may FitFail)')
    R = next((r for r in rsp if _v(r) == v), rsp[-1])
    return L, P, R


def load_brightest_bins(trigger, single_path):
    sp = Table.read(single_path, format='ascii.ecsv')
    m = sp['TRIGGER_NAME'] == trigger
    if not m.any():
        return None
    return str(sp[m][0]['DETECTOR']).strip()


def get_canonical_bins(trigger, bb_spectral_path, single_path, approved_dets):
    bb = Table.read(bb_spectral_path, format='ascii.ecsv')
    bb = bb[bb['TRIGGER_NAME'] == trigger]
    if len(bb) == 0:
        raise RuntimeError(f'No BB blocks in {bb_spectral_path} for {trigger}')

    dets_in_bb = sorted(set(str(r['DETECTOR']).strip() for r in bb)
                        & set(approved_dets))
    if not dets_in_bb:
        raise RuntimeError('No overlap between BB ECSV dets and approved bkg dets')

    brightest = load_brightest_bins(trigger, single_path)
    if brightest in dets_in_bb:
        canonical_det = brightest
    else:
        det_scores = {d: float(bb[bb['DETECTOR'] == d]['SIGNIFICANCE'].mean())
                      for d in dets_in_bb}
        canonical_det = max(det_scores, key=det_scores.get)

    canonical = bb[bb['DETECTOR'] == canonical_det]
    canonical.sort('T_START')
    return canonical_det, list(canonical['T_START']), list(canonical['T_STOP'])


def _collapse_rsp2_to_single(rsp2_path, src_lo, src_hi, out_dir):
    """Some GBM .rsp2 files have time-dependent matrices that only span the
    trigger window; when the analysis background interval falls outside that
    span, 3ML's count-weighted response build raises IntervalOfInterestNotCovered.
    Extract the single SPECRESP MATRIX with the largest overlap with the SOURCE
    window [src_lo, src_hi] and write it as a standalone .rsp (PRIMARY + EBOUNDS
    + that matrix). Returns the temp .rsp path, or None on failure.
    The static single matrix is the standard treatment for short/time-integrated
    GBM spectra and avoids the time-weighting that needs full coverage."""
    try:
        with fits.open(rsp2_path) as h:
            trigt = next((e.header['TRIGTIME'] for e in h
                          if 'TRIGTIME' in e.header), None)
            mats = [i for i, e in enumerate(h) if e.name == 'SPECRESP MATRIX']
            if len(mats) <= 1:
                return None       # genuinely single matrix; nothing to collapse
            best, best_ov = mats[0], -1.0
            for i in mats:
                t0 = h[i].header.get('TSTART'); t1 = h[i].header.get('TSTOP')
                if t0 is None or t1 is None or trigt is None:
                    continue
                ov = max(0.0, min(t1 - trigt, src_hi) - max(t0 - trigt, src_lo))
                if ov > best_ov:
                    best_ov, best = ov, i
            sel = fits.HDUList([h[0], h['EBOUNDS'], h[best]])
            sel[2].header['EXTVER'] = 1
            base = os.path.basename(rsp2_path).replace('.rsp2', '')
            # PID-unique: out_dir is the SHARED data/<trig>/, so concurrent coarse
            # (LLE-grid) + fine (GBM-grid) fits of the same burst/detector must not
            # write the same temp .rsp. (Codex audit MED, 2026-07-17.)
            out = os.path.join(out_dir, f'_single_{base}_p{os.getpid()}.rsp')
            sel.writeto(out, overwrite=True)
        return out
    except Exception:
        return None


def build_spectrumlike_per_block(trigger, det, pre, post, bin_starts, bin_stops):
    from threeML import TimeSeriesBuilder
    if det == 'lle':
        # LAT LLE — 30-100 MeV native; uses separate event/FT2/RSP triplet
        lle_file, ft2_file, rsp_file = find_lle_files(trigger)
        if lle_file is None:
            return None
        try:
            tsb = TimeSeriesBuilder.from_lat_lle(
                'lle', lle_file=lle_file, ft2_file=ft2_file,
                rsp_file=rsp_file, verbose=False)
        except Exception as exc:
            print(f'    lle: from_lat_lle failed — {exc}')
            return None
        ranges = LLE_RANGES
    else:
        tte = find_tte(trigger, det)
        rsp = find_rsp(trigger, det)
        if tte is None or rsp is None:
            return None
        tsb = TimeSeriesBuilder.from_gbm_tte(det, tte, rsp_file=rsp,
                                              verbose=False)
        ranges = NAI_RANGES if det.startswith('n') else BGO_RANGES

    # The polynomial background fit can raise FitFailed for one detector
    # (degenerate bkg window / sparse channel). Skip that detector rather than
    # aborting the whole burst — the joint fit proceeds on the others.
    try:
        tsb.set_background_interval(f'{pre[0]:.3f}-{pre[1]:.3f}',
                                    f'{post[0]:.3f}-{post[1]:.3f}')
    except Exception as exc:
        print(f'    {det}: background polyfit failed — skipping detector ({exc})')
        return [None] * len(bin_starts)
    tsb.create_time_bins(start=list(bin_starts), stop=list(bin_stops),
                         method='custom')
    _tmp_rsp = None
    try:
        speclikes_raw = tsb.to_spectrumlike(from_bins=True)
    except Exception as exc:
        # Common cause: time-dependent .rsp2 whose matrices don't span the
        # background interval -> IntervalOfInterestNotCovered during the
        # count-weighted response build. Retry with a single static matrix
        # covering the SOURCE window. Only applies to real-detector (.rsp2) paths.
        if det != 'lle':
            rsp = find_rsp(trigger, det)
            src_lo, src_hi = float(min(bin_starts)), float(max(bin_stops))
            _tmp_rsp = _collapse_rsp2_to_single(
                rsp, src_lo, src_hi, os.path.join(DATA_DIR, trigger))
        if _tmp_rsp is not None:
            try:
                tte = find_tte(trigger, det)
                tsb = TimeSeriesBuilder.from_gbm_tte(det, tte, rsp_file=_tmp_rsp,
                                                     verbose=False)
                tsb.set_background_interval(f'{pre[0]:.3f}-{pre[1]:.3f}',
                                            f'{post[0]:.3f}-{post[1]:.3f}')
                tsb.create_time_bins(start=list(bin_starts),
                                     stop=list(bin_stops), method='custom')
                speclikes_raw = tsb.to_spectrumlike(from_bins=True)
                print(f'    {det}: recovered via single-matrix .rsp '
                      f'(rsp2 time-weighting failed)')
            except Exception as exc2:
                print(f'    {det}: to_spectrumlike failed (rsp2 + collapse) — {exc2}')
                if _tmp_rsp and os.path.exists(_tmp_rsp):
                    os.unlink(_tmp_rsp)
                return [None] * len(bin_starts)
        else:
            print(f'    {det}: to_spectrumlike failed — {exc}')
            return [None] * len(bin_starts)
    finally:
        if _tmp_rsp and os.path.exists(_tmp_rsp):
            try: os.unlink(_tmp_rsp)
            except Exception: pass
    if not isinstance(speclikes_raw, list):
        speclikes_raw = [speclikes_raw]
    speclikes = []
    for k, sl in enumerate(speclikes_raw):
        try:
            sl.set_active_measurements(*ranges)
            speclikes.append(sl)
        except Exception as exc:
            print(f'    {det} block {k}: set_active_measurements failed — {exc}')
            speclikes.append(None)
    while len(speclikes) < len(bin_starts):
        speclikes.append(None)
    return speclikes[:len(bin_starts)]


def _clamp(val, lo, hi):
    return max(lo + 1e-4 * (hi - lo), min(hi - 1e-4 * (hi - lo), val))


# ============================================================
# Model component builders
# ============================================================
def _setup_band(seed):
    from astromodels import Band
    b = Band()
    b.alpha.bounds = (-1.9, 1.9)
    b.xp.bounds    = (30.0, 5000.0)
    b.beta.bounds  = (-5.0, -1.6)
    b.alpha.value = _clamp(seed.get('band_alpha', DEFAULT_PARAMS['alpha']), -1.9, 1.9)
    b.xp.value    = _clamp(seed.get('band_Ep',    DEFAULT_PARAMS['Ep']), 30.0, 5000.0)
    b.beta.value  = _clamp(seed.get('band_beta',  DEFAULT_PARAMS['beta']), -5.0, -1.6)
    b.K.value     = max(1e-10, seed.get('band_K', DEFAULT_PARAMS['K_band']))
    return b

def _setup_cpl(seed):
    from astromodels import Cutoff_powerlaw
    c = Cutoff_powerlaw()
    c.K.bounds = (1e-10, 1e4)
    c.index.bounds = (-2.0, 1.0)
    c.xc.bounds = (10.0, 5e4)
    c.K.value = max(1e-10, seed.get('cpl_K', DEFAULT_PARAMS['K_band']))
    c.index.value = _clamp(seed.get('cpl_index', DEFAULT_PARAMS['alpha']), -2.0, 1.0)
    c.xc.value = _clamp(seed.get('cpl_xc', DEFAULT_PARAMS['Ep']), 10.0, 5e4)
    return c

def _setup_bb(seed):
    from astromodels import Blackbody
    bb = Blackbody()
    bb.K.bounds = (1e-15, 1e4)
    bb.kT.bounds = (1.0, 200.0)
    bb.K.value = max(1e-15, seed.get('bb_K', DEFAULT_PARAMS['K_bb']))
    bb.kT.value = _clamp(seed.get('bb_kT', DEFAULT_PARAMS['kT']), 1.0, 200.0)
    return bb

def _setup_sbpl(seed):
    from astromodels import SmoothlyBrokenPowerLaw
    s = SmoothlyBrokenPowerLaw()
    s.K.bounds = (1e-10, 1e4)
    s.alpha.bounds = (-2.5, 1.5)
    s.break_energy.bounds = (10.0, 5000.0)
    s.beta.bounds = (-5.0, -1.5)
    s.K.value = max(1e-10, seed.get('sbpl_K', 0.05))
    s.alpha.value = _clamp(seed.get('sbpl_alpha', DEFAULT_PARAMS['alpha']), -2.5, 1.5)
    s.break_energy.value = _clamp(seed.get('sbpl_break', 300.0), 10.0, 5000.0)
    s.beta.value = _clamp(seed.get('sbpl_beta', DEFAULT_PARAMS['beta']), -5.0, -1.5)
    s.break_scale.fix = True
    return s

def _setup_dsbpl(seed):
    from astromodels import DoubleSmoothlyBrokenPowerlaw
    d = DoubleSmoothlyBrokenPowerlaw()
    d.K.bounds = (1e-10, 1e4)
    d.alpha1.bounds = (-2.5, 2.5)
    d.xb.bounds = (10.0, 900.0)
    d.alpha2.bounds = (-3.0, 0.5)
    d.xp.bounds = (30.0, 5000.0)
    d.beta.bounds = (-5.0, -1.5)
    d.K.value = max(1e-10, seed.get('dsbpl_K', 0.05))
    d.alpha1.value = _clamp(seed.get('dsbpl_alpha1', -0.66), -2.5, 2.5)
    d.xb.value = _clamp(seed.get('dsbpl_xb', 50.0), 10.0, 900.0)
    d.alpha2.value = _clamp(seed.get('dsbpl_alpha2', -1.5), -3.0, 0.5)
    d.xp.value = _clamp(seed.get('dsbpl_xp', DEFAULT_PARAMS['Ep']), 30.0, 5000.0)
    d.beta.value = _clamp(seed.get('dsbpl_beta', DEFAULT_PARAMS['beta']), -5.0, -1.5)
    d.n1.fix = True
    d.n2.fix = True
    d.piv.fix = True
    return d


# ---- SHAPE-census variants (opt-in via --models shape|highe) ----------------
# Free the smoothness so the DATA measure the curvature around the peak
# (Ravasio+2018 fit these for 160625B; the frozen defaults above came from that).
def _setup_sbpl_free(seed):
    s = _setup_sbpl(seed)
    s.break_scale.free = True
    s.break_scale.bounds = (0.01, 2.0)
    s.break_scale.value = _clamp(seed.get('sbplf_scale', 0.3), 0.01, 2.0)
    return s

def _setup_dsbpl_free(seed):
    d = _setup_dsbpl(seed)
    d.n1.free = True
    d.n1.bounds = (0.5, 10.0)
    d.n1.value = _clamp(seed.get('dsbplf_n1', 5.38), 0.5, 10.0)
    d.n2.free = True
    d.n2.bounds = (0.5, 10.0)
    d.n2.value = _clamp(seed.get('dsbplf_n2', 2.69), 0.5, 10.0)
    return d


# ---- High-energy second components (opt-in via --models highe) --------------
# Ported from the LATBright 17-model engine (s03m_joint_5phot_lat_bins.py,
# constructors byte-identical to s03h lines 697-805; port verified 2026-07-16).
# Pivot 1e5 keV = 100 MeV anchors the extra component ABOVE the Band peak.
def _setup_extra_pl(seed):
    from astromodels import Powerlaw
    pl = Powerlaw()
    pl.piv = 1e5                               # 100 MeV
    pl.K.bounds = (1e-15, 1e2)
    pl.index.bounds = (-4.0, -1.0)
    pl.K.value = max(1e-15, seed.get('hepl_K', 1e-4))
    pl.index.value = _clamp(seed.get('hepl_index', -1.8), -4.0, -1.0)
    return pl

def _setup_extra_cpl(seed):
    from astromodels import Cutoff_powerlaw
    c = Cutoff_powerlaw()
    c.piv = 1e5                                # 100 MeV
    c.K.bounds = (1e-15, 1e2)
    c.index.bounds = (-4.0, -1.0)
    c.xc.bounds = (5e4, 1e8)                   # 50 MeV - 100 GeV
    c.K.value = max(1e-15, seed.get('hecpl_K', 1e-4))
    c.index.value = _clamp(seed.get('hecpl_index', -1.8), -4.0, -1.0)
    c.xc.value = _clamp(seed.get('hecpl_xc', 5e5), 5e4, 1e8)
    return c

def _setup_band_ep2mev(seed):
    """Band with Ep RESTRICTED below 2 MeV, so the extra CPL must be the
    high-energy component (Guiriec-style disambiguation)."""
    b = _setup_band(seed)
    b.xp.bounds = (10.0, 2000.0)
    b.xp.value = _clamp(seed.get('band_Ep', DEFAULT_PARAMS['Ep']), 10.0, 2000.0)
    return b

def _setup_cutoff_mult(seed):
    """Multiplicative pure-exponential cutoff: index=0, K=1, piv=1 all FIXED,
    only xc free (pair-production attenuation factor)."""
    from astromodels import Cutoff_powerlaw
    c = Cutoff_powerlaw()
    c.index = 0.0; c.index.fix = True
    c.K = 1.0;     c.K.fix = True
    c.piv = 1.0;   c.piv.fix = True
    c.xc.bounds = (5e4, 1e8)
    c.xc.value = _clamp(seed.get('cut_xc', 5e5), 5e4, 1e8)
    return c


# ============================================================
# Model specs — composite builders + parameter mappings
# ============================================================
# Each spec:
#   name      : display name
#   prefix    : ECSV column prefix
#   build     : seed -> astromodels composite
#   n_params  : free-parameter count (for AIC/BIC)
#   pmap      : { COLUMN_SUFFIX: short_param_name_in_best_df }
#               For composites, astromodels suffixes params with _1, _2 in
#               composition order (first added = _1).
#   seed_keys : { result_key_to_save: prefix in seed dict for downstream }
MODEL_SPECS = [
    {
        'name': 'Band', 'prefix': 'BAND', 'n_params': 4,
        'build': lambda s: _setup_band(s),
        'pmap': {'ALPHA': 'alpha', 'EP': 'xp', 'BETA': 'beta', 'K': 'K'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta', 'K': 'band_K'},
    },
    {
        'name': 'CPL', 'prefix': 'CPL', 'n_params': 3,
        'build': lambda s: _setup_cpl(s),
        'pmap': {'INDEX': 'index', 'XC': 'xc', 'K': 'K'},
        'seed_keys': {'INDEX': 'cpl_index', 'XC': 'cpl_xc', 'K': 'cpl_K'},
    },
    {
        'name': 'SBPL', 'prefix': 'SBPL', 'n_params': 4,
        'build': lambda s: _setup_sbpl(s),
        'pmap': {'ALPHA': 'alpha', 'EBREAK': 'break_energy', 'BETA': 'beta', 'K': 'K'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break', 'BETA': 'sbpl_beta', 'K': 'sbpl_K'},
    },
    {
        'name': 'DSBPL', 'prefix': 'DSBPL', 'n_params': 6,
        'build': lambda s: _setup_dsbpl(s),
        'pmap': {'ALPHA1': 'alpha1', 'XB': 'xb', 'ALPHA2': 'alpha2',
                 'XP': 'xp', 'BETA': 'beta', 'K': 'K'},
        'seed_keys': {'ALPHA1': 'dsbpl_alpha1', 'XB': 'dsbpl_xb',
                      'ALPHA2': 'dsbpl_alpha2', 'XP': 'dsbpl_xp',
                      'BETA': 'dsbpl_beta', 'K': 'dsbpl_K'},
    },
    {
        'name': 'Band+BB', 'prefix': 'BANDBB', 'n_params': 6,
        'build': lambda s: _setup_band(s) + _setup_bb(s),
        'pmap': {'ALPHA': 'alpha_1', 'EP': 'xp_1', 'BETA': 'beta_1', 'K_BAND': 'K_1',
                 'KT': 'kT_2', 'K_BB': 'K_2'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta',
                      'K_BAND': 'band_K', 'KT': 'bb_kT', 'K_BB': 'bb_K'},
    },
    {
        'name': 'CPL+BB', 'prefix': 'CPLBB', 'n_params': 5,
        'build': lambda s: _setup_cpl(s) + _setup_bb(s),
        'pmap': {'INDEX': 'index_1', 'XC': 'xc_1', 'K_CPL': 'K_1',
                 'KT': 'kT_2', 'K_BB': 'K_2'},
        'seed_keys': {'INDEX': 'cpl_index', 'XC': 'cpl_xc', 'K_CPL': 'cpl_K',
                      'KT': 'bb_kT', 'K_BB': 'bb_K'},
    },
]

# ---- SHAPE census set (--models shape): free-smoothness variants ------------
SHAPE_MODEL_SPECS = [
    {
        'name': 'SBPLfree', 'prefix': 'SBPLF', 'n_params': 5,
        'build': lambda s: _setup_sbpl_free(s),
        'pmap': {'ALPHA': 'alpha', 'EBREAK': 'break_energy', 'BETA': 'beta',
                 'SCALE': 'break_scale', 'K': 'K'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break',
                      'BETA': 'sbpl_beta', 'SCALE': 'sbplf_scale', 'K': 'sbpl_K'},
    },
    {
        'name': 'DSBPLfree', 'prefix': 'DSBPLF', 'n_params': 8,
        'build': lambda s: _setup_dsbpl_free(s),
        'pmap': {'ALPHA1': 'alpha1', 'XB': 'xb', 'ALPHA2': 'alpha2',
                 'XP': 'xp', 'BETA': 'beta', 'N1': 'n1', 'N2': 'n2', 'K': 'K'},
        'seed_keys': {'ALPHA1': 'dsbpl_alpha1', 'XB': 'dsbpl_xb',
                      'ALPHA2': 'dsbpl_alpha2', 'XP': 'dsbpl_xp',
                      'BETA': 'dsbpl_beta', 'N1': 'dsbplf_n1', 'N2': 'dsbplf_n2',
                      'K': 'dsbpl_K'},
    },
]

# ---- HIGH-E set (--models highe): second components above the peak ----------
HIGHE_MODEL_SPECS = [
    {
        'name': 'Band+PL', 'prefix': 'BANDPL', 'n_params': 6,
        'build': lambda s: _setup_band(s) + _setup_extra_pl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EP': 'xp_1', 'BETA': 'beta_1', 'K_BAND': 'K_1',
                 'PL_INDEX': 'index_2', 'PL_K': 'K_2'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta',
                      'K_BAND': 'band_K', 'PL_INDEX': 'hepl_index', 'PL_K': 'hepl_K'},
    },
    {
        'name': 'Band+CPL', 'prefix': 'BANDCPL', 'n_params': 7,
        'build': lambda s: _setup_band(s) + _setup_extra_cpl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EP': 'xp_1', 'BETA': 'beta_1', 'K_BAND': 'K_1',
                 'HE_INDEX': 'index_2', 'HE_XC': 'xc_2', 'HE_K': 'K_2'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta',
                      'K_BAND': 'band_K', 'HE_INDEX': 'hecpl_index',
                      'HE_XC': 'hecpl_xc', 'HE_K': 'hecpl_K'},
    },
    {
        'name': 'CPL+PL', 'prefix': 'CPLPL', 'n_params': 5,
        'build': lambda s: _setup_cpl(s) + _setup_extra_pl(s),
        'pmap': {'INDEX': 'index_1', 'XC': 'xc_1', 'K_CPL': 'K_1',
                 'PL_INDEX': 'index_2', 'PL_K': 'K_2'},
        'seed_keys': {'INDEX': 'cpl_index', 'XC': 'cpl_xc', 'K_CPL': 'cpl_K',
                      'PL_INDEX': 'hepl_index', 'PL_K': 'hepl_K'},
    },
    {
        'name': 'CPL+CPL', 'prefix': 'CPLCPL', 'n_params': 6,
        'build': lambda s: _setup_cpl(s) + _setup_extra_cpl(s),
        'pmap': {'INDEX': 'index_1', 'XC': 'xc_1', 'K_LO': 'K_1',
                 'HE_INDEX': 'index_2', 'HE_XC': 'xc_2', 'HE_K': 'K_2'},
        'seed_keys': {'INDEX': 'cpl_index', 'XC': 'cpl_xc', 'K_LO': 'cpl_K',
                      'HE_INDEX': 'hecpl_index', 'HE_XC': 'hecpl_xc', 'HE_K': 'hecpl_K'},
    },
    {
        'name': 'BandR+CPL', 'prefix': 'BANDRCPL', 'n_params': 7,
        'build': lambda s: _setup_band_ep2mev(s) + _setup_extra_cpl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EP': 'xp_1', 'BETA': 'beta_1', 'K_BAND': 'K_1',
                 'HE_INDEX': 'index_2', 'HE_XC': 'xc_2', 'HE_K': 'K_2'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta',
                      'K_BAND': 'band_K', 'HE_INDEX': 'hecpl_index',
                      'HE_XC': 'hecpl_xc', 'HE_K': 'hecpl_K'},
    },
    {
        'name': 'BandxCut', 'prefix': 'BANDCUT', 'n_params': 5,
        'build': lambda s: _setup_band(s) * _setup_cutoff_mult(s),
        'pmap': {'ALPHA': 'alpha_1', 'EP': 'xp_1', 'BETA': 'beta_1', 'K': 'K_1',
                 'EC': 'xc_2'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta',
                      'K': 'band_K', 'EC': 'cut_xc'},
    },
    {
        'name': 'SBPLxCut', 'prefix': 'SBPLCUT', 'n_params': 5,
        'build': lambda s: _setup_sbpl(s) * _setup_cutoff_mult(s),
        'pmap': {'ALPHA': 'alpha_1', 'EBREAK': 'break_energy_1', 'BETA': 'beta_1',
                 'K': 'K_1', 'EC': 'xc_2'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break',
                      'BETA': 'sbpl_beta', 'K': 'sbpl_K', 'EC': 'cut_xc'},
    },
    {
        # SBPL + extra-PL/CPL parents (needed so the SBPL 3-component chains
        # are gateable — Codex ultra audit CRITICAL #5)
        'name': 'SBPL+PL', 'prefix': 'SBPLPL', 'n_params': 6,
        'build': lambda s: _setup_sbpl(s) + _setup_extra_pl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EBREAK': 'break_energy_1', 'BETA': 'beta_1',
                 'K': 'K_1', 'PL_INDEX': 'index_2', 'PL_K': 'K_2'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break',
                      'BETA': 'sbpl_beta', 'K': 'sbpl_K',
                      'PL_INDEX': 'hepl_index', 'PL_K': 'hepl_K'},
    },
    {
        'name': 'SBPL+CPL', 'prefix': 'SBPLCPL', 'n_params': 7,
        'build': lambda s: _setup_sbpl(s) + _setup_extra_cpl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EBREAK': 'break_energy_1', 'BETA': 'beta_1',
                 'K': 'K_1', 'HE_INDEX': 'index_2', 'HE_XC': 'xc_2', 'HE_K': 'K_2'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break',
                      'BETA': 'sbpl_beta', 'K': 'sbpl_K',
                      'HE_INDEX': 'hecpl_index', 'HE_XC': 'hecpl_xc',
                      'HE_K': 'hecpl_K'},
    },
    {
        # Guiriec et al. 2015 (ApJ 807:148) THREE-component model: non-thermal
        # Band + thermal BB + extra PL, fitted SIMULTANEOUSLY. Their detections
        # are in MULTI-pulse bursts (080916C, 090926A); whether any clean
        # SINGLE pulse requires all three, over the widest band, is a direct
        # question of this survey (single-vs-rest). Nested parents for the
        # gate: BANDBB (+PL, 2 params) and BANDPL (+BB, 2 params).
        'name': 'Band+BB+PL', 'prefix': 'BANDBBPL', 'n_params': 8,
        'build': lambda s: _setup_band(s) + _setup_bb(s) + _setup_extra_pl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EP': 'xp_1', 'BETA': 'beta_1', 'K_BAND': 'K_1',
                 'KT': 'kT_2', 'K_BB': 'K_2',
                 'PL_INDEX': 'index_3', 'PL_K': 'K_3'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta',
                      'K_BAND': 'band_K', 'KT': 'bb_kT', 'K_BB': 'bb_K',
                      'PL_INDEX': 'hepl_index', 'PL_K': 'hepl_K'},
    },
    # ---- the FULL 3-component family (registry_v1: band_bb_cpl, cpl_bb_pl,
    # cpl_bb_cpl; + the SBPL-continuum variants Vikas specified). Same
    # composition rule everywhere: <continuum> + Blackbody + <high-E extra
    # (PL or CPL, piv=100 MeV)>. Parents for the chain gate are the
    # 2-component members (<cont>+BB, <cont>+PL/CPL). ----
    {
        'name': 'Band+BB+CPL', 'prefix': 'BANDBBCPL', 'n_params': 9,
        'build': lambda s: _setup_band(s) + _setup_bb(s) + _setup_extra_cpl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EP': 'xp_1', 'BETA': 'beta_1', 'K_BAND': 'K_1',
                 'KT': 'kT_2', 'K_BB': 'K_2',
                 'HE_INDEX': 'index_3', 'HE_XC': 'xc_3', 'HE_K': 'K_3'},
        'seed_keys': {'ALPHA': 'band_alpha', 'EP': 'band_Ep', 'BETA': 'band_beta',
                      'K_BAND': 'band_K', 'KT': 'bb_kT', 'K_BB': 'bb_K',
                      'HE_INDEX': 'hecpl_index', 'HE_XC': 'hecpl_xc',
                      'HE_K': 'hecpl_K'},
    },
    {
        'name': 'CPL+BB+PL', 'prefix': 'CPLBBPL', 'n_params': 7,
        'build': lambda s: _setup_cpl(s) + _setup_bb(s) + _setup_extra_pl(s),
        'pmap': {'INDEX': 'index_1', 'XC': 'xc_1', 'K_CPL': 'K_1',
                 'KT': 'kT_2', 'K_BB': 'K_2',
                 'PL_INDEX': 'index_3', 'PL_K': 'K_3'},
        'seed_keys': {'INDEX': 'cpl_index', 'XC': 'cpl_xc', 'K_CPL': 'cpl_K',
                      'KT': 'bb_kT', 'K_BB': 'bb_K',
                      'PL_INDEX': 'hepl_index', 'PL_K': 'hepl_K'},
    },
    {
        'name': 'CPL+BB+CPL', 'prefix': 'CPLBBCPL', 'n_params': 8,
        'build': lambda s: _setup_cpl(s) + _setup_bb(s) + _setup_extra_cpl(s),
        'pmap': {'INDEX': 'index_1', 'XC': 'xc_1', 'K_CPL': 'K_1',
                 'KT': 'kT_2', 'K_BB': 'K_2',
                 'HE_INDEX': 'index_3', 'HE_XC': 'xc_3', 'HE_K': 'K_3'},
        'seed_keys': {'INDEX': 'cpl_index', 'XC': 'cpl_xc', 'K_CPL': 'cpl_K',
                      'KT': 'bb_kT', 'K_BB': 'bb_K',
                      'HE_INDEX': 'hecpl_index', 'HE_XC': 'hecpl_xc',
                      'HE_K': 'hecpl_K'},
    },
    {
        'name': 'SBPL+BB', 'prefix': 'SBPLBB', 'n_params': 6,
        'build': lambda s: _setup_sbpl(s) + _setup_bb(s),
        'pmap': {'ALPHA': 'alpha_1', 'EBREAK': 'break_energy_1', 'BETA': 'beta_1',
                 'K': 'K_1', 'KT': 'kT_2', 'K_BB': 'K_2'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break',
                      'BETA': 'sbpl_beta', 'K': 'sbpl_K',
                      'KT': 'bb_kT', 'K_BB': 'bb_K'},
    },
    {
        'name': 'SBPL+BB+PL', 'prefix': 'SBPLBBPL', 'n_params': 8,
        'build': lambda s: _setup_sbpl(s) + _setup_bb(s) + _setup_extra_pl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EBREAK': 'break_energy_1', 'BETA': 'beta_1',
                 'K': 'K_1', 'KT': 'kT_2', 'K_BB': 'K_2',
                 'PL_INDEX': 'index_3', 'PL_K': 'K_3'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break',
                      'BETA': 'sbpl_beta', 'K': 'sbpl_K',
                      'KT': 'bb_kT', 'K_BB': 'bb_K',
                      'PL_INDEX': 'hepl_index', 'PL_K': 'hepl_K'},
    },
    {
        'name': 'SBPL+BB+CPL', 'prefix': 'SBPLBBCPL', 'n_params': 9,
        'build': lambda s: _setup_sbpl(s) + _setup_bb(s) + _setup_extra_cpl(s),
        'pmap': {'ALPHA': 'alpha_1', 'EBREAK': 'break_energy_1', 'BETA': 'beta_1',
                 'K': 'K_1', 'KT': 'kT_2', 'K_BB': 'K_2',
                 'HE_INDEX': 'index_3', 'HE_XC': 'xc_3', 'HE_K': 'K_3'},
        'seed_keys': {'ALPHA': 'sbpl_alpha', 'EBREAK': 'sbpl_break',
                      'BETA': 'sbpl_beta', 'K': 'sbpl_K',
                      'KT': 'bb_kT', 'K_BB': 'bb_K',
                      'HE_INDEX': 'hecpl_index', 'HE_XC': 'hecpl_xc',
                      'HE_K': 'hecpl_K'},
    },
]

# Guiriec 3-component test set (--models threecomp): ALL SIX 3-component
# combos {Band,CPL,SBPL} x BB x {PL,CPL} + every nested parent needed for a
# self-consistent dAIC>=10 chain gate, fitted TOGETHER in one run.
_TC_BASE = ('BAND', 'CPL', 'SBPL', 'BANDBB', 'CPLBB')
_TC_HIGHE = ('BANDPL', 'CPLPL', 'BANDCPL', 'CPLCPL',
             'SBPLPL', 'SBPLCPL', 'SBPLBB',
             'BANDBBPL', 'BANDBBCPL', 'CPLBBPL', 'CPLBBCPL',
             'SBPLBBPL', 'SBPLBBCPL')
THREECOMP_MODEL_SPECS = (
    [s for s in MODEL_SPECS if s['prefix'] in _TC_BASE]
    + [s for s in HIGHE_MODEL_SPECS if s['prefix'] in _TC_HIGHE]
)

# The RUNTIME model set. Default = the frozen benchmark 6; main() extends it
# per --models (shape -> +free-smoothness; highe -> +shape +high-E components).
ACTIVE_SPECS = list(MODEL_SPECS)


# ============================================================
# Generic fit driver
# ============================================================
def fit_one_model(data_list, spec, seed=None):
    """Fit a single MODEL_SPECS entry. Returns dict with status, params, neg2logL."""
    from threeML import Model, PointSource, JointLikelihood
    seed = seed or {}
    try:
        composite = spec['build'](seed)
        ps = PointSource('grb', SRC_RA, SRC_DEC, spectral_shape=composite)
        model = Model(ps)
        jl = JointLikelihood(model, data_list)
        jl.set_minimizer('minuit')
        best_df, _ = jl.fit(quiet=True)

        minos_table = None
        try:
            minos_table = jl.get_errors(quiet=True)
        except Exception:
            pass

        try:
            # 3ML's jl.current_minimum is -log(L), NOT -2 log(L).
            # See joint_likelihood.py:275 (minus_log_like_profile) and the
            # 3ML convention at joint_likelihood.py:1292 which itself does
            # `this_TS = 2 * (null_hyp_mlike - alt_hyp_mlike)`. We multiply
            # here so all downstream code uses the standard -2 log(L)
            # convention — AIC = N2LL + 2k, BIC = N2LL + k·ln(N), and
            # Wilks Δχ² thresholds (11.83 = 3σ at 2 dof) apply directly.
            n2ll = 2.0 * float(jl.current_minimum)
        except Exception:
            n2ll = float('nan')

        # Index best_df by short name (last dot-separated segment)
        params = {}
        for idx in best_df.index:
            short = idx.split('.')[-1]
            val = float(best_df.loc[idx, 'value'])
            try:
                err = float(best_df.loc[idx, 'error'])
            except Exception:
                err = float('nan')
            neg = pos = float('nan')
            if minos_table is not None and idx in minos_table.index:
                try:
                    neg = float(minos_table.loc[idx, 'negative_error'])
                    pos = float(minos_table.loc[idx, 'positive_error'])
                except Exception:
                    pass
            params[short] = {'val': val, 'err': err, 'neg': neg, 'pos': pos}

        # ---- empirical peak-shape statistic (shape census, 2026-07-16) ----
        # nuFnu curve of the FITTED model: peak energy from the curve itself +
        # half-max width W = log10(E2/E1) (Axelsson-Borgonovo-style, but from
        # the best-fit model curve, uniform across ALL models incl. composites).
        epk_curve = width_hm = float('nan')
        try:
            _E = np.logspace(np.log10(8.0), np.log10(1.0e6), 700)   # 8 keV - 1 GeV
            _nufnu = _E**2 * np.array([float(composite(e)) for e in _E])
            if np.all(np.isfinite(_nufnu)) and _nufnu.max() > 0:
                _i = int(np.argmax(_nufnu))
                if 0 < _i < len(_E) - 1:                 # interior peak only
                    epk_curve = float(_E[_i])
                    _half = 0.5 * _nufnu[_i]
                    _lo = np.where(_nufnu[:_i] <= _half)[0]
                    _hi = np.where(_nufnu[_i:] <= _half)[0]
                    if len(_lo) and len(_hi):            # both crossings inside band
                        e1 = np.interp(_half, _nufnu[_lo[-1]:_lo[-1]+2],
                                       _E[_lo[-1]:_lo[-1]+2])
                        j = _i + _hi[0]
                        e2 = np.interp(-_half, -_nufnu[j-1:j+1], _E[j-1:j+1])
                        if e2 > e1 > 0:
                            width_hm = float(np.log10(e2 / e1))
        except Exception:
            pass

        return {
            'status': 'OK',
            'neg2logL': n2ll,
            'n_params': spec['n_params'],
            'params': params,
            'minos_ok': (minos_table is not None),
            'epk_curve': epk_curve,
            'width_hm': width_hm,
        }
    except Exception as exc:
        return {'status': 'FAIL', 'reason': str(exc)[:120],
                'neg2logL': float('nan'), 'n_params': spec['n_params'],
                'params': {}, 'minos_ok': False}


def model_columns(spec, result, n_data):
    """Flatten a fit result into ECSV columns prefixed with spec['prefix']."""
    p = spec['prefix']
    out = {f'{p}_STATUS': result.get('status', 'NA'),
           f'{p}_N2LL':   result.get('neg2logL', float('nan')),
           f'{p}_MINOS_OK': bool(result.get('minos_ok', False)),
           f'{p}_VALID': bool(result.get('physical', False))}
    if result.get('status') == 'OK':
        n2ll = result['neg2logL']; nk = result['n_params']
        out[f'{p}_AIC'] = n2ll + 2 * nk
        out[f'{p}_BIC'] = n2ll + nk * np.log(max(n_data, 1))
    else:
        out[f'{p}_AIC'] = float('nan')
        out[f'{p}_BIC'] = float('nan')
    # peak-shape statistics from the fitted curve (NaN when peak not interior)
    out[f'{p}_EPK_CURVE'] = result.get('epk_curve', float('nan'))
    out[f'{p}_WIDTH_HM'] = result.get('width_hm', float('nan'))
    for col_suffix, short in spec['pmap'].items():
        d = result.get('params', {}).get(short)
        if d is None:
            out[f'{p}_{col_suffix}']         = float('nan')
            out[f'{p}_{col_suffix}_ERR']     = float('nan')
            out[f'{p}_{col_suffix}_NEG_ERR'] = float('nan')
            out[f'{p}_{col_suffix}_POS_ERR'] = float('nan')
        else:
            out[f'{p}_{col_suffix}']         = d['val']
            out[f'{p}_{col_suffix}_ERR']     = d['err']
            out[f'{p}_{col_suffix}_NEG_ERR'] = d['neg']
            out[f'{p}_{col_suffix}_POS_ERR'] = d['pos']
    return out


def capture_seed(spec, result):
    """Extract converged params as seed dict for downstream fits."""
    if result.get('status') != 'OK':
        return {}
    seed = {}
    for col_suffix, seed_key in spec['seed_keys'].items():
        short = spec['pmap'][col_suffix]
        d = result['params'].get(short)
        if d is not None and np.isfinite(d['val']):
            seed[seed_key] = d['val']
    return seed


# Parameter bounds (must mirror the _setup_* functions). Used to detect
# railed fits and to enforce physical break ordering for model selection.
PARAM_BOUNDS = {
    'BAND':   {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 5000.0), 'BETA': (-5.0, -1.6)},
    'CPL':    {'INDEX': (-2.0, 1.0), 'XC': (10.0, 5e4)},
    'SBPL':   {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5)},
    'DSBPL':  {'ALPHA1': (-2.5, 2.5), 'XB': (10.0, 900.0), 'ALPHA2': (-3.0, 0.5),
               'XP': (30.0, 5000.0), 'BETA': (-5.0, -1.5)},
    'BANDBB': {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 5000.0), 'BETA': (-5.0, -1.6),
               'KT': (1.0, 200.0)},
    'CPLBB':  {'INDEX': (-2.0, 1.0), 'XC': (10.0, 5e4), 'KT': (1.0, 200.0)},
    # ---- shape census (railing on the freed smoothness = unconstrained) ----
    'SBPLF':  {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5),
               'SCALE': (0.01, 2.0)},
    'DSBPLF': {'ALPHA1': (-2.5, 2.5), 'XB': (10.0, 900.0), 'ALPHA2': (-3.0, 0.5),
               'XP': (30.0, 5000.0), 'BETA': (-5.0, -1.5),
               'N1': (0.5, 10.0), 'N2': (0.5, 10.0)},
    # ---- high-E second components (LATBright s03m port) ----
    'BANDPL':   {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 5000.0), 'BETA': (-5.0, -1.6),
                 'PL_INDEX': (-4.0, -1.0)},
    'BANDCPL':  {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 5000.0), 'BETA': (-5.0, -1.6),
                 'HE_INDEX': (-4.0, -1.0), 'HE_XC': (5e4, 1e8)},
    'CPLPL':    {'INDEX': (-2.0, 1.0), 'XC': (10.0, 5e4), 'PL_INDEX': (-4.0, -1.0)},
    'CPLCPL':   {'INDEX': (-2.0, 1.0), 'XC': (10.0, 5e4),
                 'HE_INDEX': (-4.0, -1.0), 'HE_XC': (5e4, 1e8)},
    'BANDRCPL': {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 2000.0), 'BETA': (-5.0, -1.6),
                 'HE_INDEX': (-4.0, -1.0), 'HE_XC': (5e4, 1e8)},
    'BANDCUT':  {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 5000.0), 'BETA': (-5.0, -1.6),
                 'EC': (5e4, 1e8)},
    'SBPLCUT':  {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5),
                 'EC': (5e4, 1e8)},
    # Guiriec 3-component family: continuum shape + BB temperature + extra-
    # component index all gated against railing (same rails as their
    # 2-component parents).
    'BANDBBPL':  {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 5000.0), 'BETA': (-5.0, -1.6),
                  'KT': (1.0, 200.0), 'PL_INDEX': (-4.0, -1.0)},
    'BANDBBCPL': {'ALPHA': (-1.9, 1.9), 'EP': (30.0, 5000.0), 'BETA': (-5.0, -1.6),
                  'KT': (1.0, 200.0), 'HE_INDEX': (-4.0, -1.0), 'HE_XC': (5e4, 1e8)},
    'CPLBBPL':   {'INDEX': (-2.0, 1.0), 'XC': (10.0, 5e4), 'KT': (1.0, 200.0),
                  'PL_INDEX': (-4.0, -1.0)},
    'CPLBBCPL':  {'INDEX': (-2.0, 1.0), 'XC': (10.0, 5e4), 'KT': (1.0, 200.0),
                  'HE_INDEX': (-4.0, -1.0), 'HE_XC': (5e4, 1e8)},
    'SBPLBB':    {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5),
                  'KT': (1.0, 200.0)},
    'SBPLBBPL':  {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5),
                  'KT': (1.0, 200.0), 'PL_INDEX': (-4.0, -1.0)},
    'SBPLBBCPL': {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5),
                  'KT': (1.0, 200.0), 'HE_INDEX': (-4.0, -1.0), 'HE_XC': (5e4, 1e8)},
    'SBPLPL':    {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5),
                  'PL_INDEX': (-4.0, -1.0)},
    'SBPLCPL':   {'ALPHA': (-2.5, 1.5), 'EBREAK': (10.0, 5000.0), 'BETA': (-5.0, -1.5),
                  'HE_INDEX': (-4.0, -1.0), 'HE_XC': (5e4, 1e8)},
}

# Nested-parent map for the generic multistart + downstream chain gating.
# A composite is only at its true optimum if its n2logL <= every listed
# parent's (the parent is nested inside it). Order matters: 2-component
# children first, 3-component last, so each child seeds from FINAL parents.
NESTED_PARENTS = [
    ('Band+BB', ['Band']), ('CPL+BB', ['CPL']), ('SBPL+BB', ['SBPL']),
    ('Band+PL', ['Band']), ('Band+CPL', ['Band']),
    ('CPL+PL', ['CPL']), ('CPL+CPL', ['CPL']),
    ('SBPL+PL', ['SBPL']), ('SBPL+CPL', ['SBPL']),
    ('BandxCut', ['Band']), ('SBPLxCut', ['SBPL']),
    ('Band+BB+PL', ['Band+BB', 'Band+PL']),
    ('Band+BB+CPL', ['Band+BB', 'Band+CPL']),
    ('CPL+BB+PL', ['CPL+BB', 'CPL+PL']),
    ('CPL+BB+CPL', ['CPL+BB', 'CPL+CPL']),
    ('SBPL+BB+PL', ['SBPL+BB', 'SBPL+PL']),
    ('SBPL+BB+CPL', ['SBPL+BB', 'SBPL+CPL']),
]


def _fit_is_physical(spec, result, frac=0.001):
    """A fit may WIN model selection only if it is OK, has no key shape
    parameter railed within `frac` of a bound, and (for DSBPL) the low break
    xb < the peak xp. Railed / inverted fits stay in the ECSV (with VALID=False)
    but are excluded from BEST_AIC / BEST_BIC so the declared winner is always
    a physical solution. Burgess+ 2019 pre-publication railing filter + Ravasio
    physical-ordering requirement for the 2SBPL break."""
    if result.get('status') != 'OK':
        return False
    prefix = spec['prefix']
    pmap = spec['pmap']                     # col_suffix -> short param name
    params = result.get('params', {})
    for col, (lo, hi) in PARAM_BOUNDS.get(prefix, {}).items():
        short = pmap.get(col)
        if short is None:
            continue
        d = params.get(short)
        if d is None or not np.isfinite(d['val']):
            return False
        v = d['val']; span = hi - lo
        if (v - lo) < frac * span or (hi - v) < frac * span:
            return False
    if prefix in ('DSBPL', 'DSBPLF'):
        xb = params.get('xb'); xp = params.get('xp')
        if (xb and xp and np.isfinite(xb['val']) and np.isfinite(xp['val'])
                and xb['val'] >= xp['val']):
            return False
    return True


def select_best(per_spec_results, n_data):
    """Apply selection rules across all OK fits.

    - BEST_AIC: lowest AIC (Burnham-Anderson; for non-nested empirical models)
    - BEST_BIC: lowest BIC (cross-check)
    - LRT_BANDBB_BAND, LRT_CPLBB_CPL: nested-pair LRTs (Wilks)
    """
    # OK requires a FINITE likelihood — a fit whose objective read back NaN
    # must not be selectable (Codex ultra audit HIGH #16).
    ok = {sp['name']: (sp, r) for sp, r in per_spec_results
          if r.get('status') == 'OK' and np.isfinite(r.get('neg2logL', np.nan))}
    aic = {n: r['neg2logL'] + 2 * r['n_params'] for n, (_, r) in ok.items()}
    bic = {n: r['neg2logL'] + r['n_params'] * np.log(max(n_data, 1))
           for n, (_, r) in ok.items()}
    # Physical-validity gate: the winner must be a non-railed, physically
    # ordered fit (DSBPL low break xb < peak xp). Railed/inverted fits stay
    # in the ECSV but cannot WIN selection — and when NO fit passes the gate,
    # the block is INCONCLUSIVE. The old fallback silently crowned the raw
    # invalid minimum (Codex ultra audit HIGH #16: bn110721200 block 0 had
    # every candidate invalid yet BEST_AIC_MODEL=SBPL).
    phys = {n: (sp, r) for n, (sp, r) in ok.items() if _fit_is_physical(sp, r)}
    aic_p = {n: aic[n] for n in phys}
    bic_p = {n: bic[n] for n in phys}
    best_aic = min(aic_p, key=aic_p.get) if aic_p else 'INCONCLUSIVE'
    best_bic = min(bic_p, key=bic_p.get) if bic_p else 'INCONCLUSIVE'

    def _lrt(parent, child):
        if parent in ok and child in ok:
            return ok[parent][1]['neg2logL'] - ok[child][1]['neg2logL']
        return float('nan')

    lrt_bbband = _lrt('Band', 'Band+BB')
    lrt_cplbb  = _lrt('CPL',  'CPL+BB')
    lrt_dsbpl_sbpl = _lrt('SBPL', 'DSBPL')

    return {
        'BEST_AIC_MODEL': best_aic,
        'BEST_BIC_MODEL': best_bic,
        'LRT_BANDBB_BAND': lrt_bbband,
        'LRT_CPLBB_CPL':   lrt_cplbb,
        'LRT_DSBPL_SBPL':  lrt_dsbpl_sbpl,
    }


# ============================================================
# Fit a full bin: run all MODEL_SPECS, return flat row + seeds (for T_INT)
# ============================================================
def fit_all_models(plugins, plugin_dets, ref_det, seed_in=None,
                   include_dsbpl=True):
    """Apply effective-area cross-norm, then fit every MODEL_SPECS entry.
    Returns (row_dict, seed_dict_from_this_fit)."""
    from threeML import DataList
    # Keep exactly ONE detector FIXED at unit eff-area as the reference; it must be a
    # NaI, NEVER the binning detector when that is 'lle' (an LLE-driven grid would
    # otherwise free every GBM detector and create a normalization degeneracy). Prefer
    # the passed reference if present, else the first NaI present, else the first
    # plugin. (Codex audit HIGH, 2026-07-17.)
    if ref_det in plugin_dets and str(ref_det).startswith('n'):
        fixed_det = ref_det
    else:
        _nai = [d for d in plugin_dets if str(d).startswith('n')]
        fixed_det = _nai[0] if _nai else (plugin_dets[0] if plugin_dets else ref_det)
    for sl, det in zip(plugins, plugin_dets):
        if det != fixed_det:
            try:
                sl.use_effective_area_correction(*EFFAREA_BOUNDS)
            except Exception:
                pass
    dl = DataList(*plugins)

    n_data = sum(len(np.atleast_1d(getattr(pl, 'observed_counts', [0])))
                 for pl in plugins) or 1
    # FermiLATLike has no observed_counts; approximate its BIC contribution as
    # ~100 data points (LATBright s03m precedent — BIC is a cross-check only).
    n_data += 100 * sum(1 for pl in plugins
                        if type(pl).__name__ == 'FermiLATLike')
    seed_in = seed_in or {}

    per_spec = []
    flat = {}
    seed_out = {}
    for spec in ACTIVE_SPECS:
        if spec['name'] == 'DSBPL' and not include_dsbpl:
            continue
        res = fit_one_model(dl, spec, seed=seed_in)
        res['physical'] = _fit_is_physical(spec, res)
        per_spec.append((spec, res))
        flat.update(model_columns(spec, res, n_data))
        # Capture seeds — but only for the SAME spec key on next call
        seed_out.update(capture_seed(spec, res))

    # BB multi-start. The blackbody has a railing local minimum (kT -> lower
    # bound, K_BB -> 0, LRT ~ 0) that the T_INT-derived seed can fall into —
    # especially when the T_INT BB itself railed, which then poisons EVERY
    # block, since all blocks seed from T_INT. The old narrow LRT-guard only
    # fired when n2logL(superset) > n2logL(parent) (a strictly-worse fit); the
    # railed case has n2logL(superset) ~= n2logL(parent), so it slipped through.
    # Instead, re-fit each +BB model from a grid of hot kT seeds (plus pure
    # DEFAULT_PARAMS) and keep the lowest n2logL. Never worsens a fit; recovers
    # the deep BB minimum (e.g. bn110721200 block kT=30, LRT=40) reliably.
    BB_RESTART_SEEDS = [{},                                  # pure defaults (kT=30)
                        {'bb_kT': 30.0, 'bb_K': 1e-3},       # hot, warm band seed
                        {'bb_kT': 80.0, 'bb_K': 1e-3}]       # hotter
    _KT_LO, _KT_HI = 1.0, 200.0
    for child_name, parent_name in [('Band+BB', 'Band'), ('CPL+BB', 'CPL')]:
        idxs = {s['name']: i for i, (s, _) in enumerate(per_spec)}
        if child_name not in idxs:
            continue
        child_spec, child_res = per_spec[idxs[child_name]]
        parent_res = per_spec[idxs[parent_name]][1] if parent_name in idxs else {}
        # Gate: skip the extra restarts when the BB is already strongly,
        # physically detected (kT not railed AND LRT vs parent >= 9.2). The
        # keep-best rule below still guarantees no regression for cases we do
        # restart. This preserves speed for good fits and only hunts when the
        # original BB railed or is insignificant (the poisoned-seed case).
        kt0 = child_res.get('params', {}).get(
            child_spec['pmap']['KT'], {}).get('val', float('nan'))
        railed = (not np.isfinite(kt0) or kt0 <= _KT_LO*1.02 or kt0 >= _KT_HI*0.98)
        lrt0 = (parent_res.get('neg2logL', np.inf) - child_res.get('neg2logL', np.inf)
                if (child_res.get('status') == 'OK' and parent_res.get('status') == 'OK')
                else -np.inf)
        if (not railed) and np.isfinite(lrt0) and lrt0 >= 9.2:
            continue
        best_res = child_res
        for extra in BB_RESTART_SEEDS:
            s = extra if extra == {} else {**seed_in, **extra}
            alt = fit_one_model(dl, child_spec, seed=s)
            alt['physical'] = _fit_is_physical(child_spec, alt)
            if (alt.get('status') == 'OK' and np.isfinite(alt['neg2logL'])
                    and (best_res.get('status') != 'OK'
                         or not np.isfinite(best_res['neg2logL'])
                         or alt['neg2logL'] < best_res['neg2logL'] - 1e-3)):
                best_res = alt
        if best_res is not child_res:
            print(f'    [BB multistart] {child_name} '
                  f'n2logL {child_res.get("neg2logL", float("nan")):.1f} '
                  f'-> {best_res["neg2logL"]:.1f}')
            per_spec[idxs[child_name]] = (child_spec, best_res)
            flat.update(model_columns(child_spec, best_res, n_data))
            seed_out.update(capture_seed(child_spec, best_res))

    # DSBPL multi-start. DoubleSmoothlyBrokenPowerlaw is a 6-parameter model
    # whose single-shot minuit fit frequently settles in a WORSE local minimum
    # than its own submodel SBPL (LRT_DSBPL_SBPL < 0, impossible at the true
    # optimum) -- the audit found ~84-132 such bins, making the two-break
    # fraction a LOWER LIMIT. Re-fit DSBPL seeded from the converged SBPL (the
    # nesting limit: SBPL's break -> the DSBPL peak xp) plus a grid of
    # physically-ordered low-break (xb < xp) seeds, and keep the lowest n2logL.
    # Keep-best -> never worsens a fit; recovers the genuine two-break optimum.
    if include_dsbpl:
        idxs = {s['name']: i for i, (s, _) in enumerate(per_spec)}
        if 'DSBPL' in idxs:
            dsbpl_spec, dsbpl_res = per_spec[idxs['DSBPL']]
            sp = per_spec[idxs['SBPL']][1].get('params', {}) if 'SBPL' in idxs else {}
            a_s = sp.get('alpha', {}).get('val')
            br_s = sp.get('break_energy', {}).get('val')
            b_s = sp.get('beta', {}).get('val')
            k_s = sp.get('K', {}).get('val')
            DSBPL_RESTART_SEEDS = [{}]                    # pure defaults
            if all(v is not None and np.isfinite(v) for v in (a_s, br_s, b_s, k_s)):
                for frac in (0.2, 0.4, 0.6):             # trial low break BELOW the SBPL break
                    xb_try = float(np.clip(br_s * frac, 10.0, 880.0))
                    if xb_try < br_s:
                        DSBPL_RESTART_SEEDS.append({
                            'dsbpl_alpha1': a_s, 'dsbpl_xb': xb_try,
                            'dsbpl_alpha2': 0.5 * (a_s + b_s), 'dsbpl_xp': br_s,
                            'dsbpl_beta': b_s, 'dsbpl_K': k_s})
            best_d = dsbpl_res
            for extra in DSBPL_RESTART_SEEDS:
                s = extra if extra == {} else {**seed_in, **extra}
                alt = fit_one_model(dl, dsbpl_spec, seed=s)
                alt['physical'] = _fit_is_physical(dsbpl_spec, alt)
                if (alt.get('status') == 'OK' and np.isfinite(alt['neg2logL'])
                        and (best_d.get('status') != 'OK'
                             or not np.isfinite(best_d['neg2logL'])
                             or alt['neg2logL'] < best_d['neg2logL'] - 1e-3)):
                    best_d = alt
            if best_d is not dsbpl_res:
                print(f'    [DSBPL multistart] n2logL '
                      f'{dsbpl_res.get("neg2logL", float("nan")):.1f} -> {best_d["neg2logL"]:.1f}')
                per_spec[idxs['DSBPL']] = (dsbpl_spec, best_d)
                flat.update(model_columns(dsbpl_spec, best_d, n_data))
                seed_out.update(capture_seed(dsbpl_spec, best_d))

    # Generic NESTED-PARENT multistart (Codex ultra audit CRITICAL #4): every
    # composite whose n2logL is WORSE than a nested parent's is at a local
    # minimum (impossible at the true optimum — the parent solution + a null
    # extra component reproduces the parent's likelihood). Re-fit such children
    # seeded from each FITTED parent (capture_seed gives exactly the child's
    # shared seed keys), plus hot-kT variants for +BB children. Keep-best;
    # 2-component entries run before 3-component so children seed from FINAL
    # parents. The audit measured 8-12/19-25 regressed fits per 3-component
    # model with N2LL excesses up to ~7000 before this.
    idxs = {s['name']: i for i, (s, _) in enumerate(per_spec)}
    for child_name, parent_names in NESTED_PARENTS:
        if child_name not in idxs:
            continue
        child_spec, child_res = per_spec[idxs[child_name]]
        parents = [(per_spec[idxs[p]][0], per_spec[idxs[p]][1])
                   for p in parent_names if p in idxs]
        p_ok = [(ps, pr) for ps, pr in parents
                if pr.get('status') == 'OK' and np.isfinite(pr.get('neg2logL', np.nan))]
        if not p_ok:
            continue
        parent_best = min(pr['neg2logL'] for _, pr in p_ok)
        c_ok = (child_res.get('status') == 'OK'
                and np.isfinite(child_res.get('neg2logL', np.nan)))
        if c_ok and child_res['neg2logL'] <= parent_best + 1e-3:
            continue                     # already at/below every parent
        best = child_res
        for pspec, pres in p_ok:
            base = {**seed_in, **capture_seed(pspec, pres)}
            trials = [base]
            if 'KT' in child_spec.get('pmap', {}):
                trials += [{**base, 'bb_kT': 30.0, 'bb_K': 1e-3},
                           {**base, 'bb_kT': 80.0, 'bb_K': 1e-3}]
            for s in trials:
                alt = fit_one_model(dl, child_spec, seed=s)
                alt['physical'] = _fit_is_physical(child_spec, alt)
                if (alt.get('status') == 'OK' and np.isfinite(alt['neg2logL'])
                        and (best.get('status') != 'OK'
                             or not np.isfinite(best.get('neg2logL', np.nan))
                             or alt['neg2logL'] < best['neg2logL'] - 1e-3)):
                    best = alt
        if best is not child_res:
            print(f'    [nested multistart] {child_name} n2logL '
                  f'{child_res.get("neg2logL", float("nan")):.1f} '
                  f'-> {best["neg2logL"]:.1f} (parent best {parent_best:.1f})')
            per_spec[idxs[child_name]] = (child_spec, best)
            flat.update(model_columns(child_spec, best, n_data))
            seed_out.update(capture_seed(child_spec, best))

    flat.update(select_best(per_spec, n_data))
    flat['_n_data'] = n_data
    return flat, seed_out


def _print_row(label, flat):
    band_a  = flat.get('BAND_ALPHA', float('nan'))
    band_ep = flat.get('BAND_EP',    float('nan'))
    cpl_idx = flat.get('CPL_INDEX',  float('nan'))
    cpl_xc  = flat.get('CPL_XC',     float('nan'))
    bb_kt   = flat.get('BANDBB_KT',  float('nan'))
    best_a  = flat.get('BEST_AIC_MODEL', '?')
    lrt_bb  = flat.get('LRT_BANDBB_BAND', float('nan'))
    print(f'  {label}: '
          f'Band α={band_a:.2f} Ep={band_ep:.0f}  '
          f'CPL i={cpl_idx:.2f} Ec={cpl_xc:.0f}  '
          f'BB kT={bb_kt:.1f}  LRT(BB)={lrt_bb:.1f}  → {best_a}')


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--trigger', required=True)
    p.add_argument('--include-bgo', action='store_true',
                   help='Include BGO detectors in joint fit')
    p.add_argument('--models', choices=['default', 'shape', 'highe', 'threecomp'],
                   default='default',
                   help='model set: default = the frozen benchmark 6; shape = '
                        '+SBPLfree/DSBPLfree (free smoothness, peak-shape census); '
                        'highe = shape + high-E second components '
                        '(Band+PL, Band+CPL, CPL+PL, CPL+CPL, BandR+CPL, '
                        'BandxCut, SBPLxCut, Band+BB+PL — LATBright s03m port); '
                        'threecomp = Band/Band+BB/Band+PL/Band+BB+PL only '
                        '(the Guiriec-2015 3-component chain test)')
    p.add_argument('--skip-dsbpl', action='store_true',
                   help='Skip DSBPL/2SBPL (slower, often degenerate for sparse bins)')
    p.add_argument('--include-lat', action='store_true',
                   help='add a per-block LAT >100 MeV FermiLATLike plugin '
                        '(needs data/<trigger>/LAT/ FT1+FT2, grb_pipeline, and '
                        'the burst RA/DEC in results/grb_sample.ecsv; the '
                        'gtburst chain runs per block into data/<t>/LAT/blocks/)')
    p.add_argument('--skip-lle', action='store_true',
                   help='Skip LLE detector even if data files present')
    p.add_argument('--no-log', action='store_true',
                   help='Disable per-burst log file (default: log to '
                        'results/per_burst/<trigger>/logs/<script>_<UTC>.log)')
    p.add_argument('--blocks-file', required=True,
                   help='Path to the Bayesian-block ECSV (REQUIRED; e.g. '
                        'results/clean_blocks/bb_blocks_spectral_<trigger>.ecsv). '
                        'No silent default — must be passed explicitly.')
    p.add_argument('--out-dir', default=None,
                   help='Override output directory (default: '
                        'results/per_burst/<trigger>). Lets a reproduction run '
                        'write to a separate tree without clobbering production.')
    p.add_argument('--bkg-file', required=True,
                   help='Background-intervals ECSV (REQUIRED; the authoritative '
                        'human-reviewed or clean catalogue). No silent default — '
                        'prevents accidentally fitting the automatic backgrounds.')
    args = p.parse_args()

    # Runtime model set (opt-in; default stays the frozen benchmark 6)
    global ACTIVE_SPECS
    ACTIVE_SPECS = list(MODEL_SPECS)
    if args.models in ('shape', 'highe'):
        ACTIVE_SPECS += SHAPE_MODEL_SPECS
    if args.models == 'highe':
        ACTIVE_SPECS += HIGHE_MODEL_SPECS
    if args.models == 'threecomp':
        ACTIVE_SPECS = list(THREECOMP_MODEL_SPECS)
    if args.models != 'default':
        print(f"model set '{args.models}': {[s['name'] for s in ACTIVE_SPECS]}")

    trigger = args.trigger
    out_dir = args.out_dir or os.path.join(PER_BURST_DIR, trigger)
    os.makedirs(out_dir, exist_ok=True)

    # ----- LAT >100 MeV context (opt-in; joint NaI+BGO+LLE+LAT fits) -----
    lat_ctx = None
    if args.include_lat:
        global SRC_RA, SRC_DEC
        ft1, ft2lat, rsp_standin = find_lat_files(trigger)
        ra = dec = met = None
        try:
            from astropy.table import Table as _T
            _gs = _T.read(os.path.join(RESULTS_DIR, 'grb_sample.ecsv'),
                          format='ascii.ecsv')
            _row = _gs[[str(x['TRIGGER_NAME']).strip() == trigger for x in _gs]]
            if len(_row):
                ra, dec = float(_row[0]['RA']), float(_row[0]['DEC'])
        except Exception as exc:
            print(f'  --include-lat: could not read RA/DEC ({exc})')
        try:
            from astropy.io import fits as _fits
            _tte = sorted(glob.glob(os.path.join(DATA_DIR, trigger,
                                                 'glg_tte_*_v*.fit*')))
            if _tte:
                with _fits.open(_tte[0]) as _h:
                    met = float(_h[0].header['TRIGTIME'])
        except Exception as exc:
            print(f'  --include-lat: could not read TRIGTIME ({exc})')
        if ft1 and ft2lat and rsp_standin and None not in (ra, dec, met):
            try:                              # grb_pipeline (GRB_Handbook)
                from grb_pipeline.lat_pipeline import to_threeml as _lat3ml
            except ImportError:
                sys.path.insert(0, os.path.expanduser(
                    '~/Desktop/Projects/GRB_Handbook_Project'))
                from grb_pipeline.lat_pipeline import to_threeml as _lat3ml
            lat_ctx = {'mod': _lat3ml, 'ft1': ft1, 'ft2': ft2lat,
                       'rsp': rsp_standin, 'ra': ra, 'dec': dec, 'met': met,
                       'workroot': os.path.join(DATA_DIR, trigger, 'LAT',
                                                'blocks')}
            SRC_RA, SRC_DEC = ra, dec        # LAT likelihood needs the true position
            print(f'  LAT>100MeV ENABLED: ft1={os.path.basename(ft1)} '
                  f'ra={ra:.3f} dec={dec:.3f}')
        else:
            print(f'  --include-lat requested but inputs incomplete '
                  f'(ft1={bool(ft1)} ft2={bool(ft2lat)} rsp={bool(rsp_standin)} '
                  f'radec={ra is not None} met={met is not None}) — LAT disabled')

    sys.path.insert(0, os.path.dirname(__file__))
    from _burst_logger import BurstLogger
    if args.no_log:
        return _run(args, trigger, out_dir, lat_ctx)
    with BurstLogger(trigger=trigger, script='10_spectral_fit_burst',
                     base=os.path.dirname(out_dir)):
        return _run(args, trigger, out_dir, lat_ctx)


def _run(args, trigger, out_dir, lat_ctx=None):

    bkg_tab = Table.read(args.bkg_file, format='ascii.ecsv')
    bkg_tab = bkg_tab[bkg_tab['TRIGGER_NAME'] == trigger]
    if len(bkg_tab) == 0:
        sys.exit(f'No bkg intervals for {trigger}')
    approved = {str(r['DETECTOR']).strip():
                ((float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])),
                 (float(r['BKG_POS_START']), float(r['BKG_POS_STOP'])))
                for r in bkg_tab}
    nai_dets = [d for d in approved if d.startswith('n')]
    bgo_dets = [d for d in approved if d.startswith('b')]
    fit_dets = nai_dets + (bgo_dets if args.include_bgo else [])

    # LLE — auto-add if data is present (HAS_LAT bursts). LLE uses its own
    # polynomial bkg fit over these time windows. Preference order:
    #   1. an APPROVED LLE bkg window (a reviewed 'lle' row in the bkg ECSV,
    #      written by the Stage-1 GUI LLE review) — LLE particle backgrounds can
    #      differ from NaI, so a human-confirmed window is authoritative;
    #   2. else inherit the brightest-NaI windows (same quiescent epochs);
    #   3. else a synthetic wide window [-50,-10] / [300,400].
    lle_files = find_lle_files(trigger)
    if lle_files[0] is not None and not args.skip_lle:
        if 'lle' in approved:
            print(f'{trigger}: LLE data present — using APPROVED LLE bkg window '
                  f'{approved["lle"]}')
        else:
            if nai_dets and nai_dets[0] in approved:
                approved['lle'] = approved[nai_dets[0]]
                print(f'{trigger}: LLE data present — inheriting brightest-NaI '
                      f'bkg window (no reviewed LLE row)')
            else:
                approved['lle'] = ((-50.0, -10.0), (300.0, 400.0))
                print(f'{trigger}: LLE data present — synthetic wide bkg window')
        if 'lle' not in fit_dets:
            fit_dets.append('lle')

    print(f'{trigger}: approved dets = {list(approved)}; fit dets = {fit_dets}')

    blocks_file = args.blocks_file
    canonical_det, bin_starts, bin_stops = get_canonical_bins(
        trigger,
        blocks_file,
        os.path.join(RESULTS_DIR, 'single_pulse_grbs.ecsv'),
        approved.keys())
    n_bins = len(bin_starts)
    # Effective-area REFERENCE (fixed at 1) must be a NaI — NOT the binning detector,
    # which is 'lle' on an LLE-driven (coarse) grid. (Codex audit HIGH.)
    _nai_fit = [d for d in fit_dets if str(d).startswith('n')]
    reference_det = (canonical_det if str(canonical_det).startswith('n')
                     else (_nai_fit[0] if _nai_fit else canonical_det))
    grid_type = 'lle_coarse' if canonical_det == 'lle' else 'gbm_fine'
    print(f'Canonical bins from det {canonical_det} ({grid_type}): {n_bins} blocks '
          f'spanning [{bin_starts[0]:.2f}, {bin_stops[-1]:.2f}] s; '
          f'eff-area ref = {reference_det}')

    print(f'\nBuilding SpectrumLike per detector...')
    sl_by_det = {}
    for det in fit_dets:
        pre, post = approved[det]
        sl = build_spectrumlike_per_block(trigger, det, pre, post,
                                          bin_starts, bin_stops)
        if sl is None:
            print(f'  {det}: skipped (TTE/RSP missing)')
            continue
        n_ok = sum(1 for s in sl if s is not None)
        if n_ok == 0:                       # all bins failed -> NOT present in the fit
            print(f'  {det}: skipped (0/{n_bins} SpectrumLike usable — bkg/plugin failed)')
            continue
        sl_by_det[det] = sl
        print(f'  {det}: {n_ok}/{n_bins} SpectrumLike built')
    # An LLE-driven grid with no usable LLE plugin is meaningless — abort loudly rather
    # than silently fitting GBM-only on LLE-defined intervals. (Codex audit HIGH.)
    if canonical_det == 'lle' and 'lle' not in sl_by_det:
        raise RuntimeError(f'{trigger}: LLE-driven grid but no usable LLE plugin — abort')

    rows = []
    include_dsbpl = not args.skip_dsbpl

    # ----- TIME-INTEGRATED FIT FIRST -----
    print(f'\n--- TIME-INTEGRATED FIT (T_INT) ---')
    tint_path_reviewed = os.path.join(RESULTS_DIR, 'time_integrated_windows_reviewed.ecsv')
    tint_path_auto = os.path.join(RESULTS_DIR, 'time_integrated_windows.ecsv')
    tint_path = tint_path_reviewed if os.path.exists(tint_path_reviewed) else tint_path_auto
    t_int_start = t_int_stop = None
    if os.path.exists(tint_path):
        tint_tab = Table.read(tint_path, format='ascii.ecsv')
        m = tint_tab['TRIGGER_NAME'] == trigger
        if m.any():
            r = tint_tab[m][0]
            t_int_start = float(r['T_INT_START'])
            t_int_stop = float(r['T_INT_STOP'])
    if t_int_start is None:
        t_int_start = float(min(bin_starts))
        t_int_stop = float(max(bin_stops))
        print(f'  No T_INT ECSV found, fallback to BB block union: '
              f'[{t_int_start:.2f}, {t_int_stop:.2f}] s')
    else:
        print(f'  T_INT from {os.path.basename(tint_path)}: '
              f'[{t_int_start:.2f}, {t_int_stop:.2f}] s')

    ti_plugins = []; ti_plugin_dets = []
    for det in fit_dets:
        pre, post = approved[det]
        sl = build_spectrumlike_per_block(trigger, det, pre, post,
                                          [t_int_start], [t_int_stop])
        if sl and sl[0] is not None:
            ti_plugins.append(sl[0]); ti_plugin_dets.append(det)
    print(f'  T_INT plugins built: {len(ti_plugins)} detectors')

    seed_for_blocks = {}
    if ti_plugins:
        ti_flat, ti_seed = fit_all_models(
            ti_plugins, ti_plugin_dets, reference_det,
            seed_in=None, include_dsbpl=include_dsbpl)
        ti_flat = {'BLOCK': -1, 'T_START': t_int_start, 'T_STOP': t_int_stop,
                   'T_MID': 0.5 * (t_int_start + t_int_stop),
                   'N_DETS': len(ti_plugins),
                   'PLUGIN_DETS': ','.join(ti_plugin_dets), **ti_flat}
        rows.append(ti_flat)
        _print_row(f'T_INT [{t_int_start:6.2f}, {t_int_stop:6.2f}]', ti_flat)
        seed_for_blocks = ti_seed
    else:
        print('  No T_INT plugins; skipping time-integrated fit.')

    # ----- TIME-RESOLVED PER-BLOCK FITS (seeded from T_INT) -----
    print(f'\n--- TIME-RESOLVED PER-BLOCK FITS ---')
    for k in range(n_bins):
        t1, t2 = float(bin_starts[k]), float(bin_stops[k])
        plugins = []; plugin_dets = []
        for det, sl_list in sl_by_det.items():
            if sl_list[k] is not None:
                plugins.append(sl_list[k]); plugin_dets.append(det)
        if not plugins:
            print(f'  block {k} [{t1:.2f}, {t2:.2f}]: no plugins, skip')
            continue
        if lat_ctx is not None:
            # per-block LAT >100 MeV plugin (gtburst chain, cached per block)
            try:
                # workdir addressed by the EXACT interval, not the block index:
                # fine and coarse grids share the per-burst workroot, and
                # index-keyed dirs made coarse fits reuse fine-grid LAT
                # products (Codex ultra audit CRITICAL #2). to_threeml.py
                # additionally verifies cached TSTART/TSTOP before reuse.
                _tag = f'block_{t1:+.3f}_{t2:+.3f}'.replace('.', 'p')
                prod = lat_ctx['mod'].prepare_lat_block(
                    lat_ctx['ft1'], lat_ctx['ft2'], lat_ctx['rsp'],
                    lat_ctx['met'], lat_ctx['ra'], lat_ctx['dec'],
                    t1, t2, os.path.join(lat_ctx['workroot'], _tag))
                if prod['status'] == 'OK':
                    lat_pl = lat_ctx['mod'].lat_plugin_for_block(
                        prod, t1, t2, trigger)
                    plugins.append(lat_pl); plugin_dets.append('LAT')
                    print(f'  block {k}: LAT plugin ON '
                          f'({prod["n_events"]} ev >100 MeV)')
                else:
                    print(f'  block {k}: LAT skipped ({prod["status"]})')
            except Exception as exc:
                print(f'  block {k}: LAT plugin failed '
                      f'({type(exc).__name__}: {str(exc)[:90]}) — GBM/LLE only')
        # An LLE-DRIVEN block without a usable LLE plugin must not be fit
        # GBM-only on LLE-defined intervals (Codex ultra audit HIGH #18).
        if grid_type == 'lle_coarse' and 'lle' not in plugin_dets:
            print(f'  block {k} [{t1:.2f}, {t2:.2f}]: SKIPPED — LLE-driven grid '
                  f'but no usable LLE plugin (dets: {plugin_dets})')
            continue
        flat, _ = fit_all_models(
            plugins, plugin_dets, reference_det,
            seed_in=seed_for_blocks, include_dsbpl=include_dsbpl)
        flat = {'BLOCK': k, 'T_START': t1, 'T_STOP': t2,
                'T_MID': 0.5 * (t1 + t2), 'N_DETS': len(plugins),
                'PLUGIN_DETS': ','.join(plugin_dets), **flat}
        rows.append(flat)
        _print_row(f'blk {k} [{t1:6.2f}, {t2:6.2f}]', flat)

    # ----- Save -----
    if rows:
        # Union of keys across rows (DSBPL skip can produce ragged sets)
        all_keys = []
        seen = set()
        for r in rows:
            for k in r.keys():
                if k.startswith('_'): continue
                if k not in seen:
                    seen.add(k); all_keys.append(k)
        out_table = Table(rows=[[r.get(k, float('nan')) for k in all_keys]
                                 for r in rows], names=all_keys)
        out_path = os.path.join(out_dir, 'spectral_fits.ecsv')
        out_table.write(out_path, format='ascii.ecsv', overwrite=True)
        print(f'\nSaved: {out_path}  ({len(rows)} rows × {len(all_keys)} cols)')

        meta = {
            'trigger': trigger,
            'canonical_det': canonical_det,       # detector that DEFINED the time bins
            'reference_det': reference_det,        # NaI FIXED as the eff-area reference
            'grid_type': grid_type,                # 'lle_coarse' | 'gbm_fine'
            'blocks_file': os.path.abspath(blocks_file),
            'fit_dets': list(sl_by_det.keys()),
            'n_blocks': n_bins,
            'NAI_RANGES': list(NAI_RANGES),
            'BGO_RANGES': list(BGO_RANGES),
            'models': [s['name'] for s in ACTIVE_SPECS
                       if include_dsbpl or s['name'] != 'DSBPL'],
            'bin_starts': list(map(float, bin_starts)),
            'bin_stops':  list(map(float, bin_stops)),
        }
        json.dump(meta, open(os.path.join(out_dir, 'spectral_fits.json'), 'w'),
                  indent=2, default=float)

        _plot_evolution(out_table, trigger, out_dir)
        _plot_ep_kt(out_table, trigger, out_dir)
    else:
        print('No rows produced — fits failed for all blocks.')


def _plot_evolution(t, trigger, out_dir):
    """Per-block evolution using Band+BB params (Burgess+ 2014 style)."""
    fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    t_mid = t['T_MID']
    ok_bb = t['BANDBB_STATUS'] == 'OK'
    axes[0].errorbar(t_mid[ok_bb], t['BANDBB_EP'][ok_bb],
                     yerr=t['BANDBB_EP_ERR'][ok_bb], fmt='o', label='Band+BB Ep')
    axes[0].set_ylabel('Ep [keV]'); axes[0].set_yscale('log')
    axes[0].grid(alpha=0.3); axes[0].legend()
    axes[1].errorbar(t_mid[ok_bb], t['BANDBB_KT'][ok_bb],
                     yerr=t['BANDBB_KT_ERR'][ok_bb], fmt='o', color='red', label='kT')
    axes[1].set_ylabel('kT [keV]'); axes[1].set_yscale('log')
    axes[1].grid(alpha=0.3); axes[1].legend()
    axes[2].plot(t_mid[ok_bb], t['BANDBB_ALPHA'][ok_bb], 'o', color='purple')
    axes[2].axhline(-1, ls='--', color='0.5', label='line of death')
    axes[2].set_ylabel(r'$\alpha$ (Band)'); axes[2].grid(alpha=0.3); axes[2].legend()
    axes[-1].set_xlabel('Time since trigger (s)')
    fig.suptitle(f'{trigger} — spectral evolution (Band+BB)')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'spectral_evolution.png'),
                dpi=140, bbox_inches='tight')
    plt.close(fig)


def _plot_ep_kt(t, trigger, out_dir):
    fig, ax = plt.subplots(figsize=(6, 5))
    ok = (t['BANDBB_STATUS'] == 'OK') & np.isfinite(t['BANDBB_EP']) & np.isfinite(t['BANDBB_KT'])
    if ok.sum() < 2:
        plt.close(fig); return
    ep = t['BANDBB_EP'][ok]; kt = t['BANDBB_KT'][ok]
    ax.errorbar(kt, ep,
                xerr=t['BANDBB_KT_ERR'][ok],
                yerr=t['BANDBB_EP_ERR'][ok], fmt='o', color='black')
    if ok.sum() >= 3:
        log_x = np.log10(kt); log_y = np.log10(ep)
        finite = np.isfinite(log_x) & np.isfinite(log_y)
        if finite.sum() >= 3:
            slope, intercept = np.polyfit(log_x[finite], log_y[finite], 1)
            from scipy.stats import spearmanr
            rho, pval = spearmanr(kt[finite], ep[finite])
            xx = np.logspace(np.log10(kt[finite].min()),
                             np.log10(kt[finite].max()), 20)
            ax.plot(xx, 10**(intercept + slope * np.log10(xx)),
                    'b--', label=f'α = {slope:.2f}\nρ = {rho:.2f}, p = {pval:.2g}')
            ax.legend()
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('kT [keV]'); ax.set_ylabel('Ep [keV]')
    ax.set_title(f'{trigger} — Ep vs kT (Burgess+ 2014 style)')
    ax.grid(alpha=0.3, which='both')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'ep_kt_correlation.png'),
                dpi=140, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main()
