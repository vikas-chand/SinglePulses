#!/usr/bin/env python3
"""Generate paper_agentic/v3/tab_T1_roster.tex from paper_agentic/T1_component_roster_DRAFT.md.

The tex file says "GENERATED ... do not hand-edit" but the generator lived only in a session
transcript (Codex supervisor review D1/D12, 2026-09-02): a generated artefact must have a
checked-in producer that reproduces it from cold. This is that producer.

    python3 dev/build_t1_roster.py                # write the tex (default: plain status words)
    python3 dev/build_t1_roster.py --check        # exit 1 if the tex on disk differs from a fresh build
    python3 dev/build_t1_roster.py --status-notes # carry each row's status qualification into the status
                                                  # cell (D12 proposal; changes the approved table -> PI gate)

Rules (derived from the committed tex at 427fdc5/1fc7a17; since r2 the prose cells are wrapped in
\\parbox because aastex's deluxetable cannot take p{} columns): five columns component / job / kind / exec. / status; the seven roster groups become
\\multicolumn italic headers; execution words collapse to C / I / H in the fixed order C, I, H;
backticked code becomes \\texttt{} with underscores escaped; the status cell is the first word
(DEPLOYED / PROPOSED / PARKED) unless --status-notes.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'paper_agentic', 'T1_component_roster_DRAFT.md')
DST = os.path.join(ROOT, 'paper_agentic', 'v3', 'tab_T1_roster.tex')

COMMIT = '4df6884'          # the census commit named in the caption (counts), not the roster commit
ROSTER_COMMIT = '427fdc5'   # the approved roster revision named in the header comment

PREAMBLE = (
    "% T1 — component roster, GENERATED from paper_agentic/T1_component_roster_DRAFT.md (commit @@RC@@) "
    "by the build script; do not hand-edit.\n"
    "\\startlongtable\n"
    "\\begin{deluxetable*}{lllll}\n"
    "\\tabletypesize{\\footnotesize}\n"
    "\\tablecaption{The component roster: the work of each component in one sentence. Kind: guide / sensor / "
    "action / store / producer / actor / boundary; execution: computational (C), inferential (I), human (H). "
    "Status is what is on disk at commit \\texttt{@@CC@@} (census 2026-09-02): DEPLOYED = a file or product exists; "
    "PROPOSED = a register row or law-file actor without one. Origins are quoted in the source table."
    "\\label{tab:roster}}\n"
    "\\tablehead{\\colhead{component} & \\colhead{job} & \\colhead{kind} & \\colhead{exec.} & \\colhead{status}}\n"
    "\\startdata\n"
)
POSTAMBLE = "\\enddata\n\\end{deluxetable*}\n"

# Column widths for the wrapped cells (a two-column aastex page is ~18 cm wide between margins).
WIDTHS = {'component': '4.0cm', 'job': '7.2cm', 'kind': '2.0cm', 'status': '2.6cm'}


def pbox(width, text):
    """Top-aligned, ragged-right paragraph cell: the only wrapping deluxetable accepts."""
    return '\\parbox[t]{' + width + '}{\\raggedright ' + text + '}'


EXEC_ORDER = [('computational', 'C'), ('inferential', 'I'), ('human', 'H')]


UNICODE = [('→', '$\\to$'), ('νFν', '$\\nu F_\\nu$'), ('–', '--'), ('≤', '$\\le$'), ('≥', '$\\ge$'),
           ('Δ', '$\\Delta$'), ('σ', '$\\sigma$'), ('×', '$\\times$'), ('✎', '(to write)'), ('≠', '$\\neq$'),
           ('—', '---'), ('←', '$\\leftarrow$'), ('…', '\\ldots{}'), ('≈', '$\\approx$'), ('°', '$^\\circ$')]


def tex_escape(s):
    """Escape the LaTeX specials that occur in roster prose (outside code spans, which
    code_spans() handles) and map the unicode the roster uses to pdflatex-safe macros."""
    parts = re.split(r'(`[^`]+`)', s)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
            continue
        part = part.replace('\\', '\\textbackslash{}')
        for ch in ['&', '%', '#', '_']:
            part = part.replace(ch, '\\' + ch)
        for u, t in UNICODE:
            part = part.replace(u, t)
        out.append(part)
    return ''.join(out)


def code_spans(s):
    """`code` -> \\texttt{code} with underscores escaped inside."""
    def rep(m):
        inner = m.group(1).replace('_', '\\_')
        return '\\texttt{' + inner + '}'
    return re.sub(r'`([^`]+)`', rep, s)


def cell(s):
    return code_spans(tex_escape(s))


def exec_abbrev(s):
    found = [ab for word, ab in EXEC_ORDER if word in s]
    return '/'.join(found) if found else s


def status_cell(s, notes):
    m = re.match(r'(DEPLOYED|PROPOSED|PARKED)', s)
    word = m.group(1) if m else s
    if not notes:
        return word
    rest = s[len(word):].strip()
    return word + (' ' + cell(rest) if rest else '')


def parse_roster(path):
    groups = []
    cur = None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        m = re.match(r'^## Group \d+ — (.+)$', line)
        if m:
            cur = {'title': m.group(1).strip(), 'rows': []}
            groups.append(cur)
            continue
        if re.match(r'^## [A-Z]\.', line):
            cur = None
            continue
        if cur is not None and re.match(r'^\| \d+ \|', line):
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cols) < 9:
                sys.exit(f'row with {len(cols)} columns: {line[:80]}')
            cur['rows'].append(cols)
    return groups


def build(notes=False):
    out = [PREAMBLE.replace('@@RC@@', ROSTER_COMMIT).replace('@@CC@@', COMMIT)]
    for g in parse_roster(SRC):
        out.append('\\multicolumn{5}{l}{\\textit{' + tex_escape(g['title']) + '}} \\\\\n')
        for cols in g['rows']:
            _, comp, job, kind, execn, _fires, _born, status, _ev = cols[:9]
            st = status_cell(status, notes)
            if notes:
                st = pbox(WIDTHS['status'], st)
            out.append(' & '.join([pbox(WIDTHS['component'], cell(comp)), pbox(WIDTHS['job'], cell(job)),
                                   pbox(WIDTHS['kind'], cell(kind)), exec_abbrev(execn), st]) + ' \\\\\n')
    out.append(POSTAMBLE)
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--status-notes', action='store_true')
    ap.add_argument('--out', default=DST)
    a = ap.parse_args()
    text = build(notes=a.status_notes)
    if a.check:
        on_disk = open(a.out, encoding='utf-8').read() if os.path.exists(a.out) else ''
        if on_disk == text:
            print('tab_T1_roster.tex reproduces from the roster (byte-identical)')
            return 0
        import difflib
        for l in difflib.unified_diff(on_disk.splitlines(), text.splitlines(), 'on disk', 'fresh build', lineterm='', n=0):
            print(l[:200])
        return 1
    open(a.out, 'w', encoding='utf-8').write(text)
    n = text.count(' \\\\\n') - text.count('\\multicolumn')
    print(f'wrote {os.path.relpath(a.out, ROOT)}: {n} rows' + (' (with status notes)' if a.status_notes else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
