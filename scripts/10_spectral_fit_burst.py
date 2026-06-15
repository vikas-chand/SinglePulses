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
    m = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_tte_{det}_*.fit.gz'))
    return m[0] if m else None

def find_rsp(trigger, det):
    m = glob.glob(os.path.join(DATA_DIR, trigger, f'glg_cspec_{det}_*.rsp*'))
    return m[0] if m else None

def find_lle_files(trigger):
    """Return (lle_event_file, ft2_file, rsp_file) tuple or (None, None, None)
    if LLE data not present for this burst.
    Fermi LAT-triggered downloads name pointing as `gll_pt_*.fit`;
    slewing data uses `gll_ft2_*.fit`. Both are valid FT2 inputs."""
    base = os.path.join(DATA_DIR, trigger)
    lle = sorted(glob.glob(os.path.join(base, 'gll_lle_*.fit*')))
    ft2 = sorted(glob.glob(os.path.join(base, 'gll_pt_*.fit*'))
               + glob.glob(os.path.join(base, 'gll_ft2_*.fit*')))
    rsp = sorted(glob.glob(os.path.join(base, 'gll_lle_*.rsp*'))
               + glob.glob(os.path.join(base, 'gll_cspec_*.rsp*')))
    if lle and ft2 and rsp:
        return lle[-1], ft2[-1], rsp[-1]
    return None, None, None


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
            out = os.path.join(out_dir, f'_single_{base}.rsp')
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


# ============================================================
# Generic fit driver
# ============================================================
def fit_one_model(data_list, spec, seed=None):
    """Fit a single MODEL_SPECS entry. Returns dict with status, params, neg2logL."""
    from threeML import Model, PointSource, JointLikelihood
    seed = seed or {}
    try:
        composite = spec['build'](seed)
        ps = PointSource('grb', 0.0, 0.0, spectral_shape=composite)
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

        return {
            'status': 'OK',
            'neg2logL': n2ll,
            'n_params': spec['n_params'],
            'params': params,
            'minos_ok': (minos_table is not None),
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
}


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
    if prefix == 'DSBPL':
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
    ok = {sp['name']: (sp, r) for sp, r in per_spec_results
          if r.get('status') == 'OK'}
    aic = {n: r['neg2logL'] + 2 * r['n_params'] for n, (_, r) in ok.items()}
    bic = {n: r['neg2logL'] + r['n_params'] * np.log(max(n_data, 1))
           for n, (_, r) in ok.items()}
    # Physical-validity gate: the winner must be a non-railed, physically
    # ordered fit (DSBPL low break xb < peak xp). Railed/inverted fits stay
    # in the ECSV but cannot WIN selection.
    phys = {n: (sp, r) for n, (sp, r) in ok.items() if _fit_is_physical(sp, r)}
    aic_p = {n: aic[n] for n in phys}
    bic_p = {n: bic[n] for n in phys}
    best_aic = (min(aic_p, key=aic_p.get) if aic_p
                else (min(aic, key=aic.get) if aic else 'INCONCLUSIVE'))
    best_bic = (min(bic_p, key=bic_p.get) if bic_p
                else (min(bic, key=bic.get) if bic else 'INCONCLUSIVE'))

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
def fit_all_models(plugins, plugin_dets, canonical_det, seed_in=None,
                   include_dsbpl=True):
    """Apply effective-area cross-norm, then fit every MODEL_SPECS entry.
    Returns (row_dict, seed_dict_from_this_fit)."""
    from threeML import DataList
    # Cross-norm — non-reference detectors only
    for sl, det in zip(plugins, plugin_dets):
        if det != canonical_det:
            try:
                sl.use_effective_area_correction(*EFFAREA_BOUNDS)
            except Exception:
                pass
    dl = DataList(*plugins)

    n_data = sum(len(np.atleast_1d(getattr(pl, 'observed_counts', [0])))
                 for pl in plugins) or 1
    seed_in = seed_in or {}

    per_spec = []
    flat = {}
    seed_out = {}
    for spec in MODEL_SPECS:
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
    p.add_argument('--skip-dsbpl', action='store_true',
                   help='Skip DSBPL/2SBPL (slower, often degenerate for sparse bins)')
    p.add_argument('--skip-lle', action='store_true',
                   help='Skip LLE detector even if data files present')
    p.add_argument('--no-log', action='store_true',
                   help='Disable per-burst log file (default: log to '
                        'results/per_burst/<trigger>/logs/<script>_<UTC>.log)')
    p.add_argument('--blocks-file', default=None,
                   help='Override path to the Bayesian-block ECSV (default: '
                        'results/bb_blocks_spectral_<trigger>.ecsv). Used by the '
                        'Burgess reproduction to fit alternative time-binnings.')
    p.add_argument('--out-dir', default=None,
                   help='Override output directory (default: '
                        'results/per_burst/<trigger>). Lets a reproduction run '
                        'write to a separate tree without clobbering production.')
    p.add_argument('--bkg-file', default=None,
                   help='Override background-intervals ECSV (default: '
                        'results/background_intervals_prototype.ecsv).')
    args = p.parse_args()

    trigger = args.trigger
    out_dir = args.out_dir or os.path.join(PER_BURST_DIR, trigger)
    os.makedirs(out_dir, exist_ok=True)

    sys.path.insert(0, os.path.dirname(__file__))
    from _burst_logger import BurstLogger
    if args.no_log:
        return _run(args, trigger, out_dir)
    with BurstLogger(trigger=trigger, script='10_spectral_fit_burst',
                     base=os.path.dirname(out_dir)):
        return _run(args, trigger, out_dir)


def _run(args, trigger, out_dir):

    bkg_tab = Table.read(args.bkg_file or os.path.join(RESULTS_DIR,
                         'background_intervals_prototype.ecsv'),
                         format='ascii.ecsv')
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

    # LLE — auto-add if data is present (HAS_LAT bursts).
    # LLE plugin uses its own polynomial bkg fit; we provide synthetic
    # bkg windows wide of the burst (re-using brightest-NaI's windows
    # if available, else [-50,-10] / [t_stop+10, t_stop+50]).
    lle_files = find_lle_files(trigger)
    if lle_files[0] is not None and not args.skip_lle:
        # Use brightest-NaI bkg windows as LLE bkg windows
        if nai_dets and nai_dets[0] in approved:
            lle_pre, lle_post = approved[nai_dets[0]]
        else:
            lle_pre, lle_post = (-50.0, -10.0), (300.0, 400.0)
        approved['lle'] = (lle_pre, lle_post)
        fit_dets.append('lle')
        print(f'{trigger}: LLE data present — added to joint fit')

    print(f'{trigger}: approved dets = {list(approved)}; fit dets = {fit_dets}')

    blocks_file = args.blocks_file or os.path.join(
        RESULTS_DIR, f'bb_blocks_spectral_{trigger}.ecsv')
    canonical_det, bin_starts, bin_stops = get_canonical_bins(
        trigger,
        blocks_file,
        os.path.join(RESULTS_DIR, 'single_pulse_grbs.ecsv'),
        approved.keys())
    n_bins = len(bin_starts)
    print(f'Canonical bins from det {canonical_det}: {n_bins} blocks '
          f'spanning [{bin_starts[0]:.2f}, {bin_stops[-1]:.2f}] s')

    print(f'\nBuilding SpectrumLike per detector...')
    sl_by_det = {}
    for det in fit_dets:
        pre, post = approved[det]
        sl = build_spectrumlike_per_block(trigger, det, pre, post,
                                          bin_starts, bin_stops)
        if sl is None:
            print(f'  {det}: skipped (TTE/RSP missing)')
            continue
        sl_by_det[det] = sl
        n_ok = sum(1 for s in sl if s is not None)
        print(f'  {det}: {n_ok}/{n_bins} SpectrumLike built')

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
            ti_plugins, ti_plugin_dets, canonical_det,
            seed_in=None, include_dsbpl=include_dsbpl)
        ti_flat = {'BLOCK': -1, 'T_START': t_int_start, 'T_STOP': t_int_stop,
                   'T_MID': 0.5 * (t_int_start + t_int_stop),
                   'N_DETS': len(ti_plugins), **ti_flat}
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
        flat, _ = fit_all_models(
            plugins, plugin_dets, canonical_det,
            seed_in=seed_for_blocks, include_dsbpl=include_dsbpl)
        flat = {'BLOCK': k, 'T_START': t1, 'T_STOP': t2,
                'T_MID': 0.5 * (t1 + t2), 'N_DETS': len(plugins), **flat}
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
            'canonical_det': canonical_det,
            'fit_dets': list(sl_by_det.keys()),
            'n_blocks': n_bins,
            'NAI_RANGES': list(NAI_RANGES),
            'BGO_RANGES': list(BGO_RANGES),
            'models': [s['name'] for s in MODEL_SPECS
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
