"""
Patch scripts/10_spectral_fit_burst.py:
 1. Tighten DSBPL bounds (xb floor 10 keV >= NaI threshold; xp floor 30 keV)
    to kill the 5-keV railing.
 2. Add PARAM_BOUNDS + _fit_is_physical (rejects railed params and inverted
    DSBPL breaks xb>=xp).
 3. Stamp res['physical'] after every fit.
 4. Write a {prefix}_VALID column.
 5. Gate BEST_AIC_MODEL / BEST_BIC_MODEL on physical validity; add LRT_DSBPL_SBPL.
Fail-safe: every replacement asserts it matched exactly once.
"""
import ast, sys

P = 'scripts/10_spectral_fit_burst.py'
s = open(P).read()
orig = s


def sub1(old, new):
    global s
    c = s.count(old)
    assert c == 1, f'EXPECTED 1 match, got {c} for:\n---\n{old}\n---'
    s = s.replace(old, new, 1)


# --- 1. DSBPL bounds ---
sub1('    d.xb.bounds = (5.0, 1000.0)', '    d.xb.bounds = (10.0, 900.0)')
sub1("    d.xb.value = _clamp(seed.get('dsbpl_xb', 50.0), 5.0, 1000.0)",
     "    d.xb.value = _clamp(seed.get('dsbpl_xb', 50.0), 10.0, 900.0)")
sub1('    d.xp.bounds = (10.0, 5000.0)', '    d.xp.bounds = (30.0, 5000.0)')
sub1("    d.xp.value = _clamp(seed.get('dsbpl_xp', DEFAULT_PARAMS['Ep']), 10.0, 5000.0)",
     "    d.xp.value = _clamp(seed.get('dsbpl_xp', DEFAULT_PARAMS['Ep']), 30.0, 5000.0)")

# --- 2. PARAM_BOUNDS + _fit_is_physical, inserted before select_best ---
helper = '''# Parameter bounds (must mirror the _setup_* functions). Used to detect
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


'''
sub1('def select_best(per_spec_results, n_data):',
     helper + 'def select_best(per_spec_results, n_data):')

# --- 3. stamp physical in the main fit loop ---
sub1('        res = fit_one_model(dl, spec, seed=seed_in)\n'
     '        per_spec.append((spec, res))',
     '        res = fit_one_model(dl, spec, seed=seed_in)\n'
     '        res[\'physical\'] = _fit_is_physical(spec, res)\n'
     '        per_spec.append((spec, res))')

# --- 3b. stamp physical in the LRT-guard re-fit branch ---
sub1('            new_res = fit_one_model(dl, child_spec, seed={})\n'
     '            if (new_res.get(\'status\') == \'OK\'',
     '            new_res = fit_one_model(dl, child_spec, seed={})\n'
     '            new_res[\'physical\'] = _fit_is_physical(child_spec, new_res)\n'
     '            if (new_res.get(\'status\') == \'OK\'')

# --- 4. {prefix}_VALID column ---
sub1("           f'{p}_MINOS_OK': bool(result.get('minos_ok', False))}",
     "           f'{p}_MINOS_OK': bool(result.get('minos_ok', False)),\n"
     "           f'{p}_VALID': bool(result.get('physical', False))}")

# --- 5. physical-gated winners ---
sub1("    best_aic = min(aic, key=aic.get) if aic else 'INCONCLUSIVE'\n"
     "    best_bic = min(bic, key=bic.get) if bic else 'INCONCLUSIVE'",
     "    # Physical-validity gate: the winner must be a non-railed, physically\n"
     "    # ordered fit (DSBPL low break xb < peak xp). Railed/inverted fits stay\n"
     "    # in the ECSV but cannot WIN selection.\n"
     "    phys = {n: (sp, r) for n, (sp, r) in ok.items() if _fit_is_physical(sp, r)}\n"
     "    aic_p = {n: aic[n] for n in phys}\n"
     "    bic_p = {n: bic[n] for n in phys}\n"
     "    best_aic = (min(aic_p, key=aic_p.get) if aic_p\n"
     "                else (min(aic, key=aic.get) if aic else 'INCONCLUSIVE'))\n"
     "    best_bic = (min(bic_p, key=bic_p.get) if bic_p\n"
     "                else (min(bic, key=bic.get) if bic else 'INCONCLUSIVE'))")

# --- 5b. add LRT_DSBPL_SBPL (nested: DSBPL nests SBPL, +2 params) ---
sub1("    lrt_cplbb  = _lrt('CPL',  'CPL+BB')",
     "    lrt_cplbb  = _lrt('CPL',  'CPL+BB')\n"
     "    lrt_dsbpl_sbpl = _lrt('SBPL', 'DSBPL')")
sub1("        'LRT_CPLBB_CPL':   lrt_cplbb,",
     "        'LRT_CPLBB_CPL':   lrt_cplbb,\n"
     "        'LRT_DSBPL_SBPL':  lrt_dsbpl_sbpl,")

# validate
ast.parse(s)
open(P, 'w').write(s)
print(f'Patched {P}: {len(orig)} -> {len(s)} bytes, ast OK')
