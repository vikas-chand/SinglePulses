"""Invariants of the approved background catalog (the gated Stage-1 output).

Mirrors the scripts/36 QC: coverage vs the 106-burst sample, window ordering,
source-in-gap, the 5-40 s near-edge margin band, and approval stamps.
"""
import os
import pytest
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(BASE, 'results', 'background_intervals.ecsv')
SAMPLE = os.path.join(BASE, 'results', 'single_pulse_grbs.ecsv')


@pytest.fixture(scope='module')
def cat():
    if not os.path.exists(CAT):
        pytest.skip('approved catalog not present')
    return Table.read(CAT, format='ascii.ecsv')


def test_full_sample_coverage(cat):
    sample = Table.read(SAMPLE, format='ascii.ecsv')
    want = {str(r['TRIGGER_NAME']).strip() for r in sample}
    have = {str(r['TRIGGER_NAME']).strip() for r in cat}
    assert want <= have, f'missing bursts: {sorted(want - have)[:5]}'


def test_no_duplicate_rows(cat):
    pairs = [(str(r['TRIGGER_NAME']).strip(), str(r['DETECTOR']).strip())
             for r in cat]
    assert len(pairs) == len(set(pairs))


def test_ordering_and_source_in_gap(cat):
    for r in cat:
        p0, p1 = float(r['BKG_NEG_START']), float(r['BKG_NEG_STOP'])
        q0, q1 = float(r['BKG_POS_START']), float(r['BKG_POS_STOP'])
        s1, s2 = float(r['SRC_START']), float(r['SRC_STOP'])
        assert p0 < p1 <= s1 < s2 <= q0 < q1, \
            f"{r['TRIGGER_NAME']} {r['DETECTOR']}"


def test_margin_band(cat):
    """Near-edge margins in the hug-the-burst 5-40 s band (both sides)."""
    for r in cat:
        g_pre = float(r['SRC_START']) - float(r['BKG_NEG_STOP'])
        g_post = float(r['BKG_POS_START']) - float(r['SRC_STOP'])
        assert 5.0 <= g_pre <= 40.0, f"{r['TRIGGER_NAME']} g_pre={g_pre:.1f}"
        assert 5.0 <= g_post <= 40.0, f"{r['TRIGGER_NAME']} g_post={g_post:.1f}"


def test_approval_stamps(cat):
    for r in cat:
        assert str(r['APPROVED_BY']).strip() not in ('', 'unknown')
        assert str(r['APPROVAL_MODE']).strip() in ('human_gui', 'ai_vision')
