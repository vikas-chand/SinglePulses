"""Per-burst 2-panel: ref-detector LC + FITTED background poly (through approved pre/post),
   source interval shaded; bottom = background-subtracted net rate."""
import os, glob, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from astropy.io import fits
from astropy.table import Table
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.makedirs('plots/approved_selections', exist_ok=True)
cat=Table.read('results/background_intervals.ecsv',format='ascii.ecsv')
def tte(trig,det):
    g=sorted(glob.glob(f'data/{trig}/glg_tte_{det}_{trig}_v*.fit*')); return g[-1] if g else None
def fit_bkg(t,y,pre,post):
    m=((t>=pre[0])&(t<=pre[1]))|((t>=post[0])&(t<=post[1]))
    if m.sum()<4: return None,None
    best=None
    for deg in (1,2,3):
        try:
            c=np.polyfit(t[m],y[m],deg); r=y[m]-np.polyval(c,t[m]); chi=np.sum(r**2)/max(1,(m.sum()-deg-1))
            if best is None or chi<best[1]: best=(c,chi,deg)
        except Exception: pass
    return (best[0],best[2]) if best else (None,None)

targets=sys.argv[1:] if len(sys.argv)>1 else sorted(set(str(x) for x in cat['TRIGGER_NAME']))
ok=0; fail=[]
for trig in targets:
    sub=cat[cat['TRIGGER_NAME']==trig]
    dets=[str(r['DETECTOR']).strip() for r in sub]
    nai=[d for d in dets if d.startswith('n')]; ref=nai[0] if nai else dets[0]
    r=sub[[str(x['DETECTOR']).strip()==ref for x in sub]][0]
    pre=(float(r['BKG_NEG_START']),float(r['BKG_NEG_STOP'])); post=(float(r['BKG_POS_START']),float(r['BKG_POS_STOP']))
    src=(float(r['SRC_START']),float(r['SRC_STOP'])); appr=str(r['APPROVED_BY'])
    f=tte(trig,ref)
    if not f: fail.append(trig); continue
    h=fits.open(f); T0=h['PRIMARY'].header['TRIGTIME']; eb=h['EBOUNDS'].data; ev=h['EVENTS'].data
    lo,hi=(8.,900.) if ref.startswith('n') else (250.,40000.)
    chans=set(eb['CHANNEL'][(eb['E_MIN']>=lo)&(eb['E_MAX']<=hi)])
    tev=ev['TIME']-T0; tev=tev[np.isin(ev['PHA'],list(chans))]
    x0=pre[0]-15; x1=post[1]+15; tt=tev[(tev>=x0)&(tev<=x1)]
    bw=1.024; bins=np.arange(x0,x1+bw,bw); cnt,edg=np.histogram(tt,bins=bins); rate=cnt/bw; ctr=0.5*(edg[:-1]+edg[1:])
    coef,deg=fit_bkg(ctr,rate,pre,post)
    bkg=np.polyval(coef,ctr) if coef is not None else np.zeros_like(ctr)
    fig,(ax,ax2)=plt.subplots(2,1,figsize=(11,5.6),sharex=True,gridspec_kw={'height_ratios':[2,1]})
    ax.step(ctr,rate,where='mid',color='0.25',lw=0.9,label='count rate')
    if coef is not None: ax.plot(ctr,bkg,color='tab:orange',lw=1.6,label=f'fitted bkg (poly deg {deg})')
    ax.axvspan(*pre,color='tab:green',alpha=0.16); ax.axvspan(*post,color='tab:green',alpha=0.16,label='bkg windows')
    ax.axvspan(*src,color='tab:red',alpha=0.16,label='source')
    ax.set_ylabel('counts / s'); ax.legend(loc='upper right',fontsize=8,framealpha=0.9)
    ax.set_title(f"{trig}  ref={ref}  dets={dets}\npre{pre} post{post} src{src}  |  {appr}",fontsize=9)
    ax.tick_params(direction='in',which='both',top=True,right=True)
    ax2.axhline(0,color='0.6',lw=0.8); ax2.step(ctr,rate-bkg,where='mid',color='navy',lw=0.9)
    ax2.axvspan(*src,color='tab:red',alpha=0.16)
    ax2.set_xlabel('t - T0 (s)'); ax2.set_ylabel('net'); ax2.set_xlim(x0,x1); ax2.tick_params(direction='in',which='both',top=True,right=True)
    fig.tight_layout(); fig.savefig(f'plots/approved_selections/{trig}.png',dpi=105); plt.close(fig); ok+=1
print(f"generated {ok}; failed={fail}")
