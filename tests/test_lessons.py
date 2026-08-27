"""Lessons-as-tests: every SpectralFitting.md lesson that can be an invariant, IS one.

Doctrine (2026-08-08): a lesson is not learned until it exists as a CLAIM and a
TEST. The L9 fix (widen the Ep cap) was implemented correctly, validated on the
block that motivated it (bn110721200 blk0), and silently destroyed blk9 — prose
cannot fail a build; these tests can. Each test names its lesson and the burst
that generated it.

These run on the FIT TABLES already on disk (light tier: numpy/astropy only).
A failure on a walkthrough-era table is *the test doing its job* — it localizes
which products carry a known engine bug and must be regenerated before use.
"""
import glob
import os

import numpy as np
import pytest
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The tables the suite guards. Walkthrough + demo out-roots: the products of
# the CURRENT engine. (Archival clean_per_burst* roots predate several fixes
# and are quarantined separately — do not add them here without a reason.)
# results/demo_110721200 (v1) is SUPERSEDED by _v2 (refit 2026-08-09 with the
# L18/L19/L20 engine) and deliberately not guarded.
# v1 walkthrough roots + _lat forks are SUPERSEDED by the _v2 LAT-inclusive
# regenerations (2026-08-09, fixed engine) and deliberately not guarded.
GUARDED_ROOTS = [
    'results/demo_110721200_v2',
    'results/walkthrough_b3_v2', 'results/walkthrough_b4_v2',
    'results/walkthrough_b5_v2', 'results/walkthrough_b6_v2',
]

# Known-stale debt ledger: tables generated BEFORE an engine fix, failing the
# fix's test for exactly the reason the fix exists. xfail (not fail) so the
# suite stays a usable gate while the debt stays visible. An entry is removed
# when its table is regenerated — a NEW table must never appear here.
KNOWN_STALE = {
    # (test_key, path substring) -> reason
    ('L18', 'walkthrough_b5'): 'blk8 alpha=+0.257, Ep=38.6 — the same faint-'
                               'block collapse as demo blk9 (predates the L18 '
                               'simple-model multistart); clears on b5 refit',
    ('L19', 'walkthrough_b4'): 'blk0 LRT_DSBPL_SBPL=-1.12 predates the L19 '
                               'NaN+stamp guard; clears on b4 refit',
    ('L20', 'walkthrough_b3'): 'EPK_CURVE predates restore_best_fit (L20)',
    ('L24', 'walkthrough_b6'): 'T_INT BB railed at 1.0 keV with 11 VALID '
                               'resolved-kT blocks; clears when the T_INT '
                               're-seeding fix lands + b6 refit',
    ('L20', 'walkthrough_b4'): 'EPK_CURVE predates restore_best_fit (L20)',
    ('L20', 'walkthrough_b5'): 'EPK_CURVE predates restore_best_fit (L20)',
    ('L20', 'walkthrough_b6'): 'EPK_CURVE predates restore_best_fit (L20)',
}


def _xfail_if_known_stale(key, path):
    for (k, sub), why in KNOWN_STALE.items():
        if k == key and sub in path:
            pytest.xfail(f'known-stale ({sub}): {why}')


def _tables():
    out = []
    for root in GUARDED_ROOTS:
        for f in glob.glob(os.path.join(BASE, root, '**', 'spectral_fits.ecsv'),
                           recursive=True):
            out.append((os.path.relpath(f, BASE), Table.read(f)))
    return out


TABLES = _tables()
IDS = [p for p, _ in TABLES]


def test_guarded_tables_are_present():
    """The lesson suite is only as real as the tables it can see.

    `results/` is gitignored, so on GitHub Actions NONE of the guarded fit tables
    exist: every parametrized lesson test silently parametrizes over an empty list
    and the suite reports green while checking nothing (found 2026-08-13, and the
    external audit's C1 'the lesson suite is nominal').

    TAXONOMY FIX 2026-08-27 (skeleton F-STRUCTURAL: label + continue): on a
    runner that structurally CANNOT have the products (CI=true), a red X was
    functioning as documentation -- every PR looked broken and the real,
    checkable failures drowned in the expected one. In CI this now SKIPS with
    the full warning as its visible label; in any local/analysis environment
    (CI unset) it still FAILS LOUDLY, because there the tables' absence is a
    real defect, not a structural one.
    """
    import os, pytest
    if not TABLES and os.environ.get('CI'):
        pytest.skip('UNVERIFIED-IN-CI: no fit products on this runner; the '
                    'lesson suite is VACUOUS here and this green is NOT a '
                    'science pass (see workflow file + this test docstring)')
    assert TABLES, (
        'NO guarded fit tables found under %s -- the lesson tests below are '
        'VACUOUS in this environment (they parametrize over an empty list and '
        'report green while checking nothing). Either provide the products or '
        'treat this run as UNVERIFIED; do not read a green suite as a pass.'
        % ', '.join(GUARDED_ROOTS))


def _blocks(t):
    bc = next(c for c in ('BLOCK', 'BLK') if c in t.colnames)
    return t[np.asarray(t[bc]) >= 0], bc          # resolved blocks only (not T_INT)


def _f(row, col):
    try:
        v = float(row[col])
        return v
    except Exception:
        return float('nan')


# ---------------------------------------------------------------------------
# L18 (bn110721200 blk9, 2026-08-08): the simple-model chain seed can drop a
# faint block into a soft local minimum (alpha=+0.82, Ep=42 keV against
# alpha in [-1.26,-0.93], Ep 373-424 across 9 archival runs). A Band alpha
# harder than 0 in a WINNING or VALID fit is outside anything this campaign
# has ever measured on these bursts and marks a collapsed fit, not a burst.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('path,t', TABLES, ids=IDS)
def test_L18_no_positive_alpha_band_fits(path, t):
    # No VALID gate here on purpose: the collapsed blk9 fit was auto-
    # invalidated (Ep railed near the 30 keV bound) yet its alpha=+0.82
    # still sat in the table and was quoted in the Step-9 narrative. An OK
    # Band fit with alpha > 0 on these bursts is a collapsed fit, full stop
    # — the fixed engine's simple-model multistart must land elsewhere.
    tb, bc = _blocks(t)
    bad = []
    for r in tb:
        a = _f(r, 'BAND_ALPHA')
        status = str(r['BAND_STATUS']) if 'BAND_STATUS' in t.colnames else 'OK'
        if status == 'OK' and np.isfinite(a) and a > 0.0:
            bad.append(f'blk{r[bc]} alpha={a:+.3f}')
    if bad:
        _xfail_if_known_stale('L18', path)
    assert not bad, f'{path}: collapsed Band fits (L18): {bad}'


def test_L18_demo_blk9_recovers_archival_minimum():
    # Burst-anchored regression (the L9-fix regression itself): 9 archival
    # runs of bn110721200 blk9 all give alpha in [-1.26, -0.93] and
    # Ep 373-424 keV. GREEN since the 2026-08-09 _v2 refit with the L18
    # simple-model multistart: alpha=-0.927, Ep=366.0, VALID=True.
    f = os.path.join(BASE, 'results', 'demo_110721200_v2', 'fit',
                     'spectral_fits.ecsv')
    if not os.path.exists(f):
        pytest.skip('demo table not present')
    t = Table.read(f)
    bc = next(c for c in ('BLOCK', 'BLK') if c in t.colnames)
    r = t[np.asarray(t[bc]) == 9]
    if not len(r):
        pytest.skip('no blk9 row')
    r = r[0]
    a, ep = _f(r, 'BAND_ALPHA'), _f(r, 'BAND_EP')
    valid = bool(r['BAND_VALID']) if 'BAND_VALID' in t.colnames else True
    assert valid and -2.0 <= a <= 0.0 and 200.0 <= ep <= 800.0, (
        f'blk9 Band fit did not recover the archival minimum: '
        f'alpha={a:+.3f}, Ep={ep:.1f}, VALID={valid} '
        f'(archival: alpha -1.26..-0.93, Ep 373-424)')


# ---------------------------------------------------------------------------
# L16 + the two retracted claims: the declared winner must itself be a VALID
# fit — margins computed over rows whose *_VALID is False are meaningless.
# ---------------------------------------------------------------------------
_PREFIX = {  # BEST_AIC_MODEL name -> column prefix
    'Band': 'BAND', 'CPL': 'CPL', 'SBPL': 'SBPL', 'SBPLfree': 'SBPLF',
    'DSBPL': 'DSBPL', 'DSBPLfree': 'DSBPLF', 'Band+BB': 'BANDBB',
    'CPL+BB': 'CPLBB', 'SBPL+BB': 'SBPLBB',
}


@pytest.mark.parametrize('path,t', TABLES, ids=IDS)
def test_L16_winner_is_valid(path, t):
    if 'BEST_AIC_MODEL' not in t.colnames:
        pytest.skip('no BEST_AIC_MODEL column')
    tb, bc = _blocks(t)
    bad = []
    for r in tb:
        win = str(r['BEST_AIC_MODEL'])
        pfx = _PREFIX.get(win)
        col = f'{pfx}_VALID' if pfx else None
        if col and col in t.colnames and not bool(r[col]):
            bad.append(f'blk{r[bc]} winner={win} but {col}=False')
    assert not bad, f'{path}: invalid winners (L16): {bad}'


# ---------------------------------------------------------------------------
# L19 (bn110721200 demo blk1, 130518A repeat runs): a nested child strictly
# worse than its parent is impossible at the optimum. LRT ~ 0 is legal
# (component pinned to zero); LRT < -0.5 must never sit in a table as a
# clean non-detection. Nuance (demo/b4 blk0, LRT_DSBPL_SBPL = -1.66/-1.12):
# DSBPL is only APPROXIMATELY nested in SBPL (fixed-smoothness conventions
# differ), so a small negative can be parameterization mismatch rather than
# a failed fit — but either way the value is not chi2-distributed and must
# be NaN'd + stamped (engine does this at fit time since 2026-08-08).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('path,t', TABLES, ids=IDS)
def test_L19_no_impossible_negative_lrt(path, t):
    tb, bc = _blocks(t)
    _stale = None
    lrt_cols = [c for c in t.colnames if c.startswith('LRT_')
                and c != 'LRT_INVALID']
    bad = []
    for r in tb:
        for c in lrt_cols:
            v = _f(r, c)
            if np.isfinite(v) and v < -0.5:
                bad.append(f'blk{r[bc]} {c}={v:.2f}')
    if bad:
        _xfail_if_known_stale('L19', path)
    assert not bad, f'{path}: impossible negative LRTs (L19): {bad}'


# ---------------------------------------------------------------------------
# L11 (130518A reconciliation): DSBPL is symmetric under alpha1<->alpha2, so
# physical ordering must be ENFORCED, not assumed — a VALID DSBPL must have
# its low break below its peak.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('path,t', TABLES, ids=IDS)
def test_L11_dsbpl_break_below_peak_when_valid(path, t):
    tb, bc = _blocks(t)
    bad = []
    for pfx in ('DSBPL', 'DSBPLF'):
        vcol, xb_c, xp_c = f'{pfx}_VALID', f'{pfx}_XB', f'{pfx}_XP'
        if not all(c in t.colnames for c in (vcol, xb_c, xp_c)):
            continue
        for r in tb:
            if bool(r[vcol]):
                xb, xp = _f(r, xb_c), _f(r, xp_c)
                if np.isfinite(xb) and np.isfinite(xp) and xb >= xp:
                    bad.append(f'blk{r[bc]} {pfx} xb={xb:.1f} >= xp={xp:.1f}')
    assert not bad, f'{path}: VALID DSBPL with inverted breaks (L11): {bad}'


# ---------------------------------------------------------------------------
# L20 (130518A blk8/blk14, four-channel audit): EPK_CURVE was evaluated on a
# model displaced by the MINOS scan — it recorded the BB bump (3.92 kT)
# while the composite's true peak sat at the Band Ep. Symptom: EPK_CURVE
# within 5% of 3.92 kT while the Band Ep of the SAME fit is >1.5x higher
# AND the BB is subdominant. Fixed by jl.restore_best_fit() before the
# curve; stale tables fail here until regenerated.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('path,t', TABLES, ids=IDS)
def test_L20_epk_curve_not_displaced(path, t):
    need = ('BANDBB_EPK_CURVE', 'BANDBB_KT', 'BANDBB_EP', 'BANDBB_VALID')
    if not all(c in t.colnames for c in need):
        pytest.skip('no BANDBB curve columns')
    tb, bc = _blocks(t)
    bad = []
    for r in tb:
        if not bool(r['BANDBB_VALID']):
            continue
        epk, kt, ep = (_f(r, 'BANDBB_EPK_CURVE'), _f(r, 'BANDBB_KT'),
                       _f(r, 'BANDBB_EP'))
        if not all(np.isfinite(v) for v in (epk, kt, ep)):
            continue
        bump = 3.92 * kt
        if abs(epk - bump) / bump < 0.05 and ep > 1.5 * epk:
            bad.append(f'blk{r[bc]} EPK_CURVE={epk:.1f}~3.92kT={bump:.1f} '
                       f'but Band Ep={ep:.1f}')
    if bad:
        _xfail_if_known_stale('L20', path)
    assert not bad, f'{path}: EPK_CURVE stuck on the BB bump (L20): {bad}'


# ---------------------------------------------------------------------------
# L13 (081224 reconciliation): our Stage-2 binning independently reproduces
# Li & Zhang 2021's published Bayesian-block edges (1.896, 5.424, 12.502 s)
# to 3 decimals. Guard the committed blocks file against silent regeneration
# drift.
# ---------------------------------------------------------------------------
def test_L13_binning_edges_bn081224887():
    f = os.path.join(BASE, 'results', 'clean_blocks_human_final',
                     'bb_blocks_spectral_bn081224887.ecsv')
    if not os.path.exists(f):
        pytest.skip('committed blocks file not present')
    t = Table.read(f)
    edges = np.unique(np.concatenate([np.asarray(t['T_START'], dtype=float),
                                      np.asarray(t['T_STOP'], dtype=float)]))
    for want in (1.896, 5.424, 12.502):
        assert np.min(np.abs(edges - want)) < 2e-3, (
            f'published edge {want} s (Li & Zhang 2021) not found in '
            f'committed blocks — binning drifted')


# ---------------------------------------------------------------------------
# L24 (130518A): an evolving component rails in the integrated fit. If ANY
# resolved block has a VALID, significant Band+BB kT while the T_INT BB sits
# railed at the 1 keV floor, the T_INT fit is broken and must not be read as
# "no integrated thermal". xfail-ledgered until the T_INT re-seeding fix.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('path,t', TABLES, ids=IDS)
def test_L24_tint_bb_rail_vs_resolved(path, t):
    need = ('BANDBB_KT', 'BANDBB_VALID', 'LRT_BANDBB_BAND')
    if not all(c in t.colnames for c in need):
        pytest.skip('no BANDBB columns')
    bc = next(c for c in ('BLOCK', 'BLK') if c in t.colnames)
    tint = t[np.asarray(t[bc]) < 0]
    if not len(tint):
        pytest.skip('no T_INT row')
    tint = tint[0]
    kt_tint = _f(tint, 'BANDBB_KT')
    if not np.isfinite(kt_tint) or kt_tint > 1.02:      # not railed at floor
        return
    resolved = t[np.asarray(t[bc]) >= 0]
    good = [r for r in resolved
            if bool(r['BANDBB_VALID'])
            and np.isfinite(_f(r, 'LRT_BANDBB_BAND'))
            and _f(r, 'LRT_BANDBB_BAND') >= 9.2
            and _f(r, 'BANDBB_KT') > 5.0]
    if good:
        _xfail_if_known_stale('L24', path)
    assert not good, (
        f'{path}: T_INT BB railed at kT={kt_tint:.2f} while '
        f'{len(good)} resolved blocks hold VALID significant kT — broken '
        f'T_INT fit read as a non-detection (L24)')


# ---------------------------------------------------------------------------
# L27 (bn090530760, 2026-08-10): the rail test must respect parameter
# geometry. A linear margin on a (30, 5e4) bound is a ~50 keV dead zone above
# the low bound: every simple model on a soft burst (Ep 36-136 keV) was
# falsely flagged railed, handing the blocks to extra-component winners and
# biasing the census against soft-burst nulls. Unit-test the gate directly.
# ---------------------------------------------------------------------------
def test_L27_rail_margin_respects_log_geometry():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        's10', os.path.join(BASE, 'scripts', '10_spectral_fit_burst.py'))
    s10 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s10)
    sp = {'prefix': 'BAND', 'pmap': {'ALPHA': 'alpha', 'EP': 'xp', 'BETA': 'beta'}}
    def res(ep):
        return {'status': 'OK',
                'params': {'alpha': {'val': -0.5}, 'xp': {'val': ep},
                           'beta': {'val': -2.4}}}
    # soft-but-interior peaks MUST be valid (all were falsely railed pre-fix)
    for ep in (36.0, 57.5, 70.4, 100.0):
        assert s10._fit_is_physical(sp, res(ep)), (
            f'Ep={ep} keV falsely flagged as railed (L27 linear-margin bug)')
    # genuinely-at-bound peaks must still be caught
    for ep in (30.1, 49900.0):
        assert not s10._fit_is_physical(sp, res(ep)), (
            f'Ep={ep} keV should be flagged as railed')


# ---------------------------------------------------------------------------
# L28 (2026-08-11; Tierney+2013 2013A&A...550A.102T, Ravasio+2019
# 2019A&A...625A..60R App. B): a feature is constrained by its in-band nuFnu
# turnover (3.92*kT or xb). Ravasio's App. B shows GBM fits with the feature
# below ~20 keV are artifact-prone (railed hard alpha1); such values are
# stamped EDGE_CONSTRAINED: retained in records, excluded from population
# statistics/promotion until the L28 checks pass. Unit-test the classifier.
# ---------------------------------------------------------------------------
def test_L28_edge_feature_class():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        's10', os.path.join(BASE, 'scripts', '10_spectral_fit_burst.py'))
    s10 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s10)
    fc = s10.edge_feature_class
    # the night-shift low-kT class: turnover deep below the trust boundary
    assert fc(kt=3.0)[0] == 'EDGE_CONSTRAINED'      # 11.8 keV (b16 tail, b17)
    assert fc(kt=4.5)[0] == 'EDGE_CONSTRAINED'      # 17.6 keV (b11, b15)
    # kT 5.6-6.1 -> 22-24 keV: above Ravasio's boundary, below the clear zone
    assert fc(kt=6.1)[0] == 'EDGE_MARGINAL'
    # comfortably in-band temperatures stay unstamped
    assert fc(kt=10.0)[0] == 'IN_BAND'              # 39.2 keV
    assert fc(kt=41.0)[0] == 'IN_BAND'              # the high-kT class (b18)
    # published anchor cases, break costume
    assert fc(xb=12.4)[0] == 'EDGE_CONSTRAINED'     # Ravasio 171010 (quarantined)
    assert fc(xb=93.6)[0] == 'IN_BAND'              # Ravasio 180720 Fig. 1
    # L25 one-feature consistency: kt and xb = 3.92*kt classify identically,
    # and the reported feature energy is the same number
    for kt in (2.0, 4.4, 5.1, 6.1, 9.0, 25.0):
        c_kt, e_kt = fc(kt=kt)
        c_xb, e_xb = fc(xb=3.92 * kt)
        assert c_kt == c_xb and abs(e_kt - e_xb) < 1e-9, (
            f'kT={kt}: BB and break costumes classify differently (L25 breach)')
    # degenerate inputs fail closed
    assert fc()[0] == 'NO_FEATURE'
    assert fc(kt=float('nan'))[0] == 'NO_FEATURE'
    # exact boundaries (Codex audit 2026-08-11): 20 keV is MARGINAL (the
    # quarantine is < 20), 30 keV is IN_BAND ([20,30) marginal zone)
    assert fc(xb=19.999)[0] == 'EDGE_CONSTRAINED'
    assert fc(xb=20.0)[0] == 'EDGE_MARGINAL'
    assert fc(xb=29.999)[0] == 'EDGE_MARGINAL'
    assert fc(xb=30.0)[0] == 'IN_BAND'
    # dual input is the caller's L25 decision — must raise, never silently
    # prefer kT (Codex audit 2026-08-11)
    import pytest
    with pytest.raises(ValueError):
        fc(kt=5.0, xb=20.0)
