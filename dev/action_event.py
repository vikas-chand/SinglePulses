#!/usr/bin/env python3
"""action_event.py -- one JSON line per regulated action or agent invocation (harness need #1).

Born 2026-09-02: all five harness sources compared in notes/HARNESS_COMPARISON_20260902.md ask
for the same record under different names -- telemetry, "did it fire", decision capture,
invisibility, the audit stream -- and Codex's skill-graph review (2026-09-01, §2) specified its
shape as the ACTION_EVENT envelope. Nothing on disk recorded who did what, with which model,
on which inputs, with what verdict, at what cost. This module is the record.

    from action_event import record
    record('present', 'commit', actor_kind='agent', identity='GRBs Agent (building seat)',
           trigger_scope='bn110920546', step='6', inputs=[...], outputs=[...], verdict=None,
           rules_discharged=['NR-45'], model_id='claude-fable-5-1')

Properties:
  * APPEND-ONLY, one os.write per event with O_APPEND, so two terminals can log concurrently
    without interleaving (POSIX guarantees atomic appends below PIPE_BUF; one event is < 4 KB);
  * the file is results/campaign/traces/actions.jsonl (results/ is gitignored by design: products
    bind by hash, generators by commit); month-rolled files are a later option;
  * every event carries the provenance stamp (dev/provenance_stamp.py): model_id, harness,
    session, git head, tree-dirty flag -- "unknown" is an honest value, never a guess;
  * every event is validated against dev/schemas/action_event.schema.json BEFORE it is written
    when jsonschema is importable; an invalid event is refused loudly (exit 2 / ValueError);
  * a CLI for shell callers (hooks, launchers, referee script):
        python3 dev/action_event.py --primitive launch_producer --phase commit \
            --actor script --identity dev/referee/fire_referee.sh --trigger bn110920546 --note "..."
  * `tail(n)` and `count(primitive=None)` for the did-it-fire question (harness need #1/#3).

This is the artifact layer. The hook that emits an event automatically after every tool call
(PostToolUse) is Phase A-GATED in the dispatch plan: it changes a live session's settings and
waits for the PI's explicit go. Until then the session records by protocol.
"""
import argparse
import datetime as _dt
import json
import os
import sys
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance_stamp import stamp as _stamp  # noqa: E402

TRACE_DIR = os.path.join(ROOT, 'results', 'campaign', 'traces')
TRACE_FILE = os.path.join(TRACE_DIR, 'actions.jsonl')
SCHEMA = os.path.join(ROOT, 'dev', 'schemas', 'action_event.schema.json')

PRIMITIVES = ('present', 'approve', 'feedback', 'promote', 'quarantine', 'invalidate', 'launch_producer',
              'deliver', 'verify', 'distill', 'refer', 'stamp', 'write', 'other')
PHASES = ('intent', 'preflight', 'commit', 'finalize', 'refused')
ACTORS = ('human', 'agent', 'hook', 'script')


def _validate(ev):
    """Refuse an invalid event loudly. If jsonschema is not importable the event is still written
    but stamped validated=false and a warning goes to stderr -- never a silent no-op (verifier round 1)."""
    try:
        import jsonschema
    except ImportError:
        print('ACTION_EVENT WARNING: jsonschema not importable; event written UNVALIDATED', file=sys.stderr)
        ev['validated'] = False
        return
    with open(SCHEMA) as fh:
        jsonschema.validate(ev, json.load(fh))
    ev['validated'] = True


def build(primitive, phase, actor_kind, identity, trigger_scope=None, step=None, inputs=None, outputs=None,
          verdict=None, rules_discharged=None, tokens=None, wall_s=None, cost_usd=None, note=None,
          model_id=None, harness=None, harness_version=None, session_id=None, **extra):
    if primitive not in PRIMITIVES:
        raise ValueError(f'unknown primitive {primitive!r}; one of {PRIMITIVES}')
    if phase not in PHASES:
        raise ValueError(f'unknown phase {phase!r}; one of {PHASES}')
    if actor_kind not in ACTORS:
        raise ValueError(f'unknown actor kind {actor_kind!r}; one of {ACTORS}')
    prov = _stamp(model_id, harness, harness_version, session_id)
    ev = {
        'event_id': uuid.uuid4().hex,
        'utc': _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'primitive': primitive, 'phase': phase,
        'actor': {'kind': actor_kind, 'identity': identity, 'model_id': prov['model_id'], 'harness': prov['harness']},
        'trigger_scope': trigger_scope, 'step': None if step is None else str(step),
        'inputs': inputs or [], 'outputs': outputs or [],
        'verdict': verdict, 'rules_discharged': rules_discharged or [],
        'tokens': tokens, 'wall_s': wall_s, 'cost_usd': cost_usd, 'note': note,
        'provenance': prov,
    }
    ev.update(extra)
    return ev


def append(ev, path=TRACE_FILE):
    _validate(ev)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = (json.dumps(ev, ensure_ascii=False) + '\n').encode('utf-8')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)
    return ev['event_id']


def record(primitive, phase, actor_kind, identity, path=TRACE_FILE, **kw):
    return append(build(primitive, phase, actor_kind, identity, **kw), path)


def iter_events(path=TRACE_FILE):
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def tail(n=20, path=TRACE_FILE):
    evs = list(iter_events(path))
    return evs[-n:]


def count(primitive=None, path=TRACE_FILE):
    return sum(1 for e in iter_events(path) if primitive is None or e.get('primitive') == primitive)


def main(argv=None):
    ap = argparse.ArgumentParser(description='append one ACTION_EVENT line (validated) to the trace')
    ap.add_argument('--primitive', choices=PRIMITIVES)
    ap.add_argument('--phase', default='commit', choices=PHASES)
    ap.add_argument('--actor', default='script', choices=ACTORS)
    ap.add_argument('--identity')
    ap.add_argument('--trigger'); ap.add_argument('--step'); ap.add_argument('--verdict'); ap.add_argument('--note')
    ap.add_argument('--input', action='append', default=[], help='path[:sha256] (repeatable)')
    ap.add_argument('--output', action='append', default=[], help='path[:sha256] (repeatable)')
    ap.add_argument('--rule', action='append', default=[], help='rule id discharged, e.g. NR-45 (repeatable)')
    ap.add_argument('--tokens', type=int); ap.add_argument('--wall-s', type=float); ap.add_argument('--cost-usd', type=float)
    ap.add_argument('--model-id'); ap.add_argument('--file', default=TRACE_FILE)
    ap.add_argument('--tail', type=int, help='print the last N events instead of writing')
    a = ap.parse_args(argv)
    if a.tail:
        for e in tail(a.tail, a.file):
            print(json.dumps(e))
        return 0
    if not a.primitive or not a.identity:
        ap.error('--primitive and --identity are required unless --tail is given')
    split = lambda items: [{'path': s.split(':')[0], 'sha256': (s.split(':')[1] if ':' in s else None)} for s in items]
    try:
        eid = record(a.primitive, a.phase, a.actor, a.identity, path=a.file, trigger_scope=a.trigger, step=a.step,
                     inputs=split(a.input), outputs=split(a.output), verdict=a.verdict, rules_discharged=a.rule,
                     tokens=a.tokens, wall_s=a.wall_s, cost_usd=a.cost_usd, note=a.note, model_id=a.model_id)
    except Exception as e:  # refused loudly, never silently dropped
        print(f'ACTION_EVENT REFUSED: {e}', file=sys.stderr)
        return 2
    print(eid)
    return 0


if __name__ == '__main__':
    sys.exit(main())
