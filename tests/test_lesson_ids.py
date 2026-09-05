"""Lesson IDs are skill-specific and unique — no two skill files may share a prefix.

PI ruling 2026-09-02 (verbatim): lesson IDs "should be specific to the skills". Born of
the collision found the same day: SpectralFitting.md and Temporal.md both carried L31,
L32 and L33 meaning different lessons, so a citation "L32" was ambiguous. Temporal's
five lessons became TM1–TM5; the prefix table lives in the BurstWalkthrough ledger.

These tests read the skill files as text. They guard three invariants: a header prefix
maps to exactly one file; IDs are unique within a file; every prefix found in a header
is declared in the ledger's prefix table (so a new skill cannot mint an undeclared
namespace by accident).
"""
import collections
import glob
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDES = os.path.join(BASE, 'dev', 'ai_guides')
LEDGER = os.path.join(GUIDES, 'BurstWalkthrough.md')

# A lesson header: "## L12 — ...", "### D3 ...", "## R3a ...", "### P9 ...", "## TM1 (was L29) — ..."
HEADER = re.compile(r'^#{2,4}\s+([A-Z]{1,3})-?(\d{1,3}[a-z]?)\b')
# The declaration line in the ledger: "L = SpectralFitting · TM = Temporal ..."
DECL = re.compile(r'\b([A-Z]{1,3}) = ')


def _declared_prefixes():
    with open(LEDGER, encoding='utf-8') as fh:
        text = fh.read()
    start = text.index('**Lesson-ID prefixes**')
    block = text[start:start + 1500]
    found = set(DECL.findall(block))
    assert found, 'no prefix table found in the ledger'
    return found


def _headers():
    rows = []  # (file, prefix, id)
    for path in sorted(glob.glob(os.path.join(GUIDES, '*.md'))):
        name = os.path.basename(path)
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                m = HEADER.match(line)
                if m:
                    rows.append((name, m.group(1), m.group(2)))
    assert rows, 'no lesson headers found at all'
    return rows


def test_prefix_belongs_to_one_file():
    owners = collections.defaultdict(set)
    for name, prefix, _ in _headers():
        owners[prefix].add(name)
    shared = {p: sorted(f) for p, f in owners.items() if len(f) > 1}
    assert not shared, f'lesson prefix used by more than one skill file: {shared}'


def test_ids_unique_within_file():
    counts = collections.Counter((name, prefix, num) for name, prefix, num in _headers())
    dups = sorted(k for k, c in counts.items() if c > 1)
    assert not dups, f'duplicate lesson ids inside a file: {dups}'


def test_every_prefix_is_declared():
    declared = _declared_prefixes()
    found = {prefix for _, prefix, _ in _headers()}
    undeclared = sorted(found - declared)
    assert not undeclared, (
        f'header prefixes not in the ledger prefix table: {undeclared} '
        f'(declared: {sorted(declared)})')
