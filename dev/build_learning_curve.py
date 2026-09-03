#!/usr/bin/env python3
"""F7 — the campaign learning curve, built from the campaign ledger and the dated lesson entries.

    python3 dev/build_learning_curve.py            # writes paper_agentic/figures/fig_F7_learning_curve.{pdf,png}
                                                   #   + a JSON sidecar with every number on the figure and its source

Sources (never typed numbers):
  * notes/campaign_ledger.csv — the first eight walked bursts (order, burst, walked dates, lessons_born, bugs_found):
    lessons per burst = the number of lesson ids named in `lessons_born`; defects = `bugs_found`.
  * the five step skills that carry numbered lessons (dev/ai_guides/{SpectralFitting,Temporal,DataInventory,
    GCNIntelligence,LiteratureHarvest}.md): heading-form lessons `### <PREFIX><n> — ... *(date, burst)*`; the
    walkthrough burst in progress (bn110920546, ledger #21, walked from 2026-08-30) is credited with the lessons
    whose heading names it or whose date falls on or after 2026-08-30.
The figure carries the provisional flag by construction (the caption says so; the sidecar says which rows are
ledger and which are parsed).
"""
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'paper_agentic', 'figures', 'fig_F7_learning_curve')
LEDGER = os.path.join(ROOT, 'notes', 'campaign_ledger.csv')
SKILLS = {'SpectralFitting': 'L', 'Temporal': 'TM', 'DataInventory': 'D', 'GCNIntelligence': 'G', 'LiteratureHarvest': 'T'}
WALK21 = ('bn110920546', '2026-08-30')


def ledger_rows():
    rows = []
    for r in csv.DictReader(open(LEDGER, encoding='utf-8')):
        ids = re.findall(r'\b(?:L|TM|D|G|T)\d{1,2}(?:-(?:L|TM|D|G|T)?\d{1,2})?\b', r['lessons_born'])
        n = 0
        for tok in ids:
            m = re.match(r'([A-Z]+)(\d+)-(?:[A-Z]+)?(\d+)$', tok)
            n += (int(m.group(3)) - int(m.group(2)) + 1) if m else 1
        rows.append({'order': int(r['order']), 'burst': r['burst'], 'walked': r['walked'], 'lessons': n,
                     'defects': int(r['bugs_found'] or 0), 'source': 'notes/campaign_ledger.csv', 'lessons_born': r['lessons_born']})
    return rows


def parsed_lessons():
    out = []
    for f, pre in SKILLS.items():
        for line in open(os.path.join(ROOT, 'dev', 'ai_guides', f + '.md'), encoding='utf-8'):
            m = re.match(r'^#{2,4}\s+' + pre + r'(\d{1,2})\b(.*)$', line)
            if m:
                tail = m.group(2)
                d = re.search(r'(20\d\d-\d\d-\d\d)', tail)
                b = re.search(r'(bn\d{9})', tail)
                out.append({'id': f'{pre}{m.group(1)}', 'file': f, 'date': d.group(1) if d else None, 'burst': b.group(1) if b else None})
    return out


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))
    try:
        from plot_style import apply_pub_style
        apply_pub_style()
    except Exception:
        pass
    rows = ledger_rows()
    lessons = parsed_lessons()
    w21 = [l for l in lessons if l['burst'] == WALK21[0] or (l['date'] and l['date'] >= WALK21[1])]
    rows.append({'order': 21, 'burst': WALK21[0], 'walked': WALK21[1] + '..', 'lessons': len(w21), 'defects': 0,
                 'source': 'dev/ai_guides/*.md headings (burst tag or date >= 2026-08-30)', 'lessons_born': ';'.join(l['id'] for l in w21)})
    xs = list(range(1, len(rows) + 1))
    labels = [f"#{r['order']}" for r in rows]
    cum = []
    c = 0
    for r in rows:
        c += r['lessons']
        cum.append(c)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.bar(xs, [r['lessons'] for r in rows], color='0.75', edgecolor='0.35', label='lessons distilled')
    ax.bar(xs, [r['defects'] for r in rows], color='0.3', edgecolor='0.2', width=0.5, label='engine defects found')
    ax2 = ax.twinx()
    ax2.plot(xs, cum, color='k', marker='o', ms=3.5, lw=1.2, label='cumulative lessons')
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_xlabel('walked burst (campaign order)')
    ax.set_ylabel('per burst')
    ax2.set_ylabel('cumulative lessons')
    ax.set_ylim(0, max(r['lessons'] for r in rows) * 1.75)
    ax2.set_ylim(0, max(cum) * 1.5)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=8, framealpha=0.9, edgecolor='0.6')
    ax.annotate('in progress', (xs[-1], rows[-1]['lessons']), xytext=(0, 4), textcoords='offset points', ha='center', va='bottom', fontsize=7, color='0.3')
    ax.text(0.99, 0.97, 'provisional: walkthrough era', transform=ax.transAxes, ha='right', va='top', fontsize=7, color='0.4')
    fig.tight_layout()
    fig.savefig(OUT + '.pdf')
    fig.savefig(OUT + '.png', dpi=300)
    head = subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    side = {'figure': 'F7 campaign learning curve', 'utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'git_head': head, 'rows': rows, 'cumulative': cum, 'total_lessons': cum[-1],
            'parsed_lessons_total': len(lessons), 'walkthrough_in_progress': {'burst': WALK21[0], 'since': WALK21[1], 'lessons': [l['id'] for l in w21]},
            'ledger_sha256': hashlib.sha256(open(LEDGER, 'rb').read()).hexdigest()}
    json.dump(side, open(OUT + '.json', 'w'), indent=1)
    print(f"wrote {os.path.relpath(OUT, ROOT)}.{{pdf,png,json}}: {len(rows)} bursts, {cum[-1]} lessons cumulative; "
          f"walkthrough #21 credited with {len(w21)} ({', '.join(l['id'] for l in w21)})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
