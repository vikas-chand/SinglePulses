"""Every typed object we already write validates against its schema (the campaign ontology, step 1).

Born 2026-09-02 from the five-source harness comparison (§19 #4): objects were typed on disk
but no schema existed anywhere, so a missing key, a wrong enum, or a malformed hash was
invisible until a fresh agent tripped on it (the numbers-verifier transcribed n_params by hand;
the promotion receipt's sha fields were never checked). These tests are computational sensors:
every instance on disk of each object type must validate. Instances live under results/ and
notes/reconciliation/ (gitignored or not), so a failure here is the test doing its job on a
real product, never on a fixture.
"""
import glob
import json
import os

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDIR = os.path.join(BASE, 'dev', 'schemas')


def _schemas():
    out = {}
    for p in glob.glob(os.path.join(SDIR, '*.schema.json')):
        s = json.load(open(p))
        out[s['$id']] = s
    return out


SCHEMAS = _schemas()


REGISTRY = Registry().with_resources((uri, Resource.from_contents(s)) for uri, s in SCHEMAS.items())


def _validator(name):
    return Draft202012Validator(SCHEMAS[f'urn:two_breaks:{name}'], registry=REGISTRY)


def _errors(name, obj):
    return [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in _validator(name).iter_errors(obj)]


# Known deviations: FROZEN records (never edited by rule) that do not meet the contract. Listed,
# not fixed, exactly like tests/test_lessons.py's KNOWN_STALE: the suite stays green, the debt
# stays visible, and a NEW file must never appear here. (P0 records are immutable by Phase 0.)
KNOWN_DEVIATIONS = {
    'notes/reconciliation/bn090530760_P0_frozen.json': "burst field holds prose 'bn090530760 = GRB 090530B'; no predictions key (2026-08-10 pre-fit record)",
    'notes/reconciliation/bn170114917_P0_frozen.json': "burst field holds prose 'bn170114917 (GRB 170114A)'",
    'notes/reconciliation/bn081224887_harvest.json': "paper 24 has four GCN circulars joined by '/' in the bibcode field ('2008GCN..8723....1W/8725/8726/8739'); circulars belong to step 0, one bibcode per record",
    'notes/reconciliation/bn130215063_harvest.json': "malformed bibcode '2020ApSS.365..177Z' (18 chars; the '&' of Ap&SS dropped) — a citation that would fail at ADS; fix belongs to the harvest, not to this test",
}

CASES = [
    ('approvals_file', 'results/sweep106/*/APPROVALS.json', None),
    ('promotion_receipt', 'results/convention_check/*/promotion_receipts/*.json', None),
    ('fit_sidecar', 'results/convention_check/bn*/spectral_fits.json', None),
    ('burst_state', 'results/campaign/burst_state/*.json', None),
    ('harvest_manifest', 'notes/reconciliation/*_harvest.json', None),
    ('p0_frozen', 'notes/reconciliation/*_P0_frozen.json', None),
    ('fit_table_audit', 'results/**/FIT_TABLE_AUDIT_*.json', None),
]


def test_every_schema_is_itself_valid():
    assert len(SCHEMAS) >= 8
    for s in SCHEMAS.values():
        Draft202012Validator.check_schema(s)


@pytest.mark.parametrize('name,pattern,_', CASES, ids=[c[0] for c in CASES])
def test_instances_on_disk_validate(name, pattern, _):
    files = sorted(glob.glob(os.path.join(BASE, pattern), recursive=True))
    if not files:
        pytest.skip(f'no {name} instances on disk')
    bad, known = {}, {}
    for f in files:
        rel = os.path.relpath(f, BASE)
        try:
            obj = json.load(open(f))
        except json.JSONDecodeError as e:
            bad[os.path.relpath(f, BASE)] = [f'not JSON: {e}']
            continue
        errs = _errors(name, obj)
        if errs and rel in KNOWN_DEVIATIONS:
            known[rel] = KNOWN_DEVIATIONS[rel]
        elif errs:
            bad[rel] = errs[:5]
    assert not bad, json.dumps(bad, indent=1)[:4000]
    if known:
        print(f'KNOWN DEVIATIONS ({name}): ' + '; '.join(f'{k}: {v}' for k, v in known.items()))
