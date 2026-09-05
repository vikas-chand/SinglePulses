#!/usr/bin/env python3
"""fit_table_audit.py -- the four countable step-6 checks, as CODE over a fit table.

Born 2026-09-02 from the #21 (bn110920546) step-6 gate, where five counts presented to the
PI were refuted (NR-45) and four auditors were registered as PROPOSED agents: NR-42 basis-set
declaration, NR-43 nuisance-parameter rail coverage, NR-44 margins-only reporting, NR-45
count-triple verification. Each is countable from the table and needs no judgement, so per
the enforcement hierarchy (code > hook > artifact > agent) they live here, not in an agent.

What it computes, per block, from the engine's own columns and the engine's own constants
(read from the engine source with `ast`, never re-typed -- NR-10):
  * the validity-gated candidate set (NR-26: <M>_AIC finite, <M>_VALID true, <M>_STATUS not
    FAIL/ERROR), the bare argmin (cross-checked against BEST_AIC_MODEL, loud on mismatch),
    the tie set (dAIC < 2 vs the winner, the PI's threshold), and the ADOPTED model per
    RULING A (fewest engine n_params within the tie set, then lowest AIC);
  * the runner-up margin (TRACKED construct, > 6) and the CHAIN-GATE verdict against the best
    simpler ancestor in NESTED_PARENTS (DECISIVE >= 10 / NOT_DECISIVE / UNDEFINED, with the
    two UNDEFINED flavours: no ancestor in the map vs every ancestor gate-failed) -- on BOTH
    bases, argmin and adopted, so no count can be quoted without its basis (NR-42);
  * the rail census: every PARAM_BOUNDS parameter and every EAC constant sitting on its bound,
    with direction, for the adopted and the argmin model -- because <M>_VALID tests shape
    parameters only and never the EACs (NR-43, SpectralFitting L32);
  * the AIC offset AIC - (N2LL + 2 n_params), measured per finite cell; it is a constant
    2 x n_nuisance on this engine, which is why absolutes are not reportable and margins are
    (NR-44, L33); plus `lint_absolute_aic()` for prose;
  * every count it reports carries its THREE COORDINATES -- denominator (all blocks vs
    time-resolved; BLOCK -1 is T_INT and is never a member of the time-resolved set), basis
    set, and model -- and `check_claims()` verifies a PRESENT block's claims against them
    (NR-45).

Outputs (beside the table unless --out-dir): FIT_TABLE_AUDIT_<trig>.json (everything, with the
table's sha256 and the engine's sha256) and FIT_TABLE_AUDIT_<trig>.md (the summary a PRESENT
block may quote). Light tier: numpy + astropy only. Never re-fits anything.
"""
import argparse
import ast
import datetime as _dt
import hashlib
import json
import os
import re
import sys

import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, 'scripts', '10_spectral_fit_burst.py')

TIE_DAIC = 2.0        # PI: dAIC < 2 is a tie
TRACKED_DAIC = 6.0    # PI ruling 2026-08-26/30: > 6 vs runner-up
DECISIVE_DAIC = 10.0  # PI ruling 3, 2026-08-30: >= 10 vs best simpler ancestor
RAIL_REL_TOL = 1e-4   # of the bound span; plus exact-equality check


# ----------------------------------------------------------------------------- engine constants
def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def engine_source(rev=None):
    """The engine's source text: the working file, or `git show <rev>:<path>` for the bounds in
    force when a table was fitted (verifier round 1, 2026-09-02: the quarantined 368aa01e table
    was fitted under the -5 beta floor; auditing it against today's -10 floor hid 10 rails)."""
    if rev:
        import subprocess
        rel = os.path.relpath(ENGINE, ROOT)
        out = subprocess.run(['git', 'show', f'{rev}:{rel}'], cwd=ROOT, capture_output=True, text=True)
        if out.returncode != 0:
            sys.exit(f'ERROR: cannot read the engine at revision {rev}: {out.stderr.strip()}')
        return out.stdout
    with open(ENGINE, encoding='utf-8') as fh:
        return fh.read()


def _engine_tree(rev=None):
    return ast.parse(engine_source(rev), ENGINE)


def engine_specs(tree=None):
    """[(name, prefix, n_params)] from every spec dict in the engine (NR-10)."""
    tree = tree or _engine_tree()
    out, seen = [], set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        d = {}
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant) and k.value in ('name', 'prefix', 'n_params'):
                d[k.value] = v.value
        if {'name', 'prefix', 'n_params'} <= set(d) and d['name'] not in seen:
            seen.add(d['name'])
            out.append((d['name'], d['prefix'], int(d['n_params'])))
    if not out:
        sys.exit('ERROR: no model spec dicts found in the engine')
    return out


def _assigned_literal(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    sys.exit(f'ERROR: {name} not found in the engine')


def engine_nested_parents(tree=None):
    """{child name: [parent names]} from NESTED_PARENTS (17 children; roots absent)."""
    tree = tree or _engine_tree()
    return {child: list(parents) for child, parents in _assigned_literal(tree, 'NESTED_PARENTS')}


def engine_bounds(tree=None):
    tree = tree or _engine_tree()
    return _assigned_literal(tree, 'PARAM_BOUNDS'), tuple(_assigned_literal(tree, 'EFFAREA_BOUNDS'))


def ancestors_closure(name, parents):
    """All ancestors of `name` through NESTED_PARENTS (transitive)."""
    out, stack = [], list(parents.get(name, []))
    while stack:
        p = stack.pop()
        if p not in out:
            out.append(p)
            stack.extend(parents.get(p, []))
    return out


# ----------------------------------------------------------------------------- per-row logic
def _finite(x):
    try:
        return x is not None and np.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def model_valid(row, prefix, cols):
    if f'{prefix}_AIC' not in cols or not _finite(row[f'{prefix}_AIC']):
        return False
    if f'{prefix}_VALID' in cols and not bool(row[f'{prefix}_VALID']):
        return False
    if f'{prefix}_STATUS' in cols and str(row[f'{prefix}_STATUS']).upper() in ('FAIL', 'ERROR'):
        return False
    return True


def _at_bound(v, lo, hi):
    if not _finite(v):
        return None
    v = float(v)
    tol = RAIL_REL_TOL * (hi - lo)
    if v == lo or abs(v - lo) <= tol:
        return 'LOWER'
    if v == hi or abs(v - hi) <= tol:
        return 'UPPER'
    return None


def rails_for(row, prefix, cols, bounds, eac_bounds, eac_dets):
    """[(param, value, LOWER|UPPER|LOWER_ERR|UPPER_ERR, kind)] for one model in one row.
    kind = shape | nuisance | error-bar. LOWER_ERR/UPPER_ERR: the value is off the bound but its
    MINOS error bar terminates on it (verifier round 1: blk 4/7 kT with the lower error ending
    exactly at the 1 keV floor -- a constraint from the bound, not from the data)."""
    out = []
    for par, (lo, hi) in bounds.get(prefix, {}).items():
        c = f'{prefix}_{par}'
        if c in cols:
            d = _at_bound(row[c], lo, hi)
            if d:
                out.append((par, float(row[c]), d, 'shape'))
                continue
            v = row[c]
            if f'{c}_NEG_ERR' in cols and f'{c}_POS_ERR' in cols and _finite(v) and _finite(row[f'{c}_NEG_ERR']) and _finite(row[f'{c}_POS_ERR']):
                v = float(v); ne = abs(float(row[f'{c}_NEG_ERR'])); pe = abs(float(row[f'{c}_POS_ERR']))
                tol = RAIL_REL_TOL * (hi - lo)
                if v - ne <= lo + tol:
                    out.append((par, v, 'LOWER_ERR', 'error-bar'))
                elif v + pe >= hi - tol:
                    out.append((par, v, 'UPPER_ERR', 'error-bar'))
    for det in eac_dets:
        c = f'{prefix}_EAC_{det.upper()}'
        if c in cols:
            d = _at_bound(row[c], *eac_bounds)
            if d:
                out.append((f'EAC_{det.upper()}', float(row[c]), d, 'nuisance'))
    return out


def chain_gate(model, aic_of, valid_of, parents):
    """(verdict, ancestor, dAIC). Verdict in DECISIVE / NOT_DECISIVE / UNDEFINED_NO_ANCESTOR /
    UNDEFINED_ANCESTOR_GATE_FAILED / ROOT."""
    if model not in parents:
        roots = {m for ps in parents.values() for m in ps} - set(parents)
        return ('ROOT' if model in roots else 'UNDEFINED_NO_ANCESTOR'), None, None
    anc = ancestors_closure(model, parents)
    valid_anc = [a for a in anc if valid_of.get(a)]
    if not valid_anc:
        return 'UNDEFINED_ANCESTOR_GATE_FAILED', None, None
    best = min(valid_anc, key=lambda a: aic_of[a])
    d = aic_of[best] - aic_of[model]
    return ('DECISIVE' if d >= DECISIVE_DAIC else 'NOT_DECISIVE'), best, float(d)


BB_PEAK_FACTOR = 3.92   # nuFnu peak of a Planck spectrum (engine constant of the same name)
EDGE_TRUST_KEV = 20.0   # L28: below this the turnover is EDGE_CONSTRAINED
EDGE_CLEAR_KEV = 30.0   # L28: 20-30 EDGE_MARGINAL; above IN_BAND


def edge_stamp(kt, nai_low):
    """L28 stamp for a blackbody: where its nuFnu peak (3.92 kT) sits relative to the NaI band."""
    if not _finite(kt):
        return None
    pk = BB_PEAK_FACTOR * float(kt)
    if pk < nai_low:
        return 'BELOW_BAND'
    if pk < EDGE_TRUST_KEV:
        return 'EDGE_CONSTRAINED'
    if pk < EDGE_CLEAR_KEV:
        return 'EDGE_MARGINAL'
    return 'IN_BAND'


def audit_row(row, cols, specs, parents, bounds, eac_bounds, eac_dets, nai_low=8.1):
    aic_of, valid_of, nparams = {}, {}, {}
    for name, prefix, k in specs:
        valid_of[name] = model_valid(row, prefix, cols)
        nparams[name] = k
        if valid_of[name]:
            aic_of[name] = float(row[f'{prefix}_AIC'])
    cand = sorted(aic_of, key=lambda m: aic_of[m])
    eng = str(row['BEST_AIC_MODEL']) if 'BEST_AIC_MODEL' in cols else None
    rec = {'block': int(row['BLOCK']), 'n_candidates': len(cand),
           'engine_best_aic': eng, 'engine_best_valid': (valid_of.get(eng) if eng in valid_of else None),
           'engine_best_bic': str(row['BEST_BIC_MODEL']) if 'BEST_BIC_MODEL' in cols else None}
    # all-models rail census (the per-model statement the numbers-QC makes, e.g. SBPL_BETA on the floor in 10/12 rows)
    pre = {n: p for n, p, _ in specs}
    rec['rails_all'] = {n: [{'param': p_, 'value': v, 'bound': d, 'kind': kind} for p_, v, d, kind in rails_for(row, pre[n], cols, bounds, eac_bounds, eac_dets)]
                        for n in pre if f'{pre[n]}_AIC' in cols and _finite(row[f'{pre[n]}_AIC'])}
    rec['rails_all'] = {n: r for n, r in rec['rails_all'].items() if r}
    if not cand:
        rec.update(argmin=None, adopted=None, tie_set=[], runner_up_margin=None)
        return rec
    argmin = cand[0]
    tie = [m for m in cand if aic_of[m] - aic_of[argmin] < TIE_DAIC]
    adopted = sorted(tie, key=lambda m: (nparams[m], aic_of[m]))[0]
    margin = (aic_of[cand[1]] - aic_of[argmin]) if len(cand) > 1 else None
    rec.update(argmin=argmin, argmin_matches_engine=(rec['engine_best_aic'] == argmin),
               tie_set=tie, is_tie=len(tie) > 1, adopted=adopted, adopted_n_params=nparams[adopted],
               runner_up=cand[1] if len(cand) > 1 else None, runner_up_margin=margin,
               tracked=(margin is not None and margin > TRACKED_DAIC),
               bic_agrees_adopted=(rec['engine_best_bic'] == adopted))
    for basis, m in (('argmin', argmin), ('adopted', adopted)):
        v, anc, d = chain_gate(m, aic_of, valid_of, parents)
        prefix = dict((n, p) for n, p, _ in specs)[m]
        rec[f'chain_gate_{basis}'] = {'model': m, 'verdict': v, 'ancestor': anc, 'dAIC': d}
        rec[f'rails_{basis}'] = [{'param': p, 'value': val, 'bound': dirn, 'kind': kind}
                                 for p, val, dirn, kind in rails_for(row, prefix, cols, bounds, eac_bounds, eac_dets)]
        kt_col = f'{prefix}_KT'
        rec[f'edge_{basis}'] = ({'kT': float(row[kt_col]), 'peak_keV': BB_PEAK_FACTOR * float(row[kt_col]), 'stamp': edge_stamp(row[kt_col], nai_low)}
                                if kt_col in cols and _finite(row[kt_col]) else None)
    rec['fail_cells'] = [name for name, prefix, _ in specs
                         if f'{prefix}_STATUS' in cols and str(row[f'{prefix}_STATUS']).upper() in ('FAIL', 'ERROR')]
    return rec


def aic_offsets(t, specs):
    offs = []
    for row in t:
        for name, prefix, k in specs:
            a, n = f'{prefix}_AIC', f'{prefix}_N2LL'
            if a in t.colnames and n in t.colnames and _finite(row[a]) and _finite(row[n]):
                offs.append(float(row[a]) - (float(row[n]) + 2 * k))
    offs = np.array(offs)
    return {'n_cells': int(offs.size), 'mean': float(offs.mean()) if offs.size else None,
            'std': float(offs.std()) if offs.size else None,
            'constant': bool(offs.size and np.ptp(offs) < 1e-3)}


# ----------------------------------------------------------------------------- counts with coordinates
def _count(name, members, N_all, N_tr, basis=None, model=None):
    tr = [b for b in members if b != -1]
    return [{'name': name, 'k': len(members), 'N': N_all, 'denominator': 'all_blocks', 'basis': basis, 'model': model, 'blocks': members},
            {'name': name, 'k': len(tr), 'N': N_tr, 'denominator': 'time_resolved', 'basis': basis, 'model': model, 'blocks': tr}]


def build_counts(rows):
    blocks = [r['block'] for r in rows]
    N_all, N_tr = len(blocks), len([b for b in blocks if b != -1])
    counts = []
    counts += _count('ties', [r['block'] for r in rows if r.get('is_tie')], N_all, N_tr)
    counts += _count('tracked', [r['block'] for r in rows if r.get('tracked')], N_all, N_tr, basis='argmin')
    for basis in ('argmin', 'adopted'):
        cg = f'chain_gate_{basis}'
        for verdict in ('DECISIVE', 'NOT_DECISIVE', 'UNDEFINED_NO_ANCESTOR', 'UNDEFINED_ANCESTOR_GATE_FAILED', 'ROOT'):
            counts += _count(verdict.lower(), [r['block'] for r in rows if r.get(cg) and r[cg]['verdict'] == verdict], N_all, N_tr, basis=basis)
        counts += _count('any_rail', [r['block'] for r in rows if r.get(f'rails_{basis}')], N_all, N_tr, basis=basis)
        counts += _count('eac_rail', [r['block'] for r in rows if any(x['kind'] == 'nuisance' for x in r.get(f'rails_{basis}', []))], N_all, N_tr, basis=basis)
        counts += _count('shape_rail', [r['block'] for r in rows if any(x['kind'] == 'shape' for x in r.get(f'rails_{basis}', []))], N_all, N_tr, basis=basis)
    counts += _count('bic_agrees_adopted', [r['block'] for r in rows if r.get('bic_agrees_adopted')], N_all, N_tr, basis='adopted')
    counts += _count('argmin_mismatch_engine', [r['block'] for r in rows if r.get('argmin') and not r.get('argmin_matches_engine')], N_all, N_tr, basis='argmin')
    counts += _count('engine_winner_invalid', [r['block'] for r in rows if r.get('engine_best_aic') and r.get('engine_best_valid') is False], N_all, N_tr, basis='argmin')
    for basis in ('argmin', 'adopted'):
        counts += _count('errorbar_on_bound', [r['block'] for r in rows if any(x['kind'] == 'error-bar' for x in r.get(f'rails_{basis}', []))], N_all, N_tr, basis=basis)
        for st in ('BELOW_BAND', 'EDGE_CONSTRAINED', 'EDGE_MARGINAL', 'IN_BAND'):
            counts += _count(f'bb_{st.lower()}', [r['block'] for r in rows if r.get(f'edge_{basis}') and r[f'edge_{basis}']['stamp'] == st], N_all, N_tr, basis=basis)
    counts += _count('fail_cells_rows', [r['block'] for r in rows if r.get('fail_cells')], N_all, N_tr)
    return counts


def check_claims(claims, counts):
    """claims: [{name, k, N, denominator, basis?, model?}] -> MATCH / MISMATCH / UNVERIFIABLE per claim."""
    out = []
    for c in claims:
        hits = [x for x in counts if x['name'] == c.get('name') and x['denominator'] == c.get('denominator')
                and x.get('basis') == c.get('basis') and x.get('model') == c.get('model')]
        if not hits:
            out.append(dict(c, verdict='UNVERIFIABLE', reason='no count with these coordinates'))
            continue
        h = hits[0]
        ok = (c.get('k') == h['k'] and c.get('N') == h['N'])
        out.append(dict(c, verdict='MATCH' if ok else 'MISMATCH', audited_k=h['k'], audited_N=h['N']))
    return out


_ABS_AIC = re.compile(r'(?<![ΔdD])(?<!delta )\b[AB]IC\b[^0-9\n]{0,12}(\d{3,}(?:\.\d+)?)')


def lint_absolute_aic(text):
    """Snippets rendering an ABSOLUTE AIC/BIC (>= 100) rather than a margin (NR-44)."""
    return [m.group(0) for m in _ABS_AIC.finditer(text)
            if not re.search(r'(Δ|\bd|delta|margin)\s*[AB]IC', text[max(0, m.start() - 12):m.start() + 4])]


# ----------------------------------------------------------------------------- driver
def audit_table(path, engine_rev=None):
    """engine_rev: git revision whose engine bounds/constants were in force when the table was
    fitted (default: the working file). The table itself records no bounds, so the caller MUST
    pass the fit-time revision for quarantined/older tables; the JSON says which was used."""
    t = Table.read(path)
    cols = t.colnames
    src = engine_source(engine_rev)
    tree = ast.parse(src, ENGINE)
    specs, parents = engine_specs(tree), engine_nested_parents(tree)
    bounds, eac_bounds = engine_bounds(tree)
    eac_dets = []
    if 'EAC_DETS' in cols:
        raw = str(t['EAC_DETS'][0])
        eac_dets = [d.strip() for d in re.split(r'[,;\s]+', raw) if d.strip() and d.strip() != '--']
    sidecar, nai_low = {}, 8.1
    sc = os.path.join(os.path.dirname(os.path.abspath(path)), 'spectral_fits.json')
    if os.path.exists(sc):
        try:
            with open(sc) as fh:
                sidecar = json.load(fh)
            nr = sidecar.get('NAI_RANGES')
            if isinstance(nr, (list, tuple)) and nr and isinstance(nr[0], (list, tuple)):
                nai_low = float(nr[0][0])
            elif isinstance(nr, (list, tuple)) and nr:
                nai_low = float(nr[0])
        except (OSError, ValueError, TypeError):
            pass
    rows = [audit_row(r, cols, specs, parents, bounds, eac_bounds, eac_dets, nai_low) for r in t]
    counts = build_counts(rows)
    trig = (str(t['TRIGGER_NAME'][0]) if 'TRIGGER_NAME' in cols else sidecar.get('trigger')
            or os.path.basename(os.path.dirname(os.path.abspath(path))))
    return {'schema': 'two_breaks.fit_table_audit.v1', 'trigger': trig,
            'table': os.path.abspath(path), 'table_sha256': _sha256(path),
            'engine': os.path.relpath(ENGINE, ROOT), 'engine_sha256': hashlib.sha256(src.encode('utf-8')).hexdigest(),
            'engine_rev': engine_rev or 'WORKING_FILE',
            'bounds_note': ('rail census valid only for tables fitted under the engine at engine_rev; the table records no bounds '
                            '(verifier round 1, 2026-09-02)'),
            'nai_low_keV': nai_low,
            'generated_utc': _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'thresholds': {'tie_dAIC': TIE_DAIC, 'tracked_dAIC': TRACKED_DAIC, 'decisive_dAIC': DECISIVE_DAIC},
            'n_models': len(specs), 'n_nested_children': len(parents), 'eac_dets': eac_dets,
            'ancestorless_models': sorted(n for n, _, _ in specs if n not in parents and n not in {m for ps in parents.values() for m in ps}),
            'aic_offset': aic_offsets(t, specs), 'rows': rows, 'counts': counts}


def render_md(a):
    L = [f"# FIT-TABLE AUDIT — {a['trigger']}", '',
         f"- table `{os.path.relpath(a['table'], ROOT)}` sha256 `{a['table_sha256'][:16]}…`; engine @ {a['engine_rev']} sha256 `{a['engine_sha256'][:16]}…`; NaI edge {a['nai_low_keV']} keV; {a['generated_utc']}",
         f"- {a['bounds_note']}",
         f"- {a['n_models']} models; {a['n_nested_children']} nested children; ancestor-less: {', '.join(a['ancestorless_models'])}",
         f"- AIC − (N2LL + 2·n_params) = {a['aic_offset']['mean']:+.4f} in {a['aic_offset']['n_cells']} finite cells ({'CONSTANT' if a['aic_offset']['constant'] else 'NOT constant'}) → quote MARGINS, never absolutes (NR-44)",
         '', '## Every count with its three coordinates (NR-45)', '',
         '| count | k/N | denominator | basis | blocks |', '|---|---|---|---|---|']
    for c in a['counts']:
        if c['k'] or c['name'] in ('ties', 'tracked', 'decisive'):
            L.append(f"| {c['name']} | {c['k']}/{c['N']} | {c['denominator']} | {c['basis'] or '—'} | {c['blocks']} |")
    L += ['', '## Per block', '', '| block | argmin (=engine?) | tie set | adopted (k) | runner-up margin | chain gate argmin | chain gate adopted | rails adopted | FAIL |', '|---|---|---|---|---|---|---|---|---|']
    for r in a['rows']:
        if r.get('argmin') is None:
            L.append(f"| {r['block']} | — | — | — | — | — | — | — | {r.get('fail_cells')} |"); continue
        cga, cgd = r['chain_gate_argmin'], r['chain_gate_adopted']
        f = lambda cg: f"{cg['verdict']}" + (f" vs {cg['ancestor']} ({cg['dAIC']:+.2f})" if cg['ancestor'] else '')
        rails = '; '.join(f"{x['param']}={x['value']:.4g} ({x['bound']})" for x in r['rails_adopted']) or '—'
        mg = '—' if r['runner_up_margin'] is None else f"{r['runner_up_margin']:.3f}"
        L.append(f"| {r['block']} | {r['argmin']} ({'✓' if r['argmin_matches_engine'] else '✗ MISMATCH vs ' + str(r['engine_best_aic'])}) | {len(r['tie_set'])} | {r['adopted']} ({r['adopted_n_params']}) | {mg} | {f(cga)} | {f(cgd)} | {rails} | {r['fail_cells'] or '—'} |")
    return '\n'.join(L) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--table', required=True)
    ap.add_argument('--out-dir', help='default: beside the table')
    ap.add_argument('--claims', help='JSON list of {name,k,N,denominator,basis,model} to verify (NR-45)')
    ap.add_argument('--engine-rev', help='git revision of the engine in force when the table was fitted (bounds/constants)')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args(argv)
    audit = audit_table(a.table, a.engine_rev)
    if a.claims:
        with open(a.claims) as fh:
            audit['claims'] = check_claims(json.load(fh), audit['counts'])
    out_dir = a.out_dir or os.path.dirname(os.path.abspath(a.table))
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"FIT_TABLE_AUDIT_{audit['trigger']}")
    with open(base + '.json', 'w') as fh:
        json.dump(audit, fh, indent=1)
    md = render_md(audit)
    with open(base + '.md', 'w') as fh:
        fh.write(md)
    if not a.quiet:
        print(md)
        if 'claims' in audit:
            for c in audit['claims']:
                print(f"CLAIM {c['name']} {c.get('k')}/{c.get('N')} [{c.get('denominator')}, {c.get('basis')}, {c.get('model')}] -> {c['verdict']}"
                      + (f" (audited {c['audited_k']}/{c['audited_N']})" if 'audited_k' in c else ''))
    bad = [r for r in audit['rows'] if r.get('argmin') and (not r['argmin_matches_engine'] or r.get('engine_best_valid') is False)]
    return 2 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
