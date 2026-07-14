"""Per flagged burst: ref-detector count LC with Claude vs Codex source windows shaded."""
import sys, os, json, glob
os.chdir('/Users/salim/Desktop/Projects/SingleRest/Two_Breaks')
import numpy as np
from astropy.io import fits
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.makedirs('/tmp/flag_lc', exist_ok=True)
flags = [l.split()[0] for l in open(sys.argv[1]) if l.strip()]

def tte(trig, det):
    g=sorted(glob.glob(f'data/{trig}/glg_tte_{det}_{trig}_v*.fit*'))
    return g[-1] if g else None

for trig in flags:
    cl=json.load(open(f'results/approval/{trig}_claude.json'))
    cxp=f'results/approval/{trig}_codex.json'
    cx=json.load(open(cxp)) if os.path.exists(cxp) else None
    nai=[d for d in cl['detectors'] if d.startswith('n')]
    ref=nai[0] if nai else cl['detectors'][0]
    f=tte(trig,ref)
    if not f: print(f"{trig}: no TTE for {ref}"); continue
    h=fits.open(f); T0=h['PRIMARY'].header['TRIGTIME']
    eb=h['EBOUNDS'].data; ev=h['EVENTS'].data
    lo,hi=(8.,900.) if ref.startswith('n') else (250.,40000.)
    keep=(eb['E_MIN']>=lo)&(eb['E_MAX']<=hi)
    chans=set(eb['CHANNEL'][keep])
    t=ev['TIME']-T0; pha=ev['PHA']
    m=np.isin(pha,list(chans)); t=t[m]
    s_cl=cl['source']; s_cx=cx['source'] if cx else None
    span_lo=min(s_cl['t1'], s_cx['t1'] if s_cx else s_cl['t1'])-25
    span_hi=max(s_cl['t2'], s_cx['t2'] if s_cx else s_cl['t2'])+25
    tt=t[(t>=span_lo)&(t<=span_hi)]
    bw=1.024; bins=np.arange(span_lo,span_hi+bw,bw)
    cnt,edges=np.histogram(tt,bins=bins); rate=cnt/bw; ctr=0.5*(edges[:-1]+edges[1:])
    fig,ax=plt.subplots(figsize=(11,4.2))
    ax.step(ctr,rate,where='mid',color='0.25',lw=0.9)
    ax.axvspan(s_cl['t1'],s_cl['t2'],color='tab:blue',alpha=0.22,label=f"Claude src [{s_cl['t1']:.1f},{s_cl['t2']:.1f}]")
    if s_cx: ax.axvspan(s_cx['t1'],s_cx['t2'],color='tab:orange',alpha=0.22,label=f"Codex src [{s_cx['t1']:.1f},{s_cx['t2']:.1f}]")
    for x in (s_cl['t1'],s_cl['t2']): ax.axvline(x,color='tab:blue',ls='--',lw=1)
    if s_cx:
        for x in (s_cx['t1'],s_cx['t2']): ax.axvline(x,color='tab:orange',ls=':',lw=1.2)
    ax.set_xlabel('t - T0 (s)'); ax.set_ylabel('counts / s'); ax.set_xlim(span_lo,span_hi)
    ax.set_title(f"{trig}  ref={ref}  ({lo:.0f}-{hi:.0f} keV) — SOURCE-EXTENT flag",fontsize=11)
    ax.legend(loc='upper right',fontsize=9,framealpha=0.9)
    ax.tick_params(direction='in',which='both',top=True,right=True)
    fig.tight_layout(); fig.savefig(f'/tmp/flag_lc/{trig}.png',dpi=115); plt.close(fig)
    print(f"{trig}: {ref} Claude[{s_cl['t1']:.1f},{s_cl['t2']:.1f}] vs Codex[{s_cx['t1']:.1f},{s_cx['t2']:.1f}]" if s_cx else f"{trig}: no codex")
print("saved to /tmp/flag_lc/")
