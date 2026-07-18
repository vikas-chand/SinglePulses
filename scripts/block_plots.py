"""Nice Bayesian-block plot: fine net LC (grey) + BB blocks as a bold adaptive step
   (mean net rate per block) + edges, significance-shaded. use_background=True blocks."""
import os, glob, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from astropy.io import fits
from astropy.table import Table
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm

cat=Table.read('results/background_intervals.ecsv',format='ascii.ecsv')
def tte(trig,det):
    g=sorted(glob.glob(f'data/{trig}/glg_tte_{det}_{trig}_v*.fit*')); return g[-1] if g else None

for trig in sys.argv[1:]:
    blkf=os.path.join(os.environ.get('BLK_ROOT','results/clean_blocks_consensus'),f'bb_blocks_spectral_{trig}.ecsv')
    bt=Table.read(blkf,format='ascii.ecsv')
    ref=str(bt['DETECTOR'][0]); sub=bt[bt['DETECTOR']==ref]
    edges=sorted(set(list(sub['T_START'])+list(sub['T_STOP'])))
    starts=np.array(sub['T_START'],float); stops=np.array(sub['T_STOP'],float); sig=np.array(sub['SIGNIFICANCE'],float)
    call=cat[(cat['TRIGGER_NAME']==trig)]
    if len(call)==0: print(f"{trig}: not in catalog, skip"); continue
    match=[x for x in call if str(x['DETECTOR']).strip()==ref]
    c=match[0] if match else call[0]   # block-ref not approved -> use any row's windows (~uniform)
    pre=(float(c['BKG_NEG_START']),float(c['BKG_NEG_STOP'])); post=(float(c['BKG_POS_START']),float(c['BKG_POS_STOP']))
    f=tte(trig,ref); h=fits.open(f); T0=h['PRIMARY'].header['TRIGTIME']; eb=h['EBOUNDS'].data; ev=h['EVENTS'].data
    lo,hi=(8.,900.) if ref.startswith('n') else (250.,40000.)
    chans=set(eb['CHANNEL'][(eb['E_MIN']>=lo)&(eb['E_MAX']<=hi)])
    t=ev['TIME']-T0; t=t[np.isin(ev['PHA'],list(chans))]
    s1,s2=float(c['SRC_START']),float(c['SRC_STOP'])          # source interval
    x0=pre[0]-3; x1=post[1]+3                                 # span both bkg windows +3s
    # fine net LC
    bw=0.064; fb=np.arange(x0,x1+bw,bw); cnt,edg=np.histogram(t[(t>=x0)&(t<=x1)],bins=fb); rate=cnt/bw; ctr=0.5*(edg[:-1]+edg[1:])
    # poly bkg from approved windows
    m=((ctr>=pre[0])&(ctr<=pre[1]))|((ctr>=post[0])&(ctr<=post[1]))
    # need wider range for bkg fit -> use raw over pre..post
    fb2=np.arange(pre[0],post[1]+bw,bw); c2,e2=np.histogram(t[(t>=pre[0])&(t<=post[1])],bins=fb2); r2=c2/bw; ct2=0.5*(e2[:-1]+e2[1:])
    mm=((ct2>=pre[0])&(ct2<=pre[1]))|((ct2>=post[0])&(ct2<=post[1]))
    coef=np.polyfit(ct2[mm],r2[mm],2); bkg=np.polyval(coef,ctr); net=rate-bkg
    # net rate per block
    blk_net=[net[(ctr>=s)&(ctr<e)].mean() if ((ctr>=s)&(ctr<e)).any() else 0 for s,e in zip(starts,stops)]
    fig,ax=plt.subplots(figsize=(11,4.6))
    ax.step(ctr,net,where='mid',color='0.7',lw=0.7,label=f'net LC ({bw*1000:.0f} ms)')
    # blocks as bold step + significance color
    norm=plt.Normalize(5, max(10,sig.max())); cmap=cm.viridis
    for s,e,bn,sg in zip(starts,stops,blk_net,sig):
        ax.plot([s,e],[bn,bn],color=cmap(norm(sg)),lw=2.6,solid_capstyle='butt')
    for x in edges: ax.axvline(x,color='0.5',ls=':',lw=0.6)
    ax.axhline(0,color='k',lw=0.5)
    # shaded background intervals (green) + source interval markers (red dotted verticals)
    ax.axvspan(*pre,color='tab:green',alpha=0.15,label='bkg windows'); ax.axvspan(*post,color='tab:green',alpha=0.15)
    for xs in (s1,s2): ax.axvline(xs,color='tab:red',ls='--',lw=1.3)
    ax.axvline(s1,color='tab:red',ls='--',lw=1.3,label='source interval')
    sm=cm.ScalarMappable(norm=norm,cmap=cmap); sm.set_array([]); cb=fig.colorbar(sm,ax=ax,pad=0.01); cb.set_label('block significance (σ)',fontsize=9)
    ax.set_xlabel('t - T0 (s)'); ax.set_ylabel('net counts / s'); ax.set_xlim(x0,x1)
    ax.set_title(f"{trig}  ref={ref}  —  {len(starts)} Bayesian blocks (p0=0.01, use_background=True)",fontsize=10)
    ax.legend(loc='upper right',fontsize=8,framealpha=0.9); ax.tick_params(direction='in',which='both',top=True,right=True)
    fig.tight_layout(); os.makedirs('plots/block_plots',exist_ok=True)
    fig.savefig(f'plots/block_plots/{trig}.png',dpi=115); plt.close(fig)
    print(f"{trig}: {len(starts)} blocks, sig {sig.min():.0f}-{sig.max():.0f}")
