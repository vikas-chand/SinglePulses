#!/usr/bin/env python
"""
Phase 4.1: Band + Blackbody spectral fitting for time-resolved GRB spectra.

For each single-pulse GRB with Bayesian-blocks PHA files:
1. Load Type II PHA for all available detectors (multiple NaI + BGO)
2. Fit Band+BB model (6 params) and Band-only model (4 params)
   using joint multi-detector fits (DataList with multiple OGIPLike)
3. Seed each bin's starting parameters from the previous bin's best-fit
   (each GRB is treated independently)
4. Compute AIC/BIC for model comparison
5. Save results table with all parameters, errors, and fit statistics

Multi-detector approach follows Burgess et al. (2014): jointly fitting
2-3 NaI detectors + 1 BGO detector better constrains beta and the
Band/BB decomposition.

Background: handled automatically by OGIPLike via the _bak.pha files
produced in Phase 3 (profile-Gaussian likelihood: Poisson source + Gaussian bkg).
Background intervals were selected from the GBM catalog (pre/post-burst windows).

Uses 3ML OGIPLike for data loading and JointLikelihood for fitting.
"""

import os
import sys
import warnings
import numpy as np
from astropy.io import fits
from astropy.table import Table

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')

from threeML import OGIPLike, Model, PointSource, DataList, JointLikelihood
from astromodels import Band, Blackbody

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
PHA_DIR = os.path.join(BASE_DIR, 'data', 'pha')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')

CHECKPOINT_FILE = os.path.join(RESULTS_DIR, '.spectral_fit_checkpoint.txt')
OUTPUT_FILE = os.path.join(RESULTS_DIR, 'spectral_fit_results.ecsv')

# Energy ranges
NAI_ENERGY_RANGE = '8.1-900'
BGO_ENERGY_RANGE = '300-40000'

# Default starting values (used for the first bin of each GRB)
DEFAULT_BAND_BB = {
    'K_1': 1.0,        # Band norm
    'alpha_1': -0.5,   # low-energy index
    'xp_1': 300.0,     # Ep (keV)
    'beta_1': -2.5,    # high-energy index
    'K_2': 1e-4,       # BB norm
    'kT_2': 30.0,      # BB temperature (keV)
}

DEFAULT_BAND = {
    'K': 1.0,
    'alpha': -0.5,
    'xp': 300.0,
    'beta': -2.5,
}


def read_pha_metadata(pha_path):
    """Read TSTART, TELAPSE, SPEC_NUM from Type II PHA file."""
    with fits.open(pha_path) as hdul:
        spec = hdul['SPECTRUM'].data
        tstart = spec['TSTART'].astype(float)
        telapse = spec['TELAPSE'].astype(float)
        spec_num = spec['SPEC_NUM'].astype(int)
    return spec_num, tstart, telapse


def compute_aic_bic(neg_loglike, n_params, n_data):
    """Compute AIC and BIC from negative log-likelihood."""
    aic = 2 * neg_loglike + 2 * n_params
    bic = 2 * neg_loglike + n_params * np.log(n_data)
    return aic, bic


def extract_fit_params(best_df, model_type='band_bb'):
    """Extract parameter values and errors from 3ML fit DataFrame.

    Parameters
    ----------
    best_df : DataFrame from jl.fit() with columns: value, negative_error,
              positive_error, error, unit
    model_type : 'band_bb' or 'band'

    Returns
    -------
    params : dict with output column names -> values
    raw_vals : dict with short parameter names -> best-fit values (for seeding next bin)
    """
    params = {}
    raw_vals = {}

    for idx in best_df.index:
        short = idx.split('.')[-1]  # e.g. 'K_1', 'alpha_1', 'kT_2', etc.
        val = best_df.loc[idx, 'value']
        raw_vals[short] = val

        if model_type == 'band_bb':
            if short == 'K_1':
                params['K_BAND'] = val
            elif short == 'alpha_1':
                params['ALPHA'] = val
                params['ALPHA_ERR'] = best_df.loc[idx, 'error']
            elif short == 'xp_1':
                params['EP'] = val
                params['EP_NEG_ERR'] = best_df.loc[idx, 'negative_error']
                params['EP_POS_ERR'] = best_df.loc[idx, 'positive_error']
            elif short == 'beta_1':
                params['BETA'] = val
                params['BETA_ERR'] = best_df.loc[idx, 'error']
            elif short == 'K_2':
                params['K_BB'] = val
            elif short == 'kT_2':
                params['KT'] = val
                params['KT_NEG_ERR'] = best_df.loc[idx, 'negative_error']
                params['KT_POS_ERR'] = best_df.loc[idx, 'positive_error']
        else:
            if short == 'alpha':
                params['ALPHA_BAND'] = val
            elif short == 'xp':
                params['EP_BAND'] = val
            elif short == 'beta':
                params['BETA_BAND'] = val

    return params, raw_vals


def clamp(val, lo, hi):
    """Clamp value to [lo, hi], with small offset from boundaries."""
    margin = 0.01 * (hi - lo)
    return max(lo + margin, min(hi - margin, val))


def build_plugins(pha_dir, trigger, nai_dets, bgo_det, spec_num):
    """Build OGIPLike plugins for all available detectors.

    Parameters
    ----------
    pha_dir : str
    trigger : str
    nai_dets : list of str
        NaI detector names with PHA files.
    bgo_det : str or None
        BGO detector name, or None if no BGO.
    spec_num : int
        1-indexed spectrum number within Type II PHA.

    Returns
    -------
    plugins : list of OGIPLike
    det_names : list of str
        Names of successfully loaded detectors.
    total_n_data : int
        Sum of data points across all plugins.
    """
    plugins = []
    det_names = []
    total_n_data = 0

    for det in nai_dets:
        pha_path = os.path.join(pha_dir, trigger, f'{trigger}_{det}.pha')
        if not os.path.exists(pha_path):
            continue
        try:
            ogip = OGIPLike(det, observation=pha_path, spectrum_number=spec_num)
            ogip.set_active_measurements(NAI_ENERGY_RANGE)
            total_n_data += int(ogip.n_data_points)
            plugins.append(ogip)
            det_names.append(det)
        except Exception:
            pass

    # Add BGO if available
    if bgo_det:
        bgo_pha = os.path.join(pha_dir, trigger, f'{trigger}_{bgo_det}.pha')
        if os.path.exists(bgo_pha):
            try:
                ogip_bgo = OGIPLike(bgo_det, observation=bgo_pha, spectrum_number=spec_num)
                ogip_bgo.set_active_measurements(BGO_ENERGY_RANGE)
                total_n_data += int(ogip_bgo.n_data_points)
                plugins.append(ogip_bgo)
                det_names.append(bgo_det)
            except Exception:
                pass

    return plugins, det_names, total_n_data


def fit_time_bin(pha_dir, trigger, nai_dets, bgo_det, spec_num,
                 prev_bb=None, prev_band=None):
    """Fit Band+BB and Band-only models to a single time bin using joint detectors.

    Parameters
    ----------
    pha_dir : str
    trigger : str
    nai_dets : list of str
    bgo_det : str or None
    spec_num : int (1-indexed)
    prev_bb : dict or None — previous bin's Band+BB raw parameter values
    prev_band : dict or None — previous bin's Band-only raw parameter values

    Returns
    -------
    result : dict with all output columns
    bb_raw : dict with raw Band+BB param values (for seeding next bin), or None
    band_raw : dict with raw Band-only param values, or None
    """
    result = {}
    bb_raw = None
    band_raw = None
    n_data = None

    # Starting values for this bin
    bb_start = prev_bb if prev_bb else DEFAULT_BAND_BB
    band_start = prev_band if prev_band else DEFAULT_BAND

    # ---- Fit 1: Band + Blackbody ----
    band_bb_ok = False
    try:
        plugins, det_names, n_data = build_plugins(
            pha_dir, trigger, nai_dets, bgo_det, spec_num
        )
        if not plugins:
            raise RuntimeError("No detector plugins loaded")

        band = Band()
        bb = Blackbody()

        # Set bounds
        band.K.bounds = (1e-10, 1e4)
        band.alpha.bounds = (-1.5, 3.0)
        band.xp.bounds = (10, 1e4)
        band.beta.bounds = (-5.0, -1.6)
        bb.K.bounds = (0, 1e4)
        bb.kT.bounds = (1, 200)

        # Seed starting values from previous bin
        band.K = clamp(bb_start['K_1'], 1e-10, 1e4)
        band.alpha = clamp(bb_start['alpha_1'], -1.5, 3.0)
        band.xp = clamp(bb_start['xp_1'], 10, 1e4)
        band.beta = clamp(bb_start['beta_1'], -5.0, -1.6)
        bb.K = clamp(bb_start['K_2'], 0, 1e4)
        bb.kT = clamp(bb_start['kT_2'], 1, 200)

        src = PointSource('GRB', 0, 0, spectral_shape=band + bb)
        model = Model(src)
        data = DataList(*plugins)
        jl = JointLikelihood(model, data)
        best_df, like_df = jl.fit()

        # Extract total -logL from joint fit
        if 'total' in like_df.index:
            neg_loglike = float(like_df.loc['total', '-log(likelihood)'])
        else:
            neg_loglike = float(like_df['-log(likelihood)'].sum())
        n_params_bb = 6
        aic, bic = compute_aic_bic(neg_loglike, n_params_bb, n_data)

        bb_params, bb_raw = extract_fit_params(best_df, model_type='band_bb')
        result.update(bb_params)
        result['LOGLIKE_BBBAND'] = neg_loglike
        result['AIC_BBBAND'] = aic
        result['BIC_BBBAND'] = bic
        band_bb_ok = True

    except Exception:
        result['EP'] = np.nan
        result['EP_NEG_ERR'] = np.nan
        result['EP_POS_ERR'] = np.nan
        result['ALPHA'] = np.nan
        result['ALPHA_ERR'] = np.nan
        result['BETA'] = np.nan
        result['BETA_ERR'] = np.nan
        result['KT'] = np.nan
        result['KT_NEG_ERR'] = np.nan
        result['KT_POS_ERR'] = np.nan
        result['K_BAND'] = np.nan
        result['K_BB'] = np.nan
        result['LOGLIKE_BBBAND'] = np.nan
        result['AIC_BBBAND'] = np.nan
        result['BIC_BBBAND'] = np.nan

    # ---- Fit 2: Band only ----
    band_only_ok = False
    try:
        plugins2, det_names2, n_data2 = build_plugins(
            pha_dir, trigger, nai_dets, bgo_det, spec_num
        )
        if not plugins2:
            raise RuntimeError("No detector plugins loaded")
        if n_data is None:
            n_data = n_data2

        band2 = Band()
        band2.K.bounds = (1e-10, 1e4)
        band2.alpha.bounds = (-1.5, 3.0)
        band2.xp.bounds = (10, 1e4)
        band2.beta.bounds = (-5.0, -1.6)

        # Seed from previous bin
        band2.K = clamp(band_start['K'], 1e-10, 1e4)
        band2.alpha = clamp(band_start['alpha'], -1.5, 3.0)
        band2.xp = clamp(band_start['xp'], 10, 1e4)
        band2.beta = clamp(band_start['beta'], -5.0, -1.6)

        src2 = PointSource('GRB', 0, 0, spectral_shape=band2)
        model2 = Model(src2)
        data2 = DataList(*plugins2)
        jl2 = JointLikelihood(model2, data2)
        best_df2, like_df2 = jl2.fit()

        if 'total' in like_df2.index:
            neg_loglike2 = float(like_df2.loc['total', '-log(likelihood)'])
        else:
            neg_loglike2 = float(like_df2['-log(likelihood)'].sum())
        n_params_band = 4
        aic2, bic2 = compute_aic_bic(neg_loglike2, n_params_band, n_data)

        band_params, band_raw = extract_fit_params(best_df2, model_type='band')
        result.update(band_params)
        result['LOGLIKE_BAND'] = neg_loglike2
        result['AIC_BAND'] = aic2
        result['BIC_BAND'] = bic2
        band_only_ok = True

    except Exception:
        result['EP_BAND'] = np.nan
        result['ALPHA_BAND'] = np.nan
        result['BETA_BAND'] = np.nan
        result['LOGLIKE_BAND'] = np.nan
        result['AIC_BAND'] = np.nan
        result['BIC_BAND'] = np.nan

    # ---- Model comparison ----
    if band_bb_ok and band_only_ok:
        result['DELTA_AIC'] = result['AIC_BAND'] - result['AIC_BBBAND']
        result['DELTA_BIC'] = result['BIC_BAND'] - result['BIC_BBBAND']
    else:
        result['DELTA_AIC'] = np.nan
        result['DELTA_BIC'] = np.nan

    # ---- Fit status ----
    if band_bb_ok and band_only_ok:
        result['FIT_STATUS'] = 'OK'
    elif band_only_ok:
        result['FIT_STATUS'] = 'BAND_ONLY_OK'
    else:
        result['FIT_STATUS'] = 'FAILED'

    result['N_DATA_POINTS'] = n_data if n_data is not None else 0

    return result, bb_raw, band_raw


def load_checkpoint():
    """Load checkpoint: set of completed trigger names."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_checkpoint(trigger):
    """Append a completed trigger to checkpoint file."""
    with open(CHECKPOINT_FILE, 'a') as f:
        f.write(trigger + '\n')


def save_results(all_rows):
    """Save current results to ECSV, overwriting previous."""
    if not all_rows:
        return
    t = Table(all_rows)
    t.write(OUTPUT_FILE, format='ascii.ecsv', overwrite=True)


# ==========================================================================
# Main
# ==========================================================================
if __name__ == '__main__':
    # Load Bayesian blocks results
    bb_path = os.path.join(RESULTS_DIR, 'bayesian_blocks_results.ecsv')
    if not os.path.exists(bb_path):
        print("ERROR: Run 04_bayesian_blocks.py first")
        sys.exit(1)

    bb_table = Table.read(bb_path, format='ascii.ecsv')

    # Filter: PHA must exist and at least 1 significant bin
    mask = (bb_table['PHA_WRITTEN'] == True) & (bb_table['BB_BINS_SIG'] > 0)
    grbs = bb_table[mask]
    print(f"GRBs to fit: {len(grbs)} (of {len(bb_table)} total)")

    total_bins_all = int(np.sum(grbs['BB_BINS_TOTAL']))
    total_bins_sig = int(np.sum(grbs['BB_BINS_SIG']))
    print(f"Total time bins in PHA files: {total_bins_all} ({total_bins_sig} significant)")
    print(f"Note: fitting ALL bins (significance not stored in PHA)")
    print(f"Sequential seeding: each bin seeded from previous bin's best-fit")
    print(f"Joint multi-detector fitting: NaI + BGO per Burgess et al. (2014)")

    # Load checkpoint for resumption
    completed = load_checkpoint()
    if completed:
        print(f"Resuming: {len(completed)} GRBs already completed")

    # Load existing results if resuming
    all_rows = []
    if completed and os.path.exists(OUTPUT_FILE):
        existing = Table.read(OUTPUT_FILE, format='ascii.ecsv')
        for row in existing:
            all_rows.append(dict(zip(existing.colnames, [row[c] for c in existing.colnames])))
        print(f"Loaded {len(all_rows)} existing result rows")

    n_fitted = 0
    n_failed_grbs = 0

    for i, grb_row in enumerate(grbs):
        trigger = str(grb_row['TRIGGER_NAME']).strip()
        det = str(grb_row['DETECTOR']).strip()  # brightest NaI
        name = str(grb_row['NAME']).strip()
        n_sig = int(grb_row['BB_BINS_SIG'])
        n_total = int(grb_row['BB_BINS_TOTAL'])

        if trigger in completed:
            continue

        # Parse detector info from BB results
        # DETECTORS_PHA contains comma-separated list of all detectors with PHA
        # BGO_DETECTOR contains the BGO detector name
        dets_pha_str = str(grb_row['DETECTORS_PHA']).strip() if 'DETECTORS_PHA' in grb_row.colnames else det
        bgo_det = str(grb_row['BGO_DETECTOR']).strip() if 'BGO_DETECTOR' in grb_row.colnames else None

        # Parse NaI and BGO from DETECTORS_PHA
        all_dets_pha = [d.strip() for d in dets_pha_str.split(',') if d.strip()]
        nai_dets_pha = [d for d in all_dets_pha if d.startswith('n')]
        # BGO is in DETECTORS_PHA if its PHA was exported successfully
        bgo_in_pha = bgo_det if bgo_det in all_dets_pha else None

        # Find PHA file for brightest detector (to read metadata)
        pha_path = os.path.join(PHA_DIR, trigger, f'{trigger}_{det}.pha')
        if not os.path.exists(pha_path):
            print(f"[{i+1}/{len(grbs)}] {trigger}: PHA not found, skipping")
            n_failed_grbs += 1
            save_checkpoint(trigger)
            continue

        # Read PHA metadata (tstart, telapse, spec_num) from brightest detector
        try:
            spec_nums, tstarts, telapses = read_pha_metadata(pha_path)
        except Exception as e:
            print(f"[{i+1}/{len(grbs)}] {trigger}: Cannot read PHA: {e}")
            n_failed_grbs += 1
            save_checkpoint(trigger)
            continue

        n_dets = len(nai_dets_pha) + (1 if bgo_in_pha else 0)
        print(f"[{i+1}/{len(grbs)}] {trigger} ({det}, {n_total} bins, {n_sig} sig, "
              f"{n_dets} dets: {','.join(nai_dets_pha)}"
              f"{'+' + bgo_in_pha if bgo_in_pha else ''})...",
              flush=True)

        # ---- Per-GRB sequential fitting ----
        prev_bb = None
        prev_band = None

        grb_ok = 0
        grb_fail = 0
        grb_ep_vals = []
        grb_kt_vals = []

        for j, sn in enumerate(spec_nums):
            sn = int(sn)
            tstart = float(tstarts[j])
            tstop = float(tstarts[j] + telapses[j])

            try:
                fit_result, bb_raw, band_raw = fit_time_bin(
                    PHA_DIR, trigger, nai_dets_pha, bgo_in_pha, sn,
                    prev_bb=prev_bb, prev_band=prev_band
                )
            except Exception:
                fit_result = {
                    'EP': np.nan, 'EP_NEG_ERR': np.nan, 'EP_POS_ERR': np.nan,
                    'ALPHA': np.nan, 'ALPHA_ERR': np.nan,
                    'BETA': np.nan, 'BETA_ERR': np.nan,
                    'KT': np.nan, 'KT_NEG_ERR': np.nan, 'KT_POS_ERR': np.nan,
                    'K_BAND': np.nan, 'K_BB': np.nan,
                    'LOGLIKE_BBBAND': np.nan, 'AIC_BBBAND': np.nan, 'BIC_BBBAND': np.nan,
                    'EP_BAND': np.nan, 'ALPHA_BAND': np.nan, 'BETA_BAND': np.nan,
                    'LOGLIKE_BAND': np.nan, 'AIC_BAND': np.nan, 'BIC_BAND': np.nan,
                    'DELTA_AIC': np.nan, 'DELTA_BIC': np.nan,
                    'FIT_STATUS': 'FAILED', 'N_DATA_POINTS': 0,
                }
                bb_raw = None
                band_raw = None

            # Update seeds for next bin (only if fit succeeded)
            if bb_raw is not None:
                prev_bb = bb_raw
            if band_raw is not None:
                prev_band = band_raw

            row = {
                'NAME': name,
                'TRIGGER_NAME': trigger,
                'DETECTOR': det,
                'SPEC_NUM': sn,
                'TSTART': tstart,
                'TSTOP': tstop,
                'N_DETECTORS': n_dets,
                'DETECTORS_USED': ','.join(nai_dets_pha + ([bgo_in_pha] if bgo_in_pha else [])),
            }
            row.update(fit_result)
            all_rows.append(row)

            if fit_result['FIT_STATUS'] == 'OK':
                grb_ok += 1
                ep_val = fit_result.get('EP', np.nan)
                kt_val = fit_result.get('KT', np.nan)
                if np.isfinite(ep_val):
                    grb_ep_vals.append(ep_val)
                if np.isfinite(kt_val):
                    grb_kt_vals.append(kt_val)
            elif fit_result['FIT_STATUS'] == 'BAND_ONLY_OK':
                grb_ok += 1
            else:
                grb_fail += 1

            n_fitted += 1

        # Per-GRB summary line
        ep_str = f"Ep={np.median(grb_ep_vals):.0f}" if grb_ep_vals else "Ep=N/A"
        kt_str = f"kT={np.median(grb_kt_vals):.1f}" if grb_kt_vals else "kT=N/A"
        status = "OK" if grb_fail == 0 else f"{grb_ok}ok/{grb_fail}fail"
        print(f"    -> {n_total} bins fitted, {ep_str} keV, {kt_str} keV [{status}]")

        # Incremental save after each GRB
        save_checkpoint(trigger)
        save_results(all_rows)

    # ====== Final summary ======
    print(f"\n{'='*60}")
    print(f"SPECTRAL FITTING COMPLETE")
    print(f"{'='*60}")
    print(f"Total bins fitted: {n_fitted}")
    print(f"GRBs failed: {n_failed_grbs}")

    if all_rows:
        res = Table(all_rows)

        ok_mask = np.array([s == 'OK' for s in res['FIT_STATUS']])
        band_ok_mask = np.array([s == 'BAND_ONLY_OK' for s in res['FIT_STATUS']])
        fail_mask = np.array([s == 'FAILED' for s in res['FIT_STATUS']])

        print(f"\nFit status breakdown:")
        print(f"  OK (both models):   {np.sum(ok_mask)}")
        print(f"  BAND_ONLY_OK:       {np.sum(band_ok_mask)}")
        print(f"  FAILED:             {np.sum(fail_mask)}")

        if np.any(ok_mask):
            ep_vals = res['EP'][ok_mask]
            ep_finite = ep_vals[np.isfinite(ep_vals)]
            kt_vals = res['KT'][ok_mask]
            kt_finite = kt_vals[np.isfinite(kt_vals)]

            if len(ep_finite) > 0:
                print(f"\nEp (Band+BB): median={np.median(ep_finite):.0f} keV, "
                      f"range=[{np.min(ep_finite):.0f}, {np.max(ep_finite):.0f}] keV")
            if len(kt_finite) > 0:
                print(f"kT (BB):      median={np.median(kt_finite):.1f} keV, "
                      f"range=[{np.min(kt_finite):.1f}, {np.max(kt_finite):.1f}] keV")

            # Check boundary hits
            beta_vals = res['BETA'][ok_mask]
            beta_boundary = np.sum(beta_vals == -5.0)
            kt_boundary = np.sum(kt_finite < 1.5) if len(kt_finite) > 0 else 0
            if beta_boundary > 0:
                print(f"\nWARNING: {beta_boundary} bins have beta at boundary (-5.0)")
            if kt_boundary > 0:
                print(f"WARNING: {kt_boundary} bins have kT near lower boundary (<1.5 keV)")

            # Delta AIC summary
            daic = res['DELTA_AIC'][ok_mask]
            daic_finite = daic[np.isfinite(daic)]
            if len(daic_finite) > 0:
                n_bb_pref = np.sum(daic_finite > 0)
                print(f"\nBB component preferred (delta_AIC > 0): "
                      f"{n_bb_pref}/{len(daic_finite)} bins "
                      f"({100*n_bb_pref/len(daic_finite):.1f}%)")

            # Multi-detector summary
            if 'N_DETECTORS' in res.colnames:
                n_det_vals = res['N_DETECTORS'][ok_mask]
                print(f"\nDetectors per fit: median={np.median(n_det_vals):.0f}, "
                      f"range=[{np.min(n_det_vals)}, {np.max(n_det_vals)}]")

        save_results(all_rows)
        print(f"\nResults saved to {OUTPUT_FILE}")
        print(f"Total rows: {len(all_rows)}")

    print(f"{'='*60}")
