#!/usr/bin/env python
"""
Phase 0a (backgrounds): uniform, burst-centered background re-selection for all
106 bursts. The AI-vision windows were mis-placed for 6 bursts (source on pure
background) and over-wide (>120s) for ~37. Here we:
  - locate the burst emission interval from the brightest-NaI 8-900 keV LC
    (global peak + walk-out to background+threshold), cross-checked vs catalog T90;
  - set source = [s_lo-MARGIN, s_hi+MARGIN];
  - set pre/post background windows of width ~BGW (50-150s rule), placed GAP s
    off the source, clipped to the available data span;
  - preserve each burst's detector SET from the original ECSV, only correcting
    the time windows (same times for all detectors of a burst).
Writes results/background_intervals_clean.ecsv (originals untouched) + a report.
"""
import os, glob, warnings
warnings.filterwarnings('ignore')
import numpy as np
from astropy.io import fits
from astropy.table import Table

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(BASE,'data'); RES=os.path.join(BASE,'results')
ORIG=Table.read(os.path.join(RES,'background_intervals_prototype.ecsv'),format='ascii.ecsv')
SINGLE=Table.read(os.path.join(RES,'single_pulse_grbs.ecsv'),format='ascii.ecsv')
MARGIN=3.0; GAP=8.0; BGW=80.0; BGW_MIN=40.0   # margins/widths (s)

def load(trig,det):
    f=sorted(glob.glob(f'{DATA}/{trig}/glg_tte_{det}_*.fit*'))
    if not f: return None,None
    with fits.open(f[0]) as h:
        ev=h['EVENTS'].data;t0=next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
        tt=np.asarray(ev['TIME'])-t0;eb=h['EBOUNDS'].data
        emid=0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
        m=(emid[ev['PHA']]>=8)&(emid[ev['PHA']]<=900)
    return np.sort(tt[m]),(float(tt.min()),float(tt.max()))

def emission_interval(tt, t90=None):
    """T90-style emission interval: peak-find, then 5-95% of background-subtracted
    cumulative counts within a peak-centered, T90-scaled window (cannot run away)."""
    dt=0.256; e=np.arange(-100,600,dt); c=0.5*(e[:-1]+e[1:])
    cnt,_=np.histogram(tt,bins=e); rate=cnt/dt
    pk=int(np.argmax(np.convolve(rate,np.ones(4)/4,mode='same'))); pkt=c[pk]
    T=t90 if (t90 and t90>0) else 20.0
    # generous search window scaled by T90 (FRED: short rise, long decay)
    win_lo,win_hi=pkt-max(15.0,0.8*T), pkt+max(40.0,2.5*T)
    # background from outside the search window
    far=(c<win_lo-10)|(c>win_hi+10)
    brate=np.median(rate[far]) if far.sum()>5 else np.median(rate)
    m=(c>=win_lo)&(c<=win_hi)
    cc=c[m]; net=np.clip(rate[m]-brate,0,None)
    if net.sum()<=0:
        return pkt-0.2*T, pkt+1.2*T, pkt, brate
    cum=np.cumsum(net); cum/=cum[-1]
    s_lo=float(cc[np.searchsorted(cum,0.05)]); s_hi=float(cc[min(np.searchsorted(cum,0.95),len(cc)-1)])
    if s_hi<=s_lo: s_lo,s_hi=pkt-0.2*T,pkt+1.2*T
    return s_lo,s_hi,pkt,brate

BROKEN={'bn090620400','bn090719063','bn100612726','bn100614498','bn110920546','bn200524211'}
rows=[]; rep=[]
trigs=sorted(set(ORIG['TRIGGER_NAME']))
for trig in trigs:
    sub=ORIG[ORIG['TRIGGER_NAME']==trig]
    sp=SINGLE[SINGLE['TRIGGER_NAME']==trig]
    det=str(sp[0]['DETECTOR']).strip() if len(sp) else str(sub[0]['DETECTOR']).strip()
    t90=float(sp[0]['T90']) if len(sp) else None
    tt,span=load(trig,det)
    if tt is None:
        rep.append((trig,'NODATA',0,0,0,0,'keep-old'))
        for r in sub: rows.append((trig,str(r['DETECTOR']).strip(),float(r['BKG_NEG_START']),float(r['BKG_NEG_STOP']),float(r['BKG_POS_START']),float(r['BKG_POS_STOP'])))
        continue
    dmin,dmax=span
    s_lo,s_hi,pkt,brate=emission_interval(tt,t90)
    # clamp emission width to a sane range; keep it peak-centered
    wmax=min(250.0, 3.0*(t90 or 20)+40); wmin=4.0
    if not (wmin<=(s_hi-s_lo)<=wmax) or not (s_lo<=pkt<=s_hi):
        s_lo,s_hi=pkt-0.2*min(t90 or 20,80), pkt+1.2*min(t90 or 20,80)
    src_lo=s_lo-MARGIN; src_hi=s_hi+MARGIN
    # post bkg (usually plenty of room after the burst)
    pos_a=src_hi+GAP; pos_b=min(pos_a+BGW,dmax)
    # pre bkg: whatever clean data exists before the burst (may be short for early bursts)
    neg_b=src_lo-GAP; neg_a=max(neg_b-BGW,dmin); neg_b=max(neg_b,neg_a)
    pre_w=max(0.0,neg_b-neg_a); post_w=max(0.0,pos_b-pos_a)
    # VALIDATE: peak in source, sane width, and enough TOTAL background with one
    # solid side (allows short-pre + long-post for early bursts)
    valid=(neg_b<pkt<pos_a) and (0<(pos_a-neg_b)<=wmax+2*GAP) \
          and (pre_w+post_w)>=60 and max(pre_w,post_w)>=BGW_MIN \
          and neg_a>=dmin-1 and pos_b<=dmax+1
    if valid:
        for r in sub: rows.append((trig,str(r['DETECTOR']).strip(),round(neg_a,3),round(neg_b,3),round(pos_a,3),round(pos_b,3)))
        rep.append((trig,det,round(pkt),round(src_lo),round(src_hi),round(t90 or 0),'NEW'+(' [was BROKEN]' if trig in BROKEN else '')))
    else:
        # fall back to OLD window (never write something worse); flag broken ones
        for r in sub: rows.append((trig,str(r['DETECTOR']).strip(),float(r['BKG_NEG_START']),float(r['BKG_NEG_STOP']),float(r['BKG_POS_START']),float(r['BKG_POS_STOP'])))
        rep.append((trig,det,round(pkt),round(src_lo),round(src_hi),round(t90 or 0),'KEEP-OLD'+(' !!! BROKEN-NEEDS-REVIEW' if trig in BROKEN else '')))

out=Table(rows=rows,names=['TRIGGER_NAME','DETECTOR','BKG_NEG_START','BKG_NEG_STOP','BKG_POS_START','BKG_POS_STOP'])
out.write(os.path.join(RES,'background_intervals_clean.ecsv'),format='ascii.ecsv',overwrite=True)

# report
nnew=sum(1 for r in rep if r[6].startswith('NEW')); nkeep=len(rep)-nnew
print(f'{"trigger":13s}{"det":4s}{"peak":>6s}{"src_lo":>7s}{"src_hi":>7s}{"T90":>6s}{"width":>7s}  status')
for trig,det,pk,sl,sh,t90,status in rep:
    w=sh-sl
    print(f'{trig:13s}{str(det):4s}{pk:>6}{sl:>7}{sh:>7}{t90:>6}{w:>7}  {status}')
print(f'\nwrote results/background_intervals_clean.ecsv ({len(rows)} det-rows, {len(trigs)} bursts)')
print(f'NEW (tightened/fixed): {nnew}   KEEP-OLD (new window failed validation): {nkeep}')
print('REVIEW:', [r[0] for r in rep if 'REVIEW' in r[6]])
