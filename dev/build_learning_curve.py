#!/usr/bin/env python3
"""F7 — the campaign learning curve, built from the campaign ledger and the dated lesson entries.

    python3 dev/build_learning_curve.py            # writes paper_agentic/figures/fig_F7_learning_curve.{pdf,png}
                                                   #   + a JSON sidecar with every number on the figure and its source

Sources (never typed numbers):
  * notes/campaign_ledger.csv — the first eight walked bursts. Lessons per burst = the ids named in `lessons_born`,
    (a) WHITELISTED against the heading-form lessons that exist on disk (so 'T90' is not a lesson), (b) ALIASED where
    a lesson was relocated between skill files (L26->TM3, L29->TM1) so it keeps its birth credit, and (c) DEDUPLICATED
    across rows (an id counts at its first appearance). Defects = `bugs_found`, defects at any layer.
  * the step skills that carry numbered lessons (dev/ai_guides/{SpectralFitting,Temporal,DataInventory,
    GCNIntelligence,LiteratureHarvest}.md): heading-form lessons under any of `##`..`####`, ids optionally
    sub-lettered (`L6b`); the
    walkthrough burst in progress (bn110920546, ninth walked; review-index 21) is credited ONLY with the lessons whose
    heading names it and that are not marked PROPOSED; its defects are not tallied while the walkthrough is open.
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


def review_index():
    """trigger -> row number in notes/REVIEW_INDEX_106.md (the campaign catalogue order)."""
    out = {}
    for l in open(os.path.join(ROOT, 'notes', 'REVIEW_INDEX_106.md'), encoding='utf-8'):
        m = re.match(r'^\|\s*(\d+)\s*\|\s*`(bn\d{9})`', l)
        if m:
            out[m.group(2)] = int(m.group(1))
    return out


def ledger_rows(known_ids):
    """Bursts #1-#8 from the ledger: lesson ids named in `lessons_born`, WHITELISTED against the heading-form
    lessons on disk (so 'T90' is never a lesson) and DEDUPLICATED across rows (an id counts at its first
    appearance only). `bugs_found` = defects found at any layer (engine, temporal, catalog, reporting)."""
    rows, seen = [], set()
    for r in csv.DictReader(open(LEDGER, encoding='utf-8')):
        toks = re.findall(r'\b(L|TM|D|G|T)(\d{1,2})(?:-(?:L|TM|D|G|T)?(\d{1,2}))?\b', r['lessons_born'])
        ids = []
        for pre, a, b in toks:
            for n in range(int(a), int(b or a) + 1):
                ids.append(f'{pre}{n}')
        ALIAS = {'L26': 'TM3', 'L29': 'TM1'}   # ids relocated to Temporal (2026-09-02) keep their birth credit
        ids = [ALIAS.get(i, i) for i in ids]
        ids = [i for i in ids if i in known_ids]
        new_ids = [i for i in ids if i not in seen]
        seen.update(new_ids)
        rows.append({'order': int(r['order']), 'walk_order': int(r['order']), 'review_index': None,
                     'burst': r['burst'], 'walked': r['walked'], 'lessons': len(new_ids),
                     'lesson_ids': new_ids, 'defects': int(r['bugs_found'] or 0),
                     'source': 'notes/campaign_ledger.csv (ids whitelisted against the skill-file headings; deduplicated)',
                     'lessons_born': r['lessons_born']})
    return rows


def parsed_lessons():
    out = []
    for f, pre in SKILLS.items():
        for line in open(os.path.join(ROOT, 'dev', 'ai_guides', f + '.md'), encoding='utf-8'):
            m = re.match(r'^#{2,4}\s+' + pre + r'(\d{1,2}[a-z]?)\b(.*)$', line)
            if m:
                tail = m.group(2)
                d = re.search(r'(20\d\d-\d\d-\d\d)', tail)   # kept for the sidecar record only; no rule reads it
                b = re.search(r'(bn\d{9})', tail)
                out.append({'id': f'{pre}{m.group(1)}', 'file': f, 'date': d.group(1) if d else None, 'burst': b.group(1) if b else None,
                            'proposed': 'PROPOSED' in tail.upper()})
    return out


def register_defects(burst):
    """Register rows that cite the burst: the defects the walkthrough surfaced, at any layer."""
    rows = [l for l in open(os.path.join(ROOT, 'dev', 'ai_guides', 'AgentArchitecture.md'), encoding='utf-8')
            if l.startswith('|') and re.search(r'\bNR-\d+\b', l) and burst in l]
    return sorted({m for l in rows for m in re.findall(r'\bNR-\d+\b', l)})


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))
    from plot_style import apply_pub_style, PUB   # must not fail silently (Figures.md F8)
    apply_pub_style()
    lessons = parsed_lessons()
    known = {l['id'] for l in lessons}
    rows = ledger_rows(known)
    rix = review_index()
    for i, r in enumerate(rows, 1):
        r['walk_order'] = i
        r['review_index'] = rix.get(r['burst'])
    # #21 (ninth walked burst): lessons whose HEADING names the burst and that are not marked PROPOSED
    w21 = [l for l in lessons if l['burst'] == WALK21[0] and not l['proposed']]
    d21 = register_defects(WALK21[0])   # rows CITING the burst (as instance or birth) — not a defect tally; recorded, not drawn
    rows.append({'order': 21, 'walk_order': 9, 'review_index': 21, 'burst': WALK21[0], 'walked': WALK21[1] + '..', 'lessons': len(w21),
                 'lesson_ids': [l['id'] for l in w21], 'defects': None, 'register_rows_citing': d21,
                 'source': 'dev/ai_guides/*.md headings naming the burst, PROPOSED excluded; defects = register rows citing the burst',
                 'lessons_born': ';'.join(l['id'] for l in w21)})
    xs = list(range(1, len(rows) + 1))
    labels = [f"#{r['order']}" for r in rows[:-1]] + ['#9\n(rev. 21)']
    cum = []
    c = 0
    for r in rows:
        c += r['lessons']
        cum.append(c)
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.bar(xs, [r['lessons'] for r in rows], color='0.75', edgecolor='0.35', label='lessons distilled')
    known = [(x, r['defects']) for x, r in zip(xs, rows) if r['defects'] is not None]
    ax.bar([x for x, _ in known], [d for _, d in known], color='0.3', edgecolor='0.2', width=0.5,
           label='defects found (all layers)')
    # A burst whose walkthrough is open has NO defect measurement: draw absence as absence (a cross on the axis),
    # never as a zero-height bar, and name it in the legend. (Gate 2026-09-03: an in-bar note overflowed its bar twice.)
    missing = [x for x, r in zip(xs, rows) if r['defects'] is None]
    if missing:
        import matplotlib.patheffects as pe
        ax.plot(missing, [0.55] * len(missing), linestyle='none', marker='x', ms=PUB['ms_data'],
                mew=PUB['lw_secondary'], color='0.2', label='defects not tallied (burst in progress)',
                path_effects=[pe.withStroke(linewidth=3, foreground='white')])   # clear of the 6 pt tick; haloed so it reads as the legend key
    ax2 = ax.twinx()
    ax2.plot(xs, cum, color='k', marker='o', ms=PUB['ms_data'] - 1.5, lw=PUB['lw_secondary'], label='cumulative lessons')
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_xlabel('walked burst (walk order; not time)')
    ax.set_ylabel('per burst')
    ax2.set_ylabel('cumulative lessons')
    ax.set_ylim(0, max(r['lessons'] for r in rows) * 1.95)
    ax2.set_ylim(0, max(cum) * 1.7)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    from matplotlib.ticker import MaxNLocator
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(h1 + h2, l1 + l2, loc='upper left', framealpha=0.9, edgecolor='0.6', handletextpad=0.5,
              borderaxespad=0.8)   # > tick_major/12 so the top ticks do not terminate on the legend frame
    fig.text(0.995, 0.012, 'provisional: walkthrough era', ha='right', va='bottom', color='0.4')
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(OUT + '.pdf')
    fig.savefig(OUT + '.png', dpi=PUB['dpi'])
    head = subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    side = {'figure': 'F7 campaign learning curve', 'utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'git_head': head, 'rows': rows, 'cumulative': cum, 'total_lessons': cum[-1],
            'parsed_lessons_total': len(lessons), 'walkthrough_in_progress': {'burst': WALK21[0], 'since': WALK21[1], 'lessons': [l['id'] for l in w21]},
            'ledger_sha256': hashlib.sha256(open(LEDGER, 'rb').read()).hexdigest(),
            'generator_sha256': hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest(),
            'git_head_note': 'built in the working tree: git_head is the commit the tree was based on; generator_sha256 identifies the code that drew it',
            'skill_file_sha256': {f: hashlib.sha256(open(os.path.join(ROOT, 'dev', 'ai_guides', f + '.md'), 'rb').read()).hexdigest() for f in SKILLS},
            'rules': {'ledger_rows': 'ids named in lessons_born, whitelisted against heading-form lessons, first appearance only',
                      'walkthrough_row': 'heading names the burst and is not PROPOSED; defects NOT tallied (the walkthrough is in progress; register rows citing the burst are listed, not counted)',
                      'x_axis': 'walk order (ledger order 1-8, then the ninth walked burst = review-index #21); not time'}}
    json.dump(side, open(OUT + '.json', 'w'), indent=1)
    print(f"wrote {os.path.relpath(OUT, ROOT)}.{{pdf,png,json}}: {len(rows)} bursts, {cum[-1]} lessons cumulative; "
          f"walkthrough #21 credited with {len(w21)} ({', '.join(l['id'] for l in w21)})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
