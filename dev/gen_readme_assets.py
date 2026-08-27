#!/usr/bin/env python3
"""Generate the README architecture + contribution SVGs from spec dicts.
Deterministic layout; rerun after any architecture change (R1: one generator)."""
import html

C = {'green':'#2e7d55','blue':'#3f6098','purple':'#7c5cb0','dark':'#1f2a44',
     'teal':'#1b7a8c','amber':'#b07714','rose':'#b23a6b','grey':'#6b7280',
     'ink':'#1c2126','paper':'#ffffff','chipfg':'#ffffff'}

def esc(s): return html.escape(s)

def chip(x,y,w,h,text,fill,fs=11,fg='#fff',rx=4):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>' 
            f'<text x="{x+w/2}" y="{y+h/2+fs*0.35}" text-anchor="middle" '
            f'font-size="{fs}" fill="{fg}" font-family="Helvetica,Arial,sans-serif">{esc(text)}</text>')

def panel(x,y,w,h,title,fill,body_fill='#ffffff',stroke='#d0d0d0'):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{body_fill}" stroke="{stroke}"/>' 
            f'<rect x="{x}" y="{y}" width="{w}" height="26" rx="8" fill="{fill}"/>' 
            f'<rect x="{x}" y="{y+13}" width="{w}" height="13" fill="{fill}"/>' 
            f'<text x="{x+w/2}" y="{y+18}" text-anchor="middle" font-size="13" font-weight="bold" '
            f'fill="#fff" font-family="Helvetica,Arial,sans-serif">{esc(title)}</text>')

def chiprow(x,y,w,items,fill,fs=10.5,ch=20,gap=6,cols=None):
    out=[]; cols=cols or len(items)
    cw=(w-gap*(cols-1))/cols
    for i,t in enumerate(items):
        r,c=divmod(i,cols)
        out.append(chip(x+c*(cw+gap), y+r*(ch+gap), cw, ch, t, fill, fs))
    rows=(len(items)+cols-1)//cols
    return ''.join(out), rows*(ch+gap)-gap

W=1160
S=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 900" font-family="Helvetica,Arial,sans-serif">']
S.append(f'<rect width="{W}" height="900" fill="#fbfaf7"/>')
S.append(f'<text x="{W/2}" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="{C["ink"]}">GRBs Agent</text>')

# Row 1: human + collaborator surfaces
S.append(panel(20,50,555,86,'Human Gates (the PI holds these)',C['dark']))
r,_=chiprow(32,86,531,['Stage-1 GUI approvals','Live-report stamps','Contract amendments','Freeze ruling'],C['dark'],cols=4)
S.append(r)
S.append(panel(595,50,545,86,'Deliverable Surfaces',C['dark']))
r,_=chiprow(607,86,521,['Per-burst papers','Reports (md+pdf)','Design page','Bundles + manifests'],C['dark'],cols=4)
S.append(r)

# Row 2: agent roster
S.append(panel(20,152,1120,92,'Agent Roster — producer never verifies its own work',C['blue']))
r,_=chiprow(32,188,1096,['dispatcher','skill-reader','figure-verifier','numbers-verifier','seed-auditor',
                          'tie-reporter','admission-gate','port-verifier','prior-art-reader','distiller'],C['blue'],cols=5)
S.append(r)

# Row 3: orchestration
S.append(panel(20,260,1120,92,'Orchestration — the Skeleton',C['purple']))
r,_=chiprow(32,296,1096,['14-state machine (evidence on disk)','6-class failure taxonomy','queue manager',
                          'RAM arbiter (GB, not cores)','mechanical hooks (no-ship · dispatch)','invalidation cascade (NR-19)'],C['purple'],cols=3)
S.append(r)

# Row 4: engine columns
cols_spec=[('Stage-1 & Data',C['green'],['HEASARC fetch (GBM·LLE·LAT)','detector selection ≤50°+BCAT','background windows (hug)','source interval','Bayesian-block binning + S≥10']),
 ('Spectral Engine',C['amber'],['24-model menu','seeded multistarts','ΔAIC≥10 chain gate','validity + 3.92kT edge gate','EAC cross-calibration','mandated retry contract','preference ≠ argmin (ΔAIC>6)']),
 ('Temporal Engine',C['rose'],['windowed T90/T50 + MC','MVT ×3 primitives','pulse-scaled lag (DCCF)','pulse morphology φ','estimator labels ride every number']),
 ('SED & Products',C['teal'],['strict-XSPEC unfolded SED','native 68% band + validity','AIC-ordered montages','parameter evolution','refusals as labeled results']),
 ('Papers & Context',C['grey'],['queue-ordered assembler','blind-first literature','ADS-only bibliography','caption voice corpus','conformance gate (R1–R5)'])]
x=20; cw=216; gap=10
for title,col,items in cols_spec:
    S.append(panel(x,368,cw,240,title,col))
    for j,t in enumerate(items):
        S.append(chip(x+8,404+j*27,cw-16,22,t,col,fs=9.6))
    x+=cw+gap

# Row 5: pipeline strip
S.append(panel(20,624,1120,80,'Per-burst pipeline (each arrow = a gated workflow; every product carries a provenance sidecar)',C['ink']))
steps=['fetch','select','bin','fit','retry','promote','temporal','products','assemble','gate','present','approve','bundle']
x=32; sw=76
for i,st in enumerate(steps):
    S.append(chip(x,662,sw,26,st,[C['green'],C['green'],C['green'],C['amber'],C['amber'],C['amber'],C['rose'],C['teal'],C['grey'],C['blue'],C['blue'],C['dark'],C['dark']][i],fs=11))
    if i<len(steps)-1:
        S.append(f'<text x="{x+sw+4}" y="679" font-size="12" fill="{C["ink"]}">→</text>')
    x+=sw+16
# Row 6: rails + external
S.append(panel(20,720,1120,60,'Rails (cross-cutting)',C['grey']))
r,_=chiprow(32,750,1096,['ENFORCEMENT: code guards → hooks → fresh verifiers → external audit → distiller',
                          'APPROVAL: live report → identity-bound stamps → feedback routes → cascade'],C['grey'],cols=2)
S.append(r)
S.append(f'<rect x="20" y="796" width="1120" height="34" rx="8" fill="#fff" stroke="#d0d0d0"/>')
S.append(f'<text x="{W/2}" y="817" text-anchor="middle" font-size="12" fill="{C["ink"]}">'
         f'External:  3ML (astromodels) · fermitools + CALDB · astropy · HEASARC · Bala MVT · LATBright toolset · Claude Code · Codex (external audit)</text>')
S.append('</svg>')
open('docs/assets/architecture.svg','w').write(''.join(S))

# ---- contribution overview ----
data=[('Science decisions\n& conventions',[('Human',90),('Claude',10),('Codex',0)]),
      ('Spectral / temporal\nengines',[('Human',15),('Claude',70),('Codex',15)]),
      ('Verification system\n& gates',[('Human',10),('Claude',75),('Codex',15)]),
      ('Skills, registers\n& skeleton',[('Human',25),('Claude',70),('Codex',5)]),
      ('Papers & reports\n(gated drafts)',[('Human',20),('Claude',60),('Codex',20)]),
      ('Approvals &\nsign-off',[('Human',100),('Claude',0),('Codex',0)])]
colors={'Human':C['green'],'Claude':'#c2622a','Codex':C['blue']}
W2,H2=1160,360
T=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W2} {H2}" font-family="Helvetica,Arial,sans-serif">']
T.append(f'<rect width="{W2}" height="{H2}" fill="#fbfaf7"/>')
T.append(f'<text x="{W2/2}" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{C["ink"]}">Contribution Overview (self-reported estimates; every AI product passes human-held gates)</text>')
lx=W2/2-140
for i,(k,c) in enumerate(colors.items()):
    T.append(f'<rect x="{lx+i*100}" y="38" width="12" height="12" fill="{c}"/>' 
             f'<text x="{lx+i*100+18}" y="49" font-size="12" fill="{C["ink"]}">{k}</text>')
bx,bw,bh,base=80,110,220,300
for i,(label,parts) in enumerate(data):
    x=bx+i*180; y=base
    for name,pct in parts:
        if pct==0: continue
        h=bh*pct/100; y-=h
        T.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{h}" fill="{colors[name]}"/>')
        if pct>=10:
            T.append(f'<text x="{x+bw/2}" y="{y+h/2+4}" text-anchor="middle" font-size="11" fill="#fff">{pct}%</text>')
    for j,line in enumerate(label.split('\n')):
        T.append(f'<text x="{x+bw/2}" y="{base+18+j*14}" text-anchor="middle" font-size="11.5" fill="{C["ink"]}">{esc(line)}</text>')
T.append('</svg>')
open('docs/assets/contribution.svg','w').write(''.join(T))
print('assets written')
