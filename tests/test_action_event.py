"""The action trace records what happened, validated, append-only, concurrent-safe.

Born 2026-09-02 (harness needs #1 and #2): nothing on disk recorded who did what with which
model. These tests exercise dev/action_event.py and dev/provenance_stamp.py against a temporary
trace file, never the live one: every event validates against the schema; an invalid event is
refused; two writers appending at once never interleave; the provenance stamp says "unknown"
honestly when the environment does not say the model.
"""
import json
import multiprocessing as mp
import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'dev'))
import action_event as ae  # noqa: E402
import provenance_stamp as ps  # noqa: E402


def test_stamp_is_honest_about_unknowns(monkeypatch):
    for k in ('TB_MODEL_ID', 'TB_HARNESS', 'TB_HARNESS_VERSION', 'CLAUDE_SESSION_ID', 'TB_SESSION_ID'):
        monkeypatch.delenv(k, raising=False)
    s = ps.stamp()
    assert s['model_id'] == 'unknown' and s['harness_version'] == 'unknown'
    assert ps.stamp(model_id='claude-fable-5-1')['model_id'] == 'claude-fable-5-1'
    monkeypatch.setenv('TB_MODEL_ID', 'from-env')
    assert ps.stamp()['model_id'] == 'from-env'
    assert set(s) == {'model_id', 'harness', 'harness_version', 'session_id', 'utc', 'git_head', 'tree_dirty'}


def test_event_validates_and_appends(tmp_path):
    f = str(tmp_path / 'actions.jsonl')
    eid = ae.record('present', 'commit', 'agent', 'test-session', path=f, trigger_scope='bn000000000', step='6',
                    inputs=[{'path': 'x.ecsv', 'sha256': '0' * 64}], rules_discharged=['NR-45'], model_id='claude-fable-5-1')
    evs = list(ae.iter_events(f))
    assert len(evs) == 1 and evs[0]['event_id'] == eid
    assert evs[0]['actor']['model_id'] == 'claude-fable-5-1' and evs[0]['step'] == '6'
    assert ae.count('present', f) == 1 and ae.count('approve', f) == 0


def test_invalid_event_is_refused(tmp_path):
    f = str(tmp_path / 'actions.jsonl')
    with pytest.raises(ValueError):
        ae.record('teleport', 'commit', 'agent', 'x', path=f)
    with pytest.raises(ValueError):
        ae.record('present', 'later', 'agent', 'x', path=f)
    assert not os.path.exists(f)


def _writer(args):
    f, i = args
    sys.path.insert(0, os.path.join(BASE, 'dev'))
    import action_event as ae2
    for j in range(25):
        ae2.record('write', 'commit', 'script', f'writer-{i}', path=f, note='x' * 500, model_id='t')
    return i


def test_concurrent_appends_do_not_interleave(tmp_path):
    f = str(tmp_path / 'actions.jsonl')
    with mp.get_context('spawn').Pool(4) as pool:
        pool.map(_writer, [(f, i) for i in range(4)])
    lines = open(f, encoding='utf-8').read().splitlines()
    assert len(lines) == 100
    for line in lines:
        json.loads(line)  # every line is one whole event


def test_cli_roundtrip(tmp_path):
    f = str(tmp_path / 'actions.jsonl')
    rc = ae.main(['--primitive', 'launch_producer', '--actor', 'script', '--identity', 'test.sh', '--trigger', 'bn000000000',
                  '--input', 'a.ecsv:' + 'a' * 64, '--rule', 'NR-7', '--file', f, '--model-id', 'm'])
    assert rc == 0
    ev = ae.tail(1, f)[0]
    assert ev['primitive'] == 'launch_producer' and ev['inputs'][0]['sha256'] == 'a' * 64 and ev['rules_discharged'] == ['NR-7']
