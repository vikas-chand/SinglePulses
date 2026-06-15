#!/usr/bin/env python
"""
Phase 4.1b: Spectral plots for time-resolved GRB spectral fits.

Generates three types of plots following Burgess et al. (2014):
1. nuFnu spectral decomposition per GRB (Band + BB components, color-coded by time)
2. Per-GRB Ep vs kT correlation (log-log with power-law fit)
3. Combined Ep vs kT for the full sample
"""

import os
import sys
import warnings
import numpy as np
from astropy.table import Table
from scipy import stats

warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.cm as cm

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')

SPEC_PLOTS_DIR = os.path.join(PLOTS_DIR, 'spectral_fits')
CORR_PLOTS_DIR = os.path.join(PLOTS_DIR, 'ep_kt_correlations')
os.makedirs(SPEC_PLOTS_DIR, exist_ok=True)
os.makedirs(CORR_PLOTS_DIR, exist_ok=True)

# Energy grid for nuFnu plots (keV)
E_GRID = np.geomspace(8, 1000, 300)


# =========================================================================
# Spectral model functions
# =========================================================================

def band_nufnu(E, K, alpha, xp, beta, piv=100.0):
    """Evaluate E^2 * N(E) for the Band function.

    Parameters match astromodels Band parametrization:
      K     : normalization at pivot (photons/cm2/s/keV)
      alpha : low-energy index
      xp    : Ep, peak energy of nuFnu (keV)
      beta  : high-energy index
      piv   : pivot energy (keV), default 100
    """
    # Break energy
    Ec = xp * (alpha - beta) / (2.0 + alpha) if (2.0 + alpha) != 0 else 1e10

    result = np.zeros_like(E, dtype=float)

    lo = E < Ec
    hi = ~lo

    # Low-energy piece
    if np.any(lo):
        result[lo] = K * (E[lo] / piv) ** alpha * np.exp(-(2.0 + alpha) * E[lo] / xp)

    # High-energy piece
    if np.any(hi):
        A = ((alpha - beta) * xp / (piv * (2.0 + alpha))) ** (alpha - beta) * np.exp(beta - alpha)
        result[hi] = K * A * (E[hi] / piv) ** beta

    # nuFnu = E^2 * N(E)
    return E ** 2 * result


def blackbody_nufnu(E, K, kT):
    """Evaluate E^2 * N(E) for Blackbody.

    Parameters match astromodels Blackbody:
      K  : normalization
      kT : temperature (keV)
    """
    # N(E) = K * E^2 / (exp(E/kT) - 1)
    # nuFnu = E^2 * N(E) = K * E^4 / (exp(E/kT) - 1)
    x = E / kT
    # Avoid overflow
    x = np.clip(x, 0, 500)
    denom = np.exp(x) - 1.0
    denom = np.where(denom > 0, denom, 1e-100)
    return K * E ** 4 / denom


# =========================================================================
# Plot 1: nuFnu spectral decomposition per GRB
# =========================================================================

def plot_nufnu_grb(grb_name, trigger, grb_data, outpath):
    """nuFnu plot for one GRB with Band+BB decomposition.

    Color-coded by time: cool colors (early) -> warm colors (late).
    Inspired by Burgess et al. 2014, Figure 2.
    """
    # Filter to OK fits only
    ok = grb_data[np.array([s == 'OK' for s in grb_data['FIT_STATUS']])]
    if len(ok) == 0:
        return

    n_bins = len(ok)
    fig, ax = plt.subplots(figsize=(8, 6))

    # Color map: time evolution
    cmap_band = cm.winter  # cyan -> blue for non-thermal
    cmap_bb = cm.autumn    # red -> yellow for thermal

    norm = Normalize(vmin=0, vmax=max(n_bins - 1, 1))

    # Track peak nuFnu for y-limit clamping
    all_peak_vals = []

    for j, row in enumerate(ok):
        color_band = cmap_band(norm(j))
        color_bb = cmap_bb(norm(j))

        K_band = row['K_BAND']
        alpha = row['ALPHA']
        xp = row['EP']
        beta = row['BETA']
        K_bb = row['K_BB']
        kT = row['KT']

        # Skip if parameters are NaN
        if not (np.isfinite(K_band) and np.isfinite(xp) and np.isfinite(kT)):
            continue

        # Band component
        try:
            nufnu_band = band_nufnu(E_GRID, K_band, alpha, xp, beta)
            nufnu_band = np.where(nufnu_band > 0, nufnu_band, np.nan)
            ax.plot(E_GRID, nufnu_band, color=color_band, alpha=0.7, lw=1.2)
            peak = np.nanmax(nufnu_band)
            if np.isfinite(peak) and peak > 0:
                all_peak_vals.append(peak)
        except Exception:
            pass

        # BB component
        try:
            nufnu_bb = blackbody_nufnu(E_GRID, K_bb, kT)
            nufnu_bb = np.where(nufnu_bb > 0, nufnu_bb, np.nan)
            ax.plot(E_GRID, nufnu_bb, color=color_bb, alpha=0.7, lw=1.2, ls='--')
            peak = np.nanmax(nufnu_bb)
            if np.isfinite(peak) and peak > 0:
                all_peak_vals.append(peak)
        except Exception:
            pass

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Energy (keV)', fontsize=12)
    ax.set_ylabel(r'$\nu F_\nu$  [keV$^2$ photons cm$^{-2}$ s$^{-1}$ keV$^{-1}$]', fontsize=11)
    ax.set_title(f'{grb_name}  ({n_bins} time bins)', fontsize=13)
    ax.set_xlim(8, 1000)

    # Clamp y-axis to ~5 decades below peak
    if all_peak_vals:
        y_top = max(all_peak_vals)
        ax.set_ylim(y_top * 1e-5, y_top * 5)

    # Add legend proxy
    ax.plot([], [], color=cmap_band(0.5), lw=1.5, label='Band (non-thermal)')
    ax.plot([], [], color=cmap_bb(0.5), lw=1.5, ls='--', label='Blackbody (thermal)')
    ax.legend(fontsize=10, loc='lower left')

    # Colorbar for time
    sm = ScalarMappable(cmap=cm.viridis, norm=Normalize(
        vmin=float(ok['TSTART'][0]), vmax=float(ok['TSTOP'][-1])))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.02)
    cbar.set_label('Time since trigger (s)', fontsize=10)

    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


# =========================================================================
# Plot 2: Per-GRB Ep vs kT correlation
# =========================================================================

def plot_ep_kt_single(grb_name, trigger, grb_data, outpath):
    """Ep vs kT log-log plot for one GRB with power-law fit.

    Inspired by Burgess et al. 2014, Figure 3.
    """
    ok = grb_data[np.array([s == 'OK' for s in grb_data['FIT_STATUS']])]
    if len(ok) < 3:
        return None  # Need at least 3 points for meaningful correlation

    ep = np.array(ok['EP'], dtype=float)
    kt = np.array(ok['KT'], dtype=float)

    # Filter finite and positive
    mask = np.isfinite(ep) & np.isfinite(kt) & (ep > 0) & (kt > 0)
    # Also exclude boundary hits
    mask &= (kt > 1.5) & (ep > 10.5)
    ep = ep[mask]
    kt = kt[mask]

    if len(ep) < 3:
        return None

    # Power-law fit: log(Ep) = alpha * log(kT) + log(A)
    log_kt = np.log10(kt)
    log_ep = np.log10(ep)

    slope, intercept, r_value, p_value, std_err = stats.linregress(log_kt, log_ep)

    # Spearman rank correlation
    rho, p_spearman = stats.spearmanr(kt, ep)

    fig, ax = plt.subplots(figsize=(6, 5))

    # Data points with error bars
    ep_neg = np.abs(np.array(ok['EP_NEG_ERR'][mask], dtype=float))
    ep_pos = np.abs(np.array(ok['EP_POS_ERR'][mask], dtype=float))
    kt_neg = np.abs(np.array(ok['KT_NEG_ERR'][mask], dtype=float))
    kt_pos = np.abs(np.array(ok['KT_POS_ERR'][mask], dtype=float))

    # Replace NaN errors with 0
    ep_neg = np.where(np.isfinite(ep_neg), ep_neg, 0)
    ep_pos = np.where(np.isfinite(ep_pos), ep_pos, 0)
    kt_neg = np.where(np.isfinite(kt_neg), kt_neg, 0)
    kt_pos = np.where(np.isfinite(kt_pos), kt_pos, 0)

    ax.errorbar(kt, ep, xerr=[kt_neg, kt_pos], yerr=[ep_neg, ep_pos],
                fmt='o', color='firebrick', ms=6, ecolor='gray',
                elinewidth=0.8, capsize=2, zorder=5)

    # Best-fit power law
    kt_fit = np.geomspace(max(kt.min() * 0.5, 0.5), kt.max() * 2, 100)
    ep_fit = 10 ** (slope * np.log10(kt_fit) + intercept)
    ax.plot(kt_fit, ep_fit, 'k--', lw=1.5, alpha=0.7)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('kT (keV)', fontsize=12)
    ax.set_ylabel(r'$E_{\rm p}$ (keV)', fontsize=12)
    ax.set_title(f'{grb_name}', fontsize=13)

    # Annotation
    txt = (f'$\\alpha = {slope:.2f} \\pm {std_err:.2f}$\n'
           f'$\\rho_s = {rho:.2f}$  (p={p_spearman:.1e})\n'
           f'N = {len(ep)}')
    ax.text(0.05, 0.95, txt, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)

    return {'name': grb_name, 'trigger': trigger, 'alpha': slope,
            'alpha_err': std_err, 'rho': rho, 'p_value': p_spearman, 'n_pts': len(ep)}


# =========================================================================
# Plot 3: Combined Ep vs kT for all GRBs
# =========================================================================

def plot_ep_kt_combined(results, corr_info, outpath):
    """Combined Ep vs kT plot for entire sample.

    Inspired by Burgess et al. 2014, Figure 4.
    """
    ok = results[np.array([s == 'OK' for s in results['FIT_STATUS']])]

    ep = np.array(ok['EP'], dtype=float)
    kt = np.array(ok['KT'], dtype=float)
    triggers = np.array(ok['TRIGGER_NAME'])

    mask = np.isfinite(ep) & np.isfinite(kt) & (ep > 0) & (kt > 0)
    mask &= (kt > 1.5) & (ep > 10.5)
    ep = ep[mask]
    kt = kt[mask]
    triggers = triggers[mask]

    unique_triggers = sorted(set(triggers))

    fig, ax = plt.subplots(figsize=(8, 7))

    # Use different colors per GRB
    cmap = cm.tab20
    colors = {t: cmap(i / max(len(unique_triggers) - 1, 1))
              for i, t in enumerate(unique_triggers)}

    for trigger in unique_triggers:
        tmask = triggers == trigger
        if np.sum(tmask) < 2:
            continue
        ax.scatter(kt[tmask], ep[tmask], c=[colors[trigger]], s=20, alpha=0.6,
                   edgecolors='none')

    # Overall Spearman correlation
    rho, p_val = stats.spearmanr(kt, ep)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('kT (keV)', fontsize=13)
    ax.set_ylabel(r'$E_{\rm peak}$ (keV)', fontsize=13)
    ax.set_title(f'Ep vs kT — {len(unique_triggers)} GRBs, {len(ep)} time bins', fontsize=13)

    txt = f'Spearman $\\rho = {rho:.2f}$\np = {p_val:.1e}'
    ax.text(0.05, 0.95, txt, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)

    # Also make a version with per-GRB power-law lines
    if corr_info:
        fig2, ax2 = plt.subplots(figsize=(8, 7))

        for trigger in unique_triggers:
            tmask = triggers == trigger
            if np.sum(tmask) < 3:
                continue
            ax2.scatter(kt[tmask], ep[tmask], c=[colors[trigger]], s=20, alpha=0.6,
                        edgecolors='none')

            # Overlay per-burst fit line
            info = next((c for c in corr_info if c['trigger'] == trigger), None)
            if info and info['p_value'] < 0.05:
                kt_sub = kt[tmask]
                kt_line = np.geomspace(kt_sub.min(), kt_sub.max(), 50)
                slope, intercept, _, _, _ = stats.linregress(
                    np.log10(kt_sub), np.log10(ep[tmask]))
                ep_line = 10 ** (slope * np.log10(kt_line) + intercept)
                ax2.plot(kt_line, ep_line, color=colors[trigger], lw=1, alpha=0.5)

        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax2.set_xlabel('kT (keV)', fontsize=13)
        ax2.set_ylabel(r'$E_{\rm peak}$ (keV)', fontsize=13)
        ax2.set_title(f'Ep vs kT with per-GRB fits — {len(unique_triggers)} GRBs', fontsize=13)
        ax2.text(0.05, 0.95, txt, transform=ax2.transAxes, fontsize=11,
                 verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

        fig2.tight_layout()
        outpath2 = outpath.replace('.png', '_with_fits.png')
        fig2.savefig(outpath2, dpi=150)
        plt.close(fig2)


# =========================================================================
# Plot: Alpha distribution histogram
# =========================================================================

def plot_alpha_histogram(corr_info, outpath):
    """Histogram of per-GRB alpha indices with jet-type annotations."""
    alphas = np.array([c['alpha'] for c in corr_info])
    alpha_errs = np.array([c['alpha_err'] for c in corr_info])

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(alphas, bins=15, color='steelblue', edgecolor='black', alpha=0.7)

    # Mark Burgess 2014 thresholds
    ax.axvline(1.0, color='green', ls='--', lw=1.5, label=r'$\alpha=1$ (baryonic)')
    ax.axvline(2.0, color='red', ls='--', lw=1.5, label=r'$\alpha=2$ (magnetic)')

    ax.set_xlabel(r'$\alpha$  ($E_p \propto T^\alpha$)', fontsize=12)
    ax.set_ylabel('Number of GRBs', fontsize=12)
    ax.set_title(f'Distribution of Ep-kT power-law index ({len(alphas)} GRBs)', fontsize=12)
    ax.legend(fontsize=10)

    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


# =========================================================================
# Main
# =========================================================================
if __name__ == '__main__':
    # Load spectral fit results
    res_path = os.path.join(RESULTS_DIR, 'spectral_fit_results.ecsv')
    if not os.path.exists(res_path):
        print("ERROR: Run 06_spectral_fitting.py first")
        sys.exit(1)

    results = Table.read(res_path, format='ascii.ecsv')
    print(f"Loaded {len(results)} spectral fit results")

    unique_grbs = []
    seen = set()
    for row in results:
        t = row['TRIGGER_NAME']
        if t not in seen:
            unique_grbs.append((row['NAME'], t))
            seen.add(t)
    print(f"Unique GRBs: {len(unique_grbs)}")

    # ---- Plot 1 & 2: Per-GRB plots ----
    corr_info = []

    for i, (name, trigger) in enumerate(unique_grbs):
        grb_data = results[results['TRIGGER_NAME'] == trigger]
        print(f"[{i+1}/{len(unique_grbs)}] {name} ({trigger}, {len(grb_data)} bins)...",
              end=' ', flush=True)

        # nuFnu decomposition
        nufnu_path = os.path.join(SPEC_PLOTS_DIR, f'{trigger}_nufnu.png')
        plot_nufnu_grb(name, trigger, grb_data, nufnu_path)

        # Ep vs kT correlation
        corr_path = os.path.join(CORR_PLOTS_DIR, f'{trigger}_ep_kt.png')
        info = plot_ep_kt_single(name, trigger, grb_data, corr_path)

        if info:
            corr_info.append(info)
            print(f"alpha={info['alpha']:.2f}+/-{info['alpha_err']:.2f}, "
                  f"rho={info['rho']:.2f}")
        else:
            print("(too few points for correlation)")

    # ---- Plot 3: Combined Ep vs kT ----
    print(f"\nGenerating combined Ep vs kT plot...")
    combined_path = os.path.join(PLOTS_DIR, 'ep_kt_combined.png')
    plot_ep_kt_combined(results, corr_info, combined_path)

    # ---- Plot 4: Alpha histogram ----
    if corr_info:
        print(f"Generating alpha histogram...")
        hist_path = os.path.join(PLOTS_DIR, 'alpha_histogram.png')
        plot_alpha_histogram(corr_info, hist_path)

    # ---- Summary ----
    print(f"\n{'='*60}")
    print(f"PLOTTING COMPLETE")
    print(f"{'='*60}")
    print(f"nuFnu plots:       {SPEC_PLOTS_DIR}/")
    print(f"Ep-kT correlations: {CORR_PLOTS_DIR}/")
    print(f"Combined plot:      {combined_path}")

    if corr_info:
        alphas = np.array([c['alpha'] for c in corr_info])
        sig = [c for c in corr_info if c['p_value'] < 0.05]
        print(f"\nPer-GRB Ep-kT correlations:")
        print(f"  GRBs with enough points: {len(corr_info)}")
        print(f"  Significant (p<0.05):    {len(sig)}")
        print(f"  alpha: median={np.median(alphas):.2f}, "
              f"range=[{alphas.min():.2f}, {alphas.max():.2f}]")

        # Classify jet type a la Burgess 2014
        baryonic = sum(1 for a in alphas if a < 1.4)
        magnetic = sum(1 for a in alphas if a >= 1.4)
        print(f"  Baryonic (alpha<1.4): {baryonic}")
        print(f"  Magnetic (alpha>=1.4): {magnetic}")

    print(f"{'='*60}")
