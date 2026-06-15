#!/usr/bin/env python
"""
Phase 0a: UNIFORM clean Bayesian re-blocking of all 106 bursts.

One method for the whole sample (fixes the 8 collapsed bursts + the mixed-method
state). For each burst:
  - source region = [pre_stop, post_start] from background_intervals_prototype
    (the AI-selected on-source window), per the brightest NaI;
  - brightest-NaI events, 8-900 keV, within that region;
  - Bayesian blocks: event-mode (fitness='events'); binned count-rate
    (fitness='measures', 64 ms) if > MAX_EVENTS to avoid the O(N^2) blow-up;
  - trim leading/trailing blocks whose net significance < 4.5 sigma (burst
    emission interval); if <2 blocks survive, retry with a more permissive prior;
  - write the SAME edges for every approved NaI detector (so the canonical-bin
    picker is method-independent), schema-compatible with scripts/10.

Output: results/clean_blocks/bb_blocks_spectral_<trigger>.ecsv
"""
import os, glob, warnings
warnings.filterwarnings('ignore')
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.stats import bayesian_blocks

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(BASE,'data'); RES=os.path.join(BASE,'results')
OUT=os.path.join(RES,'clean_blocks'); os.makedirs(OUT,exist_ok=True)
ELO,EHI=8.0,900.0; MAX_EVENTS=500_000; SIG_TRIM=4.5

single=Table.read(os.path.join(RES,'single_pulse_grbs.ecsv'),format='ascii.ecsv')
_clean=os.path.join(RES,'background_intervals_clean.ecsv')
bkg=Table.read(_clean if os.path.exists(_clean) else os.path.join(RES,'background_intervals_prototype.ecsv'),format='ascii.ecsv')

def load_nai(trig,det):
    f=sorted(glob.glob(f'{DATA}/{trig}/glg_tte_{det}_*.fit*'))
    if not f: return None
    with fits.open(f[0]) as h:
        ev=h['EVENTS'].data
        t0=next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
        tt=np.asarray(ev['TIME'])-t0
        eb=h['EBOUNDS'].data; emid=0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
        m=(emid[ev['PHA']]>=ELO)&(emid[ev['PHA']]<=EHI)
    return np.sort(tt[m])

def bb_edges(src, lo, hi, p0, dt=0.128):
    # Uniform Burgess-faithful binned count-rate BB (fitness='measures'): fast
    # (O(Nbins^2)) and consistent across the whole sample, regardless of count.
    e=np.arange(lo,hi+dt,dt); c=0.5*(e[:-1]+e[1:])
    cnt,_=np.histogram(src,bins=e); rate=cnt/dt; err=np.sqrt(np.maximum(cnt,1))/dt
    return bayesian_blocks(c,rate,err,fitness='measures',p0=p0)

def emission_window(tt, lo, hi, brate):
    """Tighten [lo,hi] to the actual burst-emission interval (the AI bkg window
    can be wide/offset; BB over a wide mostly-quiet window collapses to 1 block)."""
    dt=0.256; e=np.arange(lo,hi+dt,dt); c=0.5*(e[:-1]+e[1:])
    cnt,_=np.histogram(tt,bins=e); rate=cnt/dt
    noise=np.sqrt(max(brate,1e-6)/dt)
    net=np.convolve(rate-brate, np.ones(3)/3, mode='same')
    pk=int(np.argmax(net))
    if net[pk] < SIG_TRIM*noise:        # no clear peak: keep the full region
        return lo,hi
    L=pk
    while L>0 and net[L-1] > 1.0*noise: L-=1
    R=pk
    while R<len(net)-1 and net[R+1] > 1.0*noise: R+=1
    return float(c[L]-0.5), float(c[R]+0.5)

def net_sig(tt,s,e,brate):
    dur=max(e-s,1e-3); n=int(((tt>=s)&(tt<e)).sum()); bexp=brate*dur
    return (n-bexp)/np.sqrt(max(n+bexp,1.0))

def trim(edges, tt, brate):
    """drop leading/trailing blocks below SIG_TRIM; keep the contiguous emission."""
    sig=[net_sig(tt,edges[i],edges[i+1],brate) for i in range(len(edges)-1)]
    keep=[i for i,s in enumerate(sig) if s>=SIG_TRIM]
    if not keep: return edges  # nothing significant: keep all (rare)
    i0,i1=min(keep),max(keep)
    return edges[i0:i1+2]

rows_summary=[]
trigs=[os.path.basename(os.path.dirname(p)) for p in glob.glob(f'{DATA}/bn*/')]
trigs=sorted(set(trigs))
for trig in trigs:
    bk=bkg[bkg['TRIGGER_NAME']==trig]
    if len(bk)==0:
        rows_summary.append((trig,'-',0,'no bkg row')); continue
    sp=single[single['TRIGGER_NAME']==trig]
    brightest=str(sp[0]['DETECTOR']).strip() if len(sp) else None
    nai=sorted({str(r['DETECTOR']).strip() for r in bk if str(r['DETECTOR']).strip().startswith('n')})
    if brightest not in nai and brightest: nai=sorted(set(nai)|{brightest})
    edet=brightest if brightest in nai else (nai[0] if nai else None)
    if edet is None: rows_summary.append((trig,'-',0,'no NaI')); continue
    bkw={str(r['DETECTOR']).strip():((float(r['BKG_NEG_START']),float(r['BKG_NEG_STOP'])),
         (float(r['BKG_POS_START']),float(r['BKG_POS_STOP']))) for r in bk}
    pre,post=bkw.get(edet, list(bkw.values())[0])
    lo,hi=float(pre[1]),float(post[0])
    tt=load_nai(trig,edet)
    if tt is None or tt.size<30: rows_summary.append((trig,edet,0,'too few events')); continue
    src=tt[(tt>=lo)&(tt<=hi)]
    # background rate from pre+post windows
    bt=(pre[1]-pre[0])+(post[1]-post[0]); bc=int(((tt>=pre[0])&(tt<pre[1])).sum()+((tt>=post[0])&(tt<post[1])).sum())
    brate=bc/bt if bt>0 else 0.0
    note=''
    # tighten to the actual emission interval, then BB on it
    elo,ehi=emission_window(tt,lo,hi,brate)
    src=tt[(tt>=elo)&(tt<=ehi)]
    edges=bb_edges(src,elo,ehi,0.01)
    edges=trim(edges,tt,brate)
    if len(edges)-1<2:                         # under-segmented: finer + permissive
        edges=trim(bb_edges(src,elo,ehi,0.05,dt=0.064),tt,brate); note='dt=64ms,p0=0.05 retry'
    nblk=len(edges)-1
    if nblk<1:
        rows_summary.append((trig,edet,0,'BB gave 0')); continue
    rows=[]
    for det in nai:
        tt_d=load_nai(trig,det)
        if tt_d is None: continue
        p2,po2=bkw.get(det,(pre,post))
        bt2=(p2[1]-p2[0])+(po2[1]-po2[0]); bc2=int(((tt_d>=p2[0])&(tt_d<p2[1])).sum()+((tt_d>=po2[0])&(tt_d<po2[1])).sum())
        br2=bc2/bt2 if bt2>0 else 0.0
        for i in range(nblk):
            s,e=float(edges[i]),float(edges[i+1])
            rows.append((trig,det,i,s,e,net_sig(tt_d,s,e,br2),False,1,2))
    t=Table(rows=rows,names=['TRIGGER_NAME','DETECTOR','BLOCK_INDEX','T_START','T_STOP',
            'SIGNIFICANCE','IS_MERGED','CONSTITUENT_COUNT','POLY_ORDER'])
    t.write(os.path.join(OUT,f'bb_blocks_spectral_{trig}.ecsv'),format='ascii.ecsv',overwrite=True)
    rows_summary.append((trig,edet,nblk,note or f'{len(nai)} dets'))

# report
print(f'{"trigger":13s} {"det":4s} {"Nblk":>4s}  note')
nbad=0
for trig,det,n,note in rows_summary:
    flag='  <-- CHECK' if n<2 else ''
    if n<2: nbad+=1
    print(f'{trig:13s} {str(det):4s} {n:>4d}  {note}{flag}')
print(f'\n{len(rows_summary)} bursts; {nbad} with <2 blocks (need attention). Blocks -> {OUT}')
