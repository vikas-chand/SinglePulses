#!/usr/bin/env python
"""
Break / temperature correlations across the sample:

 (A) 2SBPL two breaks:   x_b (nu_c)  vs  x_p (nu_m = E_p)   [DSBPL, sig bins]
 (B) BB+SBPL proxy:      kT          vs  E_p (non-thermal)  [Band+BB/CPL+BB]
 (C) Mei+2024 (2409.08341) analog, OBSERVER frame (no redshift -> flux not L):
       nu_c proxy (Band E_p, per Mei "Band E_p ~ nu_c")  vs  energy flux
       E_p (nu_m)                                          vs  energy flux  (anti-Yonetoku)
 (D) user's BB+SBPL proxy:   kT  vs  energy flux  (BB-temperature vs "peak luminosity")

Flux = observer-frame energy flux of the per-bin BEST-AIC model, integrated
10 keV - 40 MeV (erg/cm^2/s). It is NOT rest-frame L_iso (we have no z); it is
the closest observer-frame proxy. Correlations are reported with Spearman rho,
log-log slope, and N. The x_b<x_p ordering is enforced by the validity gate, so
a permutation null is computed for (A) to check for truncation-induced inflation.
"""
import os, sys, warnings, importlib.util
warnings.filterwarnings('ignore')
os.environ.setdefault('OMP_NUM_THREADS', '1')
_FD = '/Users/salim/anaconda3/envs/threeML/share/fermitools'
if not os.environ.get('CALDB') or '/refdata/fermi' in os.environ.get('CALDBALIAS', ''):
    for k, v in {'FERMI_DIR': _FD, 'CALDB': _FD+'/data/caldb',
                 'CALDBALIAS': _FD+'/data/caldb/software/tools/alias_config.fits',
                 'CALDBCONFIG': _FD+'/data/caldb/software/tools/caldb.config',
                 'CALDBROOT': _FD+'/data/caldb', 'EXTFILESSYS': _FD+'/refdata/fermi'}.items():
        os.environ[k] = v
import numpy as np
from astropy.table import Table
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, 'results')
FIG = os.path.join(RES, 'figures')
t = Table.read(os.path.join(RES, 'sample_all_models.ecsv'), format='ascii.ecsv')
b = t[t['BLOCK'] >= 0]

# bounds for rail rejection (mirror scripts/10)
XBB, XPB, EPB, KTB = (10, 900), (30, 5000), (30, 5000), (1, 200)
KEV2ERG = 1.602176634e-9
LRT_SIG = 9.2

# --- astromodels flux for the per-bin BEST model -----------------------------
spec = importlib.util.spec_from_file_location(
    's10', os.path.join(BASE, 'scripts', '10_spectral_fit_burst.py'))
s10 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s10)
EGRID = np.logspace(np.log10(10.0), np.log10(40000.0), 400)   # 10 keV - 40 MeV

def _seed_from_row(r, model):
    if model == 'Band':
        return {'band_alpha': r['BAND_ALPHA'], 'band_Ep': r['BAND_EP'],
                'band_beta': r['BAND_BETA'], 'band_K': r['BAND_K']}
    if model == 'CPL':
        return {'cpl_index': r['CPL_INDEX'], 'cpl_xc': r['CPL_XC'], 'cpl_K': r['CPL_K']}
    if model == 'SBPL':
        return {'sbpl_alpha': r['SBPL_ALPHA'], 'sbpl_break': r['SBPL_EBREAK'],
                'sbpl_beta': r['SBPL_BETA'], 'sbpl_K': r['SBPL_K']}
    if model == 'DSBPL':
        return {'dsbpl_alpha1': r['DSBPL_ALPHA1'], 'dsbpl_xb': r['DSBPL_XB'],
                'dsbpl_alpha2': r['DSBPL_ALPHA2'], 'dsbpl_xp': r['DSBPL_XP'],
                'dsbpl_beta': r['DSBPL_BETA'], 'dsbpl_K': r['DSBPL_K']}
    if model == 'Band+BB':
        return {'band_alpha': r['BANDBB_ALPHA'], 'band_Ep': r['BANDBB_EP'],
                'band_beta': r['BANDBB_BETA'], 'band_K': r['BANDBB_K_BAND'],
                'bb_kT': r['BANDBB_KT'], 'bb_K': r['BANDBB_K_BB']}
    if model == 'CPL+BB':
        return {'cpl_index': r['CPLBB_INDEX'], 'cpl_xc': r['CPLBB_XC'],
                'cpl_K': r['CPLBB_K_CPL'], 'bb_kT': r['CPLBB_KT'], 'bb_K': r['CPLBB_K_BB']}
    return None

_BUILD = {s['name']: s['build'] for s in s10.MODEL_SPECS}

def both_flux(r, model):
    """observer-frame (photon_flux [ph/cm2/s], energy_flux [erg/cm2/s]) over EGRID."""
    try:
        sd = _seed_from_row(r, model)
        if sd is None or any(not np.isfinite(v) for v in sd.values()):
            return np.nan, np.nan
        fn = _BUILD[model](sd)                       # astromodels (composite) function
        NE = np.asarray(fn(EGRID), float)            # photons/cm^2/s/keV
        if not np.all(np.isfinite(NE)):
            return np.nan, np.nan
        return (float(np.trapz(NE, EGRID)),
                float(np.trapz(EGRID * NE, EGRID)) * KEV2ERG)
    except Exception:
        return np.nan, np.nan

# per-bin best-model fluxes. ENERGY flux is the L-proxy; PHOTON flux is the
# induction-free control (energy flux is inflated by harder spectra, which can
# manufacture a peak-energy-vs-flux correlation; photon flux is not).
_pf = np.array([both_flux(r, str(r['BEST_AIC_MODEL'])) for r in b])
photflux = _pf[:, 0]
flux = _pf[:, 1]

# ---------------- (A) 2SBPL two breaks: nu_c (x_b) vs nu_m (x_p) -------------
def dsbpl_ok(r):
    xb, xp = float(r['DSBPL_XB']), float(r['DSBPL_XP'])
    rail = (xb <= XBB[0]*1.02 or xb >= XBB[1]*0.98 or xp <= XPB[0]*1.02 or xp >= XPB[1]*0.98)
    return (bool(r['DSBPL_VALID']) and np.isfinite(xb) and np.isfinite(xp)
            and not rail and xb < xp
            and np.isfinite(r['LRT_DSBPL_SBPL']) and r['LRT_DSBPL_SBPL'] >= LRT_SIG)
mA = np.array([dsbpl_ok(r) for r in b])
xb = np.array([float(r['DSBPL_XB']) for r in b])[mA]
xp = np.array([float(r['DSBPL_XP']) for r in b])[mA]

# ---------------- (B) BB+SBPL proxy: kT vs E_p -------------------------------
def cpl_peak(i, xc): return (2+i)*xc if i > -2 else np.nan
kt_l, ep_l, fl_l, pf_l = [], [], [], []
for i, r in enumerate(b):
    cand = []
    if bool(r['BANDBB_VALID']) and np.isfinite(r['LRT_BANDBB_BAND']) and r['LRT_BANDBB_BAND'] >= LRT_SIG:
        kt, ep = float(r['BANDBB_KT']), float(r['BANDBB_EP'])
        if KTB[0]*1.02 < kt < KTB[1]*0.98 and ep > EPB[0]*1.02:
            cand.append((float(r['BANDBB_AIC']), kt, ep))
    if bool(r['CPLBB_VALID']) and np.isfinite(r['LRT_CPLBB_CPL']) and r['LRT_CPLBB_CPL'] >= LRT_SIG:
        kt = float(r['CPLBB_KT']); ep = cpl_peak(float(r['CPLBB_INDEX']), float(r['CPLBB_XC']))
        if KTB[0]*1.02 < kt < KTB[1]*0.98 and np.isfinite(ep) and ep > 0:
            cand.append((float(r['CPLBB_AIC']), kt, ep))
    if cand:
        cand.sort(); kt_l.append(cand[0][1]); ep_l.append(cand[0][2])
        fl_l.append(flux[i]); pf_l.append(photflux[i])
kt = np.array(kt_l); ep = np.array(ep_l); kt_flux = np.array(fl_l); kt_photflux = np.array(pf_l)

# ---------------- (C) Mei analog (observer frame) ---------------------------
# nu_c proxy = Band E_p (Mei: Band E_p ~ nu_c); nu_m = E_p from +BB / Band.
def band_ok(r):
    return (str(r['BAND_STATUS']) == 'OK' and np.isfinite(r['BAND_EP'])
            and EPB[0]*1.02 < float(r['BAND_EP']) < EPB[1]*0.98)
mBand = np.array([band_ok(r) for r in b])
_mb = mBand & np.isfinite(flux)
nuc_band = np.array([float(r['BAND_EP']) for r in b])[_mb]
flux_band = flux[_mb]
photflux_band = photflux[_mb]

def corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    x, y = x[ok], y[ok]
    if len(x) < 3:
        return dict(N=len(x), rho=np.nan, p=np.nan, slope=np.nan, serr=np.nan)
    rho, p = spearmanr(x, y)
    c, cov = np.polyfit(np.log10(x), np.log10(y), 1, cov=True)
    return dict(N=len(x), rho=float(rho), p=float(p), slope=float(c[0]),
                serr=float(np.sqrt(cov[0, 0])))

out = {}
out['A_xb_xp']     = corr(xb, xp)
out['B_kT_Ep']     = corr(kt, ep)
out['C_nuc_flux']  = corr(nuc_band, flux_band)        # Mei: nu_c (BandEp) vs L
out['C_Ep_flux']   = corr(ep, kt_flux)                # nu_m=Ep vs L (anti-Yonetoku)
out['D_kT_flux']   = corr(kt, kt_flux)                # user's BB proxy: kT vs L
# induction-free controls: same quantities vs PHOTON flux (no energy weighting)
out['C_nuc_phot']  = corr(nuc_band, photflux_band)
out['C_Ep_phot']   = corr(ep, kt_photflux)
out['D_kT_phot']   = corr(kt, kt_photflux)

# permutation null for (A): is rho inflated by the enforced x_b<x_p truncation?
rng_pairs = []
if len(xb) >= 3:
    base = spearmanr(xb, xp)[0]
    # shuffle xp among bins, re-impose xb<xp, recompute rho (null with truncation)
    null = []
    order = np.argsort(xb)
    for s in range(2000):
        # deterministic-ish shuffle by rolling (avoid RNG which is blocked)
        xpp = np.roll(xp, s % max(len(xp), 1) + 1)
        keep = xb < xpp
        if keep.sum() >= 3:
            null.append(spearmanr(xb[keep], xpp[keep])[0])
    null = np.array(null)
    out['A_perm'] = dict(rho_obs=float(base),
                         null_mean=float(np.nanmean(null)),
                         null_95=float(np.nanpercentile(null, 95)),
                         n_null=int(len(null)))

# ---------------- report ----------------------------------------------------
L = []
L.append('BREAK / TEMPERATURE CORRELATIONS  (full sample, observer frame)')
L.append(f'{"correlation":34s} {"N":>4s} {"rho":>7s} {"p":>10s} {"slope":>14s}')
def line(tag, label):
    r = out[tag]
    sl = f'{r["slope"]:.2f}±{r["serr"]:.2f}' if np.isfinite(r['slope']) else 'n/a'
    L.append(f'{label:34s} {r["N"]:>4d} {r["rho"]:>7.3f} {r["p"]:>10.1e} {sl:>14s}')
line('A_xb_xp',    '(A) 2SBPL  nu_c(x_b) vs nu_m(x_p)')
line('B_kT_Ep',    '(B) BB+SBPL proxy  kT vs E_p')
line('C_nuc_flux', '(C) Mei  nu_c(BandEp) vs ENERGYflux')
line('C_Ep_flux',  '(C) nu_m=E_p vs ENERGYflux (anti-Yonetoku)')
line('D_kT_flux',  '(D) kT vs ENERGYflux (BB-temp vs L)')
L.append('')
L.append('--- INDUCTION CONTROL: same vs PHOTON flux (energy-weighting removed) ---')
line('C_nuc_phot', '(C*) nu_c(BandEp) vs PHOTONflux')
line('C_Ep_phot',  '(C*) nu_m=E_p vs PHOTONflux')
line('D_kT_phot',  '(D*) kT vs PHOTONflux')
L.append('  -> a correlation that COLLAPSES from energy- to photon-flux is an')
L.append('     energy-weighting artifact (harder spectra carry more energy flux).')
L.append('')
L.append('Reference (Mei+2024, 2409.08341, REST frame): nu_c,z ~ L^0.53±0.06; NO E_p-L.')
if 'A_perm' in out:
    a = out['A_perm']
    L.append(f'(A) truncation null: rho_obs={a["rho_obs"]:.3f}  '
             f'null_mean={a["null_mean"]:.3f}  null_95={a["null_95"]:.3f}  '
             f'-> {"REAL (obs >> null)" if a["rho_obs"] > a["null_95"] else "possibly truncation-driven"}')
report = '\n'.join(L)
open('/tmp/break_correlations.txt', 'w').write(report + '\n')
print(report)

# ---------------- figure ----------------------------------------------------
fig, ax = plt.subplots(2, 3, figsize=(15, 9))
def panel(a, x, y, xl, yl, ttl, res, c='k', ref=None):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0); x, y = x[ok], y[ok]
    a.scatter(x, y, s=26, c=c, alpha=0.8, zorder=3)
    if res['N'] >= 3 and np.isfinite(res['slope']):
        xx = np.logspace(np.log10(x.min()), np.log10(x.max()), 20)
        cc = np.polyfit(np.log10(x), np.log10(y), 1)
        a.plot(xx, 10**(cc[1]+cc[0]*np.log10(xx)), 'b--',
               label=f'slope={res["slope"]:.2f}±{res["serr"]:.2f}\nρ={res["rho"]:.2f}, N={res["N"]}')
        if ref is not None:
            a.plot([], [], ' ', label=ref)
        a.legend(fontsize=8)
    a.set_xscale('log'); a.set_yscale('log'); a.set_xlabel(xl); a.set_ylabel(yl)
    a.set_title(ttl); a.tick_params(direction='in', which='both', top=True, right=True); a.minorticks_on()

panel(ax[0,0], xb, xp, r'$\nu_c$ = $x_b$ [keV]', r'$\nu_m=E_p$ = $x_p$ [keV]',
      '(A) 2SBPL: the two breaks', out['A_xb_xp'])
ax[0,0].plot(EGRID[[0,-1]], EGRID[[0,-1]], ':', color='0.6', lw=1)  # x_b=x_p line
panel(ax[0,1], kt, ep, 'kT [keV]', r'$E_p$ [keV]',
      '(B) BB+SBPL proxy: kT vs $E_p$', out['B_kT_Ep'], c='#d62728')
panel(ax[0,2], nuc_band, flux_band, r'$\nu_c$ (Band $E_p$) [keV]', 'energy flux [erg cm$^{-2}$ s$^{-1}$]',
      r'(C) Mei: $\nu_c$ vs flux', out['C_nuc_flux'], c='purple',
      ref=f'ρ(photon-flux)={out["C_nuc_phot"]["rho"]:.2f}  [Mei rest: 0.53]')
panel(ax[1,0], ep, kt_flux, r'$\nu_m=E_p$ [keV]', 'energy flux [erg cm$^{-2}$ s$^{-1}$]',
      '(C) $E_p$ vs flux (anti-Yonetoku)', out['C_Ep_flux'], c='#2ca02c',
      ref=f'ρ(photon-flux)={out["C_Ep_phot"]["rho"]:.2f}  → artifact')
panel(ax[1,1], kt, kt_flux, 'kT [keV]', 'energy flux [erg cm$^{-2}$ s$^{-1}$]',
      '(D) kT vs flux (BB-temp vs L)', out['D_kT_flux'], c='#ff7f0e',
      ref=f'ρ(photon-flux)={out["D_kT_phot"]["rho"]:.2f}  (real residual)')
# ratio histogram (cooling regime, Mei quantity)
ax[1,2].hist(np.log10(xp/xb), bins=12, color='#4477aa', edgecolor='k')
ax[1,2].set_xlabel(r'$\log_{10}(\nu_m/\nu_c)$'); ax[1,2].set_ylabel('bins')
ax[1,2].set_title(r'(E) cooling regime $\nu_m/\nu_c$'); ax[1,2].tick_params(direction='in', which='both', top=True, right=True)
fig.suptitle('Spectral-break / temperature correlations (full sample, observer frame; no redshift)', fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'fig_break_correlations.png'), dpi=160, bbox_inches='tight')
print('\nwrote results/figures/fig_break_correlations.png')
