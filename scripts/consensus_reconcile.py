"""Reconcile Claude vs Codex background decisions -> consensus decision.json + flags."""
import sys, json, os
os.chdir('/Users/salim/Desktop/Projects/SingleRest/Two_Breaks')
bursts = open(sys.argv[1]).read().split()

def load(t, who):
    p=f'results/approval/{t}_{who}.json'
    return json.load(open(p)) if os.path.exists(p) else None

def dets(d):  return set(d.get('detectors',[]))
def jacc(a,b): 
    u=a|b; return len(a&b)/len(u) if u else 0.0
def src(d):   s=d.get('source',{}); return (float(s['t1']),float(s['t2']))
def iou(a,b):
    lo=max(a[0],b[0]); hi=min(a[1],b[1]); inter=max(0,hi-lo)
    uni=(a[1]-a[0])+(b[1]-b[0])-inter
    return inter/uni if uni>0 else 0.0

def build_decision(t, ref):
    """consensus decision.json from the reference (Claude) decision."""
    wl = ref['windows']
    wmap = {}
    for w in wl:
        d=w['detector'] if isinstance(w,dict) else None
        if d: wmap[d]={'pre':w['pre'],'post':w['post'],'window_source':'adjusted'}
    return {'trigger':t,'approver':'Claude+Codex (AI consensus)','mode':'ai_vision',
            'detectors':ref['detectors'],'windows':wmap,
            'source':{'t1':src(ref)[0],'t2':src(ref)[1]}}

approved=[]; flagged=[]
for t in bursts:
    cl=load(t,'claude'); cx=load(t,'codex')
    if cl is None: flagged.append((t,'no_claude')); continue
    if cx is None: flagged.append((t,'no_codex_or_timeout')); continue
    dj=jacc(dets(cl),dets(cx)); si=iou(src(cl),src(cx))
    if dj>=0.8 and si>=0.5:
        dec=build_decision(t,cl)
        # validate source-in-gap for every detector; auto-repair TRIVIAL (<=3s) overlaps
        # (background edge nudged to clear the AGREED source; not a science change)
        REPAIR_MAX=3.0; s1=dec['source']['t1']; s2=dec['source']['t2']; repaired=False; ok=True
        for d,w in dec['windows'].items():
            if w['pre'][1]>s1:
                if w['pre'][1]-s1<=REPAIR_MAX: w['pre'][1]=s1; repaired=True
                else: ok=False; break
            if s2>w['post'][0]:
                if s2-w['post'][0]<=REPAIR_MAX: w['post'][0]=s2; repaired=True
                else: ok=False; break
        if ok:
            json.dump(dec,open(f'results/approval/{t}_decision.json','w'),indent=1)
            tag=f'det_jacc={dj:.2f} src_iou={si:.2f}'+(' [edge auto-repaired <=3s]' if repaired else '')
            approved.append((t,tag))
        else:
            flagged.append((t,f'source_outside_gap >3s (dj={dj:.2f} si={si:.2f})'))
    else:
        flagged.append((t,f'divergent det_jacc={dj:.2f} src_iou={si:.2f} | Claude={sorted(dets(cl))} Codex={sorted(dets(cx))}'))

print(f"\n=== CONSENSUS RESULT: {len(approved)} auto-approved, {len(flagged)} flagged ===")
for t,r in approved: print(f"  APPROVE {t}: {r}")
for t,r in flagged:  print(f"  FLAG    {t}: {r}")
