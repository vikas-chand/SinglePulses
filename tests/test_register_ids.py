"""The agent-requirements register cannot carry two rows with one id.

Born 2026-09-02: two concurrent sessions each minted "NR-41" on 2026-09-01 — the
walkthrough terminal for CHAIN-GATE ANCESTOR COVERAGE (cited by ReportSpec R3 and
SpectralFitting L31) and the building terminal for TWO-HAT SEPARATION (cited by the
referee launcher). The second row had also been appended after the file's closing
prose, outside the table. Nothing failed: the register is prose, and prose cannot
fail a build. These tests can. They read `dev/ai_guides/AgentArchitecture.md` as
text and guard three invariants: ids are unique, every NR row lives inside the
register table, and no guide cites an NR id that has no row (a citation to a row
that was never written is exactly how five rows went missing for a day).
"""
import collections
import glob
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.join(BASE, 'dev', 'ai_guides', 'AgentArchitecture.md')
HEADER = '| where | purpose (single job) | status |'
ROW = re.compile(r'^\|[^|]*\|\s*NR-(\d+)\b')
CITE = re.compile(r'\bNR-(\d+)\b')
RETIRED = {11}  # retired rows are removed from the table; citations may survive

# Guides whose NR citations must resolve to a row.
CITING_GLOBS = ['dev/ai_guides/*.md', 'dev/referee/*', '.claude/agents/*.md']


def _lines():
    with open(REGISTER, encoding='utf-8') as fh:
        return fh.read().split('\n')


def _table_span(lines):
    starts = [i for i, l in enumerate(lines) if l.strip() == HEADER]
    assert len(starts) == 1, f'expected one register header, found {len(starts)}'
    i = starts[0]
    while i < len(lines) and lines[i].startswith('|'):
        i += 1
    return starts[0], i  # [start, end)


def _rows(lines):
    return [(i, int(m.group(1))) for i, l in enumerate(lines) if (m := ROW.match(l))]


def test_register_ids_unique():
    counts = collections.Counter(n for _, n in _rows(_lines()))
    dups = sorted(n for n, c in counts.items() if c > 1)
    assert not dups, f'duplicate register ids: {["NR-%d" % n for n in dups]}'


def test_every_row_inside_the_table():
    lines = _lines()
    start, end = _table_span(lines)
    outside = [(i + 1, n) for i, n in _rows(lines) if not (start < i < end)]
    assert not outside, (
        f'NR rows outside the register table (line, id): {outside} — '
        f'table spans lines {start + 1}-{end}')


def test_no_dangling_citations():
    have = {n for _, n in _rows(_lines())} | RETIRED
    dangling = {}
    for pat in CITING_GLOBS:
        for path in glob.glob(os.path.join(BASE, pat)):
            with open(path, encoding='utf-8', errors='replace') as fh:
                cited = {int(m) for m in CITE.findall(fh.read())}
            missing = sorted(cited - have)
            if missing:
                dangling[os.path.relpath(path, BASE)] = ['NR-%d' % n for n in missing]
    assert not dangling, f'guides cite register ids that have no row: {dangling}'
