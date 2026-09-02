#!/usr/bin/env python3
"""provenance_stamp.py -- who/what/when for any writer to embed (harness need #2, 2026-09-02).

Every product in this repository was, until today, silent about the MODEL that produced it:
`generated_by` said "campaign worker", stamps said "Claude session", the commit pin carried the
generator commit but no model. Five harness sources (notes/HARNESS_COMPARISON_20260902.md §4)
say the same thing: a harness feature is a bet on a model's limitations, and the bet cannot be
retested when the model changes if nobody wrote down which model it was.

This module returns one dict a writer embeds verbatim:

    {model_id, harness, harness_version, session_id, utc, git_head, tree_dirty}

Sources, in order: explicit argument -> environment (TB_MODEL_ID, TB_HARNESS,
TB_HARNESS_VERSION, CLAUDE_SESSION_ID / TB_SESSION_ID) -> "unknown". "unknown" is a legitimate,
HONEST value: a record that says unknown is better than one that guesses. The boot ritual that
exports TB_MODEL_ID is a PROPOSED addition to FreshSessionBoot.md (the PI's call); until then the
session passes model_id explicitly when it writes.

Light tier: standard library only. Never raises on a missing git; reports what it can.
"""
import datetime as _dt
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNKNOWN = 'unknown'


def _git(args):
    try:
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def stamp(model_id=None, harness=None, harness_version=None, session_id=None):
    head = _git(['rev-parse', '--short=12', 'HEAD']) or None
    dirty = _git(['status', '--porcelain', '--untracked-files=no'])
    return {
        'model_id': model_id or os.environ.get('TB_MODEL_ID') or UNKNOWN,
        'harness': harness or os.environ.get('TB_HARNESS') or ('claude-code' if os.environ.get('CLAUDE_CODE') or os.environ.get('CLAUDECODE') else UNKNOWN),
        'harness_version': harness_version or os.environ.get('TB_HARNESS_VERSION') or UNKNOWN,
        'session_id': session_id or os.environ.get('CLAUDE_SESSION_ID') or os.environ.get('TB_SESSION_ID') or None,
        'utc': _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'git_head': head,
        'tree_dirty': bool(dirty) if head else None,
    }


def main(argv=None):
    import argparse
    import json
    ap = argparse.ArgumentParser(description='print a provenance stamp as JSON')
    ap.add_argument('--model-id'); ap.add_argument('--harness'); ap.add_argument('--harness-version'); ap.add_argument('--session-id')
    a = ap.parse_args(argv)
    print(json.dumps(stamp(a.model_id, a.harness, a.harness_version, a.session_id)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
