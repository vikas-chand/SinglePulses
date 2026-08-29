#!/usr/bin/env python3
"""Publication figures for the GRBs Agent in the Nat-Mach-Intell diagram
style the PI pointed at (ChemCrow, s42256-024-00832-8): white ground, light
grey rounded panels, magenta->violet accent ring, thin arrows, bold panel
letters, sans-serif. Regenerate after any architecture change."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

plt.rcParams.update({'font.family':'Helvetica', 'font.size':9,
                     'text.color':'#1a1a1a', 'svg.fonttype':'none'})
M1,M2,M3,M4 = '#c81f8e','#a026a8','#7a2ea0','#5a34c9'   # magenta->violet
GREY,EDGE,INK,GRN = '#f4f4f4','#c9c9c9','#1a1a1a','#2e7d55'

def box(ax,x,y,w,h,text,fc=GREY,ec=EDGE,fs=8.2,tc=INK,weight='normal',align='left',pad=0.012):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.012',
                                fc=fc,ec=ec,lw=0.8))
    tx = x+pad if align=='left' else x+w/2
    ax.text(tx,y+h/2,text,fontsize=fs,color=tc,weight=weight,
            ha=align if align=='center' else 'left',va='center',linespacing=1.45)

def arrow(ax,p,q,color=INK,lw=1.0,style='-|>',rad=0.0):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle=style,mutation_scale=11,
                 lw=lw,color=color,connectionstyle=f'arc3,rad={rad}'))

# ================= FIG 1 — overview: the gated reasoning loop ==============
fig,axs = plt.subplots(1,2,figsize=(12.2,6.4)); fig.subplots_adjust(wspace=0.06)
for ax in axs: ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')

ax=axs[0]
ax.text(0.01,0.985,'a',weight='bold',fontsize=14,va='top')
cx,cy,R,r = 0.52,0.55,0.205,0.135
# ring in 4 gradient arcs with a GAP at the bottom (the human gate breaks the loop)
arcs=[(100,190,M1),(10,100,M2),(-60,10,M3),(-155,-88,M4)]
for a0,a1,c in arcs:
    ax.add_patch(Wedge((cx,cy),R,a0,a1,width=R-r,fc=c,ec='none'))
ax.text(cx,cy+0.015,'GRBs\nAgent',ha='center',va='center',fontsize=13,weight='bold')
ax.text(cx,cy-0.06,'no actor verifies\nits own work',ha='center',va='center',fontsize=6.8,style='italic',color='#666666')
st=[(0.335,0.86,'1. Read\nskill-reader loads the law:\nskills · ledgers · contracts'),
    (0.75,0.86,'2. Plan\ndispatcher names the roster,\ngates and unguarded debt'),
    (0.80,0.30,'3. Produce\npipeline tools fit, measure,\nrender — sidecar provenance'),
    (0.215,0.345,'4. Verify\nfresh-context gates attack\nfigures · numbers ·\nseeds · ties')]
for x,y,t in st:
    h,t2 = t.split('\n',1)
    ax.text(x,y,h,fontsize=9.5,weight='bold',ha='center')
    ax.text(x,y-0.035,t2,fontsize=7.4,ha='center',va='top',color='#444444',linespacing=1.4)
# the human gate bridging the ring gap at bottom
box(ax,cx-0.115,cy-R-0.075,0.23,0.075,'PI GATE\napprove · feed back',fc='#ffffff',ec=M3,
    fs=8.4,weight='bold',align='center')
ax.text(cx,0.012,'the loop closes only through the human',fontsize=6.8,
        ha='center',style='italic',color='#666666')
box(ax,0.015,0.50,0.175,0.17,'Input\nburst trigger,\nGBM · LLE · LAT,\n25 skill files',fs=7.4)
arrow(ax,(0.19,0.585),(cx-R-0.02,0.585))
box(ax,0.015,0.015,0.185,0.135,'Feedback routes\nsame session:\ncontracts, lessons,\nregister rows',fs=7.0)
arrow(ax,(cx-0.05,cy-R-0.085),(0.205,0.105),rad=-0.15)
box(ax,0.845,0.50,0.15,0.17,'Output\ngated paper ·\ncensus rows ·\nstate S12',fs=7.4)
arrow(ax,(cx+R+0.02,0.585),(0.845,0.585))

ax=axs[1]
ax.text(0.01,0.985,'b',weight='bold',fontsize=14,va='top')
cx,cy,R,r=0.5,0.53,0.20,0.125
quads=[(45,135,M1,'Verifiers'),(-45,45,M2,'Gatekeepers'),(135,225,M3,'Orchestration'),(225,315,M4,'Enforcers')]
for a0,a1,c,_ in quads:
    ax.add_patch(Wedge((cx,cy),R,a0+3,a1-3,width=R-r,fc=c,ec='none'))
ax.text(cx,cy+0.02,'the\nroster',ha='center',va='center',fontsize=12,weight='bold')
ax.text(cx,cy-0.045,'A1-A18',ha='center',va='center',fontsize=7.2,color='#666666')
corners=[(0.03,0.93,'Verifiers',M1,['figure-verifier — vision vs contract','numbers-verifier — recompute all','seed-auditor — MC replayable','tie-reporter — dAIC<2 = tie set','notes-reviewers — per-bin critique']),
 (0.97,0.93,'Gatekeepers',M2,['admission-gate — no unscreened row','port-verifier — code ports proven','prior-art-reader — never re-derive','conformance (NR-24) — R1-R5','literature — blind-first, bibcodes']),
 (0.03,0.24,'Orchestration & oversight',M3,['skill-reader — law per step','dispatcher — roster per task','queue manager — one loop','distiller — incident -> lesson','approver — the PI\'s seat','external auditor — different model, advisory']),
 (0.97,0.24,'Enforcers (code, not LLM)',M4,['no-ship hook — unledgered = blocked','dispatch hook — no plan, no launch','RAM arbiter — GB, not cores','tools (e.g.): cascade · live report · board'])]
for x,y,h,c,items in corners:
    ha='left' if x<0.5 else 'right'
    ax.text(x,y,h,fontsize=9,weight='bold',color=c,ha=ha)
    for i,it in enumerate(items):
        ax.text(x,y-0.042-i*0.038,'• '+it,fontsize=7.0,ha=ha,color='#333333')
fig.savefig('docs/figures/fig1_agent_overview.png',dpi=300,bbox_inches='tight',facecolor='white')
fig.savefig('docs/figures/fig1_agent_overview.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)

# ============== FIG 2 — state machine + failure taxonomy ====================
fig,ax=plt.subplots(figsize=(12.6,5.6)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(0.005,0.985,'a',weight='bold',fontsize=14,va='top')
states=['S0\nregistered','S1\nstage-1\napproved','S2\nbinned','S3\nfit\n24 models','S4\nretried','S5\npromoted\nhash-current',
        'S6\ntemporal','S7\nproducts','S8\nassembled','S9\nGATED','S10\npresented','S11\nAPPROVED','S12\nbundled']
n=len(states); x0,x1,y,w,h=0.03,0.97,0.72,0.062,0.16
xs=np.linspace(x0,x1-w,n)
gatecol={9:M1,11:M4}
for i,(x,s) in enumerate(zip(xs,states)):
    fc='#ffffff' if i in gatecol else GREY
    ec=gatecol.get(i,EDGE)
    box(ax,x,y,w,h,s,fc=fc,ec=ec,fs=6.7,align='center',weight='bold' if i in gatecol else 'normal')
    if i<n-1: arrow(ax,(x+w+0.002,y+h/2),(xs[i+1]-0.002,y+h/2),lw=0.9)
# demotion arc S9->S5 + SX
arrow(ax,(xs[9]+w/2,y-0.012),(xs[5]+w/2,y-0.012),color=M1,lw=1.1,rad=-0.20)
ax.text((xs[9]+xs[5])/2+w/2,y-0.175,'invalidation cascade (NR-19): upstream change demotes to the last hash-current state',
        fontsize=7.2,ha='center',color=M1,style='italic')
box(ax,xs[0],y-0.30,0.15,0.10,'SX structural exclusion\nreason ALWAYS stated\n(from any state)',fc='#ffffff',ec='#888888',fs=6.2,align='center')
arrow(ax,(xs[1]+w/2,y-0.005),(xs[0]+0.075,y-0.195),color='#888888',lw=0.9)
ax.text(0.005,0.44,'b',weight='bold',fontsize=14,va='top')
classes=[('F-TRANSIENT','environment pressure','HOLD + resume',M4),
         ('F-STRUCTURAL','data cannot yield it','LABEL + continue',GRN),
         ('F-CONTRACT','contract violated','STOP + register row',M1),
         ('F-ORDER','out of sequence','WAIT — manager reorders',M3),
         ('F-SILENT','found after acceptance','DEMOTE + CASCADE\n+ make loud forever',M2),
         ('F-GUARD','the checker is wrong','FIX checker,\nre-run its gates','#8a6d1d')]
cw=0.138
for i,(nm,d,b,c) in enumerate(classes):
    x=0.030+i*(cw+0.0215)
    box(ax,x,0.16,cw,0.20,f'{nm}\n{d}',fc='#ffffff',ec=c,fs=6.9,align='center')
    box(ax,x,0.045,cw,0.085,b,fc=c,ec=c,fs=6.8,tc='#ffffff',align='center',weight='bold')
ax.text(0.5,0.005,'every class ends in DISTILL: lesson at the strongest layer + register row, same session — an error message is never a behavior',
        fontsize=7.6,ha='center',style='italic',color='#444444')
fig.savefig('docs/figures/fig2_state_machine.png',dpi=300,bbox_inches='tight',facecolor='white')
fig.savefig('docs/figures/fig2_state_machine.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)

# ============== FIG 3 — human–AI collaboration (their Fig 3 form) ===========
fig,ax=plt.subplots(figsize=(11.2,6.2)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(0.16,0.975,'Principal Investigator',fontsize=10.5,weight='bold',ha='center')
ax.text(0.80,0.975,'GRBs Agent',fontsize=10.5,weight='bold',ha='center')
ax.text(0.485,0.975,'gated collaboration',fontsize=8.5,ha='center',style='italic',color='#666666')
box(ax,0.02,0.60,0.30,0.33,
    'Task input:\n'
    '• the science question and the sample\n'
    '• Stage-1 selections (detectors ·\n   background · source) — approved\n'
    '• conventions, as quoted rulings\n'
    '• ΔAIC tracking rule: >6 in 1–2 bins',fs=7.6)
box(ax,0.52,0.52,0.46,0.41,
    'Agent actions:\n'
    '1. read the law (skills · ledgers · contracts)\n'
    '2. plan the roster; name unguarded debt\n'
    '3. bin (Bayesian blocks) · fit 24 models/bin ·\n    mandated retry · hash-current promotion\n'
    '4. temporal: 3 MVT primitives · pulse-scaled lag · windowed T90\n'
    '5. render SEDs · montages · evolution — refusals labeled\n'
    '6. verify: vision + numbers + seeds + ties (fresh contexts)\n'
    '7. reconcile literature blind-first; attribute every mismatch\n'
    '8. assemble the paper; conformance-gate it (R1–R5)',fs=7.4)
box(ax,0.02,0.13,0.30,0.36,
    'Human actions:\n'
    '• read the live report (evidence-linked)\n'
    '• APPROVE (identity-bound stamp)\n   or FEED BACK — routed same session\n'
    '• amend contracts in own words\n'
    '• accept lessons; own the freeze\n'
    '• a PI catch => an agent was missing',fs=7.6)
box(ax,0.52,0.10,0.46,0.33,
    'Final answer:\n'
    'the gated per-burst paper + census rows, e.g.\n'
    'break-preferring models TRACKED in 4/104 bursts;\n'
    'two-break (DSBPL family) in 3/104 — strict: bn110928180\n'
    '(literal margins 6.05/7.2 in its 2 tracked bins;\n'
    'feature-level 24.0/9.2 there, 9-39 across its 4 bins);\n'
    'thermal: per-burst candidates, e.g. kT = 16.5 / 22.4 / 25.1 keV;\n'
    'the formally strongest (kT=1.55 keV) removed as an\n'
    'edge artifact (3.92 kT gate)\n'
    '— every number recomputed, every figure ledgered,\nevery absence reasoned',fs=7.0)
arrow(ax,(0.32,0.765),(0.52,0.72),lw=1.1)
arrow(ax,(0.75,0.52),(0.75,0.43),lw=1.1)
arrow(ax,(0.515,0.265),(0.32,0.31),lw=1.1)
ax.text(0.42,0.77,'gates',fontsize=7.2,color='#666666',style='italic')
ax.text(0.335,0.325,'live report',fontsize=7.2,color='#666666',style='italic')
ax.text(0.985,0.02,'census: results/campaign/model_preference.ecsv · kT: per-burst papers + bb_census',fontsize=5.8,color='#888888',ha='right')
fig.savefig('docs/figures/fig3_collaboration.png',dpi=300,bbox_inches='tight',facecolor='white')
fig.savefig('docs/figures/fig3_collaboration.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
import json, hashlib, subprocess
def sha(f): return hashlib.sha256(open(f,'rb').read()).hexdigest()
commit = subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()
claims = {
 'fig1_agent_overview': {'actors':'A1-A18 per dev/ai_guides/AgentRoster.md',
   'skill_files':25, 'loop':'read-plan-produce-verify closed by PI gate'},
 'fig2_state_machine': {'states':'S0..S12+SX per AgentSkeleton.md §1',
   'failure_classes':6, 'demotion':'S9->S5 example (NR-19)'},
 'fig3_collaboration': {'break_preferring_tracked':'4/104','two_break_tracked':'3/104',
   'strict':'bn110928180 literal 6.05/7.2 bins 0,3; feature 24.0/9.2 there; 9-39 over 4 bins',
   'thermal_examples_keV':[16.5,22.4,25.1],'edge_artifact_kT_keV':1.55,
   'primitives':['results/campaign/model_preference.ecsv',
     'paper/GRB081125496/main.tex',
     'results/convention_check/bn110928180/spectral_fits.ecsv',
     'results/campaign/bb_census.ecsv','paper/GRB090530/main.tex','paper/GRB090804/main.tex']}}
for name,c in claims.items():
    png=f'docs/figures/{name}.png'
    json.dump({'figure':png,'sha256':sha(png),'generator':'dev/gen_paper_figures.py',
               'commit':commit,'claims':c}, open(f'docs/figures/{name}.json','w'), indent=1)
print('3 figures rendered (png+pdf) + same-run sidecars in docs/figures/')
