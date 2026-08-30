#!/usr/bin/env python3
"""NR-18 LIVE REPORT — per-burst live document + approval stamps.

  live_report.py --trig bnXXX                          # (re)build the document
  live_report.py --trig bnXXX --present 7              # mark step presented
  live_report.py --trig bnXXX --approve 7 --by VIKAS [--feedback "..."]
  live_report.py --trig bnXXX --feedback-only 7 --by VIKAS --feedback "..."

Rules (AgentArchitecture NR-18):
- A human (or, in fully-AI mode, an independent non-producer) stamps every step.
- Nonzero feedback ALWAYS routes: it is appended to the stamp AND echoed as a
  distiller instruction — a comment that only lives in chat is a protocol defect.
- Approving/feeding back a step that already had downstream steps approved
  triggers the NR-19 cascade REMINDER (invalidate_downstream.py) — printed,
  never run silently.
"""
import os, sys, json, argparse, datetime, glob, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import re as _re
_TRIG = _re.compile(r'^bn[0-9]{9}$|^bnTEST[0-9]{3}$|^bnADJ[0-9]$')
def _valid_trig(t):
    # fail loudly: the trig reaches os paths and a subprocess; never trust it raw
    if not _TRIG.match(t or ''):
        sys.stderr.write(f'ERROR: invalid trigger {t!r} — must match {_TRIG.pattern}\n'); sys.exit(2)
    return t
def _clean(x):
    # markdown table cell / prose safety: kill pipes and newlines that break the table
    return str(x).replace('|','\u2223').replace('\n',' ').replace('\r',' ').strip()
STEPS = ['0b','0','1','2','3','4','5','6','7','8','9']
STEP_NAMES = {'0b':'identity/boot','0':'inventory','1':'detector selection',
  '2':'background windows','3':'source window','4':'binning check','5':'stage-1 adopt',
  '6':'spectral fits','7':'temporal suite','8':'products (SED/evolution/montage)',
  '9':'report + literature + distill'}

def paths(trig):
    d = os.path.join(ROOT,'results','sweep106',trig)
    return d, os.path.join(d,'APPROVALS.json'), os.path.join(d,f'LIVE_REPORT_{trig}.md')

def load(trig):
    _, ap, _ = paths(trig)
    return json.load(open(ap)) if os.path.exists(ap) else {}

def save(trig, st):
    d, ap, _ = paths(trig)
    os.makedirs(d, exist_ok=True)
    json.dump(st, open(ap,'w'), indent=1)

def evidence(trig, step):
    """What exists on disk for this step — links, never claims."""
    d = os.path.join(ROOT,'results','sweep106',trig)
    cc = os.path.join(ROOT,'results','convention_check')
    e = []
    # 2026-08-30 (first fresh session): steps 0b,0,2,3,4,5 had NO evidence rule, so
    # PRESENTED was mechanically impossible for them (NR-18 gap). Links only — real
    # on-disk products, never claims. Step keys follow THIS file's STEP_NAMES; the
    # numbering offset vs BurstWalkthrough.md/scripts/44 is an open NR-27 conflict.
    def _ex(*ps): return [x for x in ps if os.path.exists(x)]
    decision = os.path.join(ROOT,'results','approval',f'{trig}_decision.json')
    if step=='0b': e += _ex(f'{ROOT}/results/gcn/{trig}/{trig}_dossier.md',
                            f'{ROOT}/notes/reconciliation/{trig}_harvest.json',
                            f'{ROOT}/notes/reconciliation/{trig}_P0_frozen.json')
    if step=='0':  e += _ex(f'{ROOT}/results/qc/{trig}_step1_response_coverage.ecsv',
                            f'{ROOT}/data/{trig}')
    if step in ('1','2','3','5'): e += _ex(decision)
    if step=='2':  e += sorted(glob.glob(f'{d}/{trig}_step3_background*.png'))
    if step=='3':  e += sorted(glob.glob(f'{d}/{trig}_step4_source*.png'))
    if step=='4':  e += _ex(f'{d}/blocks/bb_blocks_spectral_{trig}.ecsv') + sorted(glob.glob(f'{d}/{trig}_step5_binning*.png'))
    if step=='5':  e += _ex(f'{ROOT}/results/human_review_qc_flags.txt')
    if step=='1': e += glob.glob(f'{d}/{trig}_step1_*.png')
    if step=='6':
        for c in (f'{cc}/{trig}/spectral_fits.ecsv',
                  f'{ROOT}/results/campaign20_fam/{trig}_highe/spectral_fits.ecsv'):
            if os.path.exists(c): e.append(c); break
    if step=='7': e += sorted(glob.glob(f'{d}/{trig}_step7_*.png'))
    if step=='8':
        e += sorted(glob.glob(f'{cc}/sed_grid_{trig}/montage/*.png'))[:3]
        if glob.glob(f'{cc}/sed_grid_{trig}/*.png'):
            e.append(f'{len(glob.glob(f"{cc}/sed_grid_{trig}/*.png"))} SED panels in {cc}/sed_grid_{trig}/')
    if step=='9':
        for c in (f'{d}/REPORT_{trig}.pdf', f'{d}/REPORT_{trig}.md'):
            if os.path.exists(c): e.append(c)
    vq = os.path.join(d,'VISION_QC.md')
    if step in ('1','6','7','8') and os.path.exists(vq): e.append(vq)
    return [os.path.relpath(x, ROOT) if os.path.isabs(x) else x for x in e]

def build(trig):
    st = load(trig)
    d, _, out = paths(trig)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    L = [f'# LIVE REPORT — {trig}', '',
         f'Rebuilt {now}. Stamps in `APPROVALS.json` beside this file; the',
         'document is assembled from stamps + products on disk — it never asserts',
         'what it cannot link. Approval/feedback: `dev/live_report.py -h`.', '',
         '| step | what | status | by | when | evidence |', '|---|---|---|---|---|---|']
    for s in STEPS:
        rec = st.get(s, {})
        stat = rec.get('status','—')
        if stat=='APPROVED' and rec.get('feedback'): stat='APPROVED+FEEDBACK'
        ev = evidence(trig, s)
        evs = '<br>'.join(f'`{_clean(x)}`' for x in ev[:4]) if ev else '—'
        L.append(f"| {s} | {STEP_NAMES[s]} | **{stat}** | {_clean(rec.get('by',''))} | "
                 f"{rec.get('utc','')} | {evs} |")
    fbs = [(s, st[s]) for s in STEPS if st.get(s,{}).get('feedback')]
    if fbs:
        L += ['', '## Feedback trail (each item MUST be routed — PI_REVIEW_PROTOCOL)', '']
        for s, rec in fbs:
            for f in rec['feedback']:
                L.append(f"- step {s} ({rec.get('utc','')}): “{f['text']}” — routed: "
                         f"{f.get('routed','**PENDING — protocol defect if it stays here**')}")
    open(out,'w').write('\n'.join(L)+'\n')
    print(f'WROTE {os.path.relpath(out, ROOT)}')

def downstream_warning(trig, step, st):
    later = [s for s in STEPS[STEPS.index(step)+1:] if st.get(s,{}).get('status')=='APPROVED']
    if later:
        print(f'!! NR-19: steps {",".join(later)} were approved on the OLD step-{step} state.')
        print(f'!! Run: python3 dev/invalidate_downstream.py --trig {trig} --from-step {step}')

if __name__=='__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--trig', required=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--present'); g.add_argument('--approve'); g.add_argument('--feedback-only')
    ap.add_argument('--by'); ap.add_argument('--feedback')
    a = ap.parse_args()
    _valid_trig(a.trig)
    st = load(a.trig)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    step = a.present or a.approve or a.feedback_only
    if step:
        if step not in STEPS:
            sys.stderr.write(f'ERROR: unknown step {step}\n'); sys.exit(2)
        rec = st.setdefault(step, {})
        if a.present:
            # PRESENTED must carry identity + real evidence, else it "asserts what it cannot link"
            if not a.by:
                sys.stderr.write('ERROR: --by required for --present\n'); sys.exit(2)
            if not evidence(a.trig, step):
                sys.stderr.write(f'ERROR: no evidence on disk for step {step}; cannot mark PRESENTED\n'); sys.exit(2)
            rec.update(status='PRESENTED', by=_clean(a.by), utc=now)
        if a.approve or a.feedback_only:
            if not a.by:                       # runtime check, NOT assert (survives python -O)
                sys.stderr.write('ERROR: --by is required on a stamp (never fabricate an approver)\n'); sys.exit(2)
            if a.approve:
                rec.update(status='APPROVED', by=_clean(a.by), utc=now)
                # reapproval clears stale feedback-pending metadata
                for f in rec.get('feedback',[]): f.setdefault('routed','(pre-approval)')
            if a.feedback:
                rec.setdefault('feedback',[]).append(
                    {'text':_clean(a.feedback),'by':_clean(a.by),'utc':now})
                print('FEEDBACK RECORDED — now route it (distiller, same session):')
                print('  writing->WritingHelper | figure->FigureVisionQC contract | '
                      'result->L-series | method->skill+code | process->register NR row')
            downstream_warning(a.trig, step, st)
        save(a.trig, st)
    build(a.trig)
