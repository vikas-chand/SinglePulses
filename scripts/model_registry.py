#!/usr/bin/env python
"""
model_registry.py -- THE single source of truth for the spectral-model census
(Codex ultra audit CRITICAL #5/#6: scripts/10, 31 and the ad-hoc censuses each
had their own model lists / parent maps / selection rules, and scripts/31
silently converted every new-family winner to INCONCLUSIVE).

Defines, once:
  - the full 24-model prefix registry with display names and families;
  - the NESTED-PARENT map (a composite is admissible only if it beats EVERY
    nested parent by DAIC_GATE -- same map scripts/10's multistart uses);
  - the LOCKED selection doctrine (2026-06 framework):
      * a fit survives if VALID (physical, non-railed), STATUS OK, finite AIC,
        and (if composite) beats every parent by >= DAIC_GATE;
      * the block's WINNER is the min-AIC survivor ONLY when it beats the
        runner-up survivor by >= DAIC_GATE (top-two doctrine);
      * otherwise the block is INCONCLUSIVE (never silently assigned).

Import from the scripts dir (importlib, as the scripts do for each other) or
run:  python scripts/model_registry.py <spectral_fits.ecsv...>  for a census.
"""
import numpy as np

DAIC_GATE = 10.0          # locked ΔAIC≥10 doctrine (≡ LRT≥14 for 2 params)

# prefix -> (display name, family)
MODELS = {
    'BAND':      ('Band',        'single'),
    'CPL':       ('CPL',         'single'),
    'SBPL':      ('SBPL',        'single'),
    'DSBPL':     ('2SBPL',       'twobreak'),
    'SBPLF':     ('SBPLfree',    'single'),
    'DSBPLF':    ('2SBPLfree',   'twobreak'),
    'BANDBB':    ('Band+BB',     'thermal'),
    'CPLBB':     ('CPL+BB',      'thermal'),
    'SBPLBB':    ('SBPL+BB',     'thermal'),
    'BANDPL':    ('Band+PL',     'highe'),
    'BANDCPL':   ('Band+CPL',    'highe'),
    'CPLPL':     ('CPL+PL',      'highe'),
    'CPLCPL':    ('CPL+CPL',     'highe'),
    'SBPLPL':    ('SBPL+PL',     'highe'),
    'SBPLCPL':   ('SBPL+CPL',    'highe'),
    'BANDRCPL':  ('BandR+CPL',   'highe'),
    'BANDCUT':   ('BandxCut',    'cutoff'),
    'SBPLCUT':   ('SBPLxCut',    'cutoff'),
    'BANDBBPL':  ('Band+BB+PL',  'threecomp'),
    'BANDBBCPL': ('Band+BB+CPL', 'threecomp'),
    'CPLBBPL':   ('CPL+BB+PL',   'threecomp'),
    'CPLBBCPL':  ('CPL+BB+CPL',  'threecomp'),
    'SBPLBBPL':  ('SBPL+BB+PL',  'threecomp'),
    'SBPLBBCPL': ('SBPL+BB+CPL', 'threecomp'),
}

# composite prefix -> nested-parent prefixes (must beat EVERY parent by the gate)
PARENTS = {
    'BANDBB': ['BAND'], 'CPLBB': ['CPL'], 'SBPLBB': ['SBPL'],
    'BANDPL': ['BAND'], 'BANDCPL': ['BAND'],
    'CPLPL': ['CPL'], 'CPLCPL': ['CPL'],
    'SBPLPL': ['SBPL'], 'SBPLCPL': ['SBPL'],
    'BANDCUT': ['BAND'], 'SBPLCUT': ['SBPL'],
    'BANDRCPL': ['BAND'],
    'DSBPL': ['SBPL'], 'DSBPLF': ['SBPL'],
    'BANDBBPL': ['BANDBB', 'BANDPL'],
    'BANDBBCPL': ['BANDBB', 'BANDCPL'],
    'CPLBBPL': ['CPLBB', 'CPLPL'],
    'CPLBBCPL': ['CPLBB', 'CPLCPL'],
    'SBPLBBPL': ['SBPLBB', 'SBPLPL'],
    'SBPLBBCPL': ['SBPLBB', 'SBPLCPL'],
}

# scripts/10 NESTED_PARENTS equivalence (by display name) -- derived, one truth
NESTED_PARENTS_BY_NAME = [
    (MODELS[c][0], [MODELS[p][0] for p in ps]) for c, ps in PARENTS.items()
    if c not in ('DSBPL', 'DSBPLF')     # DSBPL has its own dedicated multistart
]


# ---------------------------------------------------------------------------
# DEGENERACY CLASSES (Vikas 2026-07-18): some model pairs are intrinsically
# degenerate over the fitted band — they re-adjust parameters to mimic each
# other, so a top-two AIC gap between them is structurally impossible and must
# NOT be read as "the data are ambiguous about the SHAPE". Declared a priori:
#   * 'extra_lowE_curvature': a thermal bump on a single-break continuum bends
#     nu-F-nu almost exactly like a second power-law break over the GBM band
#     (the draft's founding BB+SBPL <-> 2SBPL proxy). Distinguishing them needs
#     prompt LOW-energy coverage (XRT/optical) we do not have.
# The HIGH-E composites are deliberately NOT merged: above the peak an extra
# PL, a cutoff, and a saddle genuinely differ, and LLE/LAT sit there — that is
# exactly the regime where our band BREAKS the degeneracy.
# Census reports THREE levels: exact model (strict top-two), degeneracy class
# (top-two ACROSS classes; internal degeneracy reported separately), family.
# ---------------------------------------------------------------------------
DEGENERACY_CLASSES = {
    'extra_lowE_curvature': {'DSBPL', 'DSBPLF', 'BANDBB', 'CPLBB', 'SBPLBB'},
}


def class_of(prefix):
    """Degeneracy-class label for a prefix (its own name when not merged)."""
    for cname, members in DEGENERACY_CLASSES.items():
        if prefix in members:
            return cname
    return prefix


def _val(row, col):
    try:
        return float(row[col])
    except Exception:
        return float('nan')


def is_valid(row, prefix, cols):
    """VALID (physical) + STATUS OK + finite AIC for this prefix in this row."""
    vc, sc, ac = f'{prefix}_VALID', f'{prefix}_STATUS', f'{prefix}_AIC'
    if ac not in cols:
        return False
    okv = (vc not in cols) or str(row[vc]) in ('True', '1', '1.0')
    oks = (sc not in cols) or str(row[sc]).lower() in ('ok', 'converged',
                                                       'success', 'true')
    return okv and oks and np.isfinite(_val(row, ac))


def survivors(row, cols, daic=DAIC_GATE):
    """{prefix: AIC} of chain-gated, valid, finite fits in this row."""
    out = {}
    for p in MODELS:
        if not is_valid(row, p, cols):
            continue
        aic = _val(row, f'{p}_AIC')
        ok = True
        for par in PARENTS.get(p, []):
            if not is_valid(row, par, cols) or (_val(row, f'{par}_AIC') - aic) < daic:
                ok = False
                break
        if ok:
            out[p] = aic
    return out

def gated_winner(row, cols, daic=DAIC_GATE):
    """(winner_prefix | 'INCONCLUSIVE', top2_gap, n_survivors).

    The locked doctrine: min-AIC survivor wins ONLY when it beats the
    runner-up survivor by >= daic; otherwise INCONCLUSIVE. A single survivor
    wins by default (nothing to be confused with)."""
    sv = survivors(row, cols, daic)
    if not sv:
        return 'INCONCLUSIVE', float('nan'), 0
    order = sorted(sv.items(), key=lambda kv: kv[1])
    if len(order) == 1:
        return order[0][0], float('inf'), 1
    gap = order[1][1] - order[0][1]
    if gap >= daic:
        return order[0][0], gap, len(order)
    return 'INCONCLUSIVE', gap, len(order)


def class_gated_winner(row, cols, daic=DAIC_GATE):
    """(class_winner | 'INCONCLUSIVE', best_prefix_in_class, cross_class_gap,
    n_members_within_gate).

    Level-2 doctrine: each degeneracy CLASS is represented by its best (min
    AIC) gated survivor; the top-two gap is evaluated ACROSS classes. A class
    wins even when its members are internally indistinguishable — that
    internal degeneracy is returned as n_members_within (members of the
    winning class within `daic` of its best, i.e. how many flavors the data
    cannot separate)."""
    sv = survivors(row, cols, daic)
    if not sv:
        return 'INCONCLUSIVE', None, float('nan'), 0
    best_by_class = {}
    for p, aic in sv.items():
        c = class_of(p)
        if c not in best_by_class or aic < best_by_class[c][1]:
            best_by_class[c] = (p, aic)
    order = sorted(best_by_class.items(), key=lambda kv: kv[1][1])
    cname, (bp, baic) = order[0]
    members_within = sum(1 for p, a in sv.items()
                         if class_of(p) == cname and (a - baic) <= daic)
    if len(order) == 1:
        return cname, bp, float('inf'), members_within
    gap = order[1][1][1] - baic
    if gap >= daic:
        return cname, bp, gap, members_within
    return 'INCONCLUSIVE', bp, gap, members_within


def burst_admission(table, daic=DAIC_GATE):
    """BURST-LEVEL component admission (adopted by Vikas 2026-07-29; modeled on
    Burgess+2014 ApJ 784:17 §3.4, whose BB entered a burst's analysis only if
    it improved C-stat by >=10 in at least one bin — then was fit in EVERY bin).

    A composite is ADMITTED for this burst when >= 1 bin has it as a
    chain-gated survivor: VALID + STATUS OK + finite AIC + beats EVERY nested
    parent by >= daic (survivors() enforces exactly this). Admission does NOT
    require winning the bin — improvement over the parents suffices, per
    Burgess. Purpose: evolution/correlation studies (kT(t), Ep–kT, EC(t)) use
    the admitted-burst TRACKS across all bins instead of re-selecting bin by
    bin — mitigating the per-bin detectability selection that can imprint
    spurious parameter correlations. The strict per-bin census is unchanged.

    Returns {composite_prefix: n_bins_passing} for admitted composites."""
    cols = table.colnames
    counts = {}
    for r in table:
        try:
            blk = int(r['BLOCK'])
        except Exception:
            continue
        if blk < 0:
            continue                              # T_INT row
        for p in survivors(r, cols, daic):
            if p in PARENTS:                      # composites only
                counts[p] = counts.get(p, 0) + 1
    return counts


def component_track(table, prefix, param_cols, daic=DAIC_GATE):
    """Per-block parameter track for an (admitted) component: one entry per
    science bin with the requested parameter values/errors and a CONSTRAINED
    flag (VALID + STATUS OK + finite AIC in that bin — i.e. non-railed).
    Unconstrained bins are RETAINED, flagged False — the Burgess construction
    tracks the component everywhere and lets the flag carry the honesty.

    param_cols: iterable of column suffixes, e.g. ('KT', 'EP').
    Returns list of dicts: {block, t_mid, constrained, <col>: (val, err)}."""
    cols = table.colnames
    out = []
    for r in table:
        try:
            blk = int(r['BLOCK'])
        except Exception:
            continue
        if blk < 0:
            continue
        entry = {'block': blk,
                 't_mid': float(r['T_MID']) if 'T_MID' in cols else float('nan'),
                 'constrained': is_valid(r, prefix, cols)}
        for c in param_cols:
            v = _val(r, f'{prefix}_{c}')
            e = _val(r, f'{prefix}_{c}_ERR')
            entry[c] = (v, e)
        out.append(entry)
    return out


def census(tables, daic=DAIC_GATE):
    """Population census over astropy Tables of spectral_fits rows.

    Returns dict with per-block winners list, counts by model and family,
    and the ambiguity statistics the paper must headline."""
    winners = []
    for trig, t in tables:
        cols = t.colnames
        for r in t:
            try:
                blk = int(r['BLOCK'])
            except Exception:
                continue
            if blk < 0:
                continue                       # T_INT row
            w, gap, nsv = gated_winner(r, cols, daic)
            cw, cbest, cgap, cwithin = class_gated_winner(r, cols, daic)
            winners.append({'trigger': trig, 'block': blk,
                            'winner': w, 'top2_gap': gap, 'n_survivors': nsv,
                            'class_winner': cw, 'class_best_model': cbest,
                            'class_gap': cgap, 'class_members_within': cwithin})
    from collections import Counter
    by_model = Counter(w['winner'] for w in winners)
    by_class = Counter(w['class_winner'] for w in winners)
    by_family = Counter(
        MODELS[w['winner']][1] if w['winner'] in MODELS else 'inconclusive'
        for w in winners)
    n = len(winners)
    n_inc = by_model.get('INCONCLUSIVE', 0)
    n_cinc = by_class.get('INCONCLUSIVE', 0)
    # blocks where the CLASS is decisive but the exact flavor is not — the
    # "shape known, flavor degenerate" population (Vikas 2026-07-18)
    n_flavor_deg = sum(1 for w in winners
                       if w['class_winner'] != 'INCONCLUSIVE'
                       and w['winner'] == 'INCONCLUSIVE')
    return {
        'n_blocks': n,
        'n_inconclusive': n_inc,
        'frac_inconclusive': (n_inc / n) if n else float('nan'),
        'n_class_inconclusive': n_cinc,
        'frac_class_inconclusive': (n_cinc / n) if n else float('nan'),
        'n_flavor_degenerate': n_flavor_deg,
        'by_model': dict(by_model),
        'by_class': dict(by_class),
        'by_family': dict(by_family),
        'winners': winners,
    }


if __name__ == '__main__':
    import sys
    from astropy.table import Table
    tabs = [(f.split('/')[-2], Table.read(f, format='ascii.ecsv'))
            for f in sys.argv[1:]]
    c = census(tabs)
    print(f"blocks={c['n_blocks']}  INCONCLUSIVE={c['n_inconclusive']} "
          f"({100*c['frac_inconclusive']:.0f}%)")
    for k, v in sorted(c['by_model'].items(), key=lambda kv: -kv[1]):
        name = MODELS[k][0] if k in MODELS else k
        print(f"  {name:14s} {v}")
    print("families:", c['by_family'])
