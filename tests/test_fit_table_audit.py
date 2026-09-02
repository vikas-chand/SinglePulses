"""The four countable step-6 checks are code, and the code reproduces the verified audit.

Born 2026-09-02 from the #21 step-6 gate: five counts presented to the PI were refuted, and
the numbers-verifier's re-derivation on the pre-widening table (sha256 368aa01e…, quarantined
under _superseded_beta5_20260902) became the reference. These tests pin dev/fit_table_audit.py
to that verified re-derivation where the table is on disk, and to invariants that must hold on
ANY promoted table (the light-tier doctrine of tests/test_lessons.py: a failure on a table is
the test doing its job).
"""
import glob
import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'dev'))
import fit_table_audit as fta  # noqa: E402

REF = os.path.join(BASE, 'results', 'convention_check', 'bn110920546', '_superseded_beta5_20260902', 'spectral_fits.ecsv')
REF_SHA = '368aa01e3dbecb2e202a1fe92b169bc57c00f4322c8461c46feb369fa2b74f92'
PROMOTED = sorted(glob.glob(os.path.join(BASE, 'results', 'convention_check', 'bn1109*', 'spectral_fits.ecsv')))


def _blocks(counts, name, denominator, basis=None):
    hit = [c for c in counts if c['name'] == name and c['denominator'] == denominator and c['basis'] == basis]
    assert len(hit) == 1, (name, denominator, basis)
    return hit[0]


def test_engine_constants_parse_from_source():
    specs = fta.engine_specs()
    names = {n for n, _, _ in specs}
    assert len(specs) == 24, len(specs)
    parents = fta.engine_nested_parents()
    assert len(parents) == 17
    assert {'DSBPL', 'DSBPLfree', 'SBPLfree', 'BandR+CPL'} <= (names - set(parents) - {'Band', 'CPL', 'SBPL'})
    bounds, eac = fta.engine_bounds()
    assert eac == (0.8, 1.2) and 'BAND' in bounds and bounds['BAND']['BETA'][0] <= -5.0


@pytest.mark.skipif(not os.path.exists(REF), reason='reference table not on disk')
def test_reproduces_the_verified_numbers_qc_on_368aa01e():
    a = fta.audit_table(REF)
    if a['table_sha256'] != REF_SHA:
        pytest.skip('reference table changed sha; regression values no longer bind')
    rows = {r['block']: r for r in a['rows']}
    assert all(r['argmin_matches_engine'] for r in a['rows']), 'gated argmin must equal BEST_AIC_MODEL'
    c = a['counts']
    assert _blocks(c, 'decisive', 'time_resolved', 'argmin')['blocks'] == [0, 8]
    assert _blocks(c, 'decisive', 'time_resolved', 'adopted')['blocks'] == [0, 2, 4, 6, 8]
    assert _blocks(c, 'tracked', 'time_resolved', 'argmin')['k'] == 0
    assert _blocks(c, 'ties', 'all_blocks')['k'] == 9 and _blocks(c, 'ties', 'time_resolved')['k'] == 8
    assert _blocks(c, 'bic_agrees_adopted', 'all_blocks', 'adopted')['k'] == 10
    assert rows[0]['fail_cells'] == ['BandR+CPL'] and all(not rows[b]['fail_cells'] for b in rows if b != 0)
    assert {rows[b]['adopted'] for b in (2, 4, 6, 8)} == {'CPL+PL', 'CPL+BB'}
    eac_b0 = [b for b, r in rows.items() if any(x['param'] == 'EAC_B0' and x['bound'] == 'LOWER' for x in r['rails_adopted'])]
    assert len(eac_b0) == 9, eac_b0
    assert a['aic_offset']['constant'] and abs(a['aic_offset']['mean'] - 6.0) < 1e-3
    assert rows[10]['chain_gate_argmin']['verdict'] == 'UNDEFINED_NO_ANCESTOR'
    assert rows[3]['chain_gate_argmin']['verdict'] == 'UNDEFINED_ANCESTOR_GATE_FAILED'


@pytest.mark.skipif(not PROMOTED, reason='no promoted table on disk')
def test_invariants_on_promoted_tables():
    for p in PROMOTED:
        a = fta.audit_table(p)
        assert all(r['argmin_matches_engine'] for r in a['rows'] if r.get('argmin')), p
        for c in a['counts']:
            assert 0 <= c['k'] <= c['N'], c
            assert c['denominator'] in ('all_blocks', 'time_resolved')
        assert any(c['basis'] == 'argmin' for c in a['counts']) and any(c['basis'] == 'adopted' for c in a['counts'])
        assert a['aic_offset']['constant'], 'AIC offset should be a constant 2 x n_nuisance on this engine'


def test_claims_check_and_absolute_aic_lint():
    counts = [{'name': 'decisive', 'k': 2, 'N': 11, 'denominator': 'time_resolved', 'basis': 'argmin', 'model': None, 'blocks': [0, 8]}]
    out = fta.check_claims([
        {'name': 'decisive', 'k': 2, 'N': 11, 'denominator': 'time_resolved', 'basis': 'argmin', 'model': None},
        {'name': 'decisive', 'k': 5, 'N': 11, 'denominator': 'time_resolved', 'basis': 'argmin', 'model': None},
        {'name': 'decisive', 'k': 2, 'N': 12, 'denominator': 'all_blocks', 'basis': None, 'model': None},
    ], counts)
    assert [x['verdict'] for x in out] == ['MATCH', 'MISMATCH', 'UNVERIFIABLE']
    assert fta.lint_absolute_aic('the winner has AIC = 9697.09 here')
    assert not fta.lint_absolute_aic('ΔAIC = 15.20 vs CPL; dAIC 41.5; a margin in AIC of 3.7')
